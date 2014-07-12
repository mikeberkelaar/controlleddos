Controlled DDOS Simulation
==========================

Concept (Python 2) framework of performing controlled (D)DoS attacks for auditing purposes. This software is by no means meant, nor suited, to perform malicious denial of service attacks. 
Implementations of a basic network- and application level denial of service attack are added to demo the effects of the controlled aspect, utilizing monitored observables to control the attack rate and prevent damage. 

  * Master/master.py: Master component (Monitoring and attack orchestration)
  * Attack_Agent/attack_agent.py: Distributed attack agent
  * Monitoring_Agent/: Distributed monitoring agents
    1. high_frequency/mon_agent.py: High frequency packet-loss measurements used for network-level attacks.
    2. low_frequency/mon_agent.py: HTTP/ICMP response time/loss monitoring
  * Extra/manual_control.py: Interface to simulation graph and manual control



