# Show the student's report via editor, and manually input the scores via terminal.
# The program is stateless, but the output file is written per student, so it can break & continue in the granularity of student.

# An example grading context:
#  - Window 1: text viewer/editor (static), to show the reference report (Optional, if you can remember it in heart...)
#  - Window 2: text viewer/editor (dynamic), to show the student's report
#  - Window 3: terminal, to type in the scores
#
# An example in practice:
#  - I use VS Code, so Window 2 & 3 is integrated in a fullscreen; use another screen to show the reference report.

import json
import os

f_in = "results_part_3.json"
f_out = "scores_part_3.json"

f_display = "current_report.txt"

def load_progress():
    if f_out not in os.listdir():
        return []
    with open(f_out, "r") as f:
        data = json.load(f)
    return data

def write_progress(data):
    with open(f_out, "w") as f:
        json.dump(data, f, indent=2)

def load_results():
    with open(f_in, "r") as f:
        data = json.load(f)
    return data

def next_result_to_grade(results, progress):
    graded_id = {p["id"] for p in progress}
    for r in results:
        if r["id"] not in graded_id:
            return r
    return None


def ask_for_score(part_max, part_description):
    print(part_description)
    while True:
        try:
            res = input(f"   Please input the score (out of {part_max:.1f}): ")
            if len(res) == 0: # just hit enter if using the max
                print(f"   Using the default: {part_max:.1f}")
                score = part_max  
            else:
                score = float(res)
                if score > part_max:
                    raise
            return score
        except:
            print("Invalid score, try again.")

def ask_for_confirmation(max_score, curr_score):
    print(f"\nThe student got {curr_score:.1f}/{max_score:.1f}.")
    s = input("To confirm, just hit [ENTER]; to reset, type whatever: ")
    return len(s) == 0


def grade_one(result):
    report = result["comment"]
    with open(f_display, "w") as f:
        f.write(report)
    print(f"Now grading {result['id']} @ {f_display}!")
    max_score = 18
    confirmed = False
    while not confirmed:
        scores = [
            ask_for_score(2, "1. A textual or tabular listing of all the information returned in Part 2, "
                "with a section for each domain."),
            ask_for_score(3, "2. A table showing the RTT ranges for all domains, "
                "sorted by the minimum RTT (ordered from fastest to slowest)."),
            ask_for_score(2, "3. A table showing the number of occurrences for each observed root certificate authority "
                "(from Part 2i), sorted from most popular to least."),
            ask_for_score(2, "4. A table showing the number of occurrences of each web server (from Part 2d), "
                "ordered from most popular to least."),
            ask_for_score(4, "5. A table showing the percentage of scanned domains supporting: "
                "each version of TLS, plain http, https redirect, hsts, ipv6."),
            ask_for_score(5, "6. Rate the general readability & attractivity."),
        ]
        if ask_for_confirmation(max_score, sum(scores)):
            confirmed = True
        else:
            print("Well, let's restart!")
    parts = [
        (2, "1. A textual or tabular summary"),
        (3, "2. RTT ranges"),
        (2, "3. Popular root CA's"),
        (2, "4. Popular web servers"),
        (4, "5. Support percentages"),
        (5, "Readability & attractivity"),
    ]
    comment = "Part 3 grading:\n"
    for i, part in enumerate(parts):
        s, d = part
        comment += f"{scores[i]:.1f}/{s:.1f} for {d}\n"
    comment += f"Part 3 result: {sum(scores):.1f}/{max_score:.1f} received.\n"
    print(f"Done grading {result['id']}!\n")
    return {
        "id": result["id"],
        "name": result["name"],
        "is_valid": True,
        "score": sum(scores),
        "comment": comment,
    }


def main():
    progress = load_progress()
    results = load_results()
    while True:
        nxt = next_result_to_grade(results, progress)
        if nxt is None:
            print("No more results to grade, exiting.")
            return
        progress.append(grade_one(nxt))
        write_progress(progress)

if __name__ == "__main__":
    main()