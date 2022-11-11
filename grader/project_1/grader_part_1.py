## The grader of part_1 (http client).
## TODO: Test cases below are just illustration of workflow. They are not final test cases!!!

import grader_util_control as control
import grader_util_html_to_json as html_to_json
import os
import time

class TestUnit:
    def __init__(self, url, is_success, remark, html_file, timeout_seconds, stderr_rule):
        self.url = url
        self.is_success = is_success
        if html_file is None:
            self.html = None
        else:
            with open(html_file, "r") as f:
                self.html = f.read().strip() # removes spaces, \n and \t
                self.html = self.html[self.html.find("<html"):] # remove the doctype line
        self.stderr_rule = stderr_rule
        self.timeout_seconds = timeout_seconds
        self.remark = remark

    def http_get(self):
        self.exit_code, self.stdout_text, self.stderr_text = control.run_foreground(
            ["python3", "http_client.py", self.url],
            timeout_seconds = self.timeout_seconds
        )

    def is_timeout(self):
        return self.exit_code is None

    def is_crashed(self):
        crashed_signatures = "Traceback (most recent call last):", "SyntaxError:"
        for s in crashed_signatures:
            if s in self.stderr_text:
                return True
        return False

    def match_exit_code(self):
        if self.exit_code is None:
            return False
        if self.is_success:
            return self.exit_code == 0
        else:
            return self.exit_code > 0

    def match_exact_html(self):
        assert self.html is not None
        html = self.stdout_text
        # handle bytes:
        try:
            might_be_bytes = eval(html)
            if type(might_be_bytes) is not bytes:
                raise
            html = might_be_bytes.decode()
        except UnicodeDecodeError:
            return False
        except:
            pass
        # filter out student's extra output:
        start = "<html"
        end = "</html>"
        while True:
            pos_start = html.find(start)
            pos_end = html.find(end)
            if pos_start >= 0 and pos_end >= 0:
                html_seg = html[pos_start : pos_end + len(end)]
            else:
                return False
            if html_to_json.parse(self.html) == html_to_json.parse(html_seg):
                return True
            html = html[pos_end + len(end):]
        return False

    def match_loose_html(self):
        assert self.html is not None
        html = self.stdout_text
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, html, self.html).ratio()
        print("Simularity score: %s" % ratio)
        return ratio > 0.5

    def match_stderr(self):
        assert self.stderr_rule is not None
        return self.stderr_rule(self.stderr_text)


def test_0_basic(p):
    print("Grading basic case...")
    score = 25
    case = TestUnit("http://insecure.stevetarzia.com/basic.html", True,
        remark = "basic functionality test",
        html_file = "./test_html_files/basic_test.html",
        timeout_seconds = 20,
        stderr_rule = lambda s: len(s) == 0 ## should be nothing in stderr
    )
    # measuring time
    tick = time.time()
    case.http_get()
    tock = time.time()
    seconds_taken = tock - tick

    # (10) Program does not crash or "technically run forever":
    if case.is_timeout():
        control.log_comment("-10: timeout after %s seconds: %s (%s)" % (case.timeout_seconds, case.url, case.remark))
        score -= 10
    elif case.is_crashed():
        control.log_comment("-10: program crashed: %s (%s)" % (case.url, case.remark))
        score -= 10

    # (8) Able to show html webpage quickly:
    if case.match_exact_html():
        if seconds_taken > 3:
            control.log_comment("-1: took over 3 seconds: %s (%s)" % (case.url, case.remark))
            score -= 1
    elif case.match_loose_html():
        control.log_comment("-3: partially-correct html: %s (%s)" % (case.url, case.remark))
        score -= 3
    else:
        control.log_comment("-5: wrong html: %s (%s)" % (case.url, case.remark))
        score -= 5
    
    # (1) should exit 0:
    if not case.match_exit_code():
        control.log_comment("-1: should exit 0: %s (%s)" % (case.url, case.remark))
        score -= 1

    # (1) should have empty stderr:
    # if not case.match_stderr():
    #     control.log_comment("-1: should not output anything to stderr: %s (%s)" % (case.url, case.remark))
    #     score -= 1
        
    return score


# below are extra cases.
# (5) Special robustness: for each potential functionalities to add, program does not crash or "technically run forever"
#  (-1) for each crash / time out, until 0
class PreChecker:
    def __init__(self):
        self.counter = 5
    def _pre_check(self, case: TestUnit):
        deduct = 1 if self.counter > 0 else 0
        failed = False
        if case.is_timeout():
            control.log_comment("-%s: timeout after %s seconds: %s (%s)" % (deduct, case.timeout_seconds, case.url, case.remark))
            failed = True
        elif case.is_crashed():
            control.log_comment("-%s: program crashed: %s (%s)" % (deduct, case.url, case.remark))
            failed = True
        if failed:
            self.counter -= 1
            return deduct # return score to deduct
        return 0

def test_1_redirect_http(p):
    print("Grading redirect http...")
    score = 1.5
    case = TestUnit("http://insecure.stevetarzia.com/redirect", True,
        remark = "302 redirect to http",
        html_file = "./test_html_files/302_test.html",
        timeout_seconds = 10,
        stderr_rule = None
    )
    case.http_get()
    score -= p._pre_check(case) 
    if not case.match_exact_html():
        control.log_comment("-1: html does not match: %s (%s)" % (case.url, case.remark))
        score -= 1
    if not case.match_exit_code():
        control.log_comment("-0.5: should exit 0: %s (%s)" % (case.url, case.remark))
        score -= 0.5
    return score

def test_2_redirect_https(p):
    print("Grading redirect https...")
    score = 1.5
    case = TestUnit("http://airbedandbreakfast.com/", False,
        remark = "301 redirect to https",
        html_file = None,
        timeout_seconds = 10,
        stderr_rule = lambda s: "https://www.airbnb.com/belong-anywhere" in s
    )
    case.http_get()
    score -= p._pre_check(case)
    # if not case.match_stderr():
    #     control.log_comment("-1: stderr does not match: %s (%s)" % (case.url, case.remark))
    #     score -= 1
    if not case.match_exit_code():
        control.log_comment("-0.5: should exit non-0: %s (%s)" % (case.url, case.remark))
        score -= 0.5
    return score

def test_3_redirect_hell(p):
    print("Grading redirect hell...")
    score = 1.5
    case = TestUnit("http://insecure.stevetarzia.com/redirect-hell", False,
        remark = "should redirect 10 times and exit",
        html_file = None,
        timeout_seconds = 20,
        stderr_rule = lambda s: s.count("http://insecure.stevetarzia.com/redirect-hell") in [9,10,11]
    )
    case.http_get()
    score -= p._pre_check(case)
    # if not case.match_stderr():
    #     control.log_comment("-1: stderr does not match: %s (%s)" % (case.url, case.remark))
    #     score -= 1
    if not case.match_exit_code():
        control.log_comment("-0.5: should exit non-0: %s (%s)" % (case.url, case.remark))
        score -= 0.5
    return score 

def test_4_404(p):
    print("Grading 404...")
    score = 1
    # case = TestUnit("http://cs.northwestern.edu/340", False,
    #     remark = "should print response body when 404",
    #     html_file = "./test_html_files/404_test.html",
    #     timeout_seconds = 10,
    #     stderr_rule = None
    # )
    # case.http_get()
    # score -= p._pre_check(case)
    # if not case.match_exact_html():
    #     control.log_comment("-0.5: html does not match: %s (%s)" % (case.url, case.remark))
    #     score -= 0.5
    # if not case.match_exit_code():
    #     control.log_comment("-0.5: should exit non-0: %s (%s)" % (case.url, case.remark))
    #     score -= 0.5
    return score

def test_5_non_text_html(p):
    print("Grading non text/html...")
    score = 1
    case = TestUnit("http://www.apimages.com/Images/sdgergAP111129193343.jpg", False,
        remark = "should not print unless it is text/html",
        html_file = None,
        timeout_seconds = 10,
        stderr_rule = None
    )
    case.http_get()
    score -= p._pre_check(case)
    if not len(case.stdout_text) == 0:
        control.log_comment("-0.5: should not print anything in stdout: %s (%s)" % (case.url, case.remark))
        score -= 0.5
    if not case.match_exit_code():
        control.log_comment("-0.5: should exit non-0: %s (%s)" % (case.url, case.remark))
        score -= 0.5
    return score

def test_6_port_number(p):
    print("Grading port number...")
    score = 1.5
    case = TestUnit("http://portquiz.net:8080", True,
        remark = "should support port number",
        html_file = "./test_html_files/port_test_8080.html",
        timeout_seconds = 10,
        stderr_rule = None
    )
    case.http_get()
    score -= p._pre_check(case)
    ## There is a line "Your outgoing IP: xxx", this is environment-sensitive, we have to handle it
    # import re
    # IP_PATTERN = "[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}"
    # case.stdout_text = re.sub(IP_PATTERN, "xxx.xxx.xxx.xxx", case.stdout_text)
    # case.html = re.sub(IP_PATTERN, "xxx.xxx.xxx.xxx", case.html)
    if 'Outgoing Port Tester' not in case.html:
        control.log_comment("-1.5: html does not match: %s (%s)" % (case.url, case.remark))
        score -= 1.5
    return score

def test_7_slash(p):
    print("Grading slash...")
    score = 1.5
    case = TestUnit("http://insecure.stevetarzia.com", False,
        remark = "should not require ending slash",
        html_file = "./test_html_files/no_slash_test.html",
        timeout_seconds = 10,
        stderr_rule = None
    )
    case.http_get()
    score -= p._pre_check(case)
    if not case.match_exact_html():
        control.log_comment("-1.5: html does not match: %s (%s)" % (case.url, case.remark))
        score -= 1.5
    return score

def test_8_large_page(p):
    print("Grading large page...")
    score = 1.5
    case = TestUnit("http://insecure.stevetarzia.com/libc.html", True,
        remark = "should support large page",
        html_file = "./test_html_files/big_file_test.html",
        timeout_seconds = 60,
        stderr_rule = None
    )
    # but still I am curious on the time
    tick = time.time()
    case.http_get()
    tock = time.time()
    seconds_taken = tock - tick
    print("took %.3f seconds" % seconds_taken)
    score -= p._pre_check(case)
    if not case.match_exact_html():
        control.log_comment("-1.5: html does not match: %s (%s)" % (case.url, case.remark))
        score -= 1.5
    return score

def test_9_missing_header(p):
    print("Grading missing header...")
    score = 1.5
    case = TestUnit("http://165.124.184.237/CS340-w21/project/rfc2616.html", True,
        remark = "should work when Content-Length header is missing",
        html_file = "./rfc2616.html",
        timeout_seconds = 20,
        stderr_rule = None
    )
    case.http_get()
    score -= p._pre_check(case)
    if not case.match_exact_html():
        control.log_comment("-1.5: html does not match: %s (%s)" % (case.url, case.remark))
        score -= 1.5
    return score


def check_code_for_cheat():
    # TODO: should check whether banned packages were imported.
    return False

def check_server_good():
    exit_code, _, _ = control.run_foreground(
        ["curl", "http://165.124.184.237/CS340-w21/project/rfc2616.html"], timeout_seconds = 10
    )
    if exit_code != 0:
        print(exit_code)
        raise control.GraderException("our server at 80 is down")

    exit_code, _, _ = control.run_foreground(
        ["curl", "http://portquiz.net:8080"], timeout_seconds = 10
    )
    if exit_code != 0:
        raise control.GraderException("our server at 8080 is down")

def main():
    check_server_good()

    curr_score = 0
    control.log_comment("Part 1 grading starts!")
    if "http_client.py" not in os.listdir():
        control.log_comment("'http_client.py' not found! Zero score!")
        return 0
    if check_code_for_cheat():
        control.log_comment("Code cheating detected! Zero score!")
        return 0
    try:
        p = PreChecker()
        for f in (test_0_basic, test_1_redirect_http, test_2_redirect_https, test_3_redirect_hell,
                test_4_404, test_5_non_text_html, test_6_port_number, test_7_slash,
                test_8_large_page, test_9_missing_header):
            curr_score += f(p)
    except control.GraderException as err:
        control.handle_grader_exception(err)
        raise # we might want to debug first??
    control.log_comment("Part 1 grading done! Scored %s out of 37.5!" % curr_score)
    return curr_score
   

if __name__ == "__main__":
    score = main()
    print("SCORE:", score)