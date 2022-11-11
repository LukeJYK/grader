## entry of actual grading.

import grader_util_control as control
import grader_part_1
import grader_part_2
import grader_part_3
import grader_part_4

def main():
    score = 0
    # input("before grading pause...")
    for part in grader_part_1, grader_part_2, grader_part_3, grader_part_4:
    # for part in grader_part_1, :
        score += part.main()
    control.log_comment("Your total score is %s out of 125 raw points." % score)
    score *= 0.8
    control.log_comment("It scales to %.1f%% out of 100 percents." % score)
    if False and score < 3:
        try:
            input("pause for manual check: is our deduction correct? press anything to continue...")
        except EOFError: # Comment: I don't know why EOFError today. Was good yesterday. -- 2/5/2020
            print("Seems like an OS error. Reopening the terminal might solve the problem.")
    control.finalize(score) ## This line is important and must be there!
    # input("after grading pause...")

if __name__ == "__main__":
    main()