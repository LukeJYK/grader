import subprocess
import traceback
import time
import sys
import json

GRADER_SKIP_EXIT_CODE = 41
GRADER_ABORT_EXIT_CODE = 42

# exception that needs human inspect.
class GraderException(Exception):
    def __init__(self, message=None):
        self.message = "GraderException" + ("" if message is None else ": " + message)
        traceback.print_exc()
    def __str__(self):
        return self.message

# human to decide whether skip & log, abort, or manual
def handle_grader_exception(err):
    log_comment(str(err))
    return

    answer = input("\nPlease choose an action:\n"
        + "1) [PLEASE TYPE 'skip'] to skip the current student, log this case, and start grading another student (if any).\n"
        + "2) [PLEASE TYPE 'abort'] to exit the entire grading program now.\n"
        + "3) [PLEASE TYPE 'manual'] to type in a manual score and comment for this part of this student\n"
        + "> ")
    while True:
        if answer == "skip":
            msg = input("\nPlease type in a memo to be recorded in the log file:\n> ")
            with open("./grader_exception_log.txt", "w") as f:
                f.write(msg)
            sys.exit(GRADER_SKIP_EXIT_CODE)
        if answer == "abort":
            sys.exit(GRADER_ABORT_EXIT_CODE)
        if answer == "manual":
            validated = False
            while not validated:
                score = input("\nPlease type in a score:\n> ")
                try:
                    score = float(score)
                    validated = True
                except:
                    pass
            comment = input("\nPlease type in the comment:\n> ")
            return score, comment
        answer = input("\nPlease type 'skip', 'abort' or 'manual'. \n> ")


# run a external program in foreground (e.g. the caller waits until the program exits).
# return:
#   (nullable int) exit_code ("None" when timeout). 
#   (nullable str) stdout_text, stderr_text (only when read_output=True)
def run_foreground(args, f_in=None, f_out="./temp_stdout.txt", f_err="./temp_stderr.txt",
  timeout_seconds=3600, read_output=True, killable=False):
    from signal import SIGINT
    stdin, stdout, stderr, exit_code = None, None, None, None
    ## start the program:
    try:
        stdin = open(f_in, "r") if f_in else None
        stdout = open(f_out, "w") if f_out else None
        stderr = open(f_err, "w") if f_err else None
        proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr)
    except IOError as err:
        raise GraderException("file open error")
    ## wait for the program to finish:
    is_timeout = False
    try:
        proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as err: # send SIGINT; otherwise kill and report this part
        is_timeout = True
        print(err)
        proc.send_signal(SIGINT)
    if is_timeout:
        try:
            proc.wait(timeout=10) # wait 10 more seconds to make the program exit elegantly
        except subprocess.TimeoutExpired as err:
            proc.kill() # brute-force kill
            if not killable:
                raise GraderException("killed students' program brutally")
    else:
        exit_code = proc.returncode
    ## clean things up:
    for fp in stdin, stdout, stderr:
        if fp: fp.close()
    if read_output:
        stdout_text = _read_optional(f_out)
        stderr_text = _read_optional(f_err)
        return exit_code, stdout_text, stderr_text
    else:
        return exit_code


# these following functions run a external program in **background**. You should manually stop it.
# return:
#   (nullable int) exit_code ("None" when timeout). 
#   (nullable str) stdout_text, stderr_text (only when read_output=True)
class MyProcess:
    def __init__(self, proc, stdin, stdout, stderr, f_in, f_out, f_err, killable):
        self.proc = proc
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.f_in = f_in
        self.f_out = f_out
        self.f_err = f_err
        self.killable = killable

def run_background_start(args, f_in=None, f_out="./temp_stdout.txt", f_err="./temp_stderr.txt", killable=False):
    stdin, stdout, stderr = None, None, None
    try:
        stdin = open(f_in, "r") if f_in else None
        stdout = open(f_out, "w") if f_out else None
        stderr = open(f_err, "w") if f_err else None
        start_time = time.time()
        proc = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr)
        return MyProcess(proc, stdin, stdout, stderr, f_in, f_out, f_err, killable)
    except IOError as err:
        raise GraderException("file open error")

def run_background_liveness(my_process):
    my_process.proc.poll()
    return my_process.proc.returncode is None

def run_background_interrupt(my_process, delay_seconds=0, read_output=True):
    from signal import SIGINT
    exit_code = None
    is_timeout = False
    try:
        my_process.proc.wait(timeout=delay_seconds)
    except subprocess.TimeoutExpired as err: # send SIGINT; otherwise kill and report this part
        is_timeout = True
        if my_process.killable:
            my_process.proc.kill()
        else:
            my_process.proc.send_signal(SIGINT)
    if is_timeout:
        try:
            my_process.proc.wait(timeout=3) # wait 3 more seconds to make the program exit elegantly
        except subprocess.TimeoutExpired as err:
            my_process.proc.kill() # brute-force kill
            raise GraderException("killed students' program brutally")
    else:
        exit_code = my_process.proc.returncode
    ## clean things up:
    for fp in my_process.stdin, my_process.stdout, my_process.stderr:
        if fp: fp.close()
    if read_output:
        stdout_text = _read_optional(my_process.f_out)
        stderr_text = _read_optional(my_process.f_err)
        return exit_code, stdout_text, stderr_text
    else:
        return exit_code


# return filename's content, or None if it does not exist.
# nullable(str) -> nullable(str)
def _read_optional(filename):
    if filename is None:
        return None
    try:
        with open(filename, "r") as f:
            return f.read()
    except IOError:
        return None
    except UnicodeDecodeError: # UnicodeDecodeError: 'utf-8' codec can't decode byte ...
        with open(filename, "rb") as f:
            return str(f.read())


# log the comment to be send to a student.
def log_comment(comment, new_line=True, filename="./temp_comment.log"):
    with open(filename, "a") as f:
        if new_line:
            comment += "\n"
        f.write(comment)

# finalize grading:
def finalize(score, comment_filename="./temp_comment.log"):
    with open(comment_filename, "r") as f:
        comment = f.read()
    data = {
        "score": score,
        "comment": comment
    }
    with open("FINALIZED.json", "w") as f:
        json.dump(data, f, indent=2)


## ------------------ obsolete functions ------------------

# pauses the program somewhere and waits for human verification.
def pause(message):
    raise GraderException ## this line is added because we don't want to mess with the autograder at all!!!

    answer = input(message + "\nDo you agree with the autograder? (y/n) > ")
    while True:
        if answer == "y":
            return
        if answer == "n":
            raise GraderException
        answer = input("Please answer y or n. > ")


## ------------------ test-only area below ------------------

def test():
    print(run_foreground(["python3", "test_timeout.py"], timeout_seconds=10))
    #execute(["python3", "test_timeout.py"])

if __name__ == "__main__":
    test()