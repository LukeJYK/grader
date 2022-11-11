import sys
import json
import time

import scanners

def scan(url: str) -> dict:
    print(f"scanning {url}")
    tick = time.time()
    # using scanning tools:
    ipv4_addresses, ipv6_addresses = scanners.IPAddrScanner().scan(url)
    insecure_http = scanners.InsecurityScanner().scan(url)
    redirect_scanner = scanners.RedirectScanner()
    redirect_to_https = redirect_scanner.scan(url)
    http_server = scanners.ServerScanner().scan_final_url(url, redirect_scanner)
    hsts = scanners.HSTSScanner().scan_final_url(url, redirect_scanner)
    tsl_versions = scanners.TLSScanner().scan(url)
    root_ca = scanners.RootCAScanner().scan(url)
    rdns_names = scanners.RDNSScanner().scan(ipv4_addresses)
    rtt_range = scanners.RTTScanner().scan(ipv4_addresses)
    geo_locations = scanners.GeoScanner().scan(ipv4_addresses)
    # summing up:
    result = {
        "scan_time": time.time(),
        "ipv4_addresses": ipv4_addresses,
        "ipv6_addresses": ipv6_addresses,
        "http_server": http_server,
        "insecure_http": insecure_http,
        "redirect_to_https": redirect_to_https,
        "hsts": hsts,
        "tls_versions": tsl_versions,
        "root_ca": root_ca,
        "rdns_names": rdns_names,
        "rtt_range": rtt_range,
        "geo_locations": geo_locations
    }
    tock = time.time()
    t = "*" * int(tock-tick)
    print(f"{t} {url} done in {tock-tick} seconds")
    return {k: v for k, v in result.items()}

def main(input_file: str, output_file: str):
    with open(input_file, "r") as f:
        urls = [line.strip() for line in f.readlines()]
    result = {url: scan(url) for url in urls}
    with open(output_file, "w") as f:
        json.dump(result, f, sort_keys=True, indent=4)

if __name__ == "__main__":
    _, input_file, output_file = sys.argv
    main(input_file, output_file)