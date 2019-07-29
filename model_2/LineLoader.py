# LineLoader.py
#
# Waits until there is a stack of PCB's at its input
# then picks up one PCB at a time from the stack 
# and places it on the conveyor belt.
#
#   parameters: 
#       delay: time (in seconds) required to push a single PCB from the stack onto the conveyor belt
#       
# Author: Neha Karanjkar

import random,simpy,math
from BaseOperator import BaseOperator

class LineLoader(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        self.delay=1
        
        #states
        self.define_states(states=["idle","loading"],start_state="idle")
        self.process=env.process(self.behavior())

    
    def behavior(self):
        assert( isinstance(self.delay,int))
        assert( isinstance(self.start_time,int))
        assert(self.delay>=1)
        
        #wait until the start time 
        yield (self.env.timeout(self.start_time))

        while True:
            #wait until there's a stack of PCBs at the input
            pcb_stack=None
            while(not pcb_stack):
                if self.inp.can_get():
                    pcb_stack = self.inp.get_copy()
                    break
                else:
                    yield (self.env.timeout(1))
            
            #got a stack.
            print("T=",self.env.now+0.0,self.name,"started unloading stack")

            while (len(pcb_stack)!=0):
                
                #pick up a PCB from the stack in First-In-First-Out order:
                pcb = pcb_stack.pop(0)

                # wait until there's place at the output
                while not self.outp.can_put():
                    yield (self.env.timeout(1))
                
                #change state
                self.change_state("loading")

                # wait for an integer amount of delay
                yield (self.env.timeout(self.delay-1.0))
                yield (self.env.timeout(0.5))

                #place the PCB at the output
                yield self.outp.put(pcb)
                print("T=",self.env.now+0.0,self.name,"placed",pcb,"on",self.outp)
                yield (self.env.timeout(0.5))
                
                #change state
                self.change_state("idle")
            
            # Now remove the empty tray from the inp
            # so that the next job can arrive.
            s = yield self.inp.get()

