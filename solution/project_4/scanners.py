from utils import safe_check_output, log
import maxminddb
import time
import typing as T

# b) ipv4_addresses
# c) ipv6_addresses
# using nslookup to get ipv4+ipv6 addresses.
class IPAddrScanner:
    def __init__(self, enabled=True):
        with open("public_dns_resolvers.txt", "r") as f:
            self.dns_list = [line.strip() for line in f.readlines()]

    def _scan_once(self, url:str, dns:str, is_ipv4:bool) -> T.Set[str]:
        flag = "-type=" + ("A" if is_ipv4 else "AAAA")
        cmd = ["nslookup", flag, url]
        if dns: # else, use our local DNS server:
            cmd.append(dns)
        ret = safe_check_output(cmd, _timeout=2)
        if ret is None:
            return set()

        addrs = set()
        # skip the first 2 lines, they are just our own DNS server:
        for line in ret.splitlines()[2:]:
            if "#53" in line: # it is hacky, but anyway
                continue
            prefix = "Address:"
            if line.startswith(prefix):
                addrs.add(line[len(prefix):].strip())
        return addrs

    def _scan_multiple_times(self, n:int, url:str, dns:str, is_ipv4:bool) -> T.Set[str]:
        addrs = set()
        l = 0
        diff = []
        name = "ipv4" if is_ipv4 else "ipv6"
        for i in range(n):
            # early stop:
            if len(diff) > 10 and sum(diff[-10:]) == 0:
                break
            l0 = l
            addr = self._scan_once(url, dns, is_ipv4)
            addrs |= addr
            l = len(addrs)
            diff.append(l-l0)
        # log(f"For url={url}, dns={dns}, n={n}, {name}, diff is {diff}.\nA total of {l} found!")
        return addrs

    def scan(self, url:str) -> (T.List[str], T.List[str]):
        scan_times = 100 # It is for the grader. Don't you scan that much!
        v4addr = self._scan_multiple_times(scan_times, url, None, is_ipv4=True)
        v6addr = self._scan_multiple_times(scan_times, url, None, is_ipv4=False)
        for dns in self.dns_list:
            v4addr |= self._scan_multiple_times(scan_times, url, dns, is_ipv4=True)
            v6addr |= self._scan_multiple_times(scan_times, url, dns, is_ipv4=False)
        return sorted(v4addr), sorted(v6addr)

# d) http_server
# scan http server info from HTTP header.
# methods: curl / python http.client / openssl
# for simplicity, just using curl (can it work??...)
class ServerScanner:
    def _scan_curl(self, url:str) -> T.Optional[str]:
        timeout_seconds = 5
        cmd = ["curl", "-m", str(timeout_seconds), "-I", url]
        ret = safe_check_output(cmd)
        if ret is None:
            return None
        prefix = "server:"
        for line in ret.splitlines():
            if line.lower().startswith(prefix):
                return line[len(prefix):].strip()
        print(f"Woah... response to {cmd} has no server info?")
        return None

    def scan(self, url:str) -> T.Optional[str]:
        return self._scan_curl(url)

    def scan_final_url(self, url, redirect_scanner) -> T.Optional[str]:
        _, url = redirect_scanner._scan_curl(url)
        if url is None:
            return None
        return self.scan(url)

# e) insecure_http
# for simplicity just curl. extremely sketchy
class InsecurityScanner:
    def _scan_curl(self, url:str) -> bool:
        timeout_seconds = 2
        cmd = ["curl", "-m", str(timeout_seconds), url+":80"]
        ret = safe_check_output(cmd)
        if ret is None:
            return False
        return True

    def scan(self, url:str) -> bool:
        return self._scan_curl(url)

# f) https redirect
# again, just curl. still, very sketchy code
class RedirectScanner:
    # cache the result to avoid re-scanning
    cached_result = {}

    # return the final URL, too
    def _scan_curl(self, url:str) -> (bool, T.Optional[str]):
        if url in self.cached_result:
            return self.cached_result[url]

        redirect_count = 0
        timeout_seconds = 5
        curr_url = url
        while redirect_count < 10:
            cmd = ["curl", "-m", str(timeout_seconds), "-I", curr_url]
            ret = safe_check_output(cmd)
            if ret is None:
                self.cached_result[url] = False, curr_url
                return self.cached_result[url]
            lines = ret.splitlines()

            http_code = None
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("HTTP/"):
                    http_code = int(parts[1])
            if http_code is None:
                print("What???")
                return None, None
            
            if http_code >= 300 and http_code < 400: # is redirect
                prefix = "location:"
                for line in lines:
                    if line.lower().startswith(prefix):
                        curr_url = line[len(prefix):].strip()
                if curr_url.startswith("https://"):
                    self.cached_result[url] = True, curr_url
                    return self.cached_result[url]
            else:
                self.cached_result[url] = curr_url.startswith("https://"), curr_url
                return self.cached_result[url]
        print(f"Too many redirect for {url}")
        self.cached_result[url] = False, None
        return self.cached_result[url]

    def scan(self, url:str) -> bool:
        res, _ = self._scan_curl(url)
        return res

# g) hsts (HTTP Strict Transport Security)
class HSTSScanner:
    def _scan_curl(self, url:str) -> bool:
        timeout_seconds = 5
        cmd = ["curl", "-m", str(timeout_seconds), "-I", url]
        ret = safe_check_output(cmd)
        if ret is None:
            return None
        prefix = "strict-transport-security:"
        for line in ret.splitlines():
            if line.lower().startswith(prefix):
                return True
        return False

    def scan(self, url:str) -> bool:
        return self._scan_curl(url)

    def scan_final_url(self, url, redirect_scanner) -> bool:
        _, url = redirect_scanner._scan_curl(url)
        if url is None:
            return None
        return self.scan(url)

# h) tls_versions
# nmap is not used; they are too slow!!!
class TLSScanner:
    # also, they will not be considered when grading.
    options = {
        "-tls1": "TLSv1.0",
        "-tls1_1": "TLSv1.1",
        "-tls1_2": "TLSv1.2",
        "-tls1_3": "TLSv1.3"
    }

    def _scan_openssl(self, version, url:str) -> T.Set[str]:
        cmd = ["openssl", "s_client", version, "-connect", url+":443"]
        ret = safe_check_output(cmd, _input="", _timeout=5)
        if ret is None:
            return set()
        for line in ret.splitlines():
            if self.options[version] in line:
                return {self.options[version]}
        return set()

    def scan(self, url) -> T.List[str]:
        res = set()
        for option in self.options:
            res |= self._scan_openssl(option, url)
        return sorted(res)

# i) root_ca
class RootCAScanner:
    def _scan_openssl(self, url:str) -> T.Optional[str]:
        cmd = ["openssl", "s_client", "-connect", url+":443"]
        ret = safe_check_output(cmd, _input="", _timeout=5)
        if ret is None:
            return None
        # very very hacky:
        for line in ret.splitlines():
            if line.startswith("depth="):
                left = "O = "
                i = line.find(left)
                if i < 0:
                    print("What??")
                    return None
                line = line[i+len(left):]
                if line[0] == "\"":
                    line = line[1:]
                    line = line[:line.find("\"")]
                else:
                    j = line.find(",")
                    if j >= 0:
                        line = line[:j]
                return line
        print("What???")
        return None

    def scan(self, url) -> T.Optional[str]:
        return self._scan_openssl(url)

# j) rdns_names
class RDNSScanner:
    def _scan_ip_nslookup(self, ip:str) -> T.Set[str]:
        cmd = ["nslookup", "-type=PTR", ip]
        ret = safe_check_output(cmd, _timeout=2)
        answers = set()
        if ret is None:
            return set()
        for line in ret.splitlines()[2:]:
            left = "name = "
            i = line.find(left)
            if i >= 0:
                line = line[i+len(left):]
                answer = line.strip()[:-1]
                answers.add(answer)
        return answers

    def _scan_multiple_times(self, n:int, ip:str) -> T.Set[str]:
        addrs = set()
        l = 0
        diff = []
        for i in range(n):
            l0 = l
            addr = self._scan_ip_nslookup(ip)
            addrs |= addr
            l = len(addrs)
            diff.append(l-l0)
        #log(f"For ip={ip}, diff is {diff}.\nA total of {l} found!")
        return addrs

    def scan(self, ips: T.List[str]) -> T.List[str]:
        answers = set()
        scan_times = 5 # no need to scan multiple times, but I just do it for sure
        for ip in ips:
            answers |= self._scan_multiple_times(scan_times, ip)
        return sorted(answers)

# k) rtt_range
class RTTScanner:
    def _scan_ip_telnet(self, ip:str) -> T.Optional[float]:
        cmd = ["telnet", ip, "443"]
        tick = time.time()
        ret = safe_check_output(cmd, _input=b"\x1dclose\x0d", _timeout=2)
        tock = time.time()
        if ret is None:
            return None
        return (tock - tick) * 1000

    def _scan_once(self, ips: T.List[str]) -> T.Optional[T.List[float]]:
        answers = [self._scan_ip_telnet(ip) for ip in ips]
        answers = [ans for ans in answers if ans is not None]
        if len(answers) == 0:
            return None
        return [min(answers), max(answers)]
    
    def _scan_multiple_times(self, n:int, ips: T.List[str]) -> T.Optional[T.List[float]]:
        mins, maxs = [], []
        for i in range(n):
            answer = self._scan_once(ips)
            if answer is not None:
                mn, mx = answer
                mins.append(mn)
                maxs.append(mx)
        if len(mins) < n or max(maxs) >= 1000:
            log(f"BAD EXAMPLE, DO NOT TEST")
            return None
        mean_min = sum(mins) / len(mins)
        mean_max = sum(maxs) / len(maxs)
        # just for logging:
        for array in mins, maxs:
            # log(f"array: {' '.join(('%.2f' % elem) for elem in array)}")
            # log(f"min: {min(array):.2f}, max: {max(array):.2f}")
            mean = sum(array) / len(array)
            # sd = (sum((elem - mean)**2 for elem in array) / len(array)) ** 0.5
            # log(f"mean: {mean:.2f}, sd: {sd:.2f}")
            # log(f"3m ratio: {(min(array)/mean):.2f} to {(max(array)/mean):.2f}")
            if min(array) < mean * 0.8 or max(array) > mean * 1.4:
                log(f"BAD EXAMPLE, DO NOT TEST")
                return None
        # log(f"result: [{int(mean_min)}, {int(mean_max)}]")
        return [int(mean_min), int(mean_max)]

    def scan(self, ips: T.List[str]) -> T.Optional[T.List[float]]:
        return self._scan_multiple_times(10, ips)

# l) geo_locations
class GeoScanner:
    reader = maxminddb.open_database("GeoLite2-City.mmdb")

    def _scan_ip(self, ip: str) -> str:
        try:
            data = self.reader.get(ip)
            loc = []
            if "city" in data:
                loc.append(data["city"]["names"]["en"])
            if "subdivisions" in data:
                for subdivision in data["subdivisions"]:
                    loc.append(subdivision["names"]["en"])
            if "country" in data:
                loc.append(data["country"]["names"]["en"])
            if len(loc) != 3:
                return None ## We only test on 3-tuples!
            return ", ".join(loc)
        except Exception as e:
            print("What????")
            log("Geo Scanner exception:" + str(e))
            return None

    def scan(self, ips: T.List[str]) -> T.List[str]:
        answers = set()
        for ip in ips:
            answer = self._scan_ip(ip)
            if answer is not None:
                answers.add(answer)
        return sorted(answers)