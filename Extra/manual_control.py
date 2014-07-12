
import time,random, linecache
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons

axcolor = 'lightgoldenrodyellow'

# y = [3,6,4,0,9,0,8,6,3,2]
# x = np.empty(len(y))
# x.fill(1)
#plt.scatter(x,y,s=10,c='b', marker='o', cmap=None, norm=None, vmin=None, vmax=None, alpha=None, linewidths=None, verts=None, hold=None)
x = [] #The TIme
y = []
z = []
w = [] #The "received" one!
r = [] 
position = 0
flag_manual = False

fig = plt.figure(figsize=(14,14))
#fig_high = plt.figure(figsize=(14,14))
#fig_high.canvas.set_window_title("Attacking...")
fig.canvas.set_window_title("Live Data ...")

# attack_rate = fig_high.add_subplot(1,1,1)
#attack_rate = global_rate.twinx()
# attack_rate.set_autoscaley_on(True)
# attack_rate.set_ylabel("Attack (Agent's) rate", color='black')
# for tl in attack_rate.get_yticklabels():
#     tl.set_color('black')

monitoring = fig.add_subplot(1,1,1)
# monitoring = global_rate.twinx()
monitoring.set_autoscaley_on(True)
#monitoring.set_ylim([0,1000])
monitoring.set_ylabel('Success Rate', color='g')
for tl in monitoring.get_yticklabels():
    tl.set_color('g')
monitoring.set_ybound([0,10])

#received = monitoring.twinx()
received = fig.add_subplot(1,1,1)
received.set_autoscaley_on(True)
received.set_ylabel('Acked Monitoring', color='b')
for t1 in received.get_yticklabels():
    t1.set_color('b')

# global_rate = fig.add_subplot(1,1,1)
global_rate = monitoring.twinx()
global_rate.set_autoscaley_on(True)
global_rate.set_xlabel('time (s)')  ## THE only one!?
global_rate.set_ylabel('Global Rate', color='r')
for tl in global_rate.get_yticklabels():
    tl.set_color('r')

axslider  = plt.axes([0.15, 0.02, 0.60, 0.03], axisbg=axcolor)
sAttackRate = Slider(axslider, 'Attack INC Steps:', 0.1, 600.0, valinit=200)

def draw_it(i):
    global x, y, z, w, r, position, sAttackRate, flag_manual
    F = open('/tmp/global.csv','r')
    #F = open('global.csv','rb')
    F.seek(position,0)
    Data = F.read()
    DataArray = Data.split('\n')
    # sAttackRate.valinit = DataArray[0][0]
    if DataArray[0]:
        'aaa',DataArray[0][0]
    for eachLine in DataArray:
        if len(eachLine) > 2:
            # print eachLine
            x.append(int(len(x)+1))                 # A counter used as the Time
            y.append(int(eachLine.split(',')[0]))   #Global Attack Rate
            # z.append(int(eachLine.split(',')[1]))   #Attack Rate (Attacking agent's only)
            r.append(int(eachLine.split(',')[2]))   #Acked Monitoring Rate
	        #if len(eachLine.split(','))>3:
		    #w.append(int(eachLine.split(',')[3].split('.')[0]))   #The New one.
            w.append(int(eachLine.split(',')[3]))   #The New one.
	        #else:
		    #w.append(0)
        if len(x) > 3:
            tmp = int(y[len(y)-1])-int(y[len(y)-2])
            if (tmp > 0) and (not flag_manual):
                sAttackRate.set_val(tmp)
    global_rate.plot(x,y,'r')
    # attack_rate.plot(x,z,'black')
    monitoring.plot(x,r,'g')
    received.plot(x,w,'b')
    position = F.tell()
    fig.canvas.draw_idle()
    F.close()


def reload(i):
    global x, y, z, w, r ,position
    x = []
    y = []
    z = []
    w = []
    r = []
    position = 0
    # sAttackRate.reset()
    global_rate.clear()
    # attack_rate.clear()
    monitoring.clear()
    received.clear()
    #draw_it(0)

def newrate(val):
    global flag_manual
    if flag_manual: #If we are supposed to manually override the rate
        # flag_manual = False
        F = open('../master/command.conf',"w")
        F.write(str(val))
        F.close()

ani = animation.FuncAnimation(fig,draw_it, interval=2000)
# ani_high = animation.FuncAnimation(fig_high,draw_it, interval=2000)


reloadallax = plt.axes([0.90, .012, .07, 0.04]) #[Starting X, Starting Y, Length, Width ]
btn_ReLoad = Button(reloadallax, 'Reload All', color=axcolor, hovercolor='0.975')
btn_ReLoad.on_clicked(reload)

def loadfunc(i):
    global x,y,z,w,r
    if i == "Most Recent":
        recent = 300
        print 'Loading last '+str(recent)+ ' items only...'
        x_tmp = x[len(x)-recent-1:len(x)-1]
        y_tmp = y[len(y)-recent-1:len(y)-1]
        r_tmp = r[len(r)-recent-1:len(r)-1]
        w_tmp = w[len(w)-recent-1:len(w)-1]
        # z_tmp = z[len(z)-recent-1:len(z)-1]
        x = x_tmp
        y = y_tmp
        r = r_tmp
        w = w_tmp
        # z = z_tmp
    else: #Meaning that i = "All Rate"
        reload(20)

    # sAttackRate.reset()
    global_rate.clear()
    # attack_rate.clear()
    monitoring.clear()
    received.clear()
    #draw_it(0)

sAttackRate.on_changed(newrate)


############ Reload Recent ############
# reloadrecentax = plt.axes([0.9, .012, .07, 0.04]) #[Starting X, Starting Y, Length, Width ]
# btn_ReLoadRecent = Button(reloadrecentax, 'Reload Recent', color=axcolor, hovercolor='0.975')
# btn_ReLoadRecent.on_clicked(reload_recent)

############ CHECK BOX ############
rax = plt.axes([0.020, 0.765, 0.1, 0.10])
check = CheckButtons(rax, ('Manual Rate', 'Continues Apply'), (False, True))
def func_checkbox(label):
    global flag_manual
    if label == 'Manual Rate':
        flag_manual = not flag_manual
check.on_clicked(func_checkbox)

############ Radio Button ############
rax = plt.axes([0.020, 0.6, 0.1, 0.10], axisbg=axcolor)
radio = RadioButtons(rax, ('All Rate', 'Most Recent'), active=0)
radio.on_clicked(loadfunc)



plt.show()
