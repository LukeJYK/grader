## entry of actual grading.

import grader_util_control as control
import grader_util_network_util as network_util
import os
import time
import json

def validity_check():
    student_files = ["distance_vector_node.py", "link_state_node.py"]
    for f in student_files:
        if f not in os.listdir():
            control.log_comment("File not found: %s" % f)
            return 0
    return 100

def parse_temp_logging():
    with open("_grader_temp_logging_file.txt", "r") as f:
        lines = f.readlines()
    points = 0
    done = False
    message_count = None
    for line in lines:
        if "correct" in line:
            points += 1
        elif "done" in line:
            done = True
            message_count = int(line.split()[1])
    return points, done, message_count

def grade_case(algo, event_filename, points_count, time_limit, message_limit):
    start_time = time.time()
    assert os.system("touch _grader_temp_logging_file.txt") == 0

    exit_code = control.run_foreground(["python3", "sim.py", algo, event_filename],
        timeout_seconds=time_limit, read_output=False, killable=True)
    time_taken = time.time() - start_time

    points, done, message_count = parse_temp_logging()
    assert os.system("rm _grader_temp_logging_file.txt") == 0

    normal_exit = done and (exit_code == 0)
    too_many_messages = (message_count is not None) and (message_count > message_limit)
    report = {
        "seconds_taken": int(time_taken),
        "normal_exit": normal_exit,
        "message_count": message_count,
        "too_many_messages": too_many_messages,
        "points": points,
        "full_points":  points_count,
    }
    time_out = exit_code is None
    abnormal_exit = (not time_out) and (exit_code != 0)

    # calculate score
    msg = ""
    def foo(msg):
        if too_many_messages or (not normal_exit):
            if abnormal_exit: msg += "(Abnormal Exit)"
            if time_out: msg += "(Time Out)"
            if too_many_messages: msg += "(Too Many Messages)"
        return msg

    if points == 0:
        score = 0
        msg += "(Incorrect Solution)"
        msg = foo(msg)
    elif points < points_count:
        score = 1
        msg += "(Partially Correct Solution)"
        msg = foo(msg)
    else:
        msg = foo(msg)
        if too_many_messages or (not normal_exit): score = 3
        else: score = 5

    if score > 0:
        if time_taken > time_limit:
            score = 1
            msg += "(Time Out)"
        else:
            real_limit = time_limit / 1.1
            if time_taken > real_limit:
                multiplier = max(0, min(1, (1.1 - (time_taken / real_limit)) * 10))
                score = max(1, float("%.1f" % (score * multiplier)))
                msg += "(Near-Boundary Time Out)"

    control.log_comment("[+%.1f] %s @ %s" % (score, algo, event_filename))
    if len(msg) > 0:
        control.log_comment("    %s" % msg)
    return score, report

def code_check():
    from difflib import SequenceMatcher
    student_files = ["distance_vector_node.py", "link_state_node.py"]
    with open(student_files[0], "r") as f:
        text1 = f.read()
    with open(student_files[1], "r") as f:
        text2 = f.read()
    ratio = SequenceMatcher(lambda x: x == " ", text1, text2).ratio()
    print("Code Similarity: %s" % ratio)

    import_lines = []
    for t in text1, text2:
        for line in t.splitlines():
            if "import" in line:
                import_lines.append(line)
    return ratio, import_lines


def main():
    total_score = 0

    check_points_count = [1, 2, 1, 2, 3, 2, 1, 2, 4, 1]
    test_files = ["./test_cases/case_%d.event" % (d+1) for d in range(10)]
    # time_limit_seconds = [1.1 * t for t in [70, 70, 70, 70, 70, 70, 70, 490, 70, 730]]
    time_limit_seconds = [1.1 * t for t in [600, 600, 600, 600, 600, 600, 600, 600, 600, 730]]
    message_limit = [x * 1000 for x in [50, 50, 50, 50, 50, 50, 50, 2000, 50, 2000]]

    if True:
        for algo in "LINK_STATE", "DISTANCE_VECTOR":
            for i in range(10):
                print("Grading %s @ %s" % (algo, test_files[i]))
                tick = time.time()
                score, report = grade_case(algo, test_files[i], check_points_count[i], time_limit_seconds[i], message_limit[i])
                tock = time.time()
                print("Score: %.1f%%, Time: %.1fs\n" % (score, tock - tick))
                total_score += score
                # reports.append(report)

    # some code static analysis:
    if True:
        ratio, import_lines = code_check()
        final = {
            "code_similarity": ratio,
            "import_lines": import_lines
        }

    # input("before grading pause...")
    # control.log_comment("Your total score is %.1f%%." % total_score)
    control.log_comment("## " + json.dumps(final)) ## use this line for static analysis later... I know this is hacky...
    control.finalize(total_score)
    # input("after grading pause...")


if __name__ == "__main__":
    main()