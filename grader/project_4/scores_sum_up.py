import json

def main():
    with open("scores_part_1.json", "r") as f:
        students = json.load(f)

    id_to_score = {s["id"]: s["score"] for s in students}
    id_to_comments = {s["id"]: [s["comment"]] for s in students}

    for f_name in "scores_part_2.json", "scores_part_3.json":
        with open(f_name, "r") as f:
            sts = json.load(f)
        for s in sts:
            id_to_score[s["id"]] += s["score"]
            id_to_comments[s["id"]].append(s["comment"])

    for s in students:
        s["score"] = id_to_score[s["id"]]
        id_to_comments[s["id"]].append(f"Your final score is {id_to_score[s['id']]:.1f}%.\n")
        s["comment"] = "\n".join(id_to_comments[s["id"]])

    with open("results.json", "w") as f:
        json.dump(students, f, indent=2)

if __name__ == "__main__":
    main()