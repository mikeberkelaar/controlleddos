import threading, time, Queue, time, sys, socket, os, struct
import Ftcpconnector

#from pysnmp import debug

### Configuration Parameters ###
#target = "145.100.104.173"
#SERVER_IP = "145.100.102.108" # The Monitoring Master

SERVER_IP = "127.0.0.1" # The Monitoring Master
SERVER_PORT = 55557     # Monitoring port
average_range = 1      #How many samples should be averaged to determine the "current" status
################################

class Monflood_send(threading.Thread):
    def __init__(self, rate_q, target, pkt_size, init_rate):
        threading.Thread.__init__(self) # Required for thread class
        self.rate_q = rate_q
        self.icmp = socket.getprotobyname("icmp")
        self.i = 0
        self.j = 0 # packet seq number
        self.k = 0
        self.pkt_size = pkt_size
        self.target = target
        self.rate = init_rate # Initial rate (~100ms response time)
        self.ICMP_ECHO_REQUEST = 8

    def checksum(self,source_string):
        sum = 0
        countTo = (len(source_string)/2)*2
        count = 0
        while count<countTo:
            thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
            sum = sum + thisVal
            sum = sum & 0xffffffff # Necessary?
            count = count + 2

        if countTo<len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff # Necessary?
        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff
        # Swap bytes. Bugger me if I know why.
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def send_one_ping(self, my_socket, dest_addr, ID, data_size):
        """
        Send one ping to the given >dest_addr<.
        """
        dest_addr  =  socket.gethostbyname(dest_addr)

        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        my_checksum = 0

        # Make a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", self.ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytesInDouble = struct.calcsize("d")
        data = (data_size - bytesInDouble) * "Q"
        data = struct.pack("d", time.time()) + data

        # Calculate the checksum on the data and the dummy header.
        my_checksum = self.checksum(header + data)

        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack(
            "bbHHh", self.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data
        my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1

    def run(self):
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, self.icmp)
        except socket.error, (errno, msg):
            if errno == 1:
                print "Socket error. Got_root?!"
        my_ID = os.getpid() & 0xFFFF

        while True:
            if self.j >= self.rate:
                self.j = 0
#            if self.i == (self.rate/10): # /10 to get faster reaction times at rate changes (~100ms)
            if self.i == 500: # /10 to get faster reaction times at rate changes (~100ms)
                self.i = 0
                try:
                    temp = self.rate_q.get(False)
                    if temp:
                        self.rate = temp # Update on !None
                        #print "Upped monrate to ", str(self.rate)
                except Queue.Empty:
                    pass

            self.i += 1
            self.j += 1
            time1 = time.time()
            #self.send_one_ping(my_socket, self.target, my_ID, self.pkt_size)
            self.send_one_ping(my_socket, self.target, self.j, self.pkt_size)
            #delay = float(1) / float(2000)
            delay = float(1) / float(self.rate)
            while (time.time() - time1) < delay:
                pass

if __name__ == '__main__':
  ## Starting the TCP Connection:

  ALL_THREADS = []
  monitoring_q = Queue.Queue(maxsize=1)
  rate_q = Queue.Queue()
  print "1. Starting TCP connector ..."
  LISTENER = Ftcpconnector.TCPclient(monitoring_q, SERVER_IP, SERVER_PORT)
  ALL_THREADS.append(LISTENER)
  LISTENER.daemon = True
  LISTENER.start()
  print "  TCP connector started"


  print "2. Waiting for instructions ..."
  instruction = monitoring_q.get(True) # = dict

  print "3. Starting Monitoring flood sender ..."
  SENDER = Monflood_send(rate_q, instruction['target'], instruction['pktsize'], instruction['monrate'])
  SENDER.daemon = True
  SENDER.start()
  print "  Working"



  while True:
    try:
        rate = monitoring_q.get(True, 0.01)
        if rate:
            print "Update rate to: ", str(rate['monrate'])
            #print type(rate['monrate'])
            try:
                rate_q.put(rate['monrate'])
                #print "Internal comm"
            except:
                print "error 902"
                pass
    except:
        #print "ERROR 901"
        pass







