import json
import pickle
with open("Plan.pickle","rb") as f:
    Plan=pickle.load(f)
for n in Plan:
    s="exp"+str(n)
    print(n,Plan[n][0],Plan[n][1],s,end=" [")
    for b in Plan[n][3]:
        print(b,end=",")
    print("]")
