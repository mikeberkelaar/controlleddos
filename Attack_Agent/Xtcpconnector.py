import threading, socket, time, select, Queue
import cPickle as pickle

class TCPclient(threading.Thread):
    def __init__(self, Q, IP, PORT):
        threading.Thread.__init__(self) # Required for thread class

        self.out_Q = Q

        self.IP = IP
        self.PORT = PORT


        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.settimeout(5)
        self.Connection_List = []
        self.Connection_List.append(self.S)
        try:
            self.S.connect((self.IP, self.PORT))
        except:
            while 1:
                try: 
                    print "Master seems down. Retrying..."
                    time.sleep(2)
                    self.S.connect((self.IP, self.PORT))
                except:
                    pass


    def run(self):
        while 1:
            # Check for new instructions
            read,write,error = select.select(self.Connection_List,[],[],0.001)

            for sock in read:
                if sock == self.S: # From Master, only socket
                        data = sock.recv(4096)
                        if data:
                            #print data
                            try:
                                self.out_Q.put(pickle.loads(data))
                            except Queue.Full:
                                bogus = self.out_q.get(False)
                                self.out_Q.put(pickle.loads(data))