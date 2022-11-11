# ADD on-the-fly

import grader_util_control as control
import socket
import time
import requests

# https://stackoverflow.com/questions/43270868/verify-if-a-local-port-is-available-in-python
# be aware of race conditions; use ASAP when scanned
def scan_available_port(start_port, max_attempt=10000, udp=False):
    for i in range(max_attempt):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM)
        try:
            sock.bind(("0.0.0.0", port))
            sock.close()
            return port
        except: # port in use
            pass
    raise control.GraderException("cannot find usable port")

def scan_available_ports(start_port, num_ports, max_attempt=10000, udp=False):
    ports = []
    for i in range(max_attempt):
        if len(ports) >= num_ports:
            return ports
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM)
        try:
            sock.bind(("0.0.0.0", port))
            sock.close()
            ports.append(port)
        except: # port in use
            pass
    raise control.GraderException("cannot find usable ports")


def get_http_response(url, timeout_seconds):
    try:
        response = requests.get(url=url, timeout=timeout_seconds)
        status_code = response.status_code
        raw_headers = response.headers
        headers = {}
        for key in raw_headers.keys():
            headers[key.lower()] = raw_headers[key]
        content = response.content
    except:
        status_code, headers, content = None, None, None
    return status_code, headers, content