from socket import *
import json
import time
from datetime import datetime
from queue import Queue
from threading import Thread,Lock
import _thread as thread
import sys
from random import randint
###############################
iplist=None
op=None
keyrange=None
closeable=None
###############################
slist=[]
outfile=open("out.txt","w")
###############################

def start_up():
    global slist
    PORT_NUMBER=5000
    s=socket(AF_INET,SOCK_STREAM)
    s.bind((get_ip_address(),PORT_NUMBER))
    s.listen(0)
    while slistlen()<iplistlen():
        conn,addr=s.accept()
        slist.append(conn)





        
def main():
    print("\n\n\n\n\n\n\n\n\n\n This is the output for node "+get_ip_address())
    #start_up()
    print("hello")
    time.sleep(5)
def get_ip_address():#using google to obtain real ip, google most reliable host I know.
    s = socket(AF_INET,SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
def slistlen():
    return len(slist)
def iplistlen():
    return len(iplist)-1            
main()
