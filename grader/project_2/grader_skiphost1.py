from streamer import Streamer
import sys
import os
import lossy_socket
import traceback
import time

SUCCESS = 0
ERROR_RECEIVE_CRASHED = 101
ERROR_WRONG_NUMBER = 102
ERROR_SEND_CRASHED = 103
ERROR_CLOSE_CRASHED = 104

# this whole program may timeout, so we have to save the progress
def log_progress(msg, filename):
    with open(filename, "w") as f:
        f.write(msg)


def receive(s, NUMS, progress_filename):
    expected = 0
    str_buf = ""
    while expected < NUMS:
        try: # s is from student, so it may crash
            data = s.recv()
            print("recv returned {%s}" % data.decode('utf-8'))
            str_buf += data.decode('utf-8')
        except:
            print("student's streamer raised an exception!!")
            traceback.print_exc()
            sys.exit(ERROR_RECEIVE_CRASHED)
        ## MODIFICATION 2/15/2020 11PM: accept flexible spaces, i.e. "{[0-9]+ *}*" is ok, not necessarily "{[0-9]+ }*"
        while True:
            str_buf = str_buf.lstrip() ## move leading spaces
            l = len(str(expected))
            if len(str_buf) < l: # wait
                break
            if str_buf[0:l] == str(expected): # correct
                expected += 1
                log_progress(str(expected), progress_filename)
                str_buf = str_buf[l:] # move to next!
            else: # wrong
                print("ERROR: got %s but was expecting %d" % (str_buf[0:l], expected))
                sys.exit(ERROR_WRONG_NUMBER)


def generate_pretty_json_report():
    import time
    import json
    final_sim, final_stats = lossy_socket.sim, lossy_socket.stats
    report = {
        "seconds_taken": int(time.time() - final_sim.start_time),
        "stats": {
            "PACKETS_SENT": final_stats.packets_sent,
            "UDP_BYTES_SENT": final_stats.bytes_sent,
            "ETH_BYTES_SENT": final_stats.bytes_sent + (18+20+8) * final_stats.packets_sent,
            "PACKETS_RECV": final_stats.packets_recv,
            "UDP_BYTES_RECV": final_stats.bytes_recv,
            "ETH_BYTES_RECV": final_stats.bytes_recv + (18+20+8) * final_stats.packets_recv
        }
    }
    return json.dumps(report, indent=2)

def host1(listen_port, remote_port, NUMS):
    s = Streamer(dst_ip="localhost", dst_port=remote_port,
                 src_ip="localhost", src_port=listen_port)
    time.sleep(1) # waiting for host_2 to set up
    # receive(s, NUMS, "__grader__temp__stage1.txt")
    if True:
        # print("STAGE 1 TEST PASSED!")
        # send large chunks of data
        i = 0
        buf = ""
        try:
            while i < NUMS:
                buf += ("%d " % i)
                if len(buf) > 12345 or i == NUMS - 1:
                    print("sending {%s}" % buf)
                    s.send(buf.encode('utf-8'))
                    buf = ""
                i += 1
        except:
            print("student's streamer raised an exception!!")
            traceback.print_exc()
            sys.exit(ERROR_SEND_CRASHED)
    try:
        s.close()
    except:
        print("student's streamer raised an exception!!")
        traceback.print_exc()
        sys.exit(ERROR_CLOSE_CRASHED)

    print("CHECK THE OTHER SCRIPT FOR STAGE 2 RESULTS.")
    # make report
    report = generate_pretty_json_report()
    with open("__grader__report__host1.json", "w") as f:
        f.write(report)


def host2(listen_port, remote_port, NUMS):
    s = Streamer(dst_ip="localhost", dst_port=remote_port,
                 src_ip="localhost", src_port=listen_port)
    # time.sleep(1) # waiting for host_1 to set up
    # send small pieces of data
    # try:
    #     for i in range(NUMS):
    #         buf = ("%d " % i)
    #         print("sending {%s}" % buf)
    #         s.send(buf.encode('utf-8'))
    # except:
    #     print("student's streamer raised an exception!!")
    #     traceback.print_exc()
    #     sys._exit(ERROR_SEND_CRASHED)

    receive(s, NUMS, "__grader__temp__stage2.txt")
    log_progress(str(time.time()), "__grader__temp__timestamp.txt")
    try:
        s.close()
    except:
        print("student's streamer raised an exception!!")
        traceback.print_exc()
        sys.exit(ERROR_CLOSE_CRASHED)

    print("STAGE 2 TEST PASSED!")
    # make report
    report = generate_pretty_json_report()
    with open("__grader__report__host2.json", "w") as f:
        f.write(report)


def main():
    if len(sys.argv) < 9:
        print("usage is: python3 grader_tester.py [port1] [port2] [1|2] [loss_rate] [corruption_rate] [max_delivery_delay] [NUMS] [seed]")
        sys.exit(-1)
    p1, p2, switch, lr, cr, mdd, n, s = sys.argv[1:9]
    
    lossy_socket.sim = lossy_socket.SimulationParams(
        loss_rate=float(lr), corruption_rate=float(cr), max_delivery_delay=float(mdd),
        become_reliable_after=10000000.0, seed=int(s)
    )

    port1, port2, NUMS = int(p1), int(p2), int(n)
    if switch == "1":
        host1(port1, port2, NUMS)
    elif switch == "2":
        host2(port2, port1, NUMS)
    else:
        print("Unexpected switch")


if __name__ == "__main__":
    main()
