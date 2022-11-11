"""
This simple script helps to split assignments into N groups
It requires three MANDATORY arguments:
    - number of groups (N)
    - path to the dir of submission files
    - path to the output dirs

It assumes the submission file extension is '.tgz'
"""
import os
import sys
from random import shuffle

if len(sys.argv) != 4:
    print("It requires 3 arguments")
    exit(1)

N = int(sys.argv[1])
input_dir = sys.argv[2]
output_dir = sys.argv[3]

# Scan valid files and shuffle them
valid_files = list(filter(lambda f: f.endswith(".tgz"),  os.listdir(input_dir)))
shuffle(valid_files)

# Create output group dir
group_dirs = [os.path.join(output_dir, f'group-{i}') for i in range(N)]
for d in group_dirs:
    if not os.path.exists(d):
        os.mkdir(d)

# Move files into group dirs
for i, f in enumerate(valid_files):
    src_path = os.path.join(input_dir, f)
    dst_path = os.path.join(group_dirs[i%N], f)
    os.rename(src_path, dst_path)

 