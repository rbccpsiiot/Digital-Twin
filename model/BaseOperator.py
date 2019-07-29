# BaseOperator.py
#
# Base class for all machines and human operators.
#
# Attributes:
#   name
#   a list of states that this operator can be in, at any time.
#   for example: ["busy", idle"]
#
# Methods:
#   methods to change state, and print the fraction of time
#   spent in each state.
#
# Author: Neha Karanjkar
# Date:   20 Nov 2017


import random
import simpy


class BaseOperator(object):
    
    def __init__(self, env, name):
        self.env=env
        self.name=name
        
        #stats collection:
        self.states = ["idle","busy"]
        self.time_spent_in_state = [0.0 for s in self.states]
        self.current_state = "idle" # current state
        
        # time instant at which the last state change occured.
        self.state_change_timestamp = 0.0 

    #define the set of states for this machine
    def define_states(self,s):
        #stats collection:
        self.states = s
        self.time_spent_in_state = [0.0 for s in self.states]
        self.current_state=s[0]

    # a function to record the time spent 
    # in the current state 
    # since the last timestamp
    def update_time_spent_in_current_state(self):
        i = self.states.index(self.current_state)
        self.time_spent_in_state[i] += self.env.now - self.state_change_timestamp
    
    # change state
    def change_state(self, new_state):
        self.update_time_spent_in_current_state()
        self.current_state = new_state
        self.state_change_timestamp=self.env.now


    # print time spent in each state
    def print_utilization(self):
        
        self.update_time_spent_in_current_state()
        total_time = sum(self.time_spent_in_state)
        assert (total_time>0)
        print(self.name,":", end=' ')
        for i in range(len(self.states)):
            print(self.states[i], "=", end=' ')
            t = self.time_spent_in_state[i]
            t_percent = self.time_spent_in_state[i]/total_time*100.0
            print("{0:.2f}".format(t_percent)+"%", end=' ')
        print("")
    
    # calculate energy consumption for each state that the machine was in.
    #(an implementation should be provided in the derived classes)
    def get_energy_consumption(self):
        e = []
        for i in range(len(self.states)):
            e.append(0.0)
        return e
    
    # print energy consumption
    def print_energy_consumption(self):
        
        e = self.get_energy_consumption()
        total_e = max(sum(e),1.0)
        
        print(self.name,": (", end=' ')
        for i in range(len(self.states)):
            print(self.states[i], "=", end=' ')
            e_percent = e[i]/total_e*100.0
            print("{0:.2f}".format(e_percent)+"%", end=' ')
        print (") Total energy = ","{0:.2f}".format(total_e/1e3)," Kilo Joules.",end=' ')
        print("")
   
