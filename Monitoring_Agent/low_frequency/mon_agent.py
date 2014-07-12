import httplib,ping, threading, time, Queue, subprocess,re  # Python
from time import time,sleep
import sys
import Mtcpconnector

### Configuration Parameters ###
target = "145.100.104.173"
user_name = 'administrator'
password = '123abc+'
HTTP_GET = "/mike.php"
SNMPCom = 'Mike_Azad'

SERVER_IP = "145.100.102.108" # The Monitoring Master
SERVER_PORT = 55556     # Monitoring port
average_range = 1      #How many samples should be averaged to determine the "current" status
#################

class cPing(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)

  def run(self):
    ## ICMP Response Monitoring ##
    counter = {}
    counter['ICMP'] = {}
    while True:
      ping_delay = ping.verbose_ping(target,0.1,1,1000)
      ## Sending ("ping_delay")
      counter['ICMP'] = ping_delay
      monitoring_q.put(counter)
      if not ping_delay:
          pass
      else:
          sleep(0.1) # Simulate at least a 100 MS RTT (Low_freq)



class cHTTP(threading.Thread):
  def __init__(self, GET):
    threading.Thread.__init__(self)
    self.HTTP_GET = GET

  def run(self):
    ## HTTP Response Monitoring ##
    counter = {}
    counter["HTTP"]  = {}
    while True:
        try:
          conn = httplib.HTTPConnection(target, timeout=1)
          t_start = time()
          conn.request("GET", self.HTTP_GET)
          r1 = conn.getresponse()
          t_end = time()
          conn.close()
          ## Sending ("t_end - t_start,r1.status, r1.reason")
          counter["HTTP"]["response_time"] = t_end-t_start
          counter["HTTP"]["status"] = r1.status # 200 "OK"
          #counter["HTTP"]["reason"] = r1.reason
          print counter
          monitoring_q.put(counter)
          if t_end - t_start < 0.1:
              sleep(0.08) #Simulate +80 MS
        except:
          counter["HTTP"]["response_time"] = 1 # Timeout value
          counter["HTTP"]["status"] = 900      # 900 "NOT OK"
          monitoring_q.put(counter)


class cSNMP(threading.Thread):
    def __init__(self,rep_int):
        threading.Thread.__init__(self)
        self.rep_int = rep_int
        self.RAM = '1.3.6.1.2.1.25.3.3.1.2.2'
        self.CPU = '1.3.6.1.2.1.25.3.3.1.2.3'
        self.NIC_bytes = '1.3.6.1.2.1.2.2.1.10.1'

    def run(self):
        counter = {}
        counter["SNMP"] = {}
        while True:
            cmdGen = cmdgen.CommandGenerator()
            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData(SNMPCom),
            cmdgen.UdpTransportTarget((target, 161)),
            self.RAM, #RAM
            self.CPU, #CPU
            self.NIC_bytes, # NIC octets incoming
            )
            if errorIndication:
                return(-1)
                print(errorIndication)
            else:
                if errorStatus:
                    return(-2)
                    print('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex)-1] or '?'))
                else:
                    for name, val in varBinds:
                        print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
                        if str(name) == self.CPU:
                            counter["SNMP"]["CPU"] = int(val)
                        elif str(name) ==  self.RAM:
                            counter["SNMP"]["RAM"] = int(val)
                        elif str(name) == self.NIC_bytes:
                            counter["SNMP"]["NIC_BYTES"] = int(val)
            monitoring_q.put(counter)
            sleep(0.1)

class cWMI(threading.Thread):
    def __init__(self,rep_int):
        threading.Thread.__init__(self)
        self.rep_int = rep_int

    def run(self):
        counter = {}
        counter["WMI"] = {}
        #counter["WMI"]["CPU"] = {}
        #counter["WMI"]["RAM"] = {}
        #Calculating the total system memory
        com = subprocess.Popen(['wmic', '-U', user_name+'%'+ password , '//'+target, 'select capacity from CIM_PhysicalMemory'],shell = False, stdout=subprocess.PIPE)
        result = str(com.communicate())
        TotalMemory = re.findall(r"\\n(\d+)", result)
        while True:
            sum_cpu = 0
            sum_ram = 0
            for j in range(0,average_range):
                ## CPU Monitoring
                com = subprocess.Popen(['wmic', '-U', user_name+'%'+ password , '//'+target, 'SELECT LoadPercentage FROM Win32_Processor'],shell = False, stdout=subprocess.PIPE)
                result = str(com.communicate())
                util = re.findall(r"\|(\d+)", result)
                if not com.returncode == 0:
                    print 'The return Code:' , com.returncode
                    print 'The Process Says:'
                    print result
                    exit()
                #print 'Curernt CPU util:', util[0]
                sum_cpu = sum_cpu + int(util[0])
                ## Memory Monitoring
                com = subprocess.Popen(['wmic', '-U', user_name+'%'+ password , '//'+target, 'select AvailableBytes from Win32_PerfFormattedData_PerfOS_Memory'],shell = False, stdout=subprocess.PIPE)
                result = str(com.communicate())
                util = re.findall(r"\\n(\d+)", result)
                if not com.returncode == 0:
                    print 'The return Code:' , com.returncode
                    print 'The Process Says:'
                    print result
                    #exit()
                sum_ram = sum_ram + int(util[0])
            #print "\n >>>",TotalMemory[0],"|", sum_ram,"|", average_range , "<<<"
            counter["WMI"]["RAM"] = int(((float(TotalMemory[0]) - float(sum_ram /average_range))/float(TotalMemory[0])/1000000))
            counter["WMI"]["CPU"] = int(sum_cpu /average_range)
            #print("counter is",counter)
            monitoring_q.put(counter)
            print counter
            print counter
            print counter
            sleep(0.1)

if __name__ == '__main__':
## Starting the TCP Connection:


  ALL_THREADS = []
  monitoring_q = Queue.Queue(maxsize=1)
  #instruction_q = Queue.Queue(maxsize=1)
  print "1.Starting TCP connector ..."
  LISTENER = Mtcpconnector.TCPclient(monitoring_q, SERVER_IP, SERVER_PORT)
  ALL_THREADS.append(LISTENER)
  LISTENER.daemon = True
  LISTENER.start()
  print "  TCP connector started"

  print "2. Starting monitoring: ICMP"
  ICMP = cPing()
  ALL_THREADS.append(ICMP)
  ICMP.daemon = True
  ICMP.start()


  print "3.1 Starting monitoring; HTTP 1\n"
  HTTP1 = cHTTP(HTTP_GET)
  ALL_THREADS.append(HTTP1)
  HTTP1.daemon = True
  HTTP1.start()
  print "3.2 Starting monitoring; HTTP 2\n"
  HTTP2 = cHTTP(HTTP_GET)
  ALL_THREADS.append(HTTP2)
  HTTP2.daemon = True
  HTTP2.start()

  print "4. Starting monitoring; SNMP\n"
  SNMP = cSNMP(5)
  ALL_THREADS.append(SNMP)
  SNMP.daemon = True
  #SNMP.start()

  print "5. Starting monitoring; WMI\n"
  WMI = cWMI(5)
  ALL_THREADS.append(WMI)
  WMI.daemon = True
  #WMI.start()

  #print "6. Starting monitoring; AWESOME\n"
  #ICMP_probe = cICMP_probe()
  #ALL_THREADS.append(ICMP_probe)
  #ICMP_probe.daemon = True
  #ICMP_probe.start()


  while True:
    #ICMP.join()
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    sys.stdout.write("Monitoring |")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring /")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring -")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring \\")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring |")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring /")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring -")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    sys.stdout.write("Monitoring \\")
    sleep(0.5)
    print(CURSOR_UP_ONE + ERASE_LINE)
    #sys.stdout.flush()

