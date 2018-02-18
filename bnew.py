#Working Model
from socket import * #using sockets for now, will implement lower level if needed 
import json
import time
from datetime import datetime
from queue import Queue
from threading import Thread,Lock
import _thread as thread
import sys
from random import randint
#############
iplist=None
ops=None
keyrange=None
#to be read from file
#############
mylocks={}#list of keys I HOLD LOCKS FOR 
gotlist={}#list of return k,v pairs from get requests.
faillist={}#to count failed gets
MSGID=0
IDLOC=Lock()
PUTLOC=Lock()
LOCLOCL={}
SOCLOCL={}
putcount=1
mydata={}
idlist=[]
finlist=[]
#globals
###########
def LLS(k):
    global LOCLOCL
    k=str(k)
    if k not in LOCLOCL:
        LOCLOCL[k]=Lock()

def finlen():
    global finlist
    return len(finlist)

def myd():
    global mydata
    print(mydata)

def getput(b):
    global PUTLOC
    global putcount
    PUTLOC.acquire()
    if not b:
        nput=putcount-1
    else:
        nput=putcount
        putcount+=1
    PUTLOC.release()
    return nput

def iplen():
    global iplist
    return len(iplist)-1

def getid():
    global IDLOC
    global MSGID
    IDLOC.acquire()
    id=MSGID
    MSGID+=1
    IDLOC.release()
    return id

def readfile():
    global iplist
    global ops
    global keyrange
    data=None
    with open('config.txt','r') as f:
        data=json.load(f)
    iplist=data["ip"]
    ops=data["ops"]
    keyrange=data["keyrange"]

def main(): 
    readfile()
    slist=start_up()
    thread.start_new_thread(gencmds,(slist,))
    for s in slist:
        thread.start_new_thread(listen,(s,))
    while finlen()<(iplen()+1):
        time.sleep(1)#just for a cleaner run

def start_up():
    slist=[] 
#list of ip's for my network.Creating connections based on this list. Probably will be read in from a file                      
#I don't have static ip's so will need to update each time I move until I set it up on a AWS
    PORT_NUMBER=5000 #starting port, will iterate up as needed for more connections.
#when we create, we send out requests to connect to all other nodes, then we wait for new nodes to ask us for connection.                            
    n=10 #number of nodes, plus a few extra for safety
    partition={}
    for ip in iplist:
        i=PORT_NUMBER
        flag=True
        while i < PORT_NUMBER+n and flag:
            s=socket(AF_INET,SOCK_STREAM)
            try:
                s.connect((ip,i))
                print("connect on",ip)
                slist.append(s)
                flag=False
            except:
                i+=1
    s=socket(AF_INET,SOCK_STREAM)
    flag=True
    while flag:
        try:
            s.bind((get_ip_address(),PORT_NUMBER))
            flag=False
        except:
            PORT_NUMBER+=1
    s.listen(0)
    while len(slist)<(len(iplist)-1):
        conn,addr=s.accept()
        print("connect on",addr)
        slist.append(conn)
    for s in slist:
        SOCLOCL[s]=Lock()
    return slist

#Protocols
############################
def get(k,slist):
    global mydata
    global faillist
    global gotlist
    id=getid()
    k=str(k)
    msg="GET"+str(k)
    if k in mydata:
        return mydata[k]
    for s in slist:
        send(s,msg,id)
    id=str(id)
    while not id in faillist or not faillist[id]==iplen():
        if id in gotlist:
            return gotlist.pop(id)
    return None

def got(k,s,id):
    global mydata
    v='\xff'#denotes not found
    k=str(k)
    if k in mydata:
        v=str(mydata[k])
    msg="GOT"+k+"_"+v
    send(s,msg,id)

def put(k,v,slist):
    global mydata
    x=get(k,slist)
    k=str(k)
    b=k not in mydata
    if not x:
        if k not in mydata:
            mydata[k]=v
            return getput(True)
    return getput(False)

def lock(k,slist):
    global LOCLOCL
    global mylocks
    k=str(k)
    LLS(k)
    LOCLOCL[k].acquire()
    while k in mylocks:
        pass
    mylocks[k]=0
    LOCLOCL[k].release()
    msg="LCK"+str(k)
    id=getid()
    idlist.append(str(id))
    for s in slist:
        send(s,msg,id)
    return id

def locked(k,s,id):
    global LOCLOCL
    global mylocks
    LLS(k)
    LOCLOCL[k].acquire()
    while k in mylocks:
        pass
    msg="LKD"+str(k)
    send(s,msg,id)
    LOCLOCL[k].release()

def unlock(k,slist):
    global mylocks
    k=str(k)
    mylocks.pop(k)

def done(slist):
    global finlist
    msg="FIN"
    id=getid()
    for s in slist:
        send(s,msg,id)
    finlist.append("0")

############################
def parse(mssg,s):
    try:
        msg,id=mssg.split("\x00")
    except ValueError:
        print("Error:",mssg)#corrupted message
        return
    type=msg[:3]
    rest=msg[3:]
    k=None
    v=None
    try:
        k,v=rest.split("_")
    except ValueError:
        k=rest
        v=None

    if type=="GET":
        got(k,s,id)
        pass
    elif type=="GOT":
        if v=="\xff":
            if id not in faillist:
                faillist[id]=0
            faillist[id]+=1
        else:
            gotlist[id]=v
    elif type=="LCK":
        locked(k,s,id)
    elif type=="LKD":
        if id in idlist:#currently requested lock (time outs)
            mylocks[str(k)]+=1
    elif type=="FIN":
        finlist.append(s)

def wait(key,slist,id):
    key=str(key)
    dt=datetime.now()
    while not mylocks[key]==iplen():
        tn=datetime.now()
        td=tn-dt
        ts=td.total_seconds()
        if ts>1:
            #print('stuck2',mylocks,key) #lock on keys, threads interfeering in to
            a=randint(1,2)
            if a==1:#random chance to give up lock
                idlist.remove(str(id))
                mylocks.pop(key)
                id=lock(key,slist)
                
            dt=datetime.now()

def cmds(slist,i):
    dt=datetime.now()
    a=randint(1,10)
    key=randint(0,keyrange)
    while key in mylocks:
        #print('stuck')
        pass#currently, can't support keeping lock for multiple actions at once, need to reacquire
    value=randint(0,1000000)
    id=lock(key,slist)
    wait(key,slist,id) 
    if a>6:
        c=put(key,value,slist)
        print("Put:",key,c)
    else:
        value=get(key,slist)
        print("Get:",key,value)
    unlock(key,slist)
    #print("Command",i,"of",num)
    td=((datetime.now())-dt).total_seconds()
    return td
    
def gencmds(slist):
    global mydata
    print('doing commands')
    tl=0
    dt=datetime.now()
    for i in range(0,ops):
        td=cmds(slist,i)
        tl+=td
    td=datetime.now()-dt
    td=td.total_seconds()
    tp=ops/td
    lt=tl/ops
    print("latency:",lt)
    print("throughput:",tp)
    print("data:",mydata)
    done(slist)

def send(s,msg,id):
    msg=msg+"\x00"+str(id) #char/x00 splits msg and id
    emsg=msg.encode('utf-8')
    length=len(emsg)
    elength=int_to_bytes(length)
    SOCLOCL[s].acquire()
    s.send(elength)
    s.send(emsg)
    SOCLOCL[s].release()

def listen(s):
    while True:
        l=int_from_bytes(s.recv(1))
        emsg=s.recv(l)
        msg=emsg.decode('utf-8')
        if len(msg)>0:
            thread.start_new_thread(parse,(msg,s,))

def get_ip_address():#using google to obtain real ip, google most reliable host I know.
    s = socket(AF_INET,SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def int_to_bytes(x):#convert int to bytes to send
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def int_from_bytes(xbytes): #recieved bytes to int 
    return int.from_bytes(xbytes, 'big')

main()#program is loaded, start running
