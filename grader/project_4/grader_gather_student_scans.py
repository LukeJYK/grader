# gather scan_out.json of students (into comments).
# shall visualize these data later.

import os
import json

def gather() -> str:
    if "scan_out.json" not in os.listdir():
        return "[0] no reference, skip!"
    try:
        with open("scan_out.json", "r") as f:
            obj = json.load(f)
        return json.dumps(obj)
    except:
        return "[1] invalid json, skip!"