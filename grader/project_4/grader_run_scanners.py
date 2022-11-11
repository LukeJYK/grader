# hack the "score" to represent successfulness.
# 0 = success, non-zero = error
import os
import grader_util_control as control
import json

def run() -> (int, str):
    # ret = os.system("python3 -m venv tmp_env")
    # if ret != 0:
    #     return 1, str(ret)

    # # ret = os.system(". tmp_env/bin/activate.csh")
    # ret = os.system(". tmp_env/bin/activate")
    # if ret != 0:
    #     return 2, str(ret)

    # Just use my own env instead!! Just check requirements.txt.
    ret = os.system("pip3 install --user -r requirements.txt")
    if ret != 0:
        # return 3, str(ret)
        input("Please change student's requirements.txt file, then retry.")
        assert os.system("pip3 install --user -r requirements.txt") == 0
    
    if "scan.py" not in os.listdir():
        return 4, "PY file not found"

    # input_file = "test_test_websites.txt"
    input_file = "test_websites.txt"

    output_file = "out_nonce_2333.json" # make it un-guess-able for students
    timeout_seconds = 60*60 # 1 hour

    print("PROGRAM START!!\n\n")
    exit_code = control.run_foreground(["python3", "scan.py", input_file, output_file],
        timeout_seconds=timeout_seconds, f_out=None, f_err=None, read_output=False, killable=True)
    print("\n\nPROGRAM END!!")
    
    if exit_code is None:
        return 5, "time out"

    if exit_code != 0:
        # return 6, str(exit_code)
        input("Please copy the missing files, then retry.")
        print("PROGRAM START!!\n\n")
        exit_code = control.run_foreground(["python3", "scan.py", input_file, output_file],
            timeout_seconds=timeout_seconds, f_out=None, f_err=None, read_output=False, killable=True)
        print("\n\nPROGRAM END!!")
        if exit_code is None:
            return 5, "time out"
        assert exit_code == 0

    if output_file not in os.listdir():
        return 7, "output file not found"

    try:
        with open(output_file, "r") as f:
            obj = json.load(f)
        comment = json.dumps(obj)
        return 0, comment
    except:
        return 8, "error reading JSON"

    assert False, "unreachable"


def report():
    ret = os.system("pip3 install --user -r requirements.txt")
    if ret != 0:
        print("requirement install failure, skip...")
    
    if "report.py" not in os.listdir():
        return 4, "PY file not found"

    input_file = "report_input.json"
    output_file = "report_10086.txt"
    timeout_seconds = 60

    print("PROGRAM START!!\n\n")
    exit_code = control.run_foreground(["python3", "report.py", input_file, output_file],
        timeout_seconds=timeout_seconds, f_out=None, f_err=None, read_output=False, killable=True)
    print("\n\nPROGRAM END!!")
    
    if exit_code is None:
        return 5, "time out"

    if exit_code != 0:
        # try their own output instead
        with open("../results_part_2.json", "r") as f:
            data = json.load(f)
        while True:
            student_id = input("Please input the student ID, and then continue: ")
            if any(str(s["id"]) == student_id for s in data):
                break
            print("invalid ID, please re-input!")
        for s in data:
            if str(s["id"]) == student_id:
                content = s["comment"]
                break
        with open(input_file, "w") as f:
            f.write(content)
        exit_code = control.run_foreground(["python3", "report.py", input_file, output_file],
            timeout_seconds=timeout_seconds, f_out=None, f_err=None, read_output=False, killable=True)

    if output_file not in os.listdir():
        return 7, "output file not found"

    try:
        with open(output_file, "r") as f:
            comment = f.read()
        return 0, comment
    except:
        return 8, "error reading file"

    assert False, "unreachable"