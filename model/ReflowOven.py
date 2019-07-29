# ReflowOven.py
# 
# The ReflowOven is similar to a conveyor belt.
# The entire length of the belt is divided into a fixed number of stages, 
# with each stage representing the placeholder for a single job.
# After each 'delay' amounts of time, the conveyor belt moves right,
# (akin to a shift-right operation) and a job that was 
# in stage i moves to stage i+1.
# However, unlike a conveyour belt, the ReflowOven's belt
# does not stall. 
#
# Parameters:
#   num_stages: max number of jobs that can be present on the belt at any time
#   delay: after each 'delay' amounts of time, the conveyor belt moves right
# 
#   Author: Neha Karanjkar
#   Date: 27 Oct 2017

import random,simpy
from BaseOperator import BaseOperator



class ReflowOven(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        
        BaseOperator.__init__(self,env,name)

        self.inp=inp
        self.outp=outp

        #default parameter values
        self.num_stages=4
        self.delay=1
        self.start_time=0
        
        #create a list to model stages in the reflow oven
        self.stage=[None for i in range(self.num_stages)]
        
        #states
        self.define_states(["idle","busy"])


        #start behavior
        self.process=env.process(self.behavior())

    
    def behavior(self):
        
        #wait until the start_time
        yield (self.env.timeout(self.start_time))

        self.change_state("busy")
        
        while True:
            
            # if there's a PCB at the input,
            # pick it up and place it in stage[0]
            if(self.inp.can_get()):
                pcb = yield self.inp.get()
                self.stage[0] = pcb
                print("T=",self.env.now+0.0,self.name,"started processing",pcb,"picked up from",self.inp)
            else:
                self.stage[0] = None
               
            #delay
            yield (self.env.timeout(self.delay))
            
            
            # Check that the output
            # conveyor belt is not blocked.
            # This must never happen, as the PCBs already inside
            # the reflowOven will overheat!!!
            while (not self.outp.can_put()):
                print("T=",self.env.now+0.0,self.name,"has its output blocked! WARNING!!")
                yield self.env.timeout(1)


            #shift right
            self.stage = [None] + self.stage[0:-1]

            #output PCB from the last stage onto the output belt
            pcb = self.stage[-1]
            if(pcb !=None):
                yield self.outp.put(pcb)
                self.stage[-1]=None
                print("T=",self.env.now+0.0,self.name,"output",pcb,"to",self.outp)
    
    def get_energy_consumption(self):

        e = [0.0 for i in range(len(self.states))]
        # states(["idle","busy"])
        p = [0.0, 250*1000.0]

        for i in range(len(e)):
            e[i] = p[i]* self.time_spent_in_state[i]
        return e


