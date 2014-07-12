import threading, socket, time, select, Queue
import cPickle as pickle

class TCPserver(threading.Thread):
    def __init__(self, Q):
        threading.Thread.__init__(self) # Required for thread class

        self.out_Q = Q

        self.IP = "0.0.0.0"
        self.PORT = 55556
        #self.kill = False
        self.Connection_List = []
        
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.bind((self.IP, self.PORT))
        self.S.listen(5) # Connection backlog
        self.Connection_List.append(self.S)
        #self.S.setblocking(0)
        
        
    def run(self):
        while 1:
        
            # Receive data from remote
            read,write,error = select.select(self.Connection_List,[],[],0.001) # Should be EPOLL() to avoid ANY delay/timeout

            for sock in read:
                if sock == self.S: #New connection
                    sockFD, addr = self.S.accept()
                    print "New monitoring agent from %s" % str(addr)
                    self.Connection_List.append(sockFD)
                    
                else:
                    data = sock.recv(1024)
                    self.out_Q.put(pickle.loads(data))
