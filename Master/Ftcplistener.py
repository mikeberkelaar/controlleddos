import threading, socket, time, select, Queue
import cPickle as pickle

class TCPserver(threading.Thread):
    def __init__(self, Q):
        threading.Thread.__init__(self) # Required for thread class

        self.in_Q = Q
        self.IP = "0.0.0.0"
        self.PORT = 55557
        self.Connection_List = []

        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.bind((self.IP, self.PORT))
        self.S.listen(5) # Connection backlog
        self.Connection_List.append(self.S)
        self.S.setblocking(0)


    def run(self):
        while 1:
            read,write,error = select.select(self.Connection_List,[],[],0.001) # Should be EPOLL() to avoid ANY delay/timeout

            for sock in read:
                if sock == self.S: #New connection
                    sockFD, addr = self.S.accept()
                    print "New client from %s" % str(addr)
                    self.Connection_List.append(sockFD)

                else:
                    try:
                        print "Received data from %s" % sock
                        data = sock.recv(1024)
                        print data

                    except:
                        print "A client connection dropped?"
                        sock.close()
                        self.Connection_List.remove(sock)

            # Send data if there is anything on the queue
            try:
                MSG = self.in_Q.get(True, 0.01)
                for sock in self.Connection_List:
                    if sock is not self.S:
                        try:
                            sock.send(pickle.dumps(MSG))
                        except:
                            print "Something wrong with socket: %s" % sock
                            sock.close()
                            self.Connection_List.remove(sock)

            except Queue.Empty:
                pass