from socket import * #using sockets for now, will implement lower level if needed 
import time
import _thread as thread

def main(): 
    slist=start_up()
    for s in slist:
        
    time.sleep(1)
    print(slist)
    shut_down(slist)
def start_up():
    slist=[]
    iplist=['10.0.0.173','10.0.0.224','10.0.0.39'] 
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
                a=s.connect((ip,i))
                print("connect on",ip)
                print(a)
                slist.append(s)
                flag=False
            except:
                i+=1
    while len(slist)<(len(iplist)-1):
        s=socket(AF_INET,SOCK_STREAM)
        flag=True
        while flag:
            try:
                s.bind((get_ip_address(),PORT_NUMBER))
                flag=False
            except:
                PORT_NUMBER+=1
        s.listen(0)
        conn,addr=s.accept()
        s.listen(0)
        print("connect on",addr)
        slist.append(s)
    return slist

def shut_down(slist):
    for s in slist:
        s.close()
        slist.remove(s)
def get():
    pass
def put():
    pass
def parse():
    pass
def gencmds(slist):
    for s in slist:
        try:
            print(s.getpeername())
        except:
            print(s.getsockname())
    pass

def get_ip_address():
    s = socket(AF_INET,SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

main()
