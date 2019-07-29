# ScreenPrinter.py
#
#   The ScreenPrinter performs printing, one PCB at a time.
#   Each PCB consumes a certain amount of solder and adhesive
#   and incurs a certain amount of delay depending on the PCB's type_ID.
#   When the solder or adhesive levels falls below a certain threshold, 
#   a human operator is informed and the printing is paused 
#   until a refill is made by the operator.
#   
#   Parameters:
#       Consummables capacity and initial amounts:
#
#           solder_reserve.capacity
#           solder_reserve.init (initial amount present)
#           adhesive_reserve.capacity
#           adhesive_reserve.init
#
#       delay  (time to print a single PCB)
#
#
#   Author: Neha Karanjkar
#   Date: 19 Oct 2017

import random,simpy,math
from PCB import *
from PCB_types import *
from BaseOperator import BaseOperator


class ScreenPrinter(BaseOperator):
    def __init__(self,env,name,inp,outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp

        self.start_time=0

        #states
        self.define_states(["idle","printing","waiting_for_refill"])

        # this is the operator we interrupt 
        # when the solder/adhesive reserves are low.
        #
        self.refill_operator=None
        
        # Consumables: 
        # (Solder and adhesive reserves:)
        # default values for initial amount and capacity are 0.
        # these parameters are to be set by the user
        # in the top-level system description
        self.solder_capacity = 0
        self.solder_initial_amount = 0

        self.adhesive_capacity = 0
        self.adhesive_initial_amount =0
        
        self.solder_reserve = None
        self.adhesive_reserve=None


        # start behavior
        self.process=env.process(self.behavior())


    def set_refill_operator(self,operator):
        self.refill_operator=operator
        

    def behavior(self):

        # check if the refill operator has been assigned
        assert(self.refill_operator!=None),("please assign a refill operator to "+self.name)
       
        # check if consumable capacity parameters
        # have been set while instantiating this object
        assert(self.solder_capacity>0)
        assert(self.adhesive_capacity>0)
        
        #create the reserves
        self.solder_reserve = simpy.Container(self.env,init=self.solder_initial_amount, capacity=self.solder_capacity)
        self.adhesive_reserve=simpy.Container(self.env,init=self.adhesive_initial_amount, capacity=self.adhesive_capacity)

        
        self.change_state("idle")
        
        # wait until start time
        yield (self.env.timeout(self.start_time))
    
        while True:
            
            # keep checking at integer time instants
            # until a PCB arrives at the input
            while (not self.inp.can_get()):
                yield (self.env.timeout(1))

            # get the PCB
            pcb = self.inp.get_copy()
            print("T=",self.env.now+0.0,self.name,"started printing",pcb)
            

            # infer printing parameters from the PCB's type. 
            solder_amt_required = get_PCB_solder_amt(pcb.type_ID)
            adhesive_amt_required = get_PCB_adhesive_amt(pcb.type_ID)
            
            

            # check if required amounts of solder/adhesive are present
            # If not, interrupt a human operator to start the refilling process.
            refill_needed=False
            
            if(self.solder_reserve.level<solder_amt_required):
                print("T=",self.env.now+0.0,self.name,"WARNING: Solder reserve low!! Needs refilling.")
                refill_needed=True
                self.refill_operator.behavior.interrupt(self.name+":"+"solder_refill")
            
            if(self.adhesive_reserve.level<adhesive_amt_required):
                print("T=",self.env.now+0.0,self.name,"WARNING: Adhesive reserve low!! Needs refilling.")
                refill_needed=True
                self.refill_operator.behavior.interrupt(self.name+":"+"adhesive_refill")
            
            self.change_state("waiting_for_refill")
            
            # wait until solder/adhesive have been refilled
            yield self.solder_reserve.get(solder_amt_required)
            yield self.adhesive_reserve.get(adhesive_amt_required)
            
            if refill_needed:
                print("T=",self.env.now+0.0,self.name,"refill done.")
                refill_needed = False


            #wait until an integer time instant
            yield (self.env.timeout(math.ceil(self.env.now)-self.env.now))
            
            #print
            self.change_state("printing")
            yield (self.env.timeout(self.delay))
            print("T=",self.env.now+0.0,self.name,"finished printing",pcb)
            
            #Wait until there's place at the output,
            self.change_state("idle")

            while (not self.outp.can_put()):
                yield (self.env.timeout(1))

            #remove the PCB from this stage and send it to the output
            yield self.inp.get()
            yield self.outp.put(pcb)
            print("T=",self.env.now+0.0,self.name,"output",pcb,"on",self.outp)
    
    def get_energy_consumption(self):

        e = [0.0 for i in range(len(self.states))]
        # states(["idle","printing","waiting_for_refill"])
        p = [100, 500, 100]

        for i in range(len(e)):
            e[i] = p[i]* self.time_spent_in_state[i]
        return e

        


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

