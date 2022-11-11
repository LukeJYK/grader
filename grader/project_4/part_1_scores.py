# deductions for:
# 1. missing/empty or too-large requirements.txt (-2 pts; no one is missing it, as I see it)
# 2. program crash / timeout / malfunction (up to -6 pts; but there are no people doing this anyway)
# 3. misspelled requirements.txt (-1 pts)
# 4. missing public_dns_resolvers.txt (-0 pts) // due to my flawed logic, I cannot really check now, so let's forgive them...

# input file: results_part_1.json

# Your requirements.txt is way too big than neccesary,
# which even include a lot of 3rd libraries that cannot be installed on Moore!

import json

def main():
    with open("results_part_1.json", "r") as f:
        data = json.load(f)
    ret = []
    
    for student in data:
        score = 10
        comment = "Part 1 grading:\n"
        a, b, _ = student["comment"].split(" ")
        if int(a) == 1:
            score -= 1
            comment += "-1.0: Mis-spelled requirements.txt.\n"
        if int(b) > 30:
            score -= 2
            comment += "-2.0: Your requirements.txt is way too big than neccesary. Note that not all libraries can be installed on Moore!\n"
        comment += f"Part 1 result: {score:.1f}/10.0 received.\n"

        ret.append({
            "id": student["id"],
            "name": student["name"],
            "is_valid": True,
            "score": score,
            "comment": comment,
        })

    with open("scores_part_1.json", "w") as f:
        json.dump(ret, f, indent=2)

if __name__ == "__main__":
    main()