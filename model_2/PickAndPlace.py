# PickAndPlace.py
#
#   The PickAndPlace machine performs component placement for one PCB at a time.
#   The processing for each PCB incurs a certain amount of delay.
#   After a random number of PCBs processed, the machine requires a 
#   reel replacement. A human operator is interrupted to perform the replacement.
#   The number of PCBs after which a reel replacement is required is an
#   integer random variable, and the time required to perform a replacement
#   operation is also an integer random variable.
#   
#   Parameters:
#       processing_delay:   time to perform placement for each PCB, 
#       reel_replacement_interval:  number of PCBs processed after which a replacement is 
#                                    performed. This is an integer random variable.
#       
#   Author: Neha Karanjkar


import random,simpy,math
from PCB import *
from PCB_types import *
from BaseOperator import BaseOperator

class PickAndPlace(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        
        # parameters
        self.processing_delay=1
        self.reel_replacement_interval=2
        
        # state variables
        self.num_pcbs_processed_since_last_reel_replacement=0
        
        # states
        self.define_states(states=["idle","waiting_for_reel_replacement","processing","waiting_to_output"],start_state="idle")
        self.process=env.process(self.behavior())
        
        # this is the operator we interrupt
        # for performing reel replacements
        self.reel_replacement_operator=None
        
        # instantiate a SimPy buffer used as a flag.
        # An occupied buffer indicates that a reel replacement operation
        # has been completed by an external operator.
        self.reel_replacement_done=simpy.Store(env,capacity=1)
 
    def set_reel_replacement_operator(self,operator):
        self.reel_replacement_operator=operator
    
    
    def behavior(self):

        #checks:
        assert( (type(self.processing_delay)==int) and (self.processing_delay>=1))
        assert(type(self.start_time)==int)
        assert(self.reel_replacement_operator!=None),("please assign a reel_replacement_operator to "+self.name)
        
        # wait until the start time 
        yield (self.env.timeout(self.start_time))

        while True:
            self.change_state("idle")

            # wait at integer time instants until 
            # there's a PCB at the input
            pcb = None
            while(not pcb):
                if self.inp.can_get():
                    pcb = yield self.inp.get()
                    break
                else:
                    yield (self.env.timeout(1))
            
            # got a pcb.
            print("T=",self.env.now+0.0,self.name,"started processing pcb ",pcb)
            
            

            # check if a reel replacement is required.
            reel_replacement_required = False
            if(self.num_pcbs_processed_since_last_reel_replacement >= self.reel_replacement_interval):
                print("T=",self.env.now+0.0,self.name,"Reel replacement required! Notifying human operator.")
                self.reel_replacement_operator.behavior.interrupt(self.name+":"+"reel_replacement")
                self.change_state("waiting_for_reel_replacement")
                
                # wait until reel replacement is performed
                yield self.reel_replacement_done.get()
                print("T=",self.env.now+0.0,self.name,"reel replacement done.")
                self.num_pcbs_processed_since_last_reel_replacement = 0
                # wait until an integer time instant
                yield (self.env.timeout(math.ceil(self.env.now)-self.env.now))
            
            # start processing the PCB
            self.change_state("processing")
            yield (self.env.timeout(self.processing_delay-1.0))

            # output the PCB if the output buffer is empty,
            # else go into 'waiting_to_output' state.
            while(1):
                if self.outp.can_put():
                    # can output.
                    # wait until the middle of the time-slot.
                    yield (self.env.timeout(0.5))
                    # place the pcb at the output
                    yield self.outp.put(pcb)
                    print("T=",self.env.now+0.0,self.name,"placed",pcb,"on",self.outp)
                    self.num_pcbs_processed_since_last_reel_replacement += 1
                    yield (self.env.timeout(0.5))
                    break
                else:
                    yield (self.env.timeout(1))
                    if(self.current_state != "waiting_to_output"):
                        self.change_state("waiting_to_output")


# Reel replacement task
# to be assigned to a human operator.
# This function is executed by the operator
# whenever interrupted by the machine.
# A flag "reel_replacement_done" is set to 1
# to indicate that the machine can resume its operation.
def reel_replacement_task(machine):
    machine.reel_replacement_done.put(1)


