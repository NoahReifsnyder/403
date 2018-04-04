"""
Pyhop, version 1.2.2 -- a simple SHOP-like planner written in Python.
Author: Dana S. Nau, 2013.05.31

Copyright 2013 Dana S. Nau - http://www.cs.umd.edu/~nau

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   
Pyhop should work correctly in both Python 2.7 and Python 3.2.
For examples of how to use it, see the example files that come with Pyhop.

Pyhop provides the following classes and functions:

- foo = State('foo') tells Pyhop to create an empty state object named 'foo'.
  To put variables and values into it, you should do assignments such as
  foo.var1 = val1

- bar = Goal('bar') tells Pyhop to create an empty goal object named 'bar'.
  To put variables and values into it, you should do assignments such as
  bar.var1 = val1

- print_state(foo) will print the variables and values in the state foo.

- print_goal(foo) will print the variables and values in the goal foo.

- declare_operators(o1, o2, ..., ok) tells Pyhop that o1, o2, ..., ok
  are all of the planning operators; this supersedes any previous call
  to declare_operators.

- print_operators() will print out the list of available operators.

- declare_methods('foo', m1, m2, ..., mk) tells Pyhop that m1, m2, ..., mk
  are all of the methods for tasks having 'foo' as their taskname; this
  supersedes any previous call to declare_methods('foo', ...).

- print_methods() will print out a list of all declared methods.

- pyhop(state1,tasklist) tells Pyhop to find a plan for accomplishing tasklist
  (a list of tasks), starting from an initial state state1, using whatever
  methods and operators you declared previously.

- In the above call to pyhop, you can add an optional 3rd argument called
  'verbose' that tells pyhop how much debugging printout it should provide:
- if verbose = 0 (the default), pyhop returns the solution but prints nothing;
= {4: 1, 5: 2, 6: 3, 7: 4, 8: 5, update to python 3.4 ubuntu9: 6}
    state.agent = {'Agent3': 2, 'Agent2': 4, 'Agent1': 1}
- if verbose = 1, it prints the initial parameters and the answer;
- if verbose = 2, it also prints a message on each recursive call;
- if verbose = 3, it also prints info about what it's computing.
"""

# Pyhop's planning algorithm is very similar to the one in SHOP and JSHOP
# (see http://www.cs.umd.edu/projects/shop). Like SHOP and JSHOP, Pyhop uses
# HTN methods to decompose tasks into smaller and smaller subtasks, until it
# finds tasks that correspond directly to actions. But Pyhop differs from 
# SHOP and JSHOP in several ways that should make it easier to use Pyhop
# as part of other programs:
# 
# (1) In Pyhop, one writes methods and operators as ordinary Python functions
#     (rather than using a special-purpose language, as in SHOP and JSHOP).
# 
# (2) Instead of representing states as collections of logical assertions,
#     Pyhop uses state-variable representation: a state is a Python object
#     that contains variable bindings. For example, to define a state in
#     which box b is located in room r1, you might write something like this:
#     s = State()
#     s.loc['b'] = 'r1'
# 
# (3) You also can define goals as Python objects. For example, to specify
#     that a goal of having box b in room r2, you might write this:
#     g = Goal()
#     g.loc['b'] = 'r2'
#     Like most HTN planners, Pyhop will ignore g unless you explicitly
#     tell it what to do with g. You can do that by referring to g in
#     your methods and operators, and passing g to them as an argument.
#     In the same fashion, you could tell Pyhop to achieve any one of
#     several different goals, or to achieve them in some desired sequence.
# 
# (4) Unlike SHOP and JSHOP, Pyhop doesn't include a Horn-clause inference
#     engine for evaluating preconditions of operators and methods. So far,
#     I've seen no need for it; I've found it easier to write precondition
#     evaluations directly in Python. But I could consider adding such a
#     feature if someone convinces me that it's really necessary.
# 
# Accompanying this file are several files that give examples of how to use
# Pyhop. To run them, launch python and type "import blocks_world_examples"
# or "import simple_travel_example".


from __future__ import print_function
import copy,sys, pprint
import io
from contextlib import redirect_stdout
############################################################
# States and goals
class PlanNode():
    """The Plan Tree"""
    def __init__(self,action, cond, depth):
        self.action = action
        self.cond=cond
        self.changes=0
        self.depth=depth
        self.children=[]
        self.Fexp={}
        self.branch={}
        self.Tree=0

class TreePlan():
    def __init__(self,action,cond,branch={},Bexp={}):
        self.action=action
        self.num=-1
        self.next=0
        self.prev=0
        self.found=0
        self.cond=cond
        self.dBexp=0
        self.changes=0
        self.oChanges=0
        for d in Bexp:
            for e in Bexp[d]:
                temp=Bexp[d][e]
                if not isinstance(temp,dict):
                    Bexp[d][e]={temp:1}
        self.Bexp=Bexp
        self.branch=branch

class State():
    """A state is just a collection of variable bindings."""
    def __init__(self,name):
        self.__name__ = name

class Goal():
    """A goal is just a collection of variable bindings."""
    def __init__(self,name):
        self.__name__ = name


### print_state and print_goal are identical except for the name

def print_state(state,indent=4):
    """Print each variable in state, indented by indent spaces."""
    if state != False:
        for (name,val) in vars(state).items():
            if name != '__name__':
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(state.__name__ + '.' + name)
                print(' =', val)
    else: print('False')

def state_Fexp(newstate, state=0, indent=4):#Find changes in state caused by action, save
    """find state Fexps"""
    Fexp={}
    global testState
    if not state:
        state=testState
    #print('new')
    #print_state(newstate)
    #print_state(state)
    remove={}
    if state != False and newstate!=False:
        for (name, val) in vars(state).items():
            if name != '__name__' and name !='found':
                Fexp[name]={}
                negname="~"+name
                Fexp[negname]={}
                for x in val:
                    if not x in vars(newstate)[name]:
                        Fexp[negname][x]=vars(state)[name][x]
                    elif vars(state)[name][x] !=  vars(newstate)[name][x]:
                        #print(name,x,vars(newstate)[name][x])
                        Fexp[name][x]=vars(newstate)[name][x]
        for (name, val) in vars(newstate).items():
            if name != '__name__' and name !='found':
                if name not in Fexp:
                    Fexp[name]={}
                for x in val:
                    if not x in vars(state)[name] or vars(state)[name][x] !=  vars(newstate)[name][x]:
                        #print(name,x,vars(newstate)[name][x])
                        Fexp[name][x]=vars(newstate)[name][x]
    return Fexp

first=1
def compound_Fexp(tree):
    global first
    if hasattr(tree,'find'):
        #print('here')
        pass
    #First doesn't get set to previous actions compounded changes because no prev. action
    if first==1:
        tree.Fexp={}
        for d in tree.changes[-1]:
            if not '~' in d:
                tree.Fexp[d]={}
        first=0
    if first==2 and not tree.action=='Finished':
        first=0
        for x in tree.changes:
            remove=[]
            for d in tree.Fexp:
                if "~" in d:
                    nd=d[1:]
                    for e in tree.changes[x][d]:
                        if e in tree.changes[x][nd]:
                            tree.changes[x][nd].pop(e)
                    remove.append(d)
                    continue
            for d in remove:
                tree.changes[x].pop(d)
        for x in tree.changes:
            for d in tree.Fexp:
                if d not in tree.changes[x]:
                    tree.changes[x][d]={}
                for e in tree.Fexp[d]:
                    if e not in tree.changes[x][d]:
                        tree.changes[x][d][e]=tree.Fexp[d][e]
    if not tree.changes or not tree.next:
        return
    
    #print(tree.action,tree.cond,tree.changes[-1],'\n','\n')
    #May need to do above as well
    for x in tree.changes:
        remove=[]
        for d in tree.changes[x]:
            if "~" in d:
                nd=d[1:]
                for e in tree.changes[x][d]:
                    if e in tree.changes[x][nd]:
                        tree.changes[x][nd].pop(e)
                remove.append(d)
                continue
        for d in remove:
            tree.changes[x].pop(d)
    for x in tree.changes:
        for d in tree.changes[x]:
            if x==-1 and tree.next.changes:
                for y in tree.next.changes:
                    if not d in tree.next.changes[y]:
                        tree.next.changes[y][d]=tree.changes[x][d]
            elif not x==-1:
                if x in tree.branch and tree.branch[x].changes:
                    for y in tree.branch[x].changes:
                        if not d in tree.branch[x].changes[y]:
                            tree.branch[x].changes[y][d]=tree.changes[x][d]
            for e in tree.changes[x][d]:
                if x==-1 and tree.next.changes:
                    for y in tree.next.changes:
                        if not e in tree.next.changes[y][d]:
                            tree.next.changes[y][d][e]=tree.changes[x][d][e]
                elif not x==-1:
                    if x in tree.branch and tree.branch[x].changes:
                        for y in tree.branch[x].changes:
                            if not e in tree.branch[x].changes[y][d]:
                                tree.branch[x].changes[y][d][e]=tree.changes[x][d][e]
    if tree.next:
        tree.next.Fexp=tree.changes[-1]
        compound_Fexp(tree.next)
        if not hasattr(tree.next,'Fexp'):
            tree.next.Fexp=copy.deepcopy(tree.Fexp)
    for b in tree.branch:
        tree.branch[b].Fexp=tree.changes[b]
        compound_Fexp(tree.branch[b])
        if not hasattr(tree.branch[b],'Fexp'):
            tree.branch[b].Fexp=copy.deepcopy(tree.Fexp)
    #print(tree.action,tree.cond,tree.changes[-1],'\n','\n')
def print_goal(goal,indent=4):
    """Print each variable in goal, indented by indent spaces."""
    if goal != False:
        for (name,val) in vars(goal).items():
            if name != '__name__':
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(goal.__name__ + '.' + name)
                print(' =', val)
    else: print('False')

############################################################
# Helper functions that may be useful in domain models

def forall(seq,cond):
    """True if cond(x) holds for all x in seq, otherwise False."""
    for x in seq:
        if not cond(x): return False
    return True

def find_if(cond,seq):
    """
    Return the first x in seq such that cond(x) holds, if there is one.
    Otherwise return None.
    """
    for x in seq:
        if cond(x): return x
    return None

############################################################
# Commands to tell Pyhop what the operators and methods are

operators = {}
methods = {}
precond= {}

#name, method_reference, dict of preconditions
def declare_operators(*op_list):
    """
    Call this after defining the operators, to tell Pyhop what they are. 
    op_list must be a list of functions, not strings.
    """
    
    operators.update({op.__name__:op for op in op_list})
    return operators

def declare_methods(task_name,*method_list):
    """
    Call this once for each task, to tell Pyhop what the methods are.
    task_name must be a string.
    method_list must be a list of functions, not strings.
    """
    methods.update({task_name:list(method_list)})
    return methods[task_name]

############################################################
# Commands to find out what the operators and methods are
def print_plan(tree,indent=0, exp='Bexp'):
    if not tree:
        return
    for x in range(0,indent):
        print(' ', end='')
    if not tree.action=='Finished' and not tree.action=='branch':
        print (tree.num,tree.action,tree.cond,getattr(tree,exp)) 
    else:
        print (tree.num,tree.action,getattr(tree,exp))
    for b in tree.branch:
        if not tree.found:
            print_plan(tree.branch[b],indent+4,exp)
        else:
            if b not in tree.found:
                print_plan(tree.branch[b],indent+4,exp)
            else:
                for x in range(0,indent):
                    print(' ', end='')
                print (tree.branch[b].num)
    if not tree.found:
        print_plan(tree.next, indent,exp)
    else:
        if -1 not in tree.found:
            print_plan(tree.next,indent,exp)
        else:
            for x in range(0,indent):
                print(' ', end='')
            print (tree.next.num)
    
def print_planI(tree, indent=0):
     if not tree:
        return
     for x in range(0,indent):
         print(' ', end='')
     if not tree.action=='branch' and not tree.action=='Finished':
         print (tree.num,tree.action,tree.cond,tree.Fexp)
     else:
         print (tree.num,tree.action,tree.Fexp)
     for b in tree.branch:
         if not tree.found:
             print_planI(tree.branch[b],indent+4)
         else:
             if b not in tree.found:
                 print_planI(tree.branch[b],indent+4)
             else:
                 for x in range(0,indent):
                     print(' ', end='')
                 print (tree.branch[b].num)
     if not tree.found:
         print_planI(tree.next, indent)
     else:
         if -1 not in tree.found:
             print_planI(tree.next,indent)
         else:
             for x in range(0,indent):
                 print(' ', end='')
             print (tree.next.num)

tp=TreePlan("Tree",[])
counter=0
def tree_plan(plan,tree):
    toVisit=[plan]
    global counter
    while toVisit:
        node=toVisit.pop()
        for child in node.children:
            toVisit.append(child)
        if hasattr(node,'method') or node.action=="Plan":
            '''if tree.action!='check_state':
                newTree=TreePlan('check_state', node.Fexp)
                newTree.num=counter
                counter+=1
                newTree.next=tree
                newTree.Bexp=copy.deepcopy(node.Fexp)
                for d in newTree.Bexp:
                    for e in newTree.Bexp[d]:
                        p=newTree.Bexp[d][e]
                        perc={p:1}
                        newTree.Bexp[d][e]=perc
                tree=newTree'''
        elif hasattr(node,'find'):
            #print('here')
            pass
        else:
            newTree=TreePlan(node.action,node.cond,node.branch,node.Bexp)
            newTree.num=counter
            newTree.states=node.states
            newTree.Fexp=node.Fexp
            counter+=1
            newTree.precond=node.precond
            newTree.changes=node.changes
            newTree.oChanges=node.oChanges
            newTree.next=tree
            tree=newTree
            node.Tree=newTree
        if hasattr(node,'find'):
            tree.find=1
            tree.node=node.node
        #node.Tree=newTree
    return tree

def remove_checks(tree):
    if tree.next:
        if tree.next.action=='check_state':
            print(tree.num,tree.action,tree.Bexp,tree.next.Bexp)
            for d in tree.next.Bexp:
                if d not in tree.Bexp:
                    tree.Bexp[d]={}
                for e in tree.next.Bexp[d]:
                    if e not in tree.Bexp[d]:
                        tree.Bexp[d][e]=tree.next.Bexp[d][e]
            print(tree.num,tree.action,tree.Bexp,tree.next.Bexp)
        remove_checks(tree.next)
    for b in tree.branch:
        if tree.branch[b].action=='check_state':
            print('lol were not here')
        remove_checks(tree.branch[b])

def link(tree):
    if not tree:
        return False
    if hasattr(tree,'find'):
        tree=tree.node.Tree
        return True
    for b in tree.branch:
        if link(tree.branch[b]):
            if not tree.found:
                tree.found={b:1}
            else:
                tree.found[b]=1
    if link(tree.next):
        tree.next=tree.next.node.Tree
        if not tree.found:
            tree.found={-1:1}
        else:
            tree.found[-1]=1
    return False

#When loop is found while calculating Bexp, we must first acted like that branch does not exist. then use the root of the loop to build the branch, and rebuild the root.
def numB(tree):#used to find usable branches for coalescing
    if not tree or tree.dBexp==2:
        return 1
    if tree.dBexp==1:
        return 0
    if not tree.found:
        if numB(tree.next):
           return 1 
        for b in tree.branch:
            if numB(tree.branch[b]):
                return 1
    else: return 1
    return 0

def tree_Bexp(tree,Combine=True):
    '''if tree.next and tree.next.num==-1 and not tree.action=='branch':
        print(tree.num)
        tree.next.Fexp=tree.changes[-1]'''
    if not tree or not tree.next or tree.dBexp==2:
        return
    '''
    if bypass:
        print (tree.num)
        print (tree.next.dBexp)
        for b in tree.branch:
            print(tree.branch[b].dBexp)
    if tree.dBexp==1:
        tree.Bexp=tree.oBexp
    tree.oBexp=tree.Bexp
    tree.dBexp=1
    if not tree.next:
        return tree.Bexp
    bNum=0
    if not bypass:
        if tree.next:
            if not tree.found or not -1 in tree.found and tree.next.dBexp==0:
                tree_Bexp(tree.next)
        for b in tree.branch:
            if not tree.found or not b in tree.found:
                tree_Bexp(tree.branch[b])
        bNum=len(tree.branch)+1
    else:
        bNum=len(tree.branch)+1
        if tree.next.dBexp==1:
            bNum-=1
        for b in tree.branch:
            if tree.branch[b].dBexp==1:
                bNum-=1
    '''
    if tree.found:
        tree.dBexp=1
    if not hasattr(tree,'oBexp'):
        tree.oBexp=copy.deepcopy(tree.Bexp)
    tbNum=len(tree.branch)+1
    bNum=0
    bNum+=numB(tree.next)
    for b in tree.branch:
        bNum+=numB(tree.branch[b])
    if numB(tree.next):
        tree_Bexp(tree.next,Combine)
    for b in tree.branch:
        if numB(tree.branch[b]):
            tree_Bexp(tree.branch[b],Combine)
    if bNum==0:
        tree_Bexp(tree.next,Combine)
        bNum=1
    if tree.action=='branch':
        tree.Bexp=copy.deepcopy(tree.next.Bexp)
        if(done(tree)):
            tree.dBexp=2
    if hasattr(tree,'oBexp'):
        tree.Bexp=copy.deepcopy(tree.oBexp)
    '''if not tree.next.next:
        for d in tree.Fexp:
            if not d in tree.Bexp:
                tree.Bexp[d]={}
            for e in tree.Fexp[d]:
                if not e in tree.Bexp[d]:
                    tree.Bexp[d][e]={tree.Fexp[d][e]:1}'''
    for d in tree.next.Bexp:
        if not numB(tree.next):
            break
        if d not in tree.Bexp:
            tree.Bexp[d]={}
        for e in tree.next.Bexp[d]:
            #if this action changes this expectation, ignore further expectations
            if not tree.oChanges or not tree.oChanges[-1] or e not in tree.oChanges[-1][d]:
                if e not in tree.Bexp[d]:
                    tree.Bexp[d][e]={}
                for p in tree.next.Bexp[d][e]:
                    if p not in tree.Bexp[d][e]:
                        tree.Bexp[d][e][p]=tree.next.Bexp[d][e][p]/bNum
                    else: 
                        tree.Bexp[d][e][p]=tree.Bexp[d][e][p]+tree.next.Bexp[d][e][p]/bNum
                    if tree.Bexp[d][e][p]>1:
                        tree.Bexp[d][e][p]=1
    for b in tree.branch:
        if not numB(tree.branch[b]):
            break
        for d in tree.branch[b].Bexp:
            if d not in tree.Bexp:
                tree.Bexp[d]={}
            for e in tree.branch[b].Bexp[d]:
                if not tree.oChanges or not tree.oChanges[b] or not tree.oChanges[b][d] or e not in tree.oChanges[b][d]:
                    if e not in tree.Bexp[d]:
                        tree.Bexp[d][e]={}
                    for p in tree.branch[b].Bexp[d][e]:
                        if p not in tree.Bexp[d][e]:
                            tree.Bexp[d][e][p]=tree.branch[b].Bexp[d][e][p]/bNum
                        else:
                            tree.Bexp[d][e][p]=tree.Bexp[d][e][p]+tree.branch[b].Bexp[d][e][p]/bNum
                        if tree.Bexp[d][e][p]>1:
                            tree.Bexp[d][e][p]=1
    if done(tree):
        tree.dBexp=2
    return 

def done(tree):
    done=1
    if not tree.next.dBexp==2:
        done=0
        for b in tree.branch:
            if not tree.branch[b].dBexp==2:
                done=0
    return done

def branch_selection(tree):
    global counter
    if tree.branch:
        for b in tree.branch:
            t=TreePlan('branch',tree.branch[b].Bexp)
            t.state=tree.states[b]
            t.num=counter
            counter+=1
            t.Fexp=tree.changes[b]
            t.next=tree.branch[b]
            tree.branch[b]=t
            branch_selection(tree.branch[b])
        t=TreePlan('branch', tree.next.Bexp)
        t.Fexp=tree.changes[-1]
        t.state=tree.states[-1]
        t.num=counter
        counter+=1
        t.next=tree.next
        tree.next=t
    if tree.next:
        branch_selection(tree.next)

def tree_Rexp(tree):
    tree.dBexp=0
    tree.Rexp=copy.deepcopy(tree.Bexp)
    if not hasattr(tree,"Fexp"):
        return
    for d in tree.Fexp:
        if d not in tree.Bexp:
            tree.Bexp[d]={}
        for e in tree.Fexp[d]:
            tree.Bexp[d][e]={tree.Fexp[d][e]:1}
    if tree.action=='Finished':
        tree.Rexp={}
    if tree.found:
        return
    if tree.next:
        tree_Rexp(tree.next)
    for b in tree.branch:
        tree_Rexp(tree.branch[b])
    return

def finish(tree):
    if not hasattr(tree.next,"Fexp"):
        print('here')
        tree.next=0
    if not hasattr(tree,'oBexp'):
        tree.oBexp={}
    if tree.oBexp=={} and tree.next and hasattr(tree.next,'oBexp'):
        tree.oBexp=tree.next.oBexp
    if tree.next and not hasattr(tree.next,'states'):
        tree.next.states=tree.states
    if not hasattr(tree,'Fexp'):
        tree.Fexp={}
    if tree.action=='Finished':
        tree.oBexp={}
    remove=[]
    for d in tree.Fexp:
        if '~' in d:
            remove.append(d)
    for d in remove:
        tree.Fexp.pop(d)
    for d in tree.Fexp:
        for e in tree.Fexp[d]:
            if not isinstance(tree.Fexp[d][e],dict):
                tree.Fexp[d][e]={tree.Fexp[d][e]:1}
    if tree.num==-1:
        for d in tree.Bexp:
            for e in tree.Bexp[d]:
                if not isinstance(tree.Bexp[d][e],dict):
                    tree.Bexp[d][e]={tree.Bexp[d][e]:1}
    if not tree.next or tree.found:
        print('here')
        return
    if tree.next.num==-1:
        if tree.action=='branch':
            tree.next.Bexp=tree.Fexp
        else:
            tree.next.Bexp=tree.changes[-1]
    if tree.next.action=='branch':
        tree.next.states={-1:tree.states[-1]}
    tree.next.state=tree.states[-1]
    finish(tree.next)
    for b in tree.branch:
        if tree.branch[b].num==-1:
            if tree.action=='branch':
                tree.branch[b].Bexp=tree.Fexp
            else:
                tree.branch[b].Bexp=tree.changes[b]
        if tree.branch[b].action=='branch':
            tree.branch[b].states={-1:tree.states[b]}
        tree.branch[b].state=tree.states[b]
        finish(tree.branch[b])
    
def eq_state(s1,s2):
    c=state_Fexp(s1,s2)
    for k in c:
        for x in c[k]:
            return False
    return True
    
def print_operators(olist=operators):
    """Print out the names of the operators"""
    print('OPERATORS:', ', '.join(olist))

def print_methods(mlist=methods):
    """Print out a table of what the methods are for each task"""
    print('{:<14}{}'.format('TASK:','METHODS:'))
    for task in mlist:
        print('{:<14}'.format(task) + ', '.join([f.__name__ for f in mlist[task]]))

def string_state(state):
    f=io.StringIO()
    with redirect_stdout(f):
        print_state(state)
    return f.getvalue()

############################################################
# The actual planner
def wrapper(state,tasks,Fexp={},k=0,kMax=1,depth=0,verbose=0): #wrapper to allow me to set up globals for branched planning
    global testState
    global first
    test=0
    testState=copy.deepcopy(state)
    ####proves
    #print (state==testState)
    #print (string_state(state)==string_state(testState))
    ####SHOWING THAT 2 DIFF STATES CAN BE PROVEN EQUAL WITH SAME CONTENT
    plan=pyhop(state,tasks,k,kMax,depth,verbose)
    if not plan:
        return False
    if not Fexp=={}:
        first=2
        test=1
        plan.Fexp=Fexp
    compound_Fexp(plan)
    #remove_checks(plan)
    branch_selection(plan)
    link(plan)
    tree_Bexp(plan)
    tree_Rexp(plan)
    finish(plan)
    return plan

stateList={}
testState=0 #Using this makes changes that return items to original state to not count as changed. !!!
def pyhop(state,tasks,k=0,kMax=10000,depth=0,verbose=0):
    global stateList
    """
    Try to find a plan that accomplishes tasks in state. 
    If successful, return the plan. Otherwise return False.
    """
    oState=copy.deepcopy(state)
    Plan=PlanNode("Plan", [], -1)
    for t in tasks:
        p=PlanNode(t[0], t[1:],0)
        Plan.children=Plan.children+[p]
        state=seek_plan(state,p,1,tasks,k,kMax,verbose)
        if not state:
            break
    Plan.Fexp=state_Fexp(state)
    if verbose>0: print('** pyhop, verbose={}: **\n   state = {}\n   tasks = {}'.format(verbose, state.__name__, tasks))
    Tree=TreePlan("Finished",[])
    Tree.dBexp=2
    Tree=tree_plan(Plan,Tree)
    Tree.state=oState
    #newTree=TreePlan("Tree",[])
    #newTree.next=Tree
    return Tree

def seek_plan(state,t,depth,goals, k, kMax,verbose=0):
    global stateList
    """
    Workhorse for pyhop. state and tasks are as in pyhop.
    - plan is the current partial plan tree.
    - depth is plan tree depth, used for Informed Expectations
    - verbose is whether to print debugging messages
    """
    if verbose>1: print('depth {} tasks {}'.format(depth,tasks)) 
    if t.action in operators:
        if verbose>2: print('depth {} action {}'.format(depth,task1))
        stringState=string_state(state)
        if stringState in stateList:
            t.find=1
            t.node=stateList[stringState]
            return False
        else:
            stateList[stringState]=t
        #print(t.action,t.cond)
        operator = operators[t.action]
        opreturn = operator(copy.deepcopy(state),*t.cond)#Gets all possible states
        if not opreturn:
            #print_state(state)
            #print(t.action,t.cond)
            pass
        precond=opreturn[1]
        newstates=opreturn[0]
        newstate=newstates[0]#take first state, (Success)
        stringState=string_state(newstate)
        t.changes={}    
        t.states={}
        t.oChanges={}
        if k<kMax:#k fault tolerant. After so many fails, stop branching
            c=0
            for x in range(1,len(newstates)):#branch on failed states
                t.states[x-1]=newstates[x]
                t.changes[x-1]=state_Fexp(newstates[x],state)
                #print(x,t.changes[x-1])
                t.oChanges[x-1]=copy.deepcopy(t.changes[x-1])
                t.branch[x-1]=pyhop(newstates[x],goals,k+1)#need to pass changes?
        if verbose>2:
            print('depth {} new state:'.format(depth))
            print_state(newstate)
        if newstate:
            t.states[-1]=newstate
            t.changes[-1]=state_Fexp(newstate,state)
            #print(t.action,t.cond,t.changes,'\n')
            t.oChanges[-1]=copy.deepcopy(t.changes[-1])
            t.Fexp=state_Fexp(newstate,state)
            t.Bexp=copy.deepcopy(precond)
            t.precond=copy.deepcopy(precond)
        if hasattr(t,"find"):
            return False
        return newstate
    if t.action in methods:
        t.method=1
        if verbose>2: print('depth {} method instance {}'.format(depth,task1))
        relevant = methods[t.action]
        for method in relevant:
            subtasks = method(state,*t.cond)
            # Can't just say "if subtasks:", because that's wrong if subtasks == []
            for s in subtasks:
                p=PlanNode(s[0], s[1:], depth)
                t.children=t.children+[p]
                state=seek_plan(state, p, depth+1, goals, k, kMax, verbose)
                if not state:
                    return False
            if verbose>2:
                print('depth {} new tasks: {}'.format(depth,subtasks))
        return state
    if verbose>2: print('depth {} returns failure'.format(depth))
    return False
    if verbose>2: print('depth {} returns plan {}'.format(depth,plan))
