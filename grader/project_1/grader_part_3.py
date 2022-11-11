## The grader of part_3 (http server for multiple client).
## TODO: Test cases below are just illustration of workflow. They are not final test cases!!!

import grader_util_control as control
import grader_util_network_util as network_util
import os
import time

# have to do this, assume the student does one of these:
HOSTNAME = "localhost"
def test_student_hostname():
    import requests
    global HOSTNAME
    for name in "localhost", "moore.wot.eecs.northwestern.edu":
        port = network_util.scan_available_port(start_port=8000)
        server_proc = control.run_background_start(["python3", "http_server2.py", str(port)],
            f_in=None, f_out="./__anyway_not_stdout", f_err="./__anyway_not_stderr", killable=True)  # printing to stdout can be disaster
        time.sleep(1)
        try:
            url = "http://%s:%d/rfc2616.html" % (name, port)
            requests.get(url=url, timeout=10)
            print("The student was using %s as hostname" % name)
            HOSTNAME = name
            control.run_background_interrupt(server_proc)
            return
        except:
            control.run_background_interrupt(server_proc)
    print("I do not know what hostname hse is using... assuming localhost")

def start_server(server_file, blocking=True):
    port = network_util.scan_available_port(start_port=8000)
    server_proc = control.run_background_start(
        ["python3", server_file, str(port)], f_in=None, f_out="./__anyway_not_stdout",
        f_err="./__anyway_not_stderr", killable=True)  # printing to stdout can be disaster
    time.sleep(1)  # wait for the server to start up

    telnet_proc = None
    if blocking:
        telnet_proc = start_telnet(port)

    return server_proc, port, telnet_proc


def start_telnet(port):
    return control.run_background_start(
            ["telnet", "localhost", str(port)], f_in=None, f_out=None, f_err=None, killable=True)


def kill_server(server_proc, telnet_proc):
    if telnet_proc:
        if control.run_background_liveness(telnet_proc):
            control.run_background_interrupt(telnet_proc)
    control.run_background_interrupt(server_proc) # should close telnet before closing the server...


def test_200_with_blocking(blocking=True, server_file="http_server2.py"):
    score = 25
    curl_timeout = 2.5
    curl_timeout_large = 10
    fn = "rfc2616.html"
    with open(fn, "r") as f:
        oracle = f.read().strip()

    # (5) test curl
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)
    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout_large)

    if exit_code is None:
        control.log_comment("-5: curl time out after %s seconds (%s)" % (curl_timeout, url))
        score -= 5
    elif exit_code != 0:
        control.log_comment("-5: curl returned non-zero exit code (%s)" % url)
        score -= 5
    kill_server(server_proc, telnet_proc)

    # (10) test page
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)
    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)
    if exit_code is None: # no-return in 2.5s
        large_exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout_large)
        if large_exit_code is None:
            score -= 10
            control.log_comment("-10: base test: curl timeout (%s)" % url)
        else:
            score -= 5
            control.log_comment("-5: base test: curl timeout in 2.5 seconds (%s)" % url)
            if content != oracle:
                control.log_comment("-5: incomplete page (%s)" % url)
                score -= 5
    else:  # return in 2.5s
        content = content.strip()

        if content[:100] != oracle[:100]:
            control.log_comment("-8: wrong content (%s)" % url)
            score -= 8
        elif content != oracle:
            control.log_comment("-5: incomplete page (%s)" % url)
            score -= 5
    #
    time.sleep(1)
    is_alive = control.run_background_liveness(server_proc)
    if not is_alive:
        control.log_comment("-10: server exited early after visiting (%s)" % url)
        score -= 10
    else:
        control.run_background_interrupt(telnet_proc)
        telnet_proc = None

        time.sleep(1)
        is_alive_after_telnet = control.run_background_liveness(server_proc)
        if not is_alive_after_telnet:
            control.log_comment("-7: server exited early after exiting telnet (%s)" % url)
            score -= 7
        else:
            exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout_large)
            if content is None or exit_code is None or content == '':
                control.log_comment("-7: server exited early / content is empty after exiting telnet (%s)" % url)
                score -= 7
    kill_server(server_proc, telnet_proc)

    return score


def stability_test(server_file="http_server2.py"):
    score = 7.5
    curl_timeout = 2.5
    fn = "rfc2616.html"
    with open(fn, "r") as f:
        oracle = f.read().strip()

    server_proc, port, telnet_proc = start_server(server_file)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)

    timeout_cnt = 0
    wrong_content = 0

    for _ in range(5):
        exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)
        content = content.strip()
        if exit_code is None:
            timeout_cnt += 1
        else:
            if exit_code != 0 or content[:1000] != oracle[:1000]:
                wrong_content += 1

    kill_server(server_proc, telnet_proc)
    score -= timeout_cnt * 2.5
    score -= min(4.5, wrong_content * 1.5)
    score = max(0, score)
    if score != 7.5:
        control.log_comment("-%s: %d out of 5 requests timeout, %d out of %d contents incorrect  (stability test)" % (7.5 - score, timeout_cnt, wrong_content, 5 - timeout_cnt))
    return score


def scalability_test(server_file="http_server2.py"):
    score = 5
    curl_timeout = 2.5
    curl_timeout_large = 10
    fn = "rfc2616.html"
    with open(fn, "r") as f:
        oracle = f.read().strip()

    server_proc, port, telnet_proc = start_server(server_file)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)

    telnet_proc2 = start_telnet(port)
    telnet_proc3 = start_telnet(port)

    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout_large)
    content = content.strip()
    if exit_code is None or content is None or content == '':
        control.log_comment("-5: multi-connection block test failed")
        score -= 5
    else:
        if content[:1000] == oracle[:1000]:
            exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)
            content = content.strip()
            if content[:1000] == oracle[:1000]:
                pass
            else:
                control.log_comment("-5: multi-connection block test timeoout in 2.5s")
                score -= 2.5
        else:
            control.log_comment("-5: multi-connection block test failed")
            score -= 5

    control.run_background_interrupt(telnet_proc2)
    control.run_background_interrupt(telnet_proc3)
    kill_server(server_proc, telnet_proc)
    return score


def check_code_for_cheat():
    # TODO: should check whether banned packages were imported.
    return False

def main():
    curr_score = 0
    control.log_comment("Part 3 grading starts!")
    if "http_server2.py" not in os.listdir():
        control.log_comment("'http_server2.py' not found! Zero score!")
        return 0
    if check_code_for_cheat():
        control.log_comment("Code cheating detected! Zero score!")
        return 0
    try:
        test_student_hostname()
        for f in test_200_with_blocking, stability_test, scalability_test:
            curr_score += f()
    except control.GraderException as err:
        control.handle_grader_exception(err)
        raise
    control.log_comment("Part 3 grading done! Scored %s out of 37.5!" % curr_score)
    return curr_score

if __name__ == "__main__":
    main()