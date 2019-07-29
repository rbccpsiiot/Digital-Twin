# Buffer.py
# 
# A wrapper around SimPy's store resource class.
# Models a finite capacity FIFO buffer.
#
# Parameters:
#   capacity: max number of jobs that can be present in the buffer at any time
# 
#   Author: Neha Karanjkar
#   Date: 27 Oct 2017

import random,simpy



class Buffer():
    
    
    def __init__(self, env, name, capacity):
      
        self.env=env
        self.name=name
        self.capacity=capacity
        
        assert(isinstance(capacity,int) and (capacity>=1))
        
        #instantiate a SimPy buffer
        self.buf=simpy.Store(env,capacity=capacity)

    def __str__(self):
        return self.name

    #A blocking methods to get/put jobs.
    #to be called with "yield"
    def get(self):
        return self.buf.get()
    
    def put(self,job):
        return self.buf.put(job)
    

    #Non-blocking methods to get state of the buffer
    def can_put(self):
        if(len(self.buf.items) < self.capacity):
            return True
        else:
            return False
    
    def can_get(self):
        if(len(self.buf.items)!=0):
            return True
        else:
            return False
    
    # A non-blocking methods that 
    # returns a reference to the job
    # that would have been returned by get()
    def get_copy(self):
        assert(self.can_get())
        x = self.buf.items[-1]
        return x


