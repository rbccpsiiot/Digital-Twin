# ScreenPrinter.py
#
#   The ScreenPrinter performs printing, one PCB at a time.
#   Each PCB consumes a certain amount of solder and adhesive
#   and incurs a certain amount of delay.
#   When the solder or adhesive levels falls below a certain threshold, 
#   a human operator is informed and the printing is paused 
#   until a refill is made by the operator.
#   
#   Parameters:
#           solder_capacity  (in grams)
#           solder_initial_amount
#
#           adhesive_capacity
#           adhesive_initial_amount
#
#           printing_delay (in seconds)
#           cleaning_delay (in seconds)
#           num_pcbs_per_cleaning : a cleaning operation is performed after processing every <num_pcbs_per_cleaning> PCBs.
#
#   Author: Neha Karanjkar

import random,simpy,math
from PCB import *
from PCB_types import *
from BaseOperator import BaseOperator

class ScreenPrinter(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        
        # parameters
        self.printing_delay=1
        self.cleaning_delay=1
        self.num_pcbs_per_cleaning=2
        
        # Consumables: 
        # (Solder and adhesive reserves:)
        # default values for initial amount and capacity are 0.
        # these parameters are to be set by the user
        # in the top-level system description
        self.solder_capacity = 0.0
        self.solder_initial_amount = 0.0

        self.adhesive_capacity = 0.0
        self.adhesive_initial_amount =0.0

               
        # states
        self.define_states(states=["idle","waiting_for_refill","printing","cleaning","waiting_to_output"],start_state="idle")
        self.process=env.process(self.behavior())
        
        # this is the operator we interrupt 
        # when the solder/adhesive reserves are low.
        #
        self.refill_operator=None
        
               
        self.solder_reserve = None
        self.adhesive_reserve=None
    
    def set_refill_operator(self,operator):
        self.refill_operator=operator

    
    def behavior(self):

        # checks:
        assert( (type(self.printing_delay)==int) and (self.printing_delay>=1))
        assert( (type(self.cleaning_delay)==int) and (self.cleaning_delay>=1))
        assert( (type(self.num_pcbs_per_cleaning)==int) and (self.num_pcbs_per_cleaning>1))
        assert(self.refill_operator!=None),("please assign a refill operator to "+self.name)
        
        # check if consumable capacity parameters
        # have been set while instantiating this object
        assert(self.solder_capacity>0.0)
        assert(self.adhesive_capacity>0.0)
        
        # create the reserves
        self.solder_reserve = simpy.Container(self.env,init=self.solder_initial_amount, capacity=self.solder_capacity)
        self.adhesive_reserve=simpy.Container(self.env,init=self.adhesive_initial_amount, capacity=self.adhesive_capacity)

        self.change_state("idle")
      
        # wait until the start time 
        yield (self.env.timeout(self.start_time))

        pcb_count_for_cleaning = 0
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
            print("T=",self.env.now+0.0,self.name,"started printing pcb ",pcb)
            
            
            # infer consummable amounts from the PCB's type. 
            # check if required amounts of solder/adhesive are present
            # If not, interrupt a human operator to start the refilling process.
            solder_amt_required = get_PCB_solder_amt(pcb.type_ID)
            adhesive_amt_required = get_PCB_adhesive_amt(pcb.type_ID)
            refill_needed=False
            
            if(self.solder_reserve.level<solder_amt_required):
                print("T=",self.env.now+0.0,self.name,"Solder reserve low!! Needs refilling.")
                refill_needed=True
                self.refill_operator.behavior.interrupt(self.name+":"+"solder_refill")
            
            if(self.adhesive_reserve.level<adhesive_amt_required):
                print("T=",self.env.now+0.0,self.name,"Adhesive reserve low!! Needs refilling.")
                refill_needed=True
                self.refill_operator.behavior.interrupt(self.name+":"+"adhesive_refill")
            
            if(refill_needed):
                self.change_state("waiting_for_refill")
                
            # wait until solder/adhesive have been refilled
            # and consume the required amounts of consummables.
            yield self.solder_reserve.get(solder_amt_required)
            yield self.adhesive_reserve.get(adhesive_amt_required)
            
            if(refill_needed):
                print("T=",self.env.now+0.0,self.name,"refill done.")
                refill_needed = False

            
            # wait for an integer amount of time and start printing
            yield (self.env.timeout(math.ceil(self.env.now)-self.env.now))
            self.change_state("printing")
            yield (self.env.timeout(self.printing_delay-1.0))
            pcb_count_for_cleaning += 1

            # output the PCB if the output buffer is empty,
            # else go into 'waiting_to_output' state.
            while(1):
                if self.outp.can_put():
                    #
                    # can output.
                    # wait until the middle of the time-slot.
                    yield (self.env.timeout(0.5))
                    #
                    # place the pcb at the output
                    yield self.outp.put(pcb)
                    print("T=",self.env.now+0.0,self.name,"placed",pcb,"on",self.outp)
                    yield (self.env.timeout(0.5))
                    #
                    # shall we perform a cleaning operation now?
                    if(pcb_count_for_cleaning >= self.num_pcbs_per_cleaning):
                        self.change_state("cleaning")
                        yield (self.env.timeout(self.cleaning_delay))
                        self.change_state("idle")
                        pcb_count_for_cleaning = 0
                    break
                else:
                    yield (self.env.timeout(1))
                    if(self.current_state != "waiting_to_output"):
                        self.change_state("waiting_to_output")


#Solder refill task:
# to be assigned to a human operator
# executed by the operator
# whenever interrupted by the machine.
def solder_refill_task(machine):
    refill_amount=machine.solder_reserve.capacity-machine.solder_reserve.level
    machine.solder_reserve.put(refill_amount)

def adhesive_refill_task(machine):
    refill_amount=machine.adhesive_reserve.capacity - machine.adhesive_reserve.level
    machine.adhesive_reserve.put(refill_amount)


