# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
# Project 2
from threading import Timer, Condition
from time import sleep
import concurrent.futures as futures
import hashlib


MD5_LEN = 32
WIN_LEN = 2
WIN_SIZE = 2 ** (8 * WIN_LEN)
SEQ_LEN = 2 * WIN_LEN
SEQ_SIZE = 2 ** (8 * SEQ_LEN)
ACK_LEN = 2 * WIN_LEN
ACK_SIZE = 2 ** (8 * ACK_LEN)

MSS = 1472
# HEAD_LEN = SEQ_LEN + ACK_LEN
HEAD_LEN = MD5_LEN + SEQ_LEN + ACK_LEN
BODY_LEN = MSS - HEAD_LEN

TIMEOUT = 0.25


def debug_print(s: str):
    if False:
        print(s)


class Streamer:

    class Buffer:
        def __init__(self):
            self.data = b''
            self.packets = {}

    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port

        self.send_seq = 0
        self.send_acked = 0
        self.receive_seq = 0
        self.receive_acked = 0

        self.buffer = self.Buffer()
        self.cv = Condition()

        self.quit = False
        self.received_in_timeout = False
        self.executor = futures.ThreadPoolExecutor(max_workers=1)
        self.listener = self.executor.submit(self.listening)


    @staticmethod
    def chucking(data_bytes: bytes) -> bytes:
        while len(data_bytes) > 0:
            yield data_bytes[:BODY_LEN]
            data_bytes = data_bytes[BODY_LEN:]

    def listening(self):
        try:
            while not self.quit:
                data, addr = self.socket.recvfrom()
                if len(data) == 0:
                    continue

                self.received_in_timeout = True
                head = data[:HEAD_LEN]
                body = data[HEAD_LEN:]
                check_sum, seq, ack = self.parse_head(head)

                debug_print("RECEIVE Packet: check_sum: %s, seq: %s, ack: %s" % (check_sum, seq, ack))

                # check check_sum
                if check_sum != hashlib.md5(data[MD5_LEN:]).hexdigest().encode():
                    self.socket.sendto(self.generate_packet(), (self.dst_ip, self.dst_port))
                    continue

                # update send_acked
                self.send_acked = max(self.send_acked, ack)

                debug_print("UPDATE: self.send_acked: %s" % self.send_acked)

                # if no payload in this packet
                if len(body) == 0:
                    continue

                # update buffer and send back ack
                self.buffer.packets[seq] = body
                if seq == self.receive_acked:
                    self.update_receive_acked()
                    self.cv.acquire()
                    self.cv.notify()
                    self.cv.release()
                debug_print("UPDATE: self.receive_acked: %s" % self.receive_acked)
                self.socket.sendto(self.generate_packet(), (self.dst_ip, self.dst_port))
        except Exception as e:
            debug_print(e)
            return

    def update_receive_acked(self):
        while self.receive_acked in self.buffer.packets.keys():
            self.receive_acked += len(self.buffer.packets[self.receive_acked])

    @staticmethod
    def num_to_bytes(num: int, length: int = SEQ_LEN) -> bytes:
        return num.to_bytes(length=length, byteorder='big')

    @staticmethod
    def bytes_to_num(b: bytes) -> int:
        return int(b.hex(), base=16)

    @staticmethod
    def parse_head(head: bytes) -> (bytes, int, int):
        check_sum = head[:MD5_LEN]
        head = head[MD5_LEN:]
        seq = Streamer.bytes_to_num(head[:SEQ_LEN])
        head = head[SEQ_LEN:]
        ack = Streamer.bytes_to_num(head[:ACK_LEN])
        return check_sum, seq, ack

    def generate_packet(self, chuck=b'') -> bytes:
        seq = self.num_to_bytes(self.send_seq)
        ack = self.num_to_bytes(self.receive_acked)
        check_sum = hashlib.md5(seq + ack + chuck).hexdigest().encode()
        return check_sum + seq + ack + chuck

    def resend(self, seq, packet, timeout) -> None:
        if self.quit is False and self.send_acked <= seq:

            _, pseq, pack = self.parse_head(packet)
            debug_print('RESEND: seq: %s, pseq: %s, pack: %s, chuck: %s' % (seq, pseq, pack, packet[HEAD_LEN:]))

            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            Timer(timeout * 1.5, lambda: self.resend(seq, packet, timeout * 1.5)).start()

    def send(self, data_bytes: bytes) -> None:
        for chuck in self.chucking(data_bytes):
            packet = self.generate_packet(chuck)

            check_sum, seq, ack = self.parse_head(self.generate_packet())
            debug_print("Send Packet: check_sum: %s, seq: %s, ack: %s, chuck: %s" % (check_sum, seq, ack, chuck))

            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            seq = self.send_seq
            self.send_seq += len(chuck)
            Timer(TIMEOUT, lambda: self.resend(seq, packet, TIMEOUT)).start()


    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        self.cv.acquire()
        while self.receive_seq not in self.buffer.packets.keys():
            self.cv.wait()

        ans = b''
        while self.receive_seq in self.buffer.packets.keys():
            ans += self.buffer.packets[self.receive_seq]
            self.receive_seq += len(self.buffer.packets[self.receive_seq])

        self.cv.release()
        return ans

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        while self.send_acked < self.send_seq or self.received_in_timeout:
            self.received_in_timeout = False
            sleep(TIMEOUT * 2)
        self.socket.stoprecv()
        self.quit = True
        sleep(0.5)
        self.socket.close()
        self.listener.cancel()
        self.executor.shutdown()
