## entry of actual grading.

import grader_util_control as control
# import grader_gather_student_scans as ggss
import grader_run_scanners as grs
import grader_check_env as gce
import os
import time
import json

def main():
    # total_score, comment = gce.run()
    total_score, comment = grs.report()

    # control.log_comment(ggss.gather())
    control.log_comment(comment)
    
    control.finalize(total_score)


if __name__ == "__main__":
    main()