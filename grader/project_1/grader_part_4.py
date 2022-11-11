## The grader of part_4 (http server for JSON client).

import grader_util_control as control
import grader_util_network_util as network_util
import os
import time
import json

# have to do this, assume the student does one of these:
HOSTNAME = "localhost"
def test_student_hostname():
    import requests
    global HOSTNAME
    for name in "localhost", "moore.wot.eecs.northwestern.edu":
        port = network_util.scan_available_port(start_port=8000)
        server_proc = control.run_background_start(["python3", "http_server3.py", str(port)],
            f_in=None, f_out="./__anyway_not_stdout", f_err="./__anyway_not_stderr", killable=True)  # printing to stdout can be disaster
        time.sleep(1)
        try:
            url = "http://%s:%d/product?a=3&b=7" % (name, port)
            requests.get(url=url, timeout=10)
            print("The student was using %s as hostname" % name)
            HOSTNAME = name
            control.run_background_interrupt(server_proc)
            return
        except:
            control.run_background_interrupt(server_proc)
    print("I do not know what hostname hse is using... assuming localhost")

def get_oracle(operands):
    operands = list(map(float, operands))
    result = 1.0 # important, only floats overflow in Python
    for op in operands:
        result *= op
    oracle = {
        "operation": "product",
        "operands": operands,
        "result": result
    }
    return oracle

def get_inf_oracle(operands):
    operands = list(map(float, operands))
    result = 1.0  # important, only floats overflow in Python
    for op in operands:
        result *= op
    if result == float('inf'):
        result = "inf"
    if result == float('-inf'):
        result = "-inf"
    oracle = {
        "operation": "product",
        "operands": operands,
        "result": result
    }
    return oracle

def test_basic():
    score = 4.5
    curl_timeout = 2.5
    # start server:
    port = network_util.scan_available_port(start_port=8000)
    url = "http://%s:%d/product?a=3&b=7" % (HOSTNAME, port)
    server_proc = control.run_background_start(
        ["python3", "http_server3.py", str(port)], f_in=None, f_out=None, f_err=None)


    # test content type:
    time.sleep(1) # wait for the server to start up
    status_code, fields, content = network_util.get_http_response(url, curl_timeout)
    print("test here:\n for %s" % url, status_code, fields, content)

    if status_code is None:
        control.log_comment("-0.5: header request crash / timeout (%s)" % url)
        score -= 0.5

    if fields is None or "content-type" not in fields or "application/json" not in fields["content-type"].lower():
        control.log_comment("-2: 'content-type' should be 'application/json' (%s)" % url)
        score -= 2

    time.sleep(1)
    is_alive = control.run_background_liveness(server_proc)
    if not is_alive:
        control.log_comment("-2: server exited early after visiting (%s)" % url)
        score -= 2

    # exit the server:
    control.run_background_interrupt(server_proc)
    return score

def test_status_code(para_url, score, oracle):
    curl_timeout = 2.5
    # start server:
    port = network_util.scan_available_port(start_port=8000)
    url = "http://%s:%d/" % (HOSTNAME, port)
    url += para_url

    server_proc = control.run_background_start(
        ["python3", "http_server3.py", str(port)], f_in=None, f_out=None, f_err=None)
    time.sleep(1)

    status_code, fields, content = network_util.get_http_response(url, curl_timeout)

    if status_code == None:
        control.log_comment("-%s: request fail / timeout (%s)" % (score, url))
        score = 0
    elif status_code != oracle:
        control.log_comment("-%s: wrong status code (%s)" % (score, url))
        score = 0

    control.run_background_interrupt(server_proc)
    return score

def test_json_body(parameters, score):
    curl_timeout = 2.5
    # start server:
    port = network_util.scan_available_port(start_port=8000)
    url = "http://%s:%d/product?" % (HOSTNAME, port)
    para_list = ['a', 'b', 'c', 'd']
    for i, p in enumerate(parameters):
        url += '%s=%s&' % (para_list[i], p)
    url = url[:-1]

    server_proc = control.run_background_start(
        ["python3", "http_server3.py", str(port)], f_in=None, f_out=None, f_err=None)
    time.sleep(1)

    oracle = get_oracle(parameters)
    oracle_str = get_inf_oracle(parameters)
    exit_code, content, _ = control.run_foreground(["curl", url], timeout_seconds=curl_timeout)
    try:
        print("content for", url,  ":\n", content)
        # control.log_comment(content)
        stu_cnt = json.loads(content)
        # control.log_comment(str(stu_cnt))
        stu_cnt['operands'] = list(map(float, stu_cnt['operands']))
        stu_cnt['result'] = float(stu_cnt['result'])
        # control.log_comment(str(stu_cnt))
        # control.log_comment(str(oracle))

        if json.loads(content) != oracle and json.loads(content) != oracle_str and stu_cnt != oracle:  # Equalness of Python dict is done recursively
            raise
    except:
        control.log_comment("-%s: wrong JSON body (%s)" % (score, url))
        score = 0
    # exit the server:
    control.run_background_interrupt(server_proc)
    return score


def test_4_5_6():
    return test_json_body([4,5,6], 1)

def test_4_5_neg_6():
    return test_json_body([4,5,-6], 1)

def test_neg_5():
    return test_json_body([-5], 1)

def test_inf_3():
    return test_json_body([float('inf'), 3], 1)

def test_inf():
    return test_json_body([10 ** 200, 10 ** 200, 10 ** 200], 1)

def test_404():
    return test_status_code('404', 1, 404)

def test_400_no_number():
    return test_status_code('product?a=2&b=H', 1, 400)

def test_400_no_para():
    return test_status_code('product', 1, 400)


def check_code_for_cheat():
    # TODO: should check whether banned packages were imported.
    return False

def main():
    curr_score = 0
    control.log_comment("Part 4 grading starts!")
    if "http_server3.py" not in os.listdir():
        control.log_comment("'http_server3.py' not found! Zero score!")
        return 0
    if check_code_for_cheat():
        control.log_comment("Code cheating detected! Zero score!")
        return 0
    try:
        test_student_hostname()
        for f in test_basic, test_404, test_400_no_number, test_400_no_para, test_4_5_6, test_4_5_neg_6, test_neg_5, test_inf_3, test_inf,:
            curr_score += f()
    except control.GraderException as err:
        control.handle_grader_exception(err)
        raise
    control.log_comment("Part 4 grading done! Scored %s out of 12.5!" % curr_score)
    return curr_score


if __name__ == "__main__":
    main()