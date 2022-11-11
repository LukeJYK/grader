# The Integrated Grader Framework

## Known issues
- The file-path style is incompatible with Windows.
- stdout and stderr are lost upon **killing** a program.
- `input` function sometimes raises `EOFError` inside `grader_main.py` for some unknown reason. (Reopening the terminal might solve this)

## Secure yourself
It's not technically impossible to exploit this grader. A simple line like `os.system("rm -rf ~")` in a Python file can turn anybody into an April fool!! So I recommend running it in a **virtual / isolated environment**, and take a snapshot before grading.

## Course ID, Assignment ID, Student ID
These concepts are crucial, they are the primary keys of objects on Canvas.

Each one is an integer. Note that *Student ID is not netid or NU employment ID*. (e.g. see `grader/utils/students.json`).

## Workflow
### Runtime
- For first use, please check `grader/utils/canvas_config.json`.
  - Go to https://canvas.northwestern.edu/profile/settings and hit "New Access Token" button to get one, and copy this token into `grader/utils/token.txt` (This file is `.gitignore`d).
- `cd grader/utils` to execute `canvas.py`.
  - For group assignments, get grouping information via `python3 canvas.py group new $assignment_id > output.json`.
  - Get late submission information via `python3 canvas.py ls late > output.json`.
    - Note that the `deduction` field is `TODO`. You need to manually change it into a number between `0.0` (no deduction) to `1.0` (zero score).
- `cd` into the project directory.
  - Check `config.json`. Put the required files into their corresponding positions.
  - To warm up, run `python3 GRADER.py grade test` to "grade" the standard solution.
  - For group assignments, run `python3 GRADER.py grade remaining groups` to literally *grade remaining groups*.
  - If `GRADER.py` crashes (or interrupted via `Ctrl-C`), we don't delete temporary files right away, so that you may check what went wrong.
    - Don't worry, all already graded are not lost.
    - Please run `python3 GRADER.py clean` to delete them, so that the grading can continue.
  - For group assignments, run `python3 GRADER.py copy` to copy grades among members. (This must be executed after all groups are graded.)
  - Finally, run `python3 GRADER.py upload`. All done!

**TIP:** Although this grader is highly automated, please feel free to manually modify any JSON file `~(^o^)~`, because this framework is designed so, for flexibility on human side. For example, to force a regrade for a student, just change the `is_valid` field to `false`. Another examples include assigning a group manually, and even modifying score and comment manually!!

### Development
- Each project **must have** a `config.json`. You should really carefully examine it.
- Each project **must have** a `GRADER.py`. It is a big file (300+ lines). You should just **copy it** from previous projects, and then modify it.
  - Unless you want to add new functionalities, there are **only two places** in **only one function** that need to change. Look for `TODO`s.
- Each project **must have** a `grader_main.py`. It is the entry point of actual grading.
  - I recommend starting from copying this file from previous projects.
- Each project *should have* a `criteria.md` to describe criterias/rubrics for grading.
- Every grader file's name should start with the `grader_` prefix to (hopefully) avoid conflicting with student's filename.
  - And every util file's name should start with the `grader_util_` prefix.

**TIP:** I separate utils in a different folder from project folder. Although this makes the codebase less dirty, it is inconvenient when debugging the little units of the grader. If you prefer, `python3 GRADER.py dev` can temporarily copy all the util files to the current project folder.

## Cross Reference of Files: we KISS
- All of our code files are in Python.
- All of our persistent data are in JSON.
- In `GRADER.py` We copy all needed scripts, along with student's code, to a single flat temp directory. So, just `import xxx` is sufficient.
- `grader_main.py` is the entry in **that temp directory**, but the entry of the whole grading process is `GRADER.py`.

## Command-line implementation
- `GRADER.py` and `canvas.py` are the only two modules that use a command line.
- I used a **light-weight command-line implementation** that depends on no non-popular Python library. It is located at the end of the files.
- *If you cannot understand how it works, please re-learn Python...* `_(:з」∠)_`

## The `utils` modules:
- `canvas.py`: for interacting with Canvas, **independent module**, must be called from shell **(even when called by another python file)**, must be called from its own directory.
- `student_groups.py`: for identifying all student groups, sub-module of `canvas.py`.
- `grader_util_code_analysis.py`: sub-module of grader, now empty.
- `grader_util_control.py`: sub-module of grader, the grader's core procedural functionality.
- `grader_util_network_util.py`: sub-module of grader, network-related, frequently-used functionality.

## Pronoun disclaimer
In my code, I use **hse/hem/hir/hes/hemself** to refer to a singular human. This isn't standard.
