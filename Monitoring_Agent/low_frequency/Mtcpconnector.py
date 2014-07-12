from email import message
import threading, socket, time, Queue, select, random
import cPickle as pickle

class TCPclient(threading.Thread):
    def __init__(self, Q, IP, PORT):
        threading.Thread.__init__(self) # Required for thread class

        self.out_Q = Q

        self.IP = IP # Server will be localhost for now
        self.PORT = PORT

        
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.settimeout(5)
        self.Connection_List = []
        self.Connection_List.append(self.S)
        while 1:
            try:
                self.S.connect((self.IP, self.PORT))
                break
            except:
                print "Master seems down. Retrying..."
                time.sleep(2)
        
    def run(self):
        while 1:
            try:
              message=self.out_Q.get(True, 0.05)
              try:
                self.S.send(pickle.dumps(message))
              except:
                print "Something wrong with socket: %s" % self.S
                self.S.close()
                break
#                self.Connection_List.remove(sock)
            except Queue.Empty:
              pass
            
