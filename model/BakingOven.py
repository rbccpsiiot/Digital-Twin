# BakingOven.py
#
# A baking oven waits until there is a stack
# of PCBs at it's input, then bakes the stack
# for 'delay' time and then places the stack 
# at its output. 
#
# parameters:
#   delay
#   
# Author: Neha Karanjkar
# Date:   10 Nov 2017


import simpy
from BaseOperator import BaseOperator

class BakingOven(BaseOperator):
    
    def __init__(self, env, name, inp, outp):

        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        
        #parameters, and default values
        self.delay=10
        self.start_time=0
        self.on_temp=100
        
        #start behavior
        self.process=env.process(self.behavior())

    def behavior(self):
        
        #wait until start time
        yield self.env.timeout(self.start_time)
        self.change_state("idle")

        while(True):
            
            #wait until there's a stack at the input
            while not self.inp.can_get():
                yield (self.env.timeout(1))

            #start baking
            self.change_state("busy")
            stack = self.inp.get_copy()
            print("T=", self.env.now+0.0, self.name,"picked up stack from",self.inp)

            #delay
            yield (self.env.timeout(self.delay))
            self.change_state("idle")

            #pick it up from the input and place it at the output buffer
            stack = yield self.inp.get()
            yield self.outp.put(stack)

            print("T=", self.env.now+0.0, self.name,"output stack to",self.outp)
    
    # calculate energy consumption for each state that the machine was in.
    def get_energy_consumption(self):

        e = [0.0 for i in range(len(self.states))]
        # idle
        i = self.states.index("idle")
        P = 0 #watt
        T = self.time_spent_in_state[i]
        e[i] = P * T
        # busy
        i = self.states.index("busy")
        P = float(2500.0) #watt
        T = float(self.time_spent_in_state[i])
        temp_factor = min(2, max(1, self.on_temp/100.0))
        e[i] = P * T * temp_factor
        return e

