import requests
import json
import sys
import os

CANVAS_HOST = "https://canvas.northwestern.edu"

def pretty_json(obj):
    return json.dumps(obj, indent=2, sort_keys=True)

def get_config():
    with open("canvas_config.json", "r") as f:
        config = json.load(f)
    return config

def get_token(config):
    with open(config["token_file"], "r") as f:
        token = f.read().strip()
    return token

def manually_confirm(message):
    message += "\nType 'yes' to continue, otherwise abort.\n> "
    if input(message) != "yes":
        assert False, "confirmation failure"

def get_student_list(forced_refresh=False):
    config = get_config()
    student_list_fn = config["students_list_file"]
    if forced_refresh or not os.path.exists(student_list_fn): # then download again!
        sys.stderr.write("re-fetching student info...")
        path = "/api/v1/courses/%s/students" % config["course_id"]
        query = "?access_token=%s" % get_token(config)
        response = requests.get(CANVAS_HOST + path + query)
        assert response.status_code == 200, "Failed to get student list"
        student_list = [s for s in json.loads(response.text) if s["name"] != "Test Student"]
        with open(student_list_fn, "w") as f:
            f.write(pretty_json(student_list))
        return student_list
    else:
        with open(student_list_fn, "r") as f:
            student_list = json.load(f)
        return student_list

def double_check_assignment_id(assignment_id):
    config = get_config()
    path = "/api/v1/courses/%s/assignments/%s" % (config["course_id"], assignment_id)
    query = "?access_token=%s" % get_token(config)
    response = requests.get(CANVAS_HOST + path + query)
    assert response.status_code == 200, "Failed to check assignment id"
    name = json.loads(response.content)["name"]
    manually_confirm("Double check: the assignment (id: %s) you are grading is:\n'%s'." % (assignment_id, name))
    return

# get the whole submission page
def get_submission(student_id, assignment_id, include_comments=False):
    config = get_config()
    path = "/api/v1/courses/%s/assignments/%s/submissions/%s" % (config["course_id"], assignment_id, student_id)
    query = "?access_token=%s" % get_token(config)
    if include_comments:
        query += "&include[]=submission_comments"
    response = requests.get(CANVAS_HOST + path + query)
    assert response.status_code == 200, "Failed to get submission page"
    submission = json.loads(response.text)
    return submission

# download submission attachment, return filename or None
def download_submission(student_id, assignment_id, download_path):
    submission = get_submission(student_id, assignment_id)
    if "attachments" not in submission:
        return None
    # assert len(submission["attachments"]) <= 1, "Attachment more than 1???"
    if len(submission["attachments"]) > 1:
        sys.stderr.write(str([s["filename"] for s in submission["attachments"]]))
        sys.stderr.write("\nwhich one to choose? input an integer like 0, 1, 2 and so on...\n>")
        choice = int(input())
        sys.stderr.write("You have chosen %s!\n\n" % submission["attachments"][choice]["filename"])
    else:
        choice = 0
    filename = None
    for (i, attachment) in enumerate(submission["attachments"]):
        if choice != i: continue
        raw_filename = attachment["filename"]
        attachment_id = attachment["id"]
        filename = "DOWNLOAD_%s_%s_%s" % (student_id, attachment_id, raw_filename)
        url = attachment["url"]
        response = requests.get(url)
        assert response.status_code == 200, "Failed to download file"
        with open(os.path.join(download_path, filename), "wb") as f:
            f.write(response.content)
    return filename

## should double check assignment ID before calling this function!
def put_score_and_comment(student_id, assignment_id, score, comment, score_is_percentage):
    config = get_config()
    if score_is_percentage:
        score = "%s%%" % score
    path = "/api/v1/courses/%s/assignments/%s/submissions/%s" % (config["course_id"], assignment_id, student_id)
    query = "?access_token=%s" % get_token(config)
    response = requests.put(CANVAS_HOST + path + query, data={"comment[text_comment]": comment, "submission[posted_grade]": score})
    assert response.status_code == 200, "Failed to put grade and comment"

def download_submission_all(assignment_id, download_path):
    double_check_assignment_id(assignment_id)
    student_list = get_student_list()
    filenames = {}
    for student in student_list:
        filenames[student["id"]] = download_submission(student["id"], assignment_id, download_path)
    return filenames

# result is a json with fields "is_valid", "id", "name", "score", "comment"
def upload_results(results_fn, assignment_id, student_id=None, as_percentage=False):
    double_check_assignment_id(assignment_id)
    with open(results_fn, "r") as f:
        results = json.load(f)
    for i in range(len(results)):
        print("uploading %d/%d" % (i, len(results)), end="\r")
        r = results[i]
        if student_id is not None and r["id"] != student_id:
            continue
        put_score_and_comment(r["id"], assignment_id, r["score"], r["comment"], score_is_percentage=as_percentage)
    return

# grouping students
def get_groups(assignment_id, min_member_count=1, max_member_count=2, old_group_file=None):
    from student_groups import Grouper
    student_list = get_student_list()
    grouper = Grouper(student_list, min_member_count, max_member_count)
    if old_group_file is not None:
        with open(old_group_file, "r") as f:
            old_groups = json.load(f)["groups"]
        unassigned = grouper.load(old_groups)
    else:
        unassigned = [s["id"] for s in student_list]
    for student_id in unassigned:
        submission = get_submission(student_id, assignment_id, include_comments=True)
        grouper.accept(student_id, submission)
    groups, errors = grouper.finalize()
    return {"groups": groups, "errors": errors}

# format of dates: YYYY-MM-DD or YYYYMMDD (the split char "-" is not important)
def is_date_after(obj, ref):
    # it is just a non-elegant number trick that keeps comparability
    obj = int("".join(obj.split("-")))
    ref = int("".join(ref.split("-")))
    return obj >= ref

# gather comments
# format of start_date: a string YYYY-MM-DD
def get_comments(student_id, assignment_id, start_date=None, submission_json=None):
    if submission_json is None:
        submission = get_submission(student_id, assignment_id, include_comments=True)
    else:
        submission = submission_json
    comments = submission["submission_comments"]
    extracted_comments = []
    for comment in comments:
        comment_date = comment["created_at"][0:10]
        if start_date is None or is_date_after(comment_date, start_date):
            extracted_comments.append({
                "name": comment["author_name"],
                "content": comment["comment"],
                "time": comment["created_at"],
            })
    return extracted_comments

def get_comments_all(assignment_id, start_date=None):
    student_list = get_student_list()
    comments_all = []
    for student in student_list:
        comments = get_comments(student["id"], assignment_id, start_date=start_date)
        if len(comments) > 0:
            comments_all.append({
                "id": student["id"],
                "name": student["name"],
                "comments": comments,
            })
    return comments_all

def seconds_to_humanly(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return "%dd %dh %dm %ds" % (d, h, m, s)

# get all that information of students, skip non-late ones
def get_seconds_late_all_with_comments(assignment_id):
    student_list = get_student_list()
    lates = []
    for student in student_list:
        submission = get_submission(student["id"], assignment_id, include_comments=True)
        if "attachments" not in submission or len(submission["attachments"]) == 0:
            continue # ignore students that did not submit at all
        seconds_late = submission["seconds_late"]
        comments = get_comments(None, None, submission_json=submission) # avoid re-request
        if seconds_late > 0:
            lates.append({
                "id": student["id"],
                "name": student["name"],
                "late_duration": seconds_to_humanly(seconds_late),
                "comments": comments,
                "deduction": "TODO", # should change to a float number, like 0.1 (meaning 10% deduction)
            })
    return lates

# search for student via name, student ID or net ID, handy when doing manual interactions with Canvas
# trick: prints all students when called without parameter
def search_for_student(*strings):
    student_list = get_student_list()
    matched_students = []
    for student in student_list:
        counter = 0
        for string in strings:
            for key in student:
                if string.lower() in str(student[key]).lower(): # ignore case
                    counter += 1
                    break
        if counter == len(strings):
            matched_students.append(student)
    print("found %d matching students:" % len(matched_students))
    for student in matched_students:
        print("%s, %s, %s" % (student["id"], student["name"], student["sis_user_id"]))
    return

def send_one_message(student_id):
    print("You will send a message to: %d" % student_id)
    search_for_student(str(student_id))
    print()
    subject = input("Input Subject: ")
    content = input("Input Content: ")
    config = get_config()
    path = "/api/v1/conversations"
    query = "?access_token=%s" % get_token(config)
    response = requests.post(CANVAS_HOST + path + query, data={
        "recipients": str(student_id),
        "subject": subject,
        "body": content,
        "context_code": "course_%d" % config["course_id"],
    })
    assert response.status_code == 201, "Failed to send message to student"
    print("Message sent!")

# In message_fn, the JSON object should be a list of objects, each having fields "student_id", "subject" and "content".
def send_messages(message_fn):
    with open(message_fn, "r") as f:
        messages = json.load(f)
    config = get_config()
    path = "/api/v1/conversations"
    query = "?access_token=%s" % get_token(config)
    for i in range(len(messages)):
        print("sending %d/%d" % (i, len(messages)), end="\r")
        message = messages[i]
        response = requests.post(CANVAS_HOST + path + query, data={
            "recipients": str(message["student_id"]),
            "subject": message["subject"],
            "body": message["content"],
            "context_code": "course_%d" % config["course_id"],
        })
        if response.status_code != 201:
            sys.stderr.write("Met problem sending to: student_id=%d\n", message["student_id"])
    print("Message sending finished.")
    return

def test():
    pass

# Command line of this module:
CMD_LINE = {
    "": lambda: print("Command lines:\n", CMD_LINE),
    "test": lambda: test(), # used to try new/unstable functions
    "search": search_for_student, # this is special, usually called by human, non-json, can take any number of parameters
    "ls": {
        "students": lambda: print(pretty_json(get_student_list(forced_refresh=True))), # list all students of this course
        "late": lambda assignment_id: print(pretty_json(get_seconds_late_all_with_comments(int(assignment_id)))),
        "submission": lambda student_id, assignment_id: print(pretty_json(get_submission(student_id, assignment_id))),
        "comments": {
            "one": lambda student_id, assignment_id: print(pretty_json(get_comments(int(student_id), int(assignment_id)))),
            "all": lambda assignment_id: print(pretty_json(get_comments_all(int(assignment_id)))),
            "after": lambda start_date, assignment_id: print(pretty_json(get_comments_all(int(assignment_id), start_date=start_date))),
        }
    },
    "group": {
        "new": lambda assignment_id: print(pretty_json(get_groups(int(assignment_id)))),
        "append": lambda group_fn, assignment_id: print(pretty_json(get_groups(int(assignment_id), old_group_file=group_fn))),
    },
    "download": {
        "one": lambda student_id, assignment_id, path: print(pretty_json(download_submission(int(student_id), int(assignment_id), path))),
        "all": lambda assignment_id, path: print(pretty_json(download_submission_all(int(assignment_id), path))),
    },
    "upload": {
        "one": lambda student_id, result_fn, assignment_id: upload_results(result_fn, int(assignment_id), student_id=int(student_id)),
        "all": lambda result_fn, assignment_id: upload_results(result_fn, int(assignment_id)),
        "-p": { # as percentage:
            "one": lambda student_id, result_fn, assignment_id: upload_results(result_fn, int(assignment_id), student_id=int(student_id), as_percentage=True),
            "all": lambda result_fn, assignment_id: upload_results(result_fn, int(assignment_id), as_percentage=True), 
        }
    },
    "message": {
        "one": lambda student_id: send_one_message(int(student_id)),
        "batch": lambda message_fn: send_messages(message_fn),
    },
}

if __name__ == "__main__":
    # assure path:
    cwd = os.getcwd()
    ending = "/grader/utils"
    assert cwd[-len(ending):] == ending, "must be called from grader util directory"
    # extract commands and parameters:
    args = sys.argv[1:]
    cmd = CMD_LINE
    while type(cmd) is dict:
        key = "" if len(args) == 0 else args[0]
        cmd = cmd[key]
        args = args[1:]
    cmd(*args)
