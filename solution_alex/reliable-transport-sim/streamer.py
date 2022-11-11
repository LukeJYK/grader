# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import struct
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Timer, Condition

HEADER_LEN = 5
TIMEOUT = 0.25

class Streamer:
    def __init__(self, dst_ip, dst_port, src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        print(src_ip, src_port)
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port

        self.commit = 1 # keeps track of the next sequence number to commit for receiver
        self.seq = 1 # keeps track of the next sequence number for sender
        self.buffer = {} # stores all the incoming packets
        self.ack_received = {} # stores the acked packets
        self.ack = 1 # keeps track of the number of ack sent

        self.received = False
        self.fin = False # indicate a FIN packet is received
        self.shut_down = False # to signal the closing of the program

        self.executor = ThreadPoolExecutor(max_workers = 1)
        self.listener = self.executor.submit(self.listen)

    def listen(self):
        try:
            while not self.shut_down:
                self.received = True

                payload, addr = self.socket.recvfrom()
                if len(payload) == 0:
                    continue
                is_data, seq, data = struct.unpack('!? I %ds' % (len(payload) - HEADER_LEN), payload)

                if is_data:
                    self.buffer[seq] = data
                    # Send an ACK packet
                    self.socket.sendto(self.make_packet(False, seq), (self.dst_ip, self.dst_port))
                    self.ack += 1
                else:
                    if data == b'0':
                        # Handle for FIN packet
                        print("FIN packet received")
                        # Send an ACK packet
                        self.socket.sendto(self.make_packet(False, 0, b'1'), (self.dst_ip, self.dst_port))
                    elif data == b'1':
                        # Handle for FIN ACK packet
                        print("FIN ACK packet received")
                        self.fin = True
                    else:
                        # Handle for ACK packets
                        print("ACK packet received")
                        self.ack_received[seq] = True
        except Exception as e:
            print("Listener: exiting: %s" % e)

    def resend(self, seq: int, packet: bytes, timeout) -> None:
        # Resend the packet after timeout
        if not self.ack_received[seq]:
            print("Resending packet # %d. " % seq)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))

            Timer(timeout * 1.5, lambda: self.resend(seq, packet, timeout * 1.5)).start()

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        i = 0
        seg_len = 1024
        while i < len(data_bytes):
            # self.socket.sendto(data_bytes[i: i + seg_len], (self.dst_ip, self.dst_port))
            data = data_bytes[i: i + seg_len]
            packet = self.make_packet(True, self.seq, data)
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            i += seg_len
            self.ack_received[self.seq] = False

            seq = self.seq
            Timer(TIMEOUT, lambda: self.resend(seq, packet, TIMEOUT)).start()
            # while not self.ack_received[self.seq]:
            #     time.sleep(0.01)

            self.seq += 1

    def send_fin(self) -> None:
        if not self.fin:
            print("Sending FIN")

            packet = self.make_packet(False, 0, b'0')
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))
            Timer(1, lambda: self.send_fin()).start()

    def make_packet(self, is_data: bool, seq: int, data: bytes = b'') -> bytes:
        return struct.pack('!? I%ds' % len(data), is_data, seq, data)

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # Your code goes here!  The code below should be changed!
        ret = b''
        while True:
            if self.commit not in self.buffer:
                # Missing something in the middle
                if len(ret) == 0:
                    # Nothing to return yet
                    time.sleep(0.01)
                    continue
                return ret
            else:
                ret += self.buffer[self.commit]
                self.commit += 1

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""

        while self.ack < self.commit:
            # Wait until all ack packets have ben received
            time.sleep(0.1)
        
        print("Closing...")
        # Send the FIN packet
        self.send_fin()
        while not self.fin:
            time.sleep(0.1)

        while self.received:
            self.received = False
            time.sleep(2)

        self.shut_down = True
        self.socket.stoprecv()
        # self.listener.cancel()
        self.executor.shutdown()
