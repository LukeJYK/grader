# given result.json where comments are hacked json.

import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def parse():
    with open("results_part_2.json", "r") as f:
        result = json.load(f)
    invalid_netids = []
    name_to_data = {}
    for r in result:
        try:
            data = json.loads(r["comment"])
            name_to_data[f"{r['name']} ({r['id']})"] = data
        except:
            invalid_netids.append(f"{r['name']} ({r['id']}): {r['comment']}")
    return name_to_data

def get_urls():
    with open("test_websites.txt", "r") as f:
        lines = [l.strip() for l in f.readlines()]
    return [l for l in lines if len(l) > 0]

def load_reference():
    with open("reference.json", "r") as f:
        ref = json.load(f)
    return ref

def split_into_lines(s, length):
    rest = s
    lines = []
    if len(s) == 0:
        return ""
    n_lines = (len(s)-1)//length+1
    per_line = (len(s)-1)//n_lines+1
    while len(rest) > 0:
        lines.append(rest[:per_line])
        rest = rest[per_line:]
    return "\n".join(lines)

def entropy_and_hist(l: list) -> (float, list):
    freq = {}
    for e in l:
        if e not in freq:
            freq[e] = 0
        freq[e] += 1
    hist = sorted([(f,e) for e,f in freq.items()], reverse=True)
    # entropy:
    f = np.array(list(freq.values()))
    f = f / np.sum(f)
    entropy = np.sum(-np.log(f) * f)
    return entropy, hist

# a) scan_time
def plot_a(name_to_data, urls, ref):
    return ## Do not plot at all...
    f = "scan_time"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if type(d) not in [float, int]]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]

        plt.subplot(9, 3, i+1)
        ts = pd.Series(data)
        ts.plot.kde()
        plt.yticks([])
        plt.title(url)
        # add reference
        plt.axvline(x=ref[url][f], color="orange")
    plt.savefig("a_scan_time.pdf")

# b) ipv4_address
def plot_b(name_to_data, urls, ref):
    f = "ipv4_addresses"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if type(d) not in [list]]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [len(set(d)) for d in data if d not in bad]
        triplets.append((-sum(data)/len(data), url, data))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, data = triplet
        plt.subplot(9, 3, i+1)
        plt.hist(data, bins=[i-0.5 for i in range(max(data)+1)])
        plt.yticks([])
        plt.xlabel("# of ipv4 addr.")
        plt.title(url)
        # add reference
        plt.axvline(x=len(ref[url][f]), color="orange")
    plt.savefig("b_ipv4_addresses.pdf")

# c) ipv6_address
def plot_c(name_to_data, urls, ref):
    f = "ipv6_addresses"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if type(d) not in [list]]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [len(set(d)) for d in data if d not in bad]
        triplets.append((-sum(data)/len(data), url, data))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, data = triplet
        plt.subplot(9, 3, i+1)
        plt.hist(data, bins=[i-0.5 for i in range(max(data)+1)])
        plt.yticks([])
        plt.xlabel("# of ipv6 addr.")
        plt.title(url)
        # add reference
        plt.axvline(x=len(ref[url][f]), color="orange")
    plt.savefig("c_ipv6_addresses.pdf")

# d) http_server
def plot_d(name_to_data, urls, ref):
    f = "http_server"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.23, bottom=0.05, right=0.95, top=0.95, wspace=1.4, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (d is not None and type(d) not in [str])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [str(d).strip() for d in data if d not in bad]
        entropy, hist = entropy_and_hist(data)
        triplets.append((-entropy, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [h[1] for h in hist]
        values = [h[0] for h in hist]
        # reference
        r = ref[url][f]
        if type(r) is not list:
            r = [r]
        r = [str(ri) for ri in r]
        for ri in r:
            if ri not in labels and "*" not in ri:
                labels.append(ri)
                values.append(0)
        plt.barh(range(len(labels)), values, align="center")
        plt.yticks(range(len(labels)), labels=[split_into_lines(l, 25) for l in labels])
        plt.xlabel("# of answers")
        plt.title(url)
        # add reference
        for ri in r:
            if "*" in ri:
                for l in labels:
                    if all(seg in l for seg in ri.split("*")):
                        plt.axhline(y=labels.index(l), color="orange")
            else:
                plt.axhline(y=labels.index(ri), color="orange")
    plt.savefig("d_http_server.pdf")

# e) insecure_http
def plot_e(name_to_data, urls, ref):
    f = "insecure_http"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (type(d) not in [bool])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]
        hist = [len([d for d in data if d]), len([d for d in data if not d])]
        deviation = (max(hist)-min(hist))/len(hist)
        triplets.append((deviation, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [True, False]
        values = hist
        plt.barh([0,1], values, align="center")
        plt.yticks(range(len(labels)), labels=labels)
        plt.xlabel("# of answers")
        plt.title(url)
        # add reference
        plt.axhline(y=0 if ref[url][f] else 1, color="orange")
    plt.savefig("e_insecure_http.pdf")

# f) redirect_to_https
def plot_f(name_to_data, urls, ref):
    f = "redirect_to_https"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (type(d) not in [bool])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]
        hist = [len([d for d in data if d]), len([d for d in data if not d])]
        deviation = (max(hist)-min(hist))/len(hist)
        triplets.append((deviation, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [True, False]
        values = hist
        plt.barh([0,1], values, align="center")
        plt.yticks(range(len(labels)), labels=labels)
        plt.xlabel("# of answers")
        plt.title(url)
        # add reference
        plt.axhline(y=0 if ref[url][f] else 1, color="orange")
    plt.savefig("f_redirect_to_https.pdf")

# g) hsts
def plot_g(name_to_data, urls, ref):
    f = "hsts"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (type(d) not in [bool])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]
        hist = [len([d for d in data if d]), len([d for d in data if not d])]
        deviation = (max(hist)-min(hist))/len(hist)
        triplets.append((deviation, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [True, False]
        values = hist
        plt.barh([0,1], values, align="center")
        plt.yticks(range(len(labels)), labels=labels)
        plt.xlabel("# of answers")
        plt.title(url)
        # add reference
        plt.axhline(y=0 if ref[url][f] else 1, color="orange")
    plt.savefig("g_hsts.pdf")

# h) tls_versions
def plot_h(name_to_data, urls, ref):
    f = "tls_versions"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.1, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)
    enums = ["SSLv2","SSLv3","TLSv1.0","TLSv1.1","TLSv1.2","TLSv1.3"]

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (type(d) not in [list])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]
        hist = [len([d for d in data if e in d]) for e in enums]
        deviation = sum(max(hi/len(data),1-hi/len(data)) for hi in hist)
        triplets.append((deviation, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = enums
        values = hist
        plt.barh(range(6), values, align="center")
        plt.yticks(range(len(labels)), labels=labels)
        plt.xlabel("# of answers")
        plt.xlim([0, len(name_to_data)])
        plt.title(url)
        # add reference
        for i, e in enumerate(enums):
            if e in ref[url][f]:
                plt.axhline(y=i, color="orange")
    plt.savefig("h_tls_versions.pdf")

# i) root_ca
def plot_i(name_to_data, urls, ref):
    f = "root_ca"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.23, bottom=0.05, right=0.95, top=0.95, wspace=1.4, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (d is not None and type(d) not in [str])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [str(d).strip() for d in data if d not in bad]
        entropy, hist = entropy_and_hist(data)
        triplets.append((-entropy, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [h[1] for h in hist]
        values = [h[0] for h in hist]
        # reference
        r = ref[url][f]
        if type(r) is not list:
            r = [r]
        r = [str(ri) for ri in r]
        for ri in r:
            if ri not in labels:
                labels.append(ri)
                values.append(0)
        plt.barh(range(len(labels)), values, align="center")
        plt.yticks(range(len(labels)), labels=[split_into_lines(l, 25) for l in labels])
        plt.xlabel("# of answers")
        plt.title(url)
        # add reference
        for ri in r:
            plt.axhline(y=labels.index(ri), color="orange")
    plt.savefig("i_root_ca.pdf")

# j) rdns_names
def plot_j(name_to_data, urls, ref):
    f = "rdns_names"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if type(d) not in [list]]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [len(set(d)) for d in data if d not in bad]
        triplets.append((-sum(data)/len(data), url, data))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, data = triplet
        plt.subplot(9, 3, i+1)
        plt.hist(data, bins=[i-0.5 for i in range(max(data)+1)])
        plt.yticks([])
        plt.xlabel("# of rdns names")
        plt.title(url)
        # add reference
        plt.axvline(x=len(ref[url][f]), color="orange")
    plt.savefig("j_rdns_names.pdf")

# k) rtt_range
def plot_k(name_to_data, urls, ref):
    f = "rtt_range"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.3, hspace=0.5)

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if type(d) not in [list] or len(d) != 2 or any(type(x) not in [int, float] or x < 1 or x > 1000 for x in (d[0],d[1]))]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [d for d in data if d not in bad]
        mn, mx = np.array([d[0] for d in data]), np.array([d[1] for d in data])
        deviation = np.mean((mn-np.mean(mn))**2) * np.mean((mx-np.mean(mx))**2)
        triplets.append((-deviation, url, data))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, data = triplet
        plt.subplot(9, 3, i+1)
        ts1, ts2 = pd.Series([d[0] for d in data]), pd.Series([d[1] for d in data])
        ts1.plot.kde(color=(0.0,0.5,0.8), label="min")
        ts2.plot.kde(color=(0.5,0.0,0.8), label="max")
        plt.yticks([])
        plt.xlim([0,600])
        plt.xlabel("rtt (ms)")
        plt.legend()
        plt.title(url)
        # add no reference...
        # if ref[url][f] is not None:
        #     plt.axvline(x=ref[url][f][0], color="orange")
        #     plt.axvline(x=ref[url][f][1], color="orange")
    plt.savefig("k_rtt_range.pdf")

# l) geo_locations
def plot_l(name_to_data, urls, ref):
    f = "geo_locations"
    plt.figure(figsize=(12, 30))
    plt.suptitle(f)
    plt.subplots_adjust(left=0.20, bottom=0.05, right=0.95, top=0.95, wspace=1.5, hspace=0.5)

    def normalize(d):
        s = d.split(",")
        s = [si.strip() for si in s] # no deduction
        s = [si for si in s if len(si) > 0] # however, might deduct points if there is empty items
        d = ", ".join(s)
        d = d.strip(".") # this might deduct too
        return d

    # sort url:
    triplets = []
    for i, url in enumerate(urls):
        data = [v[url][f] for k, v in name_to_data.items() if url in v and f in v[url]]
        bad = [d for d in data if (d is not None and type(d) not in [list])]
        print("%.2f" % ((len(data)-len(bad)) / len(name_to_data)), "    ", url)
        data = [set(str(di) for di in d) for d in data if d not in bad]
        data = [[normalize(di) for di in d] for d in data]
        dd = []
        for d in data:
            dd += d
        entropy, hist = entropy_and_hist(dd)
        triplets.append((-entropy, url, hist))
        triplets.sort()
    # plot:
    for i, triplet in enumerate(triplets):
        _, url, hist = triplet
        plt.subplot(9, 3, i+1)
        labels = [h[1] for h in hist]
        values = [h[0] for h in hist]
        # reference
        r = [str(ri) for ri in ref[url][f]]
        for ri in r:
            if ri not in labels:
                labels.append(ri)
                values.append(0)
        plt.barh(range(len(labels)), values, align="center")
        plt.yticks(range(len(labels)), labels=labels, fontsize=6)
        plt.xlabel("# of answers")
        plt.title(url)
        # add no reference
        # for ri in r:
        #     plt.axhline(y=labels.index(ri), color="orange")
    plt.savefig("l_geo_locations.pdf")

if __name__ == "__main__":
    name_to_data = parse()
    urls = get_urls()
    ref = load_reference()
    for f in plot_a, plot_b, plot_c, plot_d, plot_e, plot_f, plot_g, plot_h, plot_i, plot_j, plot_k, plot_l:
        f(name_to_data, urls, ref)