#Grid World Problem File
from __future__ import print_function
from treehop import *
from MWD import *
from collections import defaultdict
from random import *




state=State('state')
state.above={}
state.behind={}
state.below={}
state.infront={}
state.lit={"B1":0,"B2":0,"B3":0}
state.beacons={}
state.agent={'Agent1':1}
state.clear={}
state.fuel={'Agent1':(30,30)}
n=10
placed=[]
for b in state.lit:
    x=randint(1,n*n)
    while x in placed:
        x=randint(1,n*n)
    placed.append(x)
    state.beacons[b]=x
i=1
while i<=n**2:
    state.clear[i]=1
    if i<=n:
        if i==1:
            state.behind[i]=i+1
        elif i==n:
            state.infront[i]=i-1
        else:
            state.behind[i]=i+1
            state.infront[i]=i-1
        state.above[i]=i+n
    elif i>(n**2-n):
        if i==(n**2-n+1):
            state.behind[i]=i+1
        elif i==n**2:
            state.infront[i]=i-1
        else:
            state.behind[i]=i+1
            state.infront[i]=i-1
        state.below[i]=i-n
    elif (i-1)%n==0:
        state.below[i]=i-n
        state.above[i]=i+n
        state.behind[i]=i+1
    elif i%n==0:
        state.below[i]=i-n
        state.above[i]=i+n
        state.infront[i]=i-1
    else:
        state.below[i]=i-n
        state.above[i]=i+n
        state.infront[i]=i-1
        state.behind[i]=i+1
    i=i+1

goals=[('light_all', 'Agent1', n)]
#Plan=wrapper(state, goals, depth=1, verbose=0)

#print_plan(Plan,exp='Bexp')

