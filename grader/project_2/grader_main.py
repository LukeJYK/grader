## entry of actual grading.

import grader_util_control as control
import grader_util_network_util as network_util
import os
import time
import json


def read_stage_progress(stage_num):
    try:
        with open("__grader__temp__stage%d.txt" % stage_num, "r") as f:
            progress = int(f.read())
    except: # no such file?
        progress = 0
    return progress

def read_timestamp():
    try:
        with open("__grader__temp__timestamp.txt", "r") as f:
            timestamp = float(f.read())
    except:
        timestamp = None
    return timestamp

# for part 1-4:
def test_single(max_points, nums, lr, cr, mdd, max_seconds, seed, trace_prefix, tester_fn="grader_tester.py"):
    # start testers:
    test_description = "lr=%s cr=%s mdd=%s n=%s ts=%s seed=%s" % (lr, cr, mdd, nums, max_seconds, seed)
    if tester_fn == "grader_skiphost1.py":
        test_description += ", stage 1 skipped"
    port_1, port_2 = network_util.scan_available_ports(8100, 2, udp=True)
    print("tesing %s (%s) on port %d and %d, waiting for %s seconds maximum..." % (trace_prefix, test_description, port_1, port_2, max_seconds))
    host_1 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "1", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_1_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_1_stderr.txt" % trace_prefix,
        killable = True
    )
    host_2 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "2", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_2_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_2_stderr.txt" % trace_prefix,
        killable = True
    )

    # waiting for exit:
    exit_codes = [None, None, None]
    start_time = time.time()
    exit_codes[1] = control.run_background_interrupt(host_1, delay_seconds=max_seconds+5, read_output=False) # add 5s just in case
    time_taken = time.time() - start_time

    time_left = max(0, (max_seconds + 1) - time_taken)
    exit_codes[2] = control.run_background_interrupt(host_2, delay_seconds=time_left, read_output=False)
    
    # grading:
    reports = []

    if exit_codes[1] != 0 or exit_codes[2] != 0:
        if read_stage_progress(2) == nums:
            msg = "crash/timeout during teardown"
            score = max_points * 0.8
        else:
            progress_1 = read_stage_progress(1)
            if progress_1 == nums:
                msg = "crash/timeout during stage 2"
                score = max_points * 0.6
            elif progress_1 >= nums * 0.5:
                msg = "crash/timeout, stage 1 progress >= 50%"
                score = max_points * 0.4
            elif progress_1 >= nums * 0.1:
                msg = "crash/timeout, stage 1 progress >= 10%"
                score = max_points * 0.2
            else:
                msg = "crash/timeout, few progress"
                score = 0
        comment = "%.1f/%.1f: %s (%s)" % (score, max_points, msg, test_description)
        control.log_comment(comment)
        print(comment)
    else: # both hosts exited normally!! Yeah~
        for i in (1, 2):
            with open("__grader__report__host%d.json" % i, "r") as f:
                report = json.load(f)
                reports.append(report)
        timestamp = read_timestamp()
        assert timestamp is not None
        timediff = timestamp - start_time
        msg = "done in %.1f seconds" % timediff
        score = max_points
        comment = "%.1f/%.1f: %s (%s)" % (score, max_points, msg, test_description)
        control.log_comment(comment)
        print(comment)

    os.system("rm -f __grader__temp__timestamp.txt")
    for i in (1, 2):
        os.system("rm -f __grader__report__host%d.json" % i)
        os.system("rm -f __grader__temp__stage%d.txt" % i)
    
    return score


def part_1():
    # return 20
    # pts_l = [2.5, 2.5, 5.0, 5.0, 5.0]
    # nums_l = [1, 10, 400, 500, 1000]
    # lr, cr, mdd = 0.0, 0.0, 0.0
    # timeouts_l = [60, 60, 180, 60, 60]
    # seed_l = [345678, 901234, 567890, 123456, 789012]
    # tester_fn = ["grader_tester.py"] * 3 + ["grader_skiphost1.py"] * 2

    # return 25
    pts_l = [5.0, 5.0, 5.0, 5.0, 5.0]
    nums_l = [1, 10, 400, 500, 1000]
    lr, cr, mdd = 0.0, 0.0, 0.0
    timeouts_l = [60, 60, 180, 60, 60]
    seed_l = [345678, 901234, 567890, 123456, 789012]
    tester_fn = ["grader_tester.py"] * 3 + ["grader_skiphost1.py"] * 2

    score = 0
    for i in range(len(nums_l)):
        score += test_single(pts_l[i], nums_l[i], lr, cr, mdd, timeouts_l[i], seed_l[i], "part_1_%d" % i, tester_fn=tester_fn[i])
    return score


def part_2():
    # return 20
    # pts = 5
    # nums_l = [100, 100, 200, 200]
    # lr, cr = 0.0, 0.0
    # mdd_l = [0.05, 0.1, 0.05, 0.1]
    # timeouts_l = [180, 180, 180, 180]
    # seed_l = [135799, 246800, 357911, 468022]

    # return 30
    pts = 7.5
    nums_l = [100, 100, 200, 200]
    lr, cr = 0.0, 0.0
    mdd_l = [0.05, 0.1, 0.05, 0.1]
    timeouts_l = [180, 180, 180, 180]
    seed_l = [135799, 246800, 357911, 468022]

    score = 0
    for i in range(len(nums_l)):
        score += test_single(pts, nums_l[i], lr, cr, mdd_l[i], timeouts_l[i], seed_l[i], "part_2_%d" % i)
    return score


def part_3():
    # return 30
    # pts = 5
    # nums_l = [200, 200, 200, 200, 300, 400]
    # cr = 0.0
    # lr_l = [0.03, 0.05, 0.07, 0.1, 0.1, 0.1]
    # mdd = 0.0
    # timeouts_l = [120, 120, 120, 120, 180, 180]
    # seed_l = [987654, 321098, 765432, 109876, 543210, 987654]

    # return 20
    pts = 4
    nums_l = [200, 200, 200, 200, 300]
    cr = 0.0
    lr_l = [0.03, 0.05, 0.07, 0.1, 0.1]
    mdd = 0.0
    timeouts_l = [120, 120, 120, 120, 180]
    seed_l = [987654, 321098, 765432, 109876, 543210]

    score = 0
    for i in range(len(nums_l)):
        score += test_single(pts, nums_l[i], lr_l[i], cr, mdd, timeouts_l[i], seed_l[i], "part_3_%d" % i)
    return score


def part_4():
    # return 15
    pts_l = [5.0, 5.0, 2.5, 2.5]
    nums_l = [200, 200, 200, 400]
    lr_l = [0.0, 0.0, 0.1, 0.1]
    cr_l = [0.05, 0.1, 0.1, 0.1]
    mdd = 0.0
    timeouts_l = [120, 120, 120, 180]
    seed_l = [531975, 420864, 319753, 208642]

    score = 0
    for i in range(len(nums_l)):
        score += test_single(pts_l[i], nums_l[i], lr_l[i], cr_l[i], mdd, timeouts_l[i], seed_l[i], "part_4_%d" % i)
    return score


# for part 5:
def interp(x, l0, r0, l1, r1):
    if x <= l0:
        return l1
    if x >= r0:
        return r1
    return l1 + (r1-l1) * ((x-l0)/(r0-l0))

def test_single_part5(max_points, nums, lr, cr, mdd, min_seconds, max_seconds, seed, trace_prefix, tester_fn="grader_tester.py"):
    # start testers:
    test_description = "lr=%s cr=%s mdd=%s n=%s ts=%s~%s seed=%s" % (lr, cr, mdd, nums, min_seconds, max_seconds, seed)
    if tester_fn == "grader_skiphost1.py":
        test_description += ", stage 1 skipped"
    port_1, port_2 = network_util.scan_available_ports(8100, 2, udp=True)
    print("tesing %s (%s) on port %d and %d, waiting for %s seconds maximum..." % (trace_prefix, test_description, port_1, port_2, max_seconds))
    host_1 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "1", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_1_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_1_stderr.txt" % trace_prefix,
        killable = True
    )
    host_2 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "2", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_2_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_2_stderr.txt" % trace_prefix,
        killable = True
    )

    # waiting for exit:
    exit_codes = [None, None, None]
    start_time = time.time()
    exit_codes[1] = control.run_background_interrupt(host_1, delay_seconds=max_seconds+5, read_output=False) # add 5s just in case
    time_taken = time.time() - start_time

    time_left = max(0, (max_seconds + 1) - time_taken)
    exit_codes[2] = control.run_background_interrupt(host_2, delay_seconds=time_left, read_output=False)
    
    # grading:
    reports = []

    if exit_codes[1] != 0 or exit_codes[2] != 0:
        timestamp = read_timestamp()
        if timestamp is not None:
            timediff = timestamp - start_time
            msg = "all messages got in %.1f seconds, but crash/timeout during teardown" % timediff
            score = max_points * 0.8 * interp(timediff, min_seconds, max_seconds, 1.0, 0.2)
            score = int(score*10+0.001)/10
        else:
            progress_1 = read_stage_progress(1)
            if progress_1 == nums:
                msg = "crash/timeout during stage 2"
                score = max_points * 0.12
            elif progress_1 >= nums * 0.5:
                msg = "crash/timeout, stage 1 progress >= 50%"
                score = max_points * 0.08
            elif progress_1 >= nums * 0.1:
                msg = "crash/timeout, stage 1 progress >= 10%"
                score = max_points * 0.04
            else:
                msg = "crash/timeout, few progress"
                score = 0
        comment = "%.1f/%.1f: %s (%s)" % (score, max_points, msg, test_description)
        control.log_comment(comment)
        print(comment)
    else: # both hosts exited normally!! Yeah~
        for i in (1, 2):
            with open("__grader__report__host%d.json" % i, "r") as f:
                report = json.load(f)
                reports.append(report)
        timestamp = read_timestamp()
        assert timestamp is not None
        timediff = timestamp - start_time
        msg = "done in %.1f seconds" % timediff
        score = max_points * interp(timediff, min_seconds, max_seconds, 1.0, 0.2)
        score = int(score*10+0.001)/10
        if score < max_points - 0.001:
            msg += ", inefficient"
        comment = "%.1f/%.1f: %s (%s)" % (score, max_points, msg, test_description)
        control.log_comment(comment)
        print(comment)

    os.system("rm -f __grader__temp__timestamp.txt")
    for i in (1, 2):
        os.system("rm -f __grader__report__host%d.json" % i)
        os.system("rm -f __grader__temp__stage%d.txt" % i)

    return score


def part_5():
    # return 15
    # pts = 2.5
    # nums = 1000
    # lr_l = [0.05, 0.1, 0.0, 0.1, 0.1, 0.1]
    # cr_l = [0.05, 0.0, 0.1, 0.1, 0.1, 0.1]
    # mdd = 0.1
    # timemin_l = [120, 120, 120, 150, 150, 150]
    # timemax_l = [170, 170, 170, 230, 230, 230]
    # seed_l = [336699, 447700, 558811, 669922, 770033, 881144]

    # return 10
    pts = 2
    nums = 1000
    lr_l = [0.05, 0.1, 0.0, 0.1, 0.1]
    cr_l = [0.05, 0.0, 0.1, 0.1, 0.1]
    mdd = 0.1
    timemin_l = [120, 120, 120, 150, 150]
    timemax_l = [170, 170, 170, 230, 230]
    seed_l = [336699, 447700, 558811, 669922, 770033]

    score = 0
    for i in range(len(seed_l)):
        score += test_single_part5(pts, nums, lr_l[i], cr_l[i], mdd, timemin_l[i], timemax_l[i], seed_l[i], "part_5_%d" % i)
    return score


# extra part:
def calc_byte_score(x, l, r, max_points):
    if x < l:
        return max_points
    if x > r:
        return 0
    import math
    xx, ll, rr = math.log(x), math.log(l), math.log(r)
    score = (rr-xx) / (rr-ll) * max_points
    score = int(score*10)/10
    return score

def test_single_extra(max_points, min_bytes, max_bytes, nums, lr, cr, mdd, max_seconds, seed, trace_prefix, with_report=False, tester_fn="grader_tester.py"):
    # start testers:
    test_description = "lr=%s cr=%s mdd=%s n=%s ts=%s seed=%s" % (lr, cr, mdd, nums, max_seconds, seed)
    if tester_fn == "grader_skiphost1.py":
        test_description += ", stage 1 skipped, only count host 2's side"
    port_1, port_2 = network_util.scan_available_ports(8100, 2, udp=True)
    print("tesing %s (%s) on port %d and %d, waiting for %s seconds maximum..." % (trace_prefix, test_description, port_1, port_2, max_seconds))
    host_1 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "1", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_1_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_1_stderr.txt" % trace_prefix,
        killable = True
    )
    host_2 = control.run_background_start(
        ["python3", tester_fn, str(port_1), str(port_2), "2", str(lr), str(cr), str(mdd), str(nums), str(seed)],
        f_in = None,
        f_out = "__grader_trace_%s_host_2_stdout.txt" % trace_prefix,
        f_err = "__grader_trace_%s_host_2_stderr.txt" % trace_prefix,
        killable = True
    )

    # waiting for exit:
    exit_codes = [None, None, None]
    start_time = time.time()
    exit_codes[1] = control.run_background_interrupt(host_1, delay_seconds=max_seconds+5, read_output=False) # add 5s just in case
    time_taken = time.time() - start_time

    time_left = max(0, (max_seconds + 1) - time_taken)
    exit_codes[2] = control.run_background_interrupt(host_2, delay_seconds=time_left, read_output=False)
    
    # grading:
    reports = []

    if exit_codes[1] != 0 or exit_codes[2] != 0:
        score = 0
        msg = "crash/timeout"
        comment = "%.1f: %s (%s)" % (score, msg, test_description)
        control.log_comment(comment)
        print(comment)
    else: # both hosts exited normally!! Yeah~
        bytes_sent = 0
        for i in (1, 2):
            with open("__grader__report__host%d.json" % i, "r") as f:
                report = json.load(f)
                reports.append(report)
                if (tester_fn != "grader_skiphost1.py") or (i != 1):
                    bytes_sent += report["stats"]["ETH_BYTES_SENT"]
        score = calc_byte_score(bytes_sent, min_bytes, max_bytes, max_points)
        msg = "done with %d bytes sent" % bytes_sent
        comment = "%.1f: %s (%s)" % (score, msg, test_description)
        control.log_comment(comment)
        print(comment)

    os.system("rm -f __grader__temp__timestamp.txt")
    for i in (1, 2):
        os.system("rm -f __grader__report__host%d.json" % i)
        os.system("rm -f __grader__temp__stage%d.txt" % i)

    return score


def part_extra():
    # return 10
    pts = 4
    nums_l = [1000, 1000, 3000, 10000]
    lr_l = [0.01, 0.1, 0.001, 0.1]
    cr_l = [0.01, 0.1, 0.001, 0.1]
    mdd_l = [0.0, 0.1, 0.0, 0.1]
    timemax = 240
    seed_l = [10203, 10409, 10827, 11681]
    min_bytes_l = [8000, 12000, 20000, 1000]
    max_bytes_l = [200000, 800000, 600000, 4000]
    tester_fn = ["grader_tester.py"] * 3 + ["grader_skiphost1.py"] * 1

    score = 0
    for i in range(len(nums_l)):
        score += test_single_extra(pts, min_bytes_l[i], max_bytes_l[i],
            nums_l[i], lr_l[i], cr_l[i], mdd_l[i], timemax, seed_l[i], "part_ex_%d" % i, tester_fn=tester_fn[i])
    if score > 10.001:
        control.log_comment("Score capped to 10.0%% although %.1f%% is achieved." % score)
        score = 10
    return score


def main():
    total_score = 0
    part_names = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Extra Part"]
    full_scores = [20, 20, 30, 15, 15, 10]
    full_scores = [25, 30, 20, 15, 10, 10]
    qualify_scores = [0, 0, 10, 5, 5, 7.5]
    grading_functions = [part_1, part_2, part_3, part_4, part_5, part_extra]

    # input("before grading pause...")
    if "streamer.py" not in os.listdir():
        control.log_comment("'streamer.py' not found! Zero score!")
    else:
        control.log_comment("lr:loss_rate  cr:corruption_rate  mdd:max_delivery_delay\nn:NUMS  ts:timeout_seconds  seed:random_seed\n")
        last_score = 0
        for i in range(6):
            if last_score < qualify_scores[i] - 0.001:
                control.log_comment("You earned too few points in %s to qualify for %s (and following stages if any)!\n" % (part_names[i-1], part_names[i]))
                break
            control.log_comment("%s grading starts!" % part_names[i])
            score = grading_functions[i]()
            control.log_comment("%s grading finishes! Earned %.1f%% out of %s%%.\n" % (part_names[i], score, full_scores[i]))
            total_score += score
            last_score = score

    control.log_comment("Your total score is %.1f%%." % total_score)
    control.finalize(total_score)
    # input("after grading pause...")

if __name__ == "__main__":
    main()