# Source.py
#
# A source creates a PCB stack of a given type after a certain delay, 
# and places the stack at its output.
# The source stalls if the output buffer is not empty.
#
# parameters:
#   delay
#   PCB_type
#   PCB_stack_size
#   
# Author: Neha Karanjkar
# Date:   19 Oct 2017


import random
import simpy

from PCB import *
from PCB_types import *


class Source():
    
    def __init__(self, env, name, outp):

        self.env=env
        self.name=name
        self.outp=outp
        
        #parameters, and default values
        self.delay=1
        self.PCB_type=1
        self.PCB_stack_size=1
        self.start_time=0
        
        #start behavior
        self.process=env.process(self.behavior())

    def behavior(self):
        
        #wait until start time
        yield self.env.timeout(self.start_time)

        while(True):
            

            #create a stack of PCBs
            stack = []
            for i in range(self.PCB_stack_size):
                stack.append(PCB(type_ID=self.PCB_type, serial_ID=i, creation_timestamp=self.env.now))

            #place it at the output buffer
            yield self.outp.put(stack)

            print("T=", self.env.now+0.0, self.name,"output PCB stack to",self.outp)

            #delay
            yield (self.env.timeout(self.delay))

