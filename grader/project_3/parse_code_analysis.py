import json

def main():
    link = "https://canvas.northwestern.edu/courses/105409/gradebook/speed_grader?assignment_id=662118&student_id="
    with open("./code_analysis.json", "r") as f:
        students = json.load(f)
    imports = open("./student_imports.txt", "w")
    code_sims = open("./student_code_sims.txt", "w")

    for student in students:
        comment = student["comment"]
        attr = json.loads(comment.split("\n")[1][3:])
        name = student["name"]
        student_id = student["id"]
        code_sim = attr["code_similarity"]
        if code_sim > 0.2:
            code_sims.write("%s (%d): Similarity=%.3f\n%s%d\n\n" % (name, student_id, code_sim, link, student_id))
        import_lines = attr["import_lines"]
        imports.write("%s (%d):\n%s%d\n" % (name, student_id, link, student_id))
        for line in import_lines:
            imports.write(line + "\n")
        imports.write("\n\n")

    imports.close()
    code_sims.close()

if __name__ == "__main__":
    main()
    
