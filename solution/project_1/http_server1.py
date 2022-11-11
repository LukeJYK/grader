import socket
import sys
import os


class Server:
    def __init__(self, port: int):
        self.port = port

    @staticmethod
    def receive(s):  # TODO: wait for a better robust solution
        buf = b''
        while True:
            data = s.recv(1024)
            if not data:
                return buf
            buf += data
            if buf.endswith(b'\r\n\r\n'):
                return buf

    @staticmethod
    def parse_req(req: bytes):
        method, path = b'', b'/'
        try:
            method, path = req.split(b'\r\n')[0].split(b' ')[:2]
        except:
            sys.stderr.write("Unable to parse request: " + req.decode())
        finally:
            return method, path

    @staticmethod
    def generate_server_rsp(path: bytes) -> bytes:
        assert path.startswith(b'/')
        path = path[1:]

        req_fmt = 'HTTP/1.0 {0}\r\nContent-Type: text/html\r\nContent-Length: {1}\r\nConnection: close\r\n\r\n{2}'

        if not os.path.isfile(path):  # 404
            content = '<html><body>404 Page Not Found</body></html>\n'
            return req_fmt.format('404 Not Found', str(len(content)), content).encode()
        elif path.endswith(b'.htm') or path.endswith(b'.html'):  # 200
            with open(path, 'r') as f:
                content = f.read()
            return req_fmt.format('200 OK', str(len(content)), content).encode()
        else:  # 403
            content = "<html><body>403 Forbidden</body></html>\n"
            return req_fmt.format('403 Forbidden', str(len(content)), content).encode()

    def response(self, conn, req: bytes) -> None:
        if req:  # Req may be empty during my test.
            method, path = Server.parse_req(req)
            rsp = self.generate_server_rsp(path)
            conn.sendall(rsp)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as accept_socket:
            accept_socket.bind(('', self.port))
            accept_socket.listen()
            while True:
                conn, _ = accept_socket.accept()
                req = Server.receive(conn)
                self.response(conn, req)
                conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(-1)
    server = Server(int(sys.argv[1]))
    server.run()
