#Problem File for Blocks World
from treehop import *
#from BWD import *
#from collections import defaultdict
from random import *

state=State('state')
state.on={}#not in on, then on table. Key is on value

tb=99
n=10
for i in range(0,tb):
    x=randint(0,tb)
    y=randint(0,2)
    val=state.on.values()
    print(val)
    if y==2 and not x==i:
        if not x in val:
            state.on[i]=x
print(state.on)

def printTowers(state):
    towers=[]
    c=0
    p=[]
    for key in state.on:
        if key in p:
            continue
        block=key
        print("############")
        while block in state.on:
            if block in p:
                print(p,block)
            p.append(block)
            print(block)
            block=state.on[block]
        p.append(block)
        print(block)
    for i in range(0,tb):
        if i not in state.on and i not in p:
            print(i in p,i in state.on)
            print("############")
            p.append(i)
            print(i)
    print("count:",len(p))
    print(p)
printTowers(state)
