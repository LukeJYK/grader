# This is a sketchy implementation. Some details are not taken care of, e.g. unreadable scan_time.
from texttable import Texttable as Table
import json
import sys

def make_caption(content):
    length = 80
    blank = length - 2 - len(content)
    assert blank >= 2
    return "\n".join([
        "@"*length,
        "@" + " "*(length-2) + "@",
        "@" + " "*(blank//2) + content + " "*(blank-blank//2) + "@",
        "@" + " "*(length-2) + "@",
        "@"*length,
    ])

def has(attr, key):
    return key in attr and attr[key] is not None

def count_popularity(l):
    counter = {}
    for item in l:
        if item not in counter:
            counter[item] = 0
        counter[item] += 1
    return sorted(counter.items(), key=lambda x: -x[1])

# 1. A textual or tabular listing of all the information returned in Part 2, with a section for each domain.
def table_1(obj):
    text = make_caption("TABLE 1: PER-URL SCAN INFO")
    section_margin = "\n\n"
    text += section_margin
    for url, attr in obj.items():
        header = "DOMAIN: " + url
        body = Table()
        body.set_deco(Table.HEADER)
        body.header(["Attribute", "Value"])
        for k, v in attr.items():
            body.add_row([k, str(v)])
        text += "\n".join([header, body.draw(), section_margin])
    return text

# 2. A table showing the RTT ranges for all domains, sorted by the minimum RTT (ordered from fastest to slowest).
def table_2(obj):
    text = make_caption("TABLE 2: RTT RANGES") + "\n\n"
    rtts = [(attr["rtt_range"], url) for url, attr in obj.items() if has(attr, "rtt_range")]
    rtts = [(a, b, url) for (a, b), url in rtts]
    rtts.sort()
    body = Table()
    body.set_deco(Table.HEADER)
    body.header(["URL", "RTT Range (ms)"])
    for a, b, url in rtts:
        body.add_row([url, "%d - %d" % (a, b)])
    text += body.draw()
    return text

# 3. A table showing the number of occurrences for each observed root certificate authority (from Part 2i),
# sorted from most popular to least.
def table_3(obj):
    text = make_caption("TABLE 3: POPULAR ROOT CA'S") + "\n\n"
    cas = [attr["root_ca"] for _, attr in obj.items() if has(attr, "root_ca")]
    pop = count_popularity(cas)
    body = Table()
    body.set_deco(Table.HEADER)
    body.header(["CA Name", "Occurence"])
    for name, count in pop:
        body.add_row([name, count])
    text += body.draw()
    return text

# 4. A table showing the number of occurrences of each web server (from Part 2d), ordered from most popular to least.
def table_4(obj):
    text = make_caption("TABLE 4: POPULAR WEB SERVERS") + "\n\n"
    servers = [attr["http_server"] for _, attr in obj.items() if has(attr, "http_server")]
    pop = count_popularity(servers)
    body = Table()
    body.set_deco(Table.HEADER)
    body.header(["Server Name", "Occurence"])
    for name, count in pop:
        body.add_row([name, count])
    text += body.draw()
    return text

# 5. A table showing the percentage of scanned domains supporting:
#  each version of TLS listed in Part 2h.  I expect to see zero percent for SSLv2 and SSLv3.
#  "plain http" (Part 2e)
#  "https redirect" (Part 2f)
#  "hsts" (Part 2g)
#  "ipv6" (from Part 2c)
def table_5(obj):
    text = make_caption("TABLE 5: PENCENTAGES") + "\n\n"
    body = Table()
    body.set_deco(Table.HEADER)
    body.header(["Item", "Percentage (%)"])
    total = len(obj)
    # tls:
    tls = [attr["tls_versions"] for _, attr in obj.items() if has(attr, "tls_versions")]
    for version in "SSLv2","SSLv3","TLSv1.0","TLSv1.1","TLSv1.2","TLSv1.3":
        percent = int(sum(version in item for item in tls) * 100 / total)
        body.add_row([version, percent])
    # others:
    plain_http = [attr["insecure_http"] for _, attr in obj.items() if has(attr, "insecure_http")]
    body.add_row(["plain http", int(sum(item for item in plain_http) * 100 / total)])
    https_redirect = [attr["redirect_to_https"] for _, attr in obj.items() if has(attr, "redirect_to_https")]
    body.add_row(["https redirect", int(sum(item for item in https_redirect) * 100 / total)])
    hsts = [attr["hsts"] for _, attr in obj.items() if has(attr, "hsts")]
    body.add_row(["hsts", int(sum(item for item in hsts) * 100 / total)])
    ipv6 = [attr["ipv6_addresses"] for _, attr in obj.items() if has(attr, "ipv6_addresses")]
    body.add_row(["ipv6", int(sum(len(item) > 0 for item in ipv6) * 100 / total)])
    # sum up:
    text += body.draw()
    return text

def main(input_file, output_file):
    with open(input_file, "r") as f:
        obj = json.load(f)
    text = ""
    for cmd in table_1, table_2, table_3, table_4, table_5:
        text += cmd(obj)
        text += "\n\n\n"
    with open(output_file, "w") as f:
        f.write(text)

if __name__ == "__main__":
    _, input_file, output_file = sys.argv
    main(input_file, output_file)