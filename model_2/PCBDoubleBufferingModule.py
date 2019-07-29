# PCBDoubleBufferingModule.py
#
#   A double-buffer for buffering the partially processed PCBs
#   between the pick and place and the reflow operations.
#
#
#   The machine has two modes: "bypass" and "buffering_enabled"
#   By default, the machine is in bypass mode. Buffering can be enabled
#   by calling the enable_buffering() function.
#
#   "BYPASS" mode:----------------------
#       In this mode, no buffering takes place. Items input
#       by the module are immediately sent to the output.
#       
#   "BUFFERING_ENABLED" mode:-------------------
#       Applicable only after enable_buffering() is called.
#       There are two identical LIFO buffers inside this module.
#       When one is filling up, the other can be emptying simultaneously.
#
#   Parameters:
#       capacity_per_stage (number of PCBs that can be held in each stage of the module.)
#       Total buffering = 2 * capacity_per_stage
#       
#   Author: Neha Karanjkar


import random,simpy,math
from PCB import *
from BaseOperator import BaseOperator
from ReflowOven import *

class PCBDoubleBufferingModule(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        
        # parameters
        self.capacity_per_stage=1
        self.k = 0 # turn on the RFO as soon as capacity-k items have accumulated in the buffer.
        self.buffering_mode = "LIFO" # can be "LIFO" or "FIFO"
        self.in_buffer = None
        self.out_buffer = None
        
        # states
        self.define_states(states=["bypass","buffering_enabled"], start_state="bypass")
        self.process=env.process(self.behavior())

        # pointer to Reflow Oven for controlling it
        self.reflow_pointer = None

        # operational mode can be "BYPASS" or "BUFFERING_ENABLED"
        self.operational_mode = "BYPASS"
    
    def enable_buffering(self):
        self.operational_mode="BUFFERING_ENABLED"
        self.start_state="buffering_enabled"

    def set_reflow_oven_control(self, RFO):
        self.reflow_pointer = RFO
        assert(isinstance(RFO, ReflowOven))
        self.reflow_pointer.set_external_control()
        

    def behavior(self):

        #checks:
        assert(isinstance(self.capacity_per_stage,int) and self.capacity_per_stage>1)
        assert(isinstance(self.k,int       ) and self.k>=0 and self.k<=(self.capacity_per_stage-1))
       
        #==============================
        #Behaviour in the BYPASS mode:
        #==============================
        if(self.operational_mode == "BYPASS"):
            self.change_state("bypass")
            while True:

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
                    print("T=",self.env.now+0.0,self.name,"input a PCB",pcb)
                    
                    # perform output at the middle of a time-slot
                    yield (self.env.timeout(0.5))
                    
                    # wait until there's place at the output 
                    while(True):
                        if self.outp.can_put():
                            yield self.outp.put(pcb)
                            break
                        else:
                            yield (self.env.timeout(1))

                    # output a single PCB.
                    print("T=",self.env.now+0.0,self.name,"output ",pcb,"to",self.outp)

                    # wait till an integer time instant
                    yield (self.env.timeout(0.5))

        #========================================
        #Behaviour in the BUFFERING_ENABLED mode:
        #=========================================
        else:
            self.change_state("buffering_enabled")

            #Initially, the reflow oven is turned off.
            if(self.reflow_pointer!=None): self.reflow_pointer.turn_OFF()
            self.in_buffer=[]
            self.out_buffer=[]
            
            
            while True:
                    #================================================
                    # Input 
                    #================================================
                    # Input can happen only at integer time-instants.(1,2,3...)
                    
                    # check if there's a PCB at the input, and place
                    # in the input buffer.
                    pcb = None
                    if (self.inp.can_get() and len(self.in_buffer)<self.capacity_per_stage):
                        pcb = yield self.inp.get()
                        self.in_buffer.append(pcb)
                        print("T=",self.env.now+0.0,self.name,"input a PCB",pcb)
                        if (len(self.in_buffer)==self.capacity_per_stage):
                            print("T=",self.env.now+0.0,self.name,"input buffer is full.")
                        
                        # Check if the reflow oven should be turned on now
                        if((len(self.in_buffer)==(self.capacity_per_stage-self.k)) and self.reflow_pointer!=None):
                            self.reflow_pointer.turn_ON()

                    
                    #================================================
                    # wait until the middle of the slot.
                    #================================================
                    yield (self.env.timeout(0.5))
                    
                    # If in_buffer is full and out_buffer is empty,
                    # send contents of in_buffer to out_buffer
                    if( (len(self.in_buffer) >= self.capacity_per_stage) and len(self.out_buffer)==0):
                        self.out_buffer.extend(self.in_buffer)
                        self.in_buffer=[]
                        print("T=",self.env.now+0.0,self.name,"transferring contents of in_buffer to out_buffer.")
                        
                    #================================================
                    # Output 
                    #================================================
                    # Output can happen only at the middle of time-slots. (0.5, 1.5, 2.5...)
                    # check if there's a PCB in the out_buffer and place at the output:
                    if(len(self.out_buffer)>0 and self.outp.can_put()):
                        if(self.buffering_mode=="LIFO"):
                            out_pcb = self.out_buffer.pop()
                        else:
                            out_pcb = self.out_buffer.pop(0)
                        yield self.outp.put(out_pcb)
                        
                        print("T=",self.env.now+0.0,self.name,"output a PCB",out_pcb,"to",self.outp)
                        if (len(self.out_buffer)==0):
                            print("T=",self.env.now+0.0,self.name,"output buffer is empty.")
                            # Now turn the reflow oven OFF
                            self.reflow_pointer.turn_OFF()
                
                    #================================================
                    # wait until the start of the next slot.
                    #================================================
                    yield (self.env.timeout(0.5))
                
