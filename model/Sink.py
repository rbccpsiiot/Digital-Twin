# Sink.py
#
# Consumes finished PCB stacks as they arrive.
# 
# Author: Neha Karanjkar
# Date: 30 Oct 2017

import random
import simpy


class Sink():
    def __init__(self, env, name, inp):
        self.env=env
        self.name=name
        self.inp=inp

        #default parameter values

        self.delay=0
        self.start_time=0.0
        
        #start behavior
        self.process=env.process(self.behavior())

        #count of the number of stacks completed and avg
        #time that each stack spent in the system
        self.num_stacks_completed=0.0
        self.average_cycle_time=0.0


    def behavior(self):
        
        yield self.env.timeout(self.start_time)
        
        while(True):
            
            #wait until there's a stack at the input buffer

            pcb_stack=yield self.inp.get()
            pcb = pcb_stack[0]
            print("T=", self.env.now+0.0, self.name, "consumed PCB stack from",self.inp)

            stack_cycle_time = self.env.now - pcb.creation_timestamp
            self.average_cycle_time = self.average_cycle_time * self.num_stacks_completed + stack_cycle_time
            self.num_stacks_completed+=1
            self.average_cycle_time = self.average_cycle_time/self.num_stacks_completed

            
            #produce a delay
            yield self.env.timeout(self.delay)


