# MUST BE CALLED FROM '.'!
import json
import os
import sys

GRADER_TEMP_FOLDER = "./__grader__temp"
DOWNLOAD_TEMP_FOLDER = "./__download__temp"
DOWNLOAD_RESULT_TEMP_FILE = "__download__result.json"

## TODO: THIS IS THE **ONLY FUNCTION** YOU SHOULD MODIFY FOR EACH PROJECT!!!
## contains destructive shell commands, improper use can be dangerous!!!
def grade_at(answer_path):
    # make sure it is executed in the correct path (or there can be disaster!!):
    ## very important!!!!!!!!!!!!!!!!!!!!!!
    cwd = os.getcwd()
    ending = "/grader/project_1" # TODO: change this line across projects
    assert cwd[-len(ending):] == ending, "must be called from project directory"
    # copy student files to a temp folder:
    assert not os.path.exists(GRADER_TEMP_FOLDER)
    assert os.system("cp -r %s %s" % (answer_path, GRADER_TEMP_FOLDER)) == 0
    # copy grading files and folders into that folder:
    # TODO: change these below lists across projects
    grading_files = [ # don't override student
        "grader_main.py",
        "grader_part_1.py",
        "grader_part_2.py",
        "grader_part_3.py",
        "grader_part_4.py",
        "../utils/grader_util_control.py",
        "../utils/grader_util_network_util.py",
        "../utils/grader_util_html_to_json.py"
    ]
    grading_folders = [ # don't override student
        "test_html_files"
    ]
    grading_files_override = [ # please override student
        "rfc2616.html"
    ]
    for f in grading_files:
        assert f not in os.listdir(GRADER_TEMP_FOLDER)
        assert os.system("cp %s %s" % (f, GRADER_TEMP_FOLDER)) == 0
    for f in grading_folders:
        assert f not in os.listdir(GRADER_TEMP_FOLDER)
        assert os.system("cp -r %s %s" % (f, GRADER_TEMP_FOLDER)) == 0
    for f in grading_files_override:
        assert os.system("cp %s %s" % (f, GRADER_TEMP_FOLDER)) == 0
    # switch to the temp directory and do the grading:
    os.chdir(GRADER_TEMP_FOLDER)
    assert os.system("python3 grader_main.py") == 0
    score, comment = get_finalized()
    os.chdir("..")
    # delete stuff
    assert cwd == os.getcwd()
    if os.system("rm -rf %s" % GRADER_TEMP_FOLDER) != 0: # it happens when testing on Moore, strange...
        moore_username = "yjl6286" # TODO: change it if yours are different
        kill_cmd = "ps -Af | grep '%s' | grep 'python3 http_[a-z]' | awk '{ print $2 }' | xargs kill" % moore_username
        assert os.system(kill_cmd) == 0
        assert os.system("rm -rf %s" % GRADER_TEMP_FOLDER) == 0
    # return result
    return score, comment

## -------- below are GRADER's library functions --------
## - they can be **safely copied** from project to project
## - on the other hand, I have no better idea than copying

def get_config():
    with open("./config.json", "r") as f:
        data = json.load(f)
    return data

def get_finalized():
    with open("./FINALIZED.json", "r") as f:
        data = json.load(f)
    return data["score"], data["comment"]

# handle different types of zip files
def unzip_universal(file_name, to_folder_name):
    temp_fn = "__temp__file__type.txt"
    assert os.system("file %s > %s" % (file_name, temp_fn)) == 0
    with open(temp_fn, "r") as f:
        res = f.read()
    assert os.system("rm %s" % temp_fn) == 0
    info = res[len(file_name) + 2:]
    if "gzip" in info or "tar" in info: # unzip with tar
        assert os.system("tar -xf %s -C %s" % (file_name, to_folder_name)) == 0
    elif "RAR" in info: # is RAR (-.-)...(orz)
        assert os.system("unrar x %s %s" % (file_name, to_folder_name)) == 0
    elif "Zip" in info: # is Zip
        assert os.system("unzip %s -d %s" % (file_name, to_folder_name)) == 0
    else: # perhaps not a zip file??
        assert os.system("cp %s %s" % (file_name, to_folder_name)) == 0

def grade_student_solution(student_id):
    config = get_config()
    assignment_id = config["assignment_id"]
    # download solution:
    cwd = os.getcwd() 
    os.chdir("../utils")
    stdout_file = os.path.join(cwd, DOWNLOAD_RESULT_TEMP_FILE)
    print(cwd)
    assert os.system("python3 canvas.py download one %d %d \"%s\" > \"%s\"" % (student_id, assignment_id, cwd, stdout_file)) == 0, "student_id: %s" % student_id
    os.chdir(cwd)
    # if download success, decompress, otherwise zero score
    with open(stdout_file, "r") as f:
        file_name = json.load(f)
    if file_name is None:
        return 0, "No attachment found!\n"
    assert not os.path.exists(DOWNLOAD_TEMP_FOLDER)
    os.mkdir(DOWNLOAD_TEMP_FOLDER)
    unzip_universal(file_name, DOWNLOAD_TEMP_FOLDER)
    # in an extra folder?
    normal_files = [x for x in os.listdir(DOWNLOAD_TEMP_FOLDER) if (x[0] != '.' and x != "__MACOSX")]
    if len(normal_files) == 1:
        real_folder = os.path.join(DOWNLOAD_TEMP_FOLDER, normal_files[0])
        if os.path.isdir(real_folder):
            assert os.system("mv %s/* %s" % (real_folder, DOWNLOAD_TEMP_FOLDER)) == 0
    # grade, clean, and return
    score, comment = grade_at(DOWNLOAD_TEMP_FOLDER)
    assert os.system("rm %s" % DOWNLOAD_RESULT_TEMP_FILE) == 0
    assert os.system("rm -rf %s" % DOWNLOAD_TEMP_FOLDER) == 0
    assert os.system("rm %s" % file_name) == 0
    return score, comment

def load_current_results():
    config = get_config()
    fn = config["results_filename"]
    if not os.path.exists(fn):
        return []
    with open(fn, "r") as f:
        return json.load(f)

def load_late_deduction(student_id):
    config = get_config()
    fn = config["late_filename"]
    with open(fn, "r") as f:
        late_data = json.load(f)
    for student in late_data:
        if student["id"] == student_id:
            deduction = float(student["deduction"])
            assert deduction >= 0.0 and deduction <= 1.0
            return deduction
    return 0.0

def load_students(with_groups=False):
    config = get_config()
    fn = config["students_filename"]
    with open(fn, "r") as f:
        students = json.load(f)
    if not with_groups:
        return students
    fn = config["groups_filename"]
    with open(fn, "r") as f:
        groups = json.load(f)["groups"]
    return students, groups

def pretty_json(obj):
    return json.dumps(obj, indent=2, sort_keys=True)

def safe_update_results(new_result):
    config = get_config()
    fn = config["results_filename"]
    fn_backup = fn + ".backup"
    # make a backup
    if os.path.exists(fn):
        assert not os.path.exists(fn_backup)
        assert os.system("cp %s %s" % (fn, fn_backup)) == 0
    # write the original file
    with open(fn, "w") as f:
        f.write(pretty_json(new_result))
    # delete the backup file
    if os.path.exists(fn_backup):
        assert os.system("rm %s" % fn_backup) == 0

def apply_late_deduction(deduction, score, comment):
    score -= 100 * deduction
    if deduction > 0:
        comment += "Final score is %s%% after late deduction.\n" % score
    return score, comment

## ------------ below are GRADER's interfaces ------------
## - they can be **safely copied** from project to project
## - on the other hand, I have no better idea than copying

# grade one student and update the results:
def grade_one_student(student_id):
    # assure the student exists (and BTW get hir name):
    students = load_students()
    for student in students:
        if student["id"] == student_id:
            student_name = student["name"]
            break
    else: # not found
        assert False, "student not found"
    # grade & apply deduction:
    deduction = load_late_deduction(student_id)
    score, comment = grade_student_solution(student_id)
    score, comment = apply_late_deduction(deduction, score, comment)
    print(comment)
    # update result:
    struct = {
        "is_valid": True,
        "id": student_id,
        "name": student_name,
        "score": score,
        "comment": comment
    }
    results = load_current_results()
    for i in range(len(results)):
        if student_id == results[i]["id"]: # then override
            results[i] = struct
            print("%s(%d): score overriden!" % (student_name, student_id))
            break
    else: # then append
        results.append(struct)
        print("%s(%d): score appended!" % (student_name, student_id))
    safe_update_results(results)
    return

# regrade a group:
def regrade_group(student_id):
    assert "regrade.json" in os.listdir()
    students, groups = load_students(with_groups=True)
    # assure the student exists (and BTW get hir name):
    for student in students:
        if student["id"] == student_id:
            student_name = student["name"]
            break
    else: # not found
        assert False, "student not found"
    # find the group of the student:
    for group in groups:
        if any(student_id == member_id for member_id in group["members"]):
            break
    else: # not found
        assert False, "group not found"
    # grade & apply deduction:
    deduction = load_late_deduction(student_id)
    score, comment = grade_student_solution(student_id)
    score, comment = apply_late_deduction(deduction, score, comment)
    print(comment)
    # update result:
    import time
    now = time.ctime()
    with open("regrade.json", "r") as f:
        try:
            regrade_list = json.load(f)
        except:
            regrade_list = []
    for member_id in group["members"]:
        for student in students:
            if student["id"] == member_id:
                member_name = student["name"]
                break
        regrade_list.append({
            "posted": False,
            "regraded_at": now,
            "id": member_id,
            "name": member_name,
            "score": score,
            "comment": comment
        })
    with open("regrade.json", "w") as f:
        json.dump(regrade_list, f, indent=2)

def regrade_to_result():
    with open("regrade.json", "r") as f:
        items = json.load(f)
    filtered_items = [item for item in items if not item["posted"]]
    for item in items:
        item["posted"] = True
    with open("regrade.json", "w") as f:
        json.dump(items, f, indent=2)
    for item in filtered_items:
        item["is_valid"] = True
    with open("results.json", "w") as f:
        json.dump(filtered_items, f, indent=2)

# grade all students / all groups
def grade_all_students(with_groups=True, ignore_graded=True):
    # fetch student list / group list / result list
    if with_groups:
        students, groups = load_students(with_groups=True)
        leader_set = set(g["leader"] for g in groups)
        students = [s for s in students if s["id"] in leader_set]
    else:
        students = load_students(with_groups=False)
    if ignore_graded:
        results = [] # restart from scrach!
    else:
        results = [r for r in load_current_results() if r["is_valid"]]
        skip_set = set(r["id"] for r in results)
        students = [s for s in students if s["id"] not in skip_set]
    # start grading & writing results:
    for student in students:
        student_id = student["id"]
        student_name = student["name"]
        deduction = load_late_deduction(student_id)
        score, comment = grade_student_solution(student_id)
        score, comment = apply_late_deduction(deduction, score, comment)
        print(comment)
        struct = {
            "is_valid": True,
            "id": student_id,
            "name": student_name,
            "score": score,
            "comment": comment
        }
        results.append(struct)
        print("%s(%d): score appended!" % (student_name, student_id))
        safe_update_results(results) # update once every student, so data keeps when program crashes
    return

# should be called the last
# copy score from leader to all group members, and give a zero to un-grouped students
def copy_grades():
    # loading old data:
    students, groups = load_students(with_groups=True)
    old_results = load_current_results()
    id_to_results = {}
    for results in old_results:
        id_to_results[results["id"]] = results
    # temporarily shallow copy among members:
    for group in groups:
        leader = group["leader"]
        for member in group["members"]:
            id_to_results[member] = id_to_results[leader]
    # build for everyone, BTW pick out un-grouped students:
    results = []
    for student in students:
        student_id = student["id"]
        student_name = student["name"]
        if student_id in id_to_results:
            score = id_to_results[student_id]["score"]
            comment = id_to_results[student_id]["comment"]
        else:
            score = 0
            comment = "You are not found in any group. Cannot grade.\n"
        results.append({
            "is_valid": True,
            "id": student_id,
            "name": student_name,
            "score": score,
            "comment": comment
        })
    safe_update_results(results)
    return

# grade the standard solution, and print the results:
def test_grade():
    config = get_config()
    score, comment = grade_at(config["solution_path"])
    print("-----------------------------------")
    print("Score: ", score)
    print(comment)

def filter_score_changed_students(file_old, file_new):
    with open(file_old, "r") as f:
        results_old = json.load(f)
    with open(file_new, "r") as f:
        results_new = json.load(f)
    d = {}
    for r in results_old:
        d[r["id"]] = r["score"]
    results_filtered = [r for r in results_new if d[r["id"]] != r["score"]]
    with open(file_new, "w") as f:
        json.dump(results_filtered, f, indent=2)
    return

# HIGHLIGHT MOMENT!! Upload all scores to Canvas!!
def upload_all(regrade=False, as_percent=True):
    # firstly, check that all students are graded...
    students = load_students(with_groups=False)
    results = load_current_results()
    if not regrade:
        assert len(students) == len(results), "not all students graded"
    assert all(r["is_valid"] for r in results), "not all students valid"
    # then, switch to the right folder... and upload!!
    config = get_config()
    assignment_id = config["assignment_id"]
    results_fn = os.path.join(os.getcwd(), config["results_filename"])
    cwd = os.getcwd()
    os.chdir("../utils")
    assert os.system("python3 canvas.py ls students") == 0
    os.chdir(cwd)
    students = load_students(with_groups=False)
    assert all(r["id"] in [s["id"] for s in students] for r in results), "student list changed!"
    os.chdir("../utils")
    assert os.system("python3 canvas.py upload %s all \"%s\" %s" % ("-p" if as_percent else "", results_fn, assignment_id)) == 0
    return

# Copy grader utils into the folder; this will make cross-ref easy when writing graders.
# Anyway before you "git push", you should remove them.
def development_mode_start():
    assert os.path.exists("GRADER.py"), "wrong folder??"
    assert os.system("cp ../utils/grader_util_*.py ./") == 0

# override the util files after development
def development_mode_end(discard_changes=False):
    assert os.path.exists("GRADER.py"), "wrong folder??"
    if discard_changes:
        assert input("Discard all changes to utils? Type 'yes' to continue: ") == "yes"
        assert os.system("rm ./grader_util_*.py") == 0
    else:
        assert input("Apply all changes to utils and override old ones? Type 'yes' to continue: ") == "yes"
        assert os.system("mv ./grader_util_*.py ../utils/") == 0

# clean the workspace after crash:
def clean():
    assert os.path.exists("GRADER.py"), "wrong folder??"
    moore_username = "gzp4143" # TODO: change it if yours are different
    kill_cmd = "ps -Af | grep '%s' | grep 'python3 http_[a-z]' | awk '{ print $2 }' | xargs kill" % moore_username
    os.system(kill_cmd)
    for s in [DOWNLOAD_TEMP_FOLDER, GRADER_TEMP_FOLDER]:
        os.system("rm -r %s" % s)
    for s in [DOWNLOAD_RESULT_TEMP_FILE, "DOWNLOAD_*", "*.backup"]:
        os.system("rm %s" % s)


# Command line of this module:
CMD_LINE = {
    "": lambda: print("Command lines:\n", CMD_LINE),
    "grade": { # these names below are quite self-explanatory
        "one": lambda student_id: grade_one_student(int(student_id)),
        "all": {
            "groups": lambda: grade_all_students(with_groups=True, ignore_graded=True),
            "individuals": lambda: grade_all_students(with_groups=False, ignore_graded=True),
        },
        "remaining": {
            "groups": lambda: grade_all_students(with_groups=True, ignore_graded=False),
            "individuals": lambda: grade_all_students(with_groups=False, ignore_graded=False),
        },
        "test": lambda: test_grade(), # will grade the standard solution (provided by TA?)
    },
    "regrade": lambda student_id: regrade_group(int(student_id)),
    "translate": lambda: regrade_to_result(),
    "copy": lambda: copy_grades(), # for group assignments, will copy grade among members
    "clean": lambda: clean(), # will clean the temporary files after a crash
    "filter": lambda file_old, file_new: filter_score_changed_students(file_old, file_new),
    "upload": {
        "": lambda: upload_all(as_percent=True), # will upload grades of all students
        "-f": lambda: upload_all(regrade=True, as_percent=True)
    },
    "dev": { # development mode
        "": lambda: development_mode_start(), # just an alias...
        "start": lambda: development_mode_start(),
        "discard": lambda: development_mode_end(discard_changes=True),
        "finish": lambda: development_mode_end(discard_changes=False),
    },
}

if __name__ == "__main__":
    # extract commands and parameters:
    args = sys.argv[1:]
    cmd = CMD_LINE
    while type(cmd) is dict:
        key = "" if len(args) == 0 else args[0]
        cmd = cmd[key]
        args = args[1:]
    cmd(*args)
