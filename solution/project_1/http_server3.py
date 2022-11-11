import sys
import json
from http_server1 import Server


class Server3(Server):

    @staticmethod
    def calculate_product(query: bytes):
        operands, result = [], 1.0
        try:
            for parameter in query.split(b'&'):
                operand = float(parameter[parameter.index(b'=') + 1:].strip(b'"'))
                operands.append(operand)
                result *= operand
        except:
            result = None
        finally:
            return operands, result

    @staticmethod
    def generate_server_rsp(path: bytes) -> bytes:
        assert path.startswith(b'/')
        path = path[1:]

        req_fmt = 'HTTP/1.0 {0}\r\nContent-Type: {1}\r\nContent-Length: {2}\r\nConnection: close\r\n\r\n{3}'

        if not path.startswith(b'product'):  # 404
            content = '<html><body>404 Page Not Found</body></html>\n'
            return req_fmt.format('404 Not Found', 'text/html', str(len(content)), content).encode()

        operands, result = Server3.calculate_product(path[8:])
        if result is None:  # 400
            content = "<html><body>400 Bad Request</body></html>\n"
            return req_fmt.format('400 Bad Request', 'text/html', str(len(content)), content).encode()
        else:  # 200
            content = json.dumps({
                "operation": "product",
                "operands": operands,
                "result": result
            })
            return req_fmt.format('200 OK', 'application/json', str(len(content)), content).encode()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(-1)
    server3 = Server3(int(sys.argv[1]))
    server3.run()
