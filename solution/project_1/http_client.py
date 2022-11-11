import sys
import socket
import collections


class ErrorCode:
    SUCCESS = 0
    WRONG_ARGV = 1
    WRONG_URL = 2
    TOO_MANY_REDIRECTS = 3
    INVALID_CONTENT_TYPE = 4
    UNSUPPORTED_STATUS = 5
    STATUS_400 = 6
    UNSUPPORTED_HTTPS = 7

    msg = collections.defaultdict(str)
    msg[WRONG_URL] = 'Invalid URL: '
    msg[TOO_MANY_REDIRECTS] = 'Too many redirects: '
    msg[INVALID_CONTENT_TYPE] = "Content-Type does not start with text/html"
    msg[UNSUPPORTED_STATUS] = "Status Code does not support: "
    msg[STATUS_400] = "HTTP Response code >= 400: "
    msg[UNSUPPORTED_HTTPS] = "HTTPS does not support: "


def exit_with_code(error_code, msg=''):
    if error_code == ErrorCode.SUCCESS:
        sys.exit(0)
    else:
        sys.stderr.write(ErrorCode.msg[error_code] + msg + '\n')
        sys.exit(error_code)


def check_url(url):
    if url.startswith('https://'):
        exit_with_code(ErrorCode.UNSUPPORTED_HTTPS, url)
    if not url.startswith('http://'):
        exit_with_code(ErrorCode.WRONG_URL)


def parse_domain_port_path(url):
    url = url[7:]  # remove "http://"
    if '/' in url:
        domain_port, path = url[:url.find('/')], url[url.find('/'):]
    else:
        domain_port, path = url, '/'
    if ':' in domain_port and domain_port[-1] != ':':
        domain, port = domain_port[:domain_port.find(':')], int(domain_port[domain_port.find(':') + 1:])
    else:
        domain, port = domain_port, None
    return domain, port, path


def generate_client_req(path, host, port) -> bytes:
    fmt_req = 'GET {0} HTTP/1.0\r\nHost: {1}\r\n\r\n'
    fmt_req_with_port = 'GET {0} HTTP/1.0\r\nHost: {1}:{2}\r\n\r\n'
    return fmt_req_with_port.format(path, host, port).encode() if port else fmt_req.format(path, host).encode()


def receive(s):  # TODO: wait for a better robust solution
    buf = b''
    while True:
        data = s.recv(1024)
        if not data:
            break
        buf += data
    return buf


def parse_http_rsp(rsp: bytes) -> (int, bytes, bytes, bytes):
    head, content = rsp[:rsp.find(b'\r\n\r\n')], rsp[rsp.find(b'\r\n\r\n') + 4:]
    if rsp.find(b'\r\n\r\n') + 4 == len(rsp):  # Case that rsp does not have a body content
        content = b''
    head_metas = head.split(b'\r\n')
    status = int(head_metas[0][9:12])
    content_type = b''
    location = b''
    for meta in head_metas:
        meta = meta.strip()
        if meta.startswith(b'Content-Type:'):
            content_type = meta[len(b'Content-Type:'):].strip()
        if meta.startswith(b'Location:'):
            location = meta[len(b'Location:'):].strip()
    return status, content_type, location, content


def _status_200(content: bytes, content_type: bytes):
    if content_type.startswith(b'text/html'):
        print(content.decode(errors='ignore'))
        exit_with_code(ErrorCode.SUCCESS)
    else:
        exit_with_code(ErrorCode.INVALID_CONTENT_TYPE)


def _status_301(location: bytes, count: int):
    sys.stderr.write('Redirected to: ' + location.decode() + '\n')
    main(location.decode(), count + 1)


def _status_400(content: bytes, status: int):
    print(content.decode(errors='ignore'))
    exit_with_code(ErrorCode.STATUS_400, str(status))


def main(url: str, count=0):
    if count >= 10:
        exit_with_code(ErrorCode.TOO_MANY_REDIRECTS, url)

    check_url(url)

    domain, port, path = parse_domain_port_path(url)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((domain, port)) if port else s.connect((domain, 80))
        s.sendall(generate_client_req(path, domain, port))
        rsp = receive(s)
        s.close()

        status, content_type, location, content = parse_http_rsp(rsp)

        if status == 200:
            _status_200(content, content_type)
        elif status in [301, 302]:
            _status_301(location, count)
        elif status >= 400:
            _status_400(content, status)
        else:
            exit_with_code(ErrorCode.UNSUPPORTED_STATUS, str(status))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        exit_with_code(ErrorCode.WRONG_ARGV)
    main(sys.argv[1])
