# calculate part 2 scores

import json

# Does not verify field correctness. I will figure out how to punish the invalid fields
def parse_and_verify():
    with open("results_part_2.json", "r") as f:
        result = json.load(f)
    invalid_students = []
    id_to_data = {}
    for r in result:
        try:
            data = json.loads(r["comment"])
            if "scan_time" in data:
                del data["scan_time"]
            if type(data) != dict and len(data) != 27:
                raise
            if any(type(v) != dict for k,v in data.items()):
                raise
            id_to_data[r["id"]] = data
        except:
            invalid_students.append(f"{r['name']} ({r['id']})")
    if len(invalid_students) > 0:
        print(invalid_students)
        assert False # I hope there is not!!
    return id_to_data

def load_urls():
    with open("test_websites.txt", "r") as f:
        lines = [l.strip() for l in f.readlines()]
    return [l for l in lines if len(l) > 0]

def load_reference():
    with open("reference.json", "r") as f:
        ref = json.load(f)
    return ref

def load_dns_resolvers():
    with open("public_dns_resolvers.txt", "r") as f:
        lines = [l.strip() for l in f.readlines()]
    return set(l for l in lines if len(l) > 0)

def adjusted(score, d):
    mapped = 0
    for x, y in d.items():
        if score >= x:
            mapped = max(mapped, y)
    return mapped

# below are per-scanner graders: (raw score is 0-100 per url, adjusted score is 0-6, from the average raw scores.)
#
# auto-correction: auto-correct things, like misspelled field, wrong format, space stripping, wrong unit like ms/s, and so on, before grading.
# in such case, some % of points can be deducted.
# 
# for raw_score, assume it is corrected data from auto_correction function, and raise for unexpected situations.
#
class a_scan_time:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "scan_time"

    # a value ususally between 0-2, and 1 by default. For weighted average.
    # if weight is zero, the students' answers will not be checked at all
    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        if url not in self.id_to_data[student_id]:
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        assert (ans is None) or (type(ans) == int) or (type(ans) == float)
        if ans is None:
            return 0
        return 100 # Yes, simply give 100, score-giver

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            0: 3,
            30: 4,
            60: 5,
            90: 5.5,
            100: 6
        })


class b_ipv4_addresses:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "ipv4_addresses"
        self.dns = load_dns_resolvers()

    def weight(self, url) -> float:
        l = len(self.ref[url][self.field])
        return min(3, l)

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            if "ipv4" not in self.id_to_data[student_id][url]:
                print(2, student_id, url)
                return 0
            else:
                deduction_rate += 0.2 # misspelled field name
            ans = self.id_to_data[student_id][url]["ipv4"]
        else:
            ans = self.id_to_data[student_id][url][self.field]
        if (ans is None) or (type(ans) != list):
            print(3, student_id, url)
            return 0
        ## no duplicates:
        l0 = len(ans)
        ans = set([a.strip() for a in ans])
        if len(ans) < l0:
            deduction_rate += 0.1
        ## no DNS:
        if len(ans & self.dns) > 0:
            deduction_rate += 0.1
        ## no bad-format addresses:
        def is_ipv4(s):
            if type(s) != str: return False
            segs = s.split(".")
            if len(segs) == 4 and all(all(c in "0123456789" for c in seg) for seg in segs):
                return True
            return False
        if any(not is_ipv4(s) for s in ans):
            deduction_rate += 0.1
        ## covering the ref addresses:
        ref_addr = set(self.ref[url][self.field])
        if len(ref_addr) == 0:
            rate = 1
        else:
            rate = len(ans & ref_addr) / len(ref_addr)
        score = min(1, rate*1.5)
        return 100 * score * (1-deduction_rate)
    
    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            30: 4,
            60: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class c_ipv6_addresses:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "ipv6_addresses"

    def weight(self, url) -> float:
        l = len(self.ref[url][self.field])
        return min(3, l)+0.5

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            if "ipv6" not in self.id_to_data[student_id][url]:
                print(2, student_id, url)
                return 0
            else:
                deduction_rate += 0.2 # misspelled field name
            ans = self.id_to_data[student_id][url]["ipv6"]
        else:
            ans = self.id_to_data[student_id][url][self.field]
        if ans is None:
            ans = []
        if (type(ans) != list):
            print(3, student_id, url)
            return 0
        ## no duplicates:
        l0 = len(ans)
        ans = set([a.strip() for a in ans])
        if len(ans) < l0:
            deduction_rate += 0.1
        ## no bad-format addresses:
        def is_ipv6(s):
            if type(s) != str: return False
            segs = s.split(":")
            if all(all(c in "0123456789ABCDEFabcdef" for c in seg) for seg in segs):
                return True
            return False
        if any(not is_ipv6(s) for s in ans):
            deduction_rate += 0.1
        ## covering the ref addresses:
        ref_addr = set(self.ref[url][self.field])
        if len(ref_addr) == 0:
            rate = 1
        else:
            rate = len(ans & ref_addr) / len(ref_addr)
        score = min(1, rate*1.5)
        return 100 * score * (1-deduction_rate)
    
    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            20: 4,
            40: 4.5,
            60: 5,
            80: 5.5,
            90: 6
        })


class d_http_server:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "http_server"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if (ans is not None and type(ans) != str):
            print(3, student_id, url)
            return 0
        ans = str(ans).strip()
        refs = self.ref[url][self.field]
        if type(refs) != list:
            refs = [refs]
        refs = [str(r) for r in refs]
        def exact_match(s, p):
            if s == p:
                return True
            if "*" in p and all(pi in s for pi in p.split("*")):
                return True
            return False
        def rough_match(s, p):
            from difflib import SequenceMatcher
            ratio = SequenceMatcher(None, s, p).ratio()
            return ratio
        def get_score(ans, ref):
            return 100 if exact_match(ans, ref) else 80 * rough_match(ans, ref)
        return max(get_score(ans, ref) for ref in refs) * (1-deduction_rate)

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            30: 4,
            60: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class e_insecure_http:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "insecure_http"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != bool:
            print(3, student_id, url)
            return 0
        ref = self.ref[url][self.field]
        if ans == ref:
            return 100
        return 10

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            5: 2,
            10: 2.5,
            20: 3,
            30: 3.5,
            50: 4,
            70: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class f_redirect_to_https:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "redirect_to_https"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != bool:
            print(3, student_id, url)
            return 0
        ref = self.ref[url][self.field]
        if ans == ref:
            return 100
        return 10

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            5: 2,
            10: 2.5,
            20: 3,
            30: 3.5,
            50: 4,
            70: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class g_hsts:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "hsts"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != bool:
            # print(3, student_id, url)
            # return 0
            ans = False if ans is None else True
            deduction_rate += 0.5 # incorrect type
        ref = self.ref[url][self.field]
        if ans == ref:
            return 100 * (1-deduction_rate)
        return 10 * (1-deduction_rate)

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            5: 2,
            10: 2.5,
            20: 3,
            30: 3.5,
            50: 4,
            70: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class h_tls_versions:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "tls_versions"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            if "tls_version" not in self.id_to_data[student_id][url]:
                print(2, student_id, url)
                return 0
            else:
                deduction_rate += 0.2 # misspelled name
                ans = self.id_to_data[student_id][url]["tls_version"]
        else:
            ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != list:
            print(3, student_id, url)
            return 0
        ref = self.ref[url][self.field]
        score = 100
        for s in "SSLv2","SSLv3","TLSv1.0","TLSv1.1","TLSv1.2","TLSv1.3":
            if (s in ans) != (s in ref):
                score -= 15
        score *= (1-deduction_rate)
        return score

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            5: 2,
            10: 2.5,
            20: 3,
            40: 3.5,
            60: 4,
            80: 4.5,
            90: 5,
            95: 5.5,
            98: 6
        })


class i_root_ca:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "root_ca"

    def weight(self, url) -> float:
        return 1

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if (ans is not None and type(ans) != str):
            print(3, student_id, url)
            return 0
        ans = str(ans).strip()
        refs = self.ref[url][self.field]
        if type(refs) != list:
            refs = [refs]
        refs = [str(r) for r in refs]
        def exact_match(s, p):
            if s == p:
                return True
            if "*" in p and all(pi in s for pi in p.split("*")):
                return True
            return False
        def rough_match(s, p):
            from difflib import SequenceMatcher
            ratio = SequenceMatcher(None, s, p).ratio()
            return ratio
        def get_score(ans, ref):
            return 100 if exact_match(ans, ref) else 80 * rough_match(ans, ref)
        return max(get_score(ans, ref) for ref in refs) * (1-deduction_rate)

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            0: 1,
            5: 1.5,
            10: 2,
            15: 2.5,
            20: 3,
            30: 3.5,
            40: 4,
            60: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class j_rdns_names:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "rdns_names"

    def weight(self, url) -> float:
        l = len(self.ref[url][self.field])
        return min(3, l)+0.5

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            if "rdns_name" not in self.id_to_data[student_id][url]:
                print(2, student_id, url)
                return 0
            else:
                deduction_rate += 0.2 # misspelled name
                ans = self.id_to_data[student_id][url]["rdns_name"]
        else:
            ans = self.id_to_data[student_id][url][self.field]
        if ans is None:
            ans = []
        if (type(ans) != list):
            print(3, student_id, url)
            return 0
        ## no duplicates:
        l0 = len(ans)
        ans = set([a.strip().strip(".") for a in ans])
        if len(ans) < l0:
            deduction_rate += 0.1
        ## covering the ref addresses:
        ref_addr = set(self.ref[url][self.field])
        if len(ref_addr) == 0:
            rate = 1
        else:
            rate = len(ans & ref_addr) / len(ref_addr)
        score = min(1, rate*2)
        return 100 * score * (1-deduction_rate)
    
    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            10: 3,
            30: 3.5,
            50: 4,
            70: 4.5,
            80: 5,
            90: 5.5,
            95: 6
        })


class k_rtt_range:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "rtt_range"

    def weight(self, url) -> float:
        return 1 if (self.ref[url][self.field] is not None) else 0

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != list or len(ans) != 2 or any(type(a) not in [int, float] for a in ans):
            print(3, student_id, url)
            return 10 if ans is not None else 0 # give something if it is anything ever
        ref = self.ref[url][self.field]
        def err(ans, ref):
            err0 = abs(ans[0]-ref[0])/(10+ref[0])
            err1 = abs(ans[1]-ref[1])/(10+ref[1])
            return max(0, min(1, err0 + err1 - 0.2))
        score = max(
            80*(1-err(ans,ref))+20,
            60*(1-err([ans[0]*1000, ans[1]*1000],ref))+10 # punish of unit
        )
        score *= (1-deduction_rate)
        return score

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            10: 2,
            20: 4,
            50: 4.5,
            70: 5,
            85: 5.5,
            95: 6
        })


class l_geo_locations:
    def __init__(self, id_to_data, ref):
        self.id_to_data = id_to_data
        self.ref = ref
        self.field = "geo_locations"

    def weight(self, url) -> float:
        return 1 if len(self.ref[url][self.field]) > 0 else 0

    def raw_score(self, student_id, url) -> float:
        deduction_rate = 0
        if url not in self.id_to_data[student_id]:
            print(1, student_id, url)
            return 0
        if self.field not in self.id_to_data[student_id][url]:
            print(2, student_id, url)
            return 0
        ans = self.id_to_data[student_id][url][self.field]
        if ans is None or type(ans) != list or any(type(a) != str for a in ans):
            print(3, student_id, url)
            return 0
        # ans normalization:
        def normalize(d):
            local_rate = 0
            if len(d) == 0:
                local_rate += 0.05
            s = d.split(",")
            l0 = len(s)
            s = [si.strip() for si in s] # no deduction
            s = [si for si in s if len(si) > 0] # however, might deduct points if there is empty items
            if len(s) < l0:
                local_rate += 0.05
            d = ", ".join(s)
            l1 = len(d)
            d = d.strip(".") # this might deduct too
            if len(d) < l1:
                local_rate += 0.05
            return d, local_rate
        n_ans = []
        for a in ans:
            d, r = normalize(a)
            n_ans.append(d)
            deduction_rate += (r / len(ans))
        l = len(n_ans)
        n_ans = set(n_ans)
        if len(n_ans) < l:
            deduction_rate += 0.1 # duplicate elements
        # compare with ref:
        ref = self.ref[url][self.field]
        hit = 0
        for r in ref:
            city, province, country = r.split(", ")
            if any(city in n and country in n for n in n_ans):
                hit += 1
        score = 80 * hit / len(ref) + 20
        score *= (1-deduction_rate)
        return score

    def adjusted_score(self, raw_average) -> float:
        return adjusted(raw_average, {
            10: 3,
            20: 3.5,
            40: 4,
            60: 4.5,
            80: 5,
            85: 5.5,
            90: 6
        })
        

def test(class_name, has_adjust, debug=False):
    id_to_data = parse_and_verify()
    urls = load_urls()
    ref = load_reference()
    # start test
    tester = class_name(id_to_data, ref)
    id_to_raw = {}
    id_to_adj = {}
    for student_id in tester.id_to_data:
        scores, weights = [], []
        for url in urls:
            w = tester.weight(url)
            if w == 0:
                continue
            s = tester.raw_score(student_id, url)
            scores.append(s)
            weights.append(w)
        weighted_average = sum(s*w for s,w in zip(scores, weights)) / sum(weights)
        id_to_raw[student_id] = weighted_average
        if has_adjust:
            id_to_adj[student_id] = tester.adjusted_score(weighted_average)
    # give me the distribution
    if debug:
        print([float("%.2f"%v) for v in sorted(id_to_raw.values())])
    for k, v in id_to_raw.items():
        if v < 20:
            if debug:
                print(k,v)
    if has_adjust:
        if debug:
            print([float("%.1f"%v) for v in sorted(id_to_adj.values())])
        return id_to_adj


def main():
    with open("results_part_2.json", "r") as f:
        data = json.load(f)
    ret = []
    id_to_pts = {}
    for student in data:
        id_to_pts[student["id"]] = []
    parts = [
        a_scan_time, b_ipv4_addresses, c_ipv6_addresses, d_http_server, e_insecure_http, f_redirect_to_https,
        g_hsts, h_tls_versions, i_root_ca, j_rdns_names, k_rtt_range, l_geo_locations
    ]
    part_names = [
        "a) scan_time", "b) ipv4_addresses", "c) ipv6_addresses", "d) http_server", "e) insecure_http", "f) redirect_to_https",
        "g) hsts", "h) tls_versions", "i) root_ca", "j) rdns_names", "k) rtt_range", "l) geo_locations"
    ]
    for part in parts:
        id_to_adj = test(part, True)
        for student_id, pt in id_to_adj.items():
            id_to_pts[student_id].append(pt)

    for student in data:
        score = 0
        comment = "Part 2 grading:\n"
        i = 0
        for pt in id_to_pts[student["id"]]:
            score += pt
            comment += f"{pt:.1f}/6.0 for {part_names[i]}\n"
            i += 1
        comment += f"Part 2 result: {score:.1f}/72.0 received.\n"

        ret.append({
            "id": student["id"],
            "name": student["name"],
            "is_valid": True,
            "score": score,
            "comment": comment,
        })

    with open("scores_part_2.json", "w") as f:
        json.dump(ret, f, indent=2)

if __name__ == "__main__":
    main()