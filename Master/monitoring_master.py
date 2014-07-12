import threading, Queue, math, time, socket, struct, cPickle #,select
import ping

class slope_watcher():
    def __init__(self):
        self.lastrate = 0
        self.currentrate = 0
        self.rates = {}
        self.results = {} # {RATE: {AVG:X, VARIANCE_FACTOR: Y, ...}}
        self.som = 0
        global attack_rate
        attack_rate = 0
            
    def avg(self, value):
        self.som = 0
        for I in value:
            self.som += I
        length = len(value)
        return (self.som/length)
    
    def watch(self, value):
        if attack_rate != self.currentrate:
            # Prepare new phase / bootstrap
            self.rates[attack_rate] = []
            self.lastrate = self.currentrate
            self.currentrate = attack_rate
            #print "new rate : ", str(attack_rate) 

            if self.lastrate != 0:
                average = self.avg(self.rates[self.lastrate])
                self.results[self.lastrate] = {"AVG": average, "VARIANCE": "-"}
   
        print self.results
        self.value = value
        #self.som += value
        self.rates[self.currentrate].append(self.value)
        # With very big lists we may not be able to calculate the average quick enough!
        #  so we may have to calculate the average for every X input values, instead of all.

        time1 = time.time()
        print " avg: ", self.avg(self.rates[self.currentrate]), " time to calc: ", (time.time() - time1)

class predictor():
    def __init__(self):
        self.first_sample = 0
        self.last_sample = 0
        self.direction = True
        self.counter = 0
        self.flag = 0
        self.asf = 0
        self.i = 0


    def calc(self, caller, current_sample, threshold=90):
        if not current_sample:
            current_sample = threshold*10
        if Gflag > self.flag:
            self.flag = Gflag
            self.asf = 0
        else:
            self.asf += current_sample
            self.i += 1

        #print current_sample, "~" , threshold, "Average so far:" , self.asf/self.i

        if (abs(current_sample-self.last_sample) >= (threshold*0.1)) or (abs(current_sample-self.first_sample) >= 0.1):
            if (self.direction and current_sample < self.last_sample) or ((not self.direction) and (current_sample >= self.last_sample)):
                self.direction = not self.direction
                self.first_sample = self.last_sample
                self.counter = 0
            else:
                self.last_sample = current_sample  # I've added this? Needed????!
                self.counter += 1 # I will assume that the sampling rate is constant
            if not self.counter == 0 and self.last_sample > self.first_sample:
                self.s = (self.last_sample-self.first_sample)/self.counter
                print "Current Slope is:", self.s
                print "threshold" , threshold, "Curernt Sample:" ,current_sample
                if not self.s == 0: #Just to avoid division y zero
                    print caller,": Current Sample: ",current_sample,"With this rate(",self.s,"), The threshold will reach in next", int(math.ceil(float(threshold -  self.last_sample)/self.s)) , "samples!"
                #elif abs(threshold-current_sample) < threshold/10: #if we are in range of 10% of the threshold:

                return self.s
        else:
            self.counter += 1   #If the change is not noticeable, still count a sample,
                                # but don't measure the slop, nor update the sample variables

class http_treshold():
    def __init__(self, treshold, Q):
        self.status = 0
        self.treshold = treshold
        self.Q = Q # maxsize=1
        self.result_count = 20 # = treshold, 20 probes per second max. status = 20 = bad

    def check(self, val):
        if val > self.treshold:
            self.status += 1
        else:
            if self.status > 0:
                self.status -= 1

        if self.status >= self.result_count:
            response = ["BAD", str(val)]
        else:
            response = ["GOOD", str(val)]

        print " ABC   ", str(val), "   ", str(self.treshold), "    ", str(self.status)

        try:
            self.Q.put(response, False)
        except Queue.Full: # Only a single response on the queue at all times
            bogus = self.Q.get(False)
            self.Q.put(response, False)


class cICMP_probe(threading.Thread):
  def __init__(self, Q_in, Q_out):  #rate, size):
    threading.Thread.__init__(self)
    self.Q_in = Q_in
    self.Q_out = Q_out

    #self.rate = rate # How fast should we probe
    #self.pktsize = size # What is the size of the attack packets ( approx)

  def run(self):
    while True:
        try:
          instruction = self.Q_in.get(True)
        except Queue.Empty: # Not needed
          pass

        if instruction:
            self.rate = instruction["rate"]
            self.pktsize = instruction["size"]
            self.target = instruction["target"]
            BUCKET = 0

            sleep_delay = float(1) / self.rate # Delay should be (1 - rate * RTT)/rate ????? <--------------------------------------------------
            counter = {}
            counter['ICMP_probe'] = [] # appro
            for i in range(0,self.rate): # Do it for 1 second worth of the attack, equal to the increase of the attack rate
              ping_delay = ping.verbose_ping(self.target,1,1,self.pktsize) #timeout = 1
              ## Sending ("ping_delay")
              if ping_delay == float(1):
                  BUCKET += 1
                  if BUCKET > 2:
                      break
              counter['ICMP_probe'].append(ping_delay)
              time.sleep(sleep_delay)

            print counter
            if BUCKET > 2:
                CONCLUSION = "NO"
            else:
                CONCLUSION = "YES"
            self.Q_out.put(CONCLUSION)

class monitoring_flood_recv(threading.Thread):
    def __init__(self, Q):
        threading.Thread.__init__(self)
        self.Q_out = Q
        self.seq = {}

    def run(self):
        icmp = socket.getprotobyname("icmp")
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error, (errno, msg):
            print errno
            print msg

        while True:
            status, id = self.receive_one_ping(my_socket)
            self.Q_out.put(cPickle.dumps([status,id]))

    def receive_one_ping(self, my_socket):
        """
        receive the ping from the socket.
        """
        #timeLefstatust = timeout
        while True:
            #print "ok"
            #startedSelect = time.time()
            #whatReady = select.select([my_socket], [], [], timeLeft)
            #howLongInSelect = (time.time() - startedSelect)
            #if whatReady[0] == []: # Timeout
            #    return

            #timeReceived = time.time()
            recPacket, addr = my_socket.recvfrom(1564)
            icmpHeader = recPacket[20:28]
            type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmpHeader
            )
            if packetID:
                time1 = time.time()

                return time1, packetID

            #timeLeft = timeLeft - howLongInSelect
            #if timeLeft <= 0:
            #    return

class monitoring_flood(threading.Thread):
  def __init__(self, Q_in, Q_out, Q_recvping):  #rate, size):
    threading.Thread.__init__(self)
    self.Q_in = Q_in
    self.Q_out = Q_out
    self.Q_rcvping = Q_recvping
    self.pinglist = []
    self.writelist = [0]
    self.writedict = {}
    self.monitoring_range = float(1) # We monitor the last X seconds on missing packets / time-outs
    self.timeout = float(0.1) # We may want to account for the RTT that could increase?
    self.i = 0
    self.Z = 0
    self.Y = 0
    #self.rate = rate # How fast should we probe
    #self.pktsize = size # What is the size of the attack packets ( approx)

  def run(self):
    while True:
        try:
          instruction = self.Q_in.get(False)
        except Queue.Empty: # Not needed, cannot happen
          instruction = None
          pass

        if instruction:
            # if True:
            #     if instruction['command'] == "number_received":
            #         print "Writing to file"
            #         f = open('/tmp/azad.csv', 'a')
            #         for ITEM in self.writedict:
            #             towrite2 = str(ITEM) + ' '
            #             f.write(towrite2)
            #             for BLA in self.writedict[ITEM]:
            #                 towrite = str(BLA) + ","
            #                 f.write(towrite)
            #             f.write("\n")
            #         f.close()
            #     self.Y = 0
            # else:
            #     self.Y += 1

            number = self.check_list()

            self.Q_out.put(number)

            #self.rate = instruction["rate"]
            #self.pktsize = instruction["size"]
            #self.target = instruction["target"]

        try:
            incoming = self.Q_rcvping.get(False)
        except Queue.Empty:
            incoming = None
            #print "Empty Queue"
            pass

        if incoming:
            #print "Got something: ", incoming
            received = cPickle.loads(incoming) # 0 time, 1 seq/id
            self.pinglist.append(received[0])
            if self.writelist[-1] < received[1]:
                self.writelist.append(received[1])
                #print self.writelist
            else:
                self.Z += 1
                self.writedict[self.Z] = self.writelist
                self.writelist = [received[1]]
            #self.check_list() # Returns length of pinglist


        #else:
        #    time.sleep(0.1) # starvation

  def check_list(self):
    #Check if there are outdated items on the list that should be popped
    remove_list = []
    #print len(self.pinglist), "    ", self.pinglist[0], "   ", time.time()

    for I in self.pinglist:
        if (time.time() - self.monitoring_range) > I:
            remove_list.append(I) # Dont edit the list while we are iterating...


    # PERHAPS: instead of removing items. Copy the list from the point where the items are fresh enough to a new list.


    if len(remove_list) > 0:
        for J in remove_list:
            #del self.pinglist[J]
            self.pinglist.remove(J)

    ##received_packets = self.pinglist
    ##print len(received_packets), "    ", received_packets[0], "   ", time.time()
    ##if (2000-received_packets)/self.rate > 0.01:
    ##    print 'We should stop'

    #self.i += 1
    #if self.i == 2000:
    #    cPickle.dump(self.pinglist, open('/tmp/pinglist.obj', 'wb'))
    #    #f = open('/tmp/ping.lst','a')
    #    #f.write("\nA\n")
    #    self.i = 0

    return len(self.pinglist)





    #
    #         sleep_delay = float(1) / self.rate # Delay should be (1 - rate * RTT)/rate ????? <--------------------------------------------------
    #         counter = {}
    #         counter['ICMP_probe'] = [] # approx
    #         for i in range(0,self.rate): # Do it for 1 second worth of the attack, equal to the increase of the attack rate
    #           ping_delay = ping.verbose_ping(self.target,1,1,self.pktsize) #timeout = 1
    #           ## Sending ("ping_delay")
    #           if ping_delay == float(1):
    #               BUCKET += 1
    #               if BUCKET > 2:
    #                   break
    #           counter['ICMP_probe'].append(ping_delay)
    #           time.sleep(sleep_delay)
    #
    #         print counter
    #         if BUCKET > 2:
    #             CONCLUSION = "NO"
    #         else:
    #             CONCLUSION = "YES"
    #         self.Q_out.put(CONCLUSION)

class Monitoring(threading.Thread):
    def __init__(self, Q1, Q2, Q3, Q4, Q5, Q6, http_treshold_val):
        global Gflag
        Gflag = 0
        threading.Thread.__init__(self) # Required for thread class
        self.probe_queue_out = Q4
        self.probe_queue_in = Q3
        self.http_treshold_q_rep = Q6
        self.mon_flood_recv_q = Queue.Queue()

        self.http_treshold_val = http_treshold_val

        self.ICMP_calc = predictor()
        self.HTTP_calc = predictor()
        self.WMI_calc_RAM = predictor()
        self.WMI_calc_CPU = predictor()
        self.SNMP_calc_RAM = predictor()
        self.SNMP_calc_CPU = predictor()

        self.ICMP_probe = cICMP_probe(self.probe_queue_in, self.probe_queue_out)

        self.mon_flood = monitoring_flood(self.probe_queue_in, self.probe_queue_out, self.mon_flood_recv_q)
        self.mon_flood_recv = monitoring_flood_recv(self.mon_flood_recv_q)

        self.HTTP_treshold = http_treshold(self.http_treshold_val, self.http_treshold_q_rep)
        
        self.ICMP_watch = slope_watcher()
        self.HTTP_watch = slope_watcher()
        self.in_q = Q1
        self.attk_q = Q2
        self.application_mon_q = Q5



        self.parsed = {}



    def run(self):
        #data = None
        #change = None
        self.pingexcel = []
        self.httpexcel = []
        self.ICMP_probe.daemon = True
        #self.ICMP_probe.start()


        #Monitoring flood (ICMP) threads:
        self.mon_flood.daemon = True
        self.mon_flood.start()
        self.mon_flood_recv.daemon = True
        self.mon_flood_recv.start()
        
        
        while 1:
            #print self.parsed
            try:
                data = self.in_q.get(True, 0.05)
            except:
                data = None
                pass
            try:
                change = self.attk_q.get(False)
                # Gives us the rate of the attack right now.
                # Use it to signal the end of the monitoring phase, orchestrated by the attack_master?
                
            except:
                change = None
                pass
            if change:
                global attack_rate
                attack_rate = change["rate"]


            if data:
                self.parse(data)




    def parse(self, data):
        self.data = data

        for K in self.data.keys():
            if K == "ICMP":
                #print self.data
                if "ICMP" not in self.parsed.keys():
                    self.parsed[K] = []
                    
                # Add to list > EXCEL
                #self.pingexcel.append(self.data[K])
                #print self.pingexcel
                self.fp = open("/tmp/ping.csv", "a")
        
                bla1 = str(self.data[K])+","+str(time.time())+"\n"
                self.fp.write(bla1)
                
                    
                datavalue = self.data[K]
                self.parsed[K].insert(0,datavalue)
#                self.ICMP_watch.watch(datavalue)
                printer = self.ICMP_calc.calc(K,self.data[K],0.1)
                #if printer: print printer


            elif K == "HTTP":
                if "HTTP" not in self.parsed.keys():
                    self.parsed[K] = []

                #self.httpexcel.append(self.data["HTTP"]["response_time"])
                #print self.httpexcel
                self.fh = open("/tmp/http.csv", "a")
                bla2 = str(self.data["HTTP"]["response_time"])+","+str(time.time())+"\n"
                self.fh.write(bla2)
                self.fh.close()

                self.HTTP_treshold.check(self.data["HTTP"]["response_time"])
                    
                if self.data[K]["status"] != 900:
                    self.parsed[K].insert(0,self.data["HTTP"]["response_time"])
 #                   self.HTTP_watch.watch(self.data["HTTP"]["response_time"])
                    #printer = str('MIKE:' , self.HTTP_calc.calc(self.data["HTTP"]["response_time"]))
                    ##printer = self.HTTP_calc.calc(K,self.data["HTTP"]["response_time"],0.1)
                    #if printer: print printer
                else:
                    print "HTTP response code was NOT 200..."

##### YOU ARE HERE !!!!
            elif K == "WMI":
                if "WMI" not in self.parsed.keys():
                    self.parsed[K] = []
                self.parsed[K].insert(0,self.data["WMI"])
                #printer = str('MIKE:' , self.HTTP_calc.calc(self.data["HTTP"]["response_time"]))
                printer_CPU = self.WMI_calc_CPU.calc("WMI_CPU",self.data["WMI"]["CPU"],90)
                #printer_RAM = self.WMI_calc_RAM.calc("WMI_RAM",self.data["WMI"]["RAM"],2000000) #Thershold is in MB
                # if printer_CPU: print printer_CPU
                # if printer_RAM: print printer_RAM



            elif K == "SNMP":
                if "SNMP" not in self.parsed.keys():
                    self.parsed[K] = []
                self.parsed[K].insert(0,self.data["SNMP"])

                self.fh = open("/tmp/snmp.csv", "a")
                bla2 = str(self.data["SNMP"]["CPU"]+","+self.data["SNMP"]["NIC_BYTES"])+","+str(time.time())+"\n"
                self.fh.write(bla2)

                printer_CPU = self.SNMP_calc_CPU.calc("SNMP_CPU",self.data["SNMP"]["CPU"],90)
                #RAM SNMP yet to be found                # printer_RAM = self.SNMP_calc_RAM.calc("SNMP_RAM",self.data["SNMP"]["RAM"],2000000) #Thershold is in MB
                # if printer_CPU: print printer_CPU
                # if printer_RAM: print printer_RAM

            else:
                print "Malformed/unknown monitoring data:", K
                pass

