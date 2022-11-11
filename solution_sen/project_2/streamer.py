# do not import anything else from loss_socket besides LossyUDP
import struct

from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from queue import PriorityQueue
from struct import *
from concurrent.futures import ThreadPoolExecutor
import time
import hashlib

HEADER_LEN = 6 + 16
PAYLOAD_LEN = 1472-HEADER_LEN
# STRUCT_FORMATTER = f'i{PAYLOAD_LEN}p'


class Segment:
    def __init__(self, seq: int, data: bytes, is_ack: bool = False, is_fin: bool = False):
        self.seq = seq  # 4 byte long
        self.data = data
        self.is_ack = is_ack
        self.is_fin = is_fin

    def pack(self) -> bytes:
        return pack(f'I??16s{len(self.data)}s', self.seq, self.is_ack, self.is_fin, self.hash(), self.data)

    @classmethod
    def unpack(cls, raw_bytes: bytes):
        seq, is_ack, is_fin, hash_value, data = unpack(f'I??16s{len(raw_bytes) - HEADER_LEN}s', raw_bytes)
        # Check if hash is correct
        seg = Segment(seq, data, is_ack, is_fin)
        if seg.hash() == hash_value:
            return seg
        else:
            return None

    def __lt__(self, other):
        return self.seq < other.seq

    def hash(self) -> bytes:
        m = hashlib.md5()
        m.update(bytes(self.seq))
        m.update(bytes(self.is_ack))
        m.update(bytes(self.is_fin))
        m.update(self.data)
        return m.digest()


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.closed = False
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)
        # Sender
        self.sender_seq = 0
        self.acked = False
        self.fin_acked = False
        # Receiver
        self.receiver_seq = 0
        self.receiver_buffer = PriorityQueue()


    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        i = 0
        while i < len(data_bytes):
            self.acked = False
            # Load the next chuck
            data2send = data_bytes[i: i + PAYLOAD_LEN]
            # Pack the segment and send it
            seg = Segment(self.sender_seq, data2send)
            bytes2send = seg.pack()
            self.socket.sendto(bytes2send, (self.dst_ip, self.dst_port))
            # Stop and wait for ACK
            while not self.acked:
                time.sleep(0.25)
                # print("send again")
                self.socket.sendto(bytes2send, (self.dst_ip, self.dst_port))
            # Update sender_seq
            self.sender_seq += len(data2send)
            # Forward the loading window
            i += PAYLOAD_LEN

        # for now I'm just sending the raw application-level data in one UDP payload
        # self.socket.sendto(data_bytes, (self.dst_ip, self.dst_port))

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        data = b''
        while not self.receiver_buffer.empty():
            if self.receiver_buffer.queue[0].seq == self.receiver_seq:
                seg = self.receiver_buffer.get(0)
                self.receiver_seq += len(seg.data)
                data += seg.data
            else:
                break
        return data
        # For now, I'll just pass the full UDP payload to the app

    def listener(self):
        while not self.closed:
            try:
                # Receive from the UDP socket
                received_raw_bytes, addr = self.socket.recvfrom()
                # Unpack the bytes
                received_seg = Segment.unpack(received_raw_bytes)
                if received_seg is None:
                    # Broken packets. Skip!
                    continue
                if received_seg.is_fin:
                    # FIN and FIN_ACK
                    if received_seg.is_ack:
                        # FIN_ACK
                        if received_seg.seq == self.sender_seq:
                            self.fin_acked = True
                    else:
                        # FIN
                        if received_seg.seq == self.receiver_seq:
                            self.socket.sendto(Segment(received_seg.seq, b'', True, True).pack(),
                                            (self.dst_ip, self.dst_port))
                        else:
                            print("discard FIN")
                elif received_seg.is_ack:
                    # Normal ACKs
                    if received_seg.seq == self.sender_seq:
                        self.acked = True
                else:
                    # Data packets
                    if received_seg.seq >= self.receiver_seq and received_seg.seq not in self.receiver_buffer.queue:
                        # Avoid duplicates and accept out-of-order packets
                        self.receiver_buffer.put(received_seg)
                    self.socket.sendto(Segment(received_seg.seq, b'', True).pack(),
                                       (self.dst_ip, self.dst_port))
            except Exception as e:
                print("listener died!")
                print(e)

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        while self.fin_acked:
            # Send FIN
            self.socket.sendto(Segment(self.sender_seq, b'', False, True).pack(),
                           (self.dst_ip, self.dst_port))
            time.sleep(0.25)

        time.sleep(2)  # In case the FIN_ACK lost
        self.closed = True
        self.socket.stoprecv()
