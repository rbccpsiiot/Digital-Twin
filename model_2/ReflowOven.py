# ReflowOven.py
#
# A reflow oven is effectively just a conveyor belt.
# The entire length of the reflow oven is divided into a fixed number of stages, 
# with each stage representing the placeholder for a single PCB/job.
# After each 'delay_per_stage' amounts of time, the conveyor belt moves right,
# (akin to a shift-right operation) and a job that was 
# in stage i moves to stage i+1.
# If the object in the last stage of the conveyor belt is
# not picked up, the belt stalls.
#
# Parameters:
#   num_stages: num of PCBS that can fit on the belt end-to-end. 
#   delay_per_stage: delay for a PCB to move along the belt by a distance equal to the length of the PCB.
#
# States:
#   "off": low power
#   "setup": high power consumed until the required temperature profile is achieved.
#   "temperature_maintain_unoccupied" : reflow oven is on but there are no PCBs on the belt.
#   "temperature_maintain_occupied" : reflow oven is on and there is atleast on PCB on the belt.
#
#
# Modes:
#   The reflow oven supports two operational modes:
#       AUTONOMOUS:
#           In this mode, the reflow oven immediately goes into the "setup" state
#           at the beginning and when the setup is completed, it remains in the "maintain" states.
#       
#       EXTERNAL_CONTROL:
#           In this mode the switching ON and OFF of the relow oven is controlled by an external machine,
#           (the automatic PCB buffering module.) A fixed setup time is incurred each time the machine is turned ON. 
#
#   Author: Neha Karanjkar


import random,simpy
from BaseOperator import BaseOperator
import math

class ReflowOven(BaseOperator):
    
    def __init__(self, env, name, inp, outp):
        BaseOperator.__init__(self,env,name)
        self.inp=inp
        self.outp=outp
        
        # parameters
        self.num_stages=1
        self.delay_per_stage=1
        
        # Operational Modes.
        self.operational_mode="AUTONOMOUS"  #can be set to "EXTERNAL_CONTROL"

        # External control signal that is used
        # only when the operational_mode is EXTERNAL_CONTROL
        self.external_signal = "TURN_ON"  # can be "TURN_OFF".
        
        # states
        self.define_states(states=["off","setup","temperature_maintain_unoccupied","temperature_maintain_occupied"],start_state="off")
        
        # Parameters that determine the setup time
        #(time to raise the temperature of teh oven to a required value.)
        self.temp_max = 200.0 # Temp (degrees Celcius) in maintain state.
        self.temp_room = 30.0 # Temp (degrees Celcius) ambient.
        self.temp_current = 0.0 # variable that strores the current temperature.
        self.timestamp_turn_OFF =0 # time instant at which the oven was last turned OFF.
        self.cooling_rate_constant = 0.5 # constant that determines cooling rate
        self.heating_rate_constant = 170.0 # constant that determines heating rate (degrees celcius per hour)
        self.setup_time=0 #<== value is dynamically computed using the above parameters.

        # create a list to model stages
        self.stages=[]

        # start behavior
        self.process=env.process(self.behavior())
    
   
    def empty(self):
        for i in range(self.num_stages):
            if self.stages[i]!=None:
                return False
        return True
    
    # methods that allow an external machine to 
    # control the turning ON/OFF of the reflow oven.
    def set_external_control(self):
        self.operational_mode="EXTERNAL_CONTROL"

    def turn_ON(self):
        self.external_signal="TURN_ON"
        print("T=",self.env.now+0.0,self.name,"External control registered a TURN ON request")

    def turn_OFF(self):
        self.external_signal="TURN_OFF"
        print("T=",self.env.now+0.0,self.name,"External control registered a TURN OFF request")
        
    def behavior(self):

        # checks:
        assert( (type(self.num_stages)==int) and (self.num_stages>=2))
        assert( (type(self.delay_per_stage)==int) and (self.delay_per_stage>=1))
        
        # create a list to model stages
        self.stages=[None for i in range(self.num_stages)]
       
        # set the initial temperature to room temperature.
        self.temp_current = self.temp_room

        # set the initial state
        if(self.operational_mode=="AUTONOMOUS"):
            self.change_state("setup")
        else:
            self.change_state("off")
        
        while True:
            
            # if the RFO is in setup state, perform the full setup.
            # irrespective of the external control.
            # After finishing the setup, check the external control signal.
            if (self.current_state=="setup"):
                # =====================
                # SETUP
                #
                # compute the setup time which depends on current temperature
                # and the maximum temperature to be attained.
                t_setup = (self.temp_max - self.temp_current)/self.heating_rate_constant*3600
                # round the setup time to an integer.
                self.setup_time = int(round(t_setup))
                assert( (type(self.setup_time)==int) and (self.setup_time>1))
                print("T=",self.env.now+0.0,self.name,"Starting setup. Expected setup time = %0.2f hours"%(self.setup_time/3600.0))
                yield (self.env.timeout(self.setup_time))
                self.temp_current = self.temp_max

                # at the end of setup period, check the external signals:
                if(self.operational_mode=="EXTERNAL_CONTROL" and self.external_signal=="TURN_OFF"): 
                    assert(self.empty())
                    #================
                    # SETUP -> OFF
                    #
                    self.change_state("off")
                    self.timestamp_turn_OFF = self.env.now
                    #================
                
                else:
                    assert(self.empty())
                    #===================
                    # SETUP -> MAINTAIN
                    #
                    self.change_state("temperature_maintain_unoccupied")
                    #===================

            
            # if the RFO is off, do nothing.
            # keep waiting for external control to turn on the oven.
            elif (self.current_state=="off"):
                assert(self.empty())
                if(self.operational_mode=="EXTERNAL_CONTROL" and self.external_signal=="TURN_ON"): 
                    
                    #===================
                    # OFF -> SETUP
                    #
                    # compute the current temperature, which has decayed since the
                    # oven was turned off.
                    time_elapsed_in_hours = (self.env.now- self.timestamp_turn_OFF)/3600.0
                    self.temp_new = self.temp_room + (self.temp_current-self.temp_room)\
                        * math.exp(-1.0* self.cooling_rate_constant *time_elapsed_in_hours)
                    self.temp_current = self.temp_new 
                    print("T=",self.env.now+0.0,self.name,"Turning ON. Time elapsed since last turn_OFF = %0.2f"%time_elapsed_in_hours,"hours. Current_temp = %0.2f"%self.temp_current)
                    self.change_state("setup")
                    #================
                else:
                    yield (self.env.timeout(1))
            
            
            # if the RFO is in the temperature_maintain states:
            else:
                
                # pick up the object from input if there's any. 
                if(self.inp.can_get()):
                    pcb=yield self.inp.get()
                    self.stages[0]=pcb
                else:
                    self.stages[0]=None
                
                # if the reflow oven is empty,
                # we can update the state as suggested
                # by the external control.
                if(self.empty()):
                    if (self.operational_mode=="EXTERNAL_CONTROL" and self.external_signal=="TURN_OFF"):
                        #================
                        # MAINTAIN -> OFF
                        #
                        self.change_state("off")
                        self.timestamp_turn_OFF = self.env.now
                        #================
                    else:
                        self.change_state("temperature_maintain_unoccupied")
                else:
                    self.change_state("temperature_maintain_occupied")
                
                if(self.current_state=="temperature_maintain_occupied" or self.current_state=="temperature_maintain_unoccupied"):
                    #shift right
                    self.stages = [None] + self.stages[0:-1]
                    
                    # delay
                    yield (self.env.timeout(self.delay_per_stage-1))
                    
                    # wait until the middle of the time-slot
                    yield (self.env.timeout(0.5))
                    
                    # put the last object in output_buf
                    pcb=self.stages[-1]
                    if(pcb!=None):
                         
                        # place the pcb at the output
                        yield self.outp.put(pcb)
                        self.stages[-1]=None
                        print("T=",self.env.now+0.0,self.name,"placed",pcb,"on",self.outp)

                    # wait until an integer time instant
                    yield (self.env.timeout(0.5))
                
