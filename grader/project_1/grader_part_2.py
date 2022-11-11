## The grader of part_2 (http server for single client).
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
        server_proc = control.run_background_start(["python3", "http_server1.py", str(port)],
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

def start_server(server_file, blocking=False):
    port = network_util.scan_available_port(start_port=8000)
    server_proc = control.run_background_start(
        ["python3", server_file, str(port)], f_in=None, f_out="./__anyway_not_stdout",
        f_err="./__anyway_not_stderr", killable=True)  # printing to stdout can be disaster
    time.sleep(1)  # wait for the server to start up

    telnet_proc = None
    return server_proc, port, telnet_proc

def kill_server(server_proc, telnet_proc):
    control.run_background_interrupt(server_proc)
    if telnet_proc:
        control.run_background_interrupt(telnet_proc)


def test_200(blocking=False, server_file="http_server1.py"):
    score = 20
    curl_timeout = 8
    keep_alive_score = 5

    # test curl and header:
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)

    status_code, fields, content = network_util.get_http_response(url, curl_timeout)

    # (5) `curl` should not crash / timed out
    if status_code is None:
        control.log_comment("-5: header request fail/time out after %s seconds (%s)" % (curl_timeout, url))
        score -= 5

    # (5) Header Should be correct:
    if status_code is None or status_code < 200 or status_code >= 300:
        control.log_comment("-5: wrong HTTP status code (%s)" % url)
        score -= 5
    # else:
    #     if "content-type" not in fields or fields["content-type"][0:9].lower() != "text/html":
    #         control.log_comment("-2: 'content-type' should be 'text/html' (%s)" % url)
    #         score -= 2

    time.sleep(1)
    is_alive = control.run_background_liveness(server_proc)
    if not is_alive:
        control.log_comment("-5: server exited early after visiting (%s)" % url)
        keep_alive_score = 0

    kill_server(server_proc, telnet_proc)

    # (10) Should show page when we `curl`
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    fn = "rfc2616.html"
    with open(fn, "r") as f:
        oracle = f.read().strip()
    url = "http://%s:%d/%s" % (HOSTNAME, port, fn)
    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)
    content = content.strip()

    if content[:100] != oracle[:100]:
        control.log_comment("-8: wrong content (%s)" % url)
        score -= 8
    elif content != oracle:
        control.log_comment("-5: incomplete page (%s)" % url)
        score -= 5

    # (5) Should stay running (until we kill)
    if keep_alive_score == 0:
        kill_server(server_proc, telnet_proc)
        return score

    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)

    time.sleep(1)
    is_alive = control.run_background_liveness(server_proc)
    if exit_code is None or content is None or len(content.strip()) == 0 or is_alive == False:
        control.log_comment("-5: server exited early after visiting or no html page got (%s)" % url)
        keep_alive_score = 0

    kill_server(server_proc, telnet_proc)
    return score + keep_alive_score


def test_403_404(status: int, file_name: str, blocking=False, server_file="http_server1.py"):
    score = 5
    curl_timeout = 5

    # test curl and header:
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/%s" % (HOSTNAME, port, file_name)

    status_code, fields, content = network_util.get_http_response(url, curl_timeout)

    # (5) `curl` should not crash / timed out
    if status_code is None:
        control.log_comment("-5: status code request fail/time out after %s seconds (%s)" % (curl_timeout, url))
        score -= 5
        kill_server(server_proc, telnet_proc)
        return score

    # (5) status code Should be correct:
    if status_code != status:
        control.log_comment("-5: wrong HTTP status code, should return %d (%s)" % (status, url))
        score -= 5
        kill_server(server_proc, telnet_proc)
        return score

    # (5) server should keep running
    time.sleep(1)
    is_alive = control.run_background_liveness(server_proc)
    if not is_alive:
        control.log_comment("-2: server exited early after visiting (%s)" % url)
        score -= 2

    kill_server(server_proc, telnet_proc)
    return score

def test_refreshability(blocking=False, server_file="http_server1.py"):
    score = 2.5
    curl_timeout = 5

    # test curl and header:
    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/http_server1.py" % (HOSTNAME, port)
    status_code, fields, content = network_util.get_http_response(url, curl_timeout)

    if status_code is None:
        control.log_comment("-2.5: server should be able to return 200 pages after return 403/404")
        score -= 2.5
        kill_server(server_proc, telnet_proc)
        return score

    url = "http://%s:%d/404" % (HOSTNAME, port)
    status_code, fields, content = network_util.get_http_response(url, curl_timeout)

    if status_code is None:
        control.log_comment(
            "-2.5: server should be able to return 200 pages after return 403/404")
        score -= 2.5
        kill_server(server_proc, telnet_proc)
        return score

    server_proc, port, telnet_proc = start_server(server_file, blocking)
    url = "http://%s:%d/rfc2616.html" % (HOSTNAME, port)
    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)

    if exit_code is None:
        control.log_comment(
            "-2.5: server should be able to return 200 pages after return 403/404")
        score -= 2.5
        kill_server(server_proc, telnet_proc)
        return score

    if content is None or len(content) < 1000:
        control.log_comment(
            "-2.5: server should be able to return 200 pages after return 403/404")
        score -= 2.5
        kill_server(server_proc, telnet_proc)
        return score

    kill_server(server_proc, telnet_proc)
    return score

def check_code_for_cheat():
    # TODO: should check whether banned packages were imported.
    return False

def main():
    curr_score = 0
    control.log_comment("Part 2 grading starts!")
    if "http_server1.py" not in os.listdir():
        control.log_comment("'http_server1.py' not found! Zero score!")
        return 0
    if check_code_for_cheat():
        control.log_comment("Code cheating detected! Zero score!")
        return 0
    try:
        test_student_hostname()
        test_403 = lambda: test_403_404(status=403, file_name='http_server1.py')
        test_404 = lambda: test_403_404(status=404, file_name='404.html')
        for f in test_200, test_403, test_404, test_refreshability, :
            curr_score += f()
    except control.GraderException as err:
        control.handle_grader_exception(err)
        raise
    control.log_comment("Part 2 grading done! Scored %s out of 37.5!" % curr_score)
    return curr_score

if __name__ == "__main__":
    main()