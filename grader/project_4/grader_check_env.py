# part 1, environment checking

import os
import grader_util_control as control
import json

# simply return:
# score: 0 for OK, 1 for problematic
# comment: a tuple (requirement missing/misspelled?, # lines, missing files?)
# the number of lines in requirements.txt

def run() -> (int, str):
    file_name = "requirements.txt"
    if file_name not in os.listdir():
        req_missing = 1
        file_name = "requirement.txt"
    else:
        req_missing = 0

    if file_name not in os.listdir():
        n_lines = -1
    else:
        with open(file_name, "r") as f:
            lines = f.readlines()
        lines = [l.strip() for l in lines]
        lines = [l for l in lines if len(l) > 0]
        n_lines = len(lines)

    if "public_dns_resolvers.txt" not in os.listdir():
        dns_missing = 1
    else:
        dns_missing = 0
    
    if req_missing > 0 or dns_missing > 0 or n_lines == 0 or n_lines > 30:
        score = 1
    else:
        score = 0

    comment = f"{req_missing} {n_lines} {dns_missing}"
    return score, comment