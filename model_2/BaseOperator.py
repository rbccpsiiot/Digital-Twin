# BaseOperator.py
#
# Base class for all machines and human operators.
#
# Attributes:
#   name
#   states: a list of states that this operator can be in, at any time. For example: ["busy", idle"]
#   start_time: the time at which the behavior starts.
#
# Member functions:
#   methods to change state, and print the fraction of time spent in each state.
#
# Author: Neha Karanjkar
# Date:   20 Nov 2017


import random
import simpy

class BaseOperator(object):
    
    def __init__(self, env, name):
        self.env=env
        self.name=name

        #start_time
        self.start_time=0
        
        #default states:
        self.states = ["none"]

        #power rating of the machine/operator for each state
        self.power_ratings  = [0.0]
        self.time_spent_in_state = [0.0 for s in self.states]
        
        # current state
        self.current_state = "none" 
        
        # variable to remember the time instant 
        # at which the last state change occured.
        self.state_change_timestamp = 0.0 

    

    # function (to be called inside the constructor of all derived classes) 
    # to define the set of states for a particular type of machine.
    # Optionally the power (in watts) for each state can also be specified.
    def define_states(self,states, start_state):
        
        self.states = states
        self.time_spent_in_state = [0.0 for s in states]
        assert(start_state in states)
        self.current_state=start_state
        self.power_ratings = [0.0 for s in states]
    
    def set_power_ratings(self, power_ratings):
        assert (len(power_ratings)==len(self.states))
        for p in power_ratings:
            assert(p>0)
        self.power_ratings = power_ratings

    # function to record the time spent in the current state 
    # since the last timestamp
    def update_time_spent_in_current_state(self):
        i = self.states.index(self.current_state)
        self.time_spent_in_state[i] += self.env.now - self.state_change_timestamp
    
    # change state
    def change_state(self, new_state):
        prev_state = self.current_state 
        self.update_time_spent_in_current_state()
        self.current_state = new_state
        self.state_change_timestamp=self.env.now
        if(new_state!=prev_state):
            print("T=", self.env.now+0.0, self.name, "changed state to ",new_state)
    
    
    def get_utilization(self):
        utilization = []
        self.update_time_spent_in_current_state()
        total_time = sum(self.time_spent_in_state)
        assert (total_time>0)
        for i in range(len(self.states)):
            t = self.time_spent_in_state[i]
            t_percent = self.time_spent_in_state[i]/total_time*100.0
            utilization.append(t_percent)
        return utilization


    # print time spent in each state
    def print_utilization(self):
        
        u = self.get_utilization()
        print(self.name,":",end=' ')
        for i in range(len(self.states)):
            print(self.states[i], "=",end=' ')
            print("{0:.2f}".format(u[i])+"%",end=' ')
        print("")
    
        
    # calculate energy consumption (in joules) 
    # for each state that the machine was in.
    def get_energy_consumption(self):
        e = []
        for i in range(len(self.states)):
            e.append(self.power_ratings[i]*self.time_spent_in_state[i])
        return e
    
    # print energy consumption
    def print_energy_consumption(self):
        e = self.get_energy_consumption()
        total_e = sum(e)
        denominator = max(sum(e),1.0)
        
        print(self.name,": (",end=' ')
        for i in range(len(self.states)):
            print(self.states[i], "=",end=' ')
            e_percent = e[i]/denominator*100.0
            print("{0:.2f}".format(e_percent)+"%",end=' ')
        print (") Total energy = ","{0:.2f}".format(total_e/1e3)," Kilo Joules.",end=' ')
        print("")
   
