import subprocess
import typing as T

# log the important events.
def log(content:str, new_line=True, file_name="log.txt"):
    if new_line:
        content += "\n"
    with open(file_name, "a") as f:
        f.write(content)

# wraps subprocess.check_output as a string.
# if the proc breaks, return None
def safe_check_output(cmd: T.List[str], _input=None, _timeout=None) -> T.Optional[str]:
    ret = None
    try:
        kwargs = {}
        if _input is not None:
            kwargs["input"] = _input
        if _timeout is not None:
            kwargs["timeout"] = _timeout
        output:bytes = subprocess.check_output(cmd, stderr=subprocess.STDOUT, **kwargs)
        ret = output.decode("utf-8", errors="ignore")
    except subprocess.TimeoutExpired as e:
        log(f"Oops! {cmd} timed-out after {_timeout} seconds.")
    except subprocess.CalledProcessError as e:
        log(f"Oops! {cmd} exited with code {e.returncode}. Maybe you wanna try it outside?")
        # log(e.output.decode("utf-8", errors="ignore"))
    except FileNotFoundError as e:
        log(f"Oops! '{e.filename}' is not on this machine.")
    return ret