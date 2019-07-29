# Sink.py
#
# Consumes finished items as they arrive at its input buffer.
# 
# Author: Neha Karanjkar
# Date: 30 Oct 2017

import random
import simpy
from PCB import PCB

class Sink():
    def __init__(self, env, name, inp):
        self.env=env
        self.name=name
        self.inp=inp

        #default parameter values

        self.delay=0
        self.batch_size = 1000 # stop simulation after these many PCBs have been processed.
        self.start_time=0.0
        
        #start behavior
        self.process=env.process(self.behavior())
        self.stop_condition = simpy.events.Event(env) # create an event for the stop condition.
        # simulation is stopped whan this even is triggered.


        #count of the number of stacks completed and avg
        #time that each stack spent in the system
        self.num_items_finished=0.0
        self.average_cycle_time=0.0
        self.max_cycle_time=0.0


    def behavior(self):
        
        yield self.env.timeout(self.start_time)
        
        while(True):
            
            #wait until there's a PCB at the input.
            pcb =yield self.inp.get()
            assert(isinstance(pcb,PCB))
            PCB_cycle_time = self.env.now - pcb.creation_timestamp
            self.max_cycle_time = max(self.max_cycle_time, PCB_cycle_time) 
            self.average_cycle_time = self.average_cycle_time * self.num_items_finished + PCB_cycle_time
            self.num_items_finished+=1
            self.average_cycle_time = self.average_cycle_time/self.num_items_finished
            print("T=", self.env.now+0.0, self.name, "consumed a single PCB ",pcb,"from ",self.inp," which incurred a cycle time of %0.2f"%(PCB_cycle_time/3600.0),"hours. The Max cycle-time so far is %0.2f"%(self.max_cycle_time/3600.0),"hours.")

            
            #produce a delay
            yield self.env.timeout(self.delay)

            # stop simulation if <batch_size> number of PCBs have been processed.
            if (self.num_items_finished >= self.batch_size):
                print("T=", self.env.now+0.0, self.name, "finished processing",self.num_items_finished,"PCBs. Stopping simulation.")
                self.stop_condition.succeed()
                
                


