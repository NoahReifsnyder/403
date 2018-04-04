import sys
import copy
domain=sys.argv[1]
problem=sys.argv[2]
planner=sys.argv[3]
#actuator=sys.argv[4]
#metaAQUA=sys.argv[5]
D=__import__(domain[:-3])
P=__import__(problem[:-3])#substitute problem file here
T=__import__(planner[:-3])
#A=__import__(actuator[:-3])
#M=__import__(metaAQUA[:-3])
nstate=copy.deepcopy(P.state)
#T.wrapper(P.state,P.goals)
Plan=T.wrapper(P.state,P.goals)
T.print_plan(Plan)
