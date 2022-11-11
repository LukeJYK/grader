import sys
import select
import socket
from http_server1 import Server


class Server2(Server):
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as accept_socket:
            conns = [accept_socket]
            accept_socket.bind(('', self.port))
            accept_socket.listen()
            while True:
                readable, _, _ = select.select(conns, [], [])
                for s in readable:
                    if s is accept_socket:
                        try:
                            conn, _ = s.accept()
                            conns.append(conn)
                        except:
                            print("connection establishment failure")
                    else:
                        try:
                            req = self.receive(s)
                            self.response(s, req)
                        except:
                            print("communication failure")
                        s.close()
                        conns.remove(s)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(-1)
    server2 = Server2(int(sys.argv[1]))
    server2.run()
