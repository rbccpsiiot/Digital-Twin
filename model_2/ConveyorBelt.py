# ConveyorBelt.py
# 
# This conveyor belt is modeled like a shift-register.
# The entire length of the belt is divided into a fixed number of stages, 
# with each stage representing the placeholder for a single job.
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
#   Author: Neha Karanjkar

import random,simpy
from BaseOperator import BaseOperator


class ConveyorBelt(BaseOperator):
    
     
    def __init__(self, env, name, num_stages,delay_per_stage):
        BaseOperator.__init__(self,env,name)
        
        self.num_stages=num_stages
        self.delay_per_stage=delay_per_stage
        
        #default parameter values
        self.start_time=0
        
        #A conveyor belt has at-least two stages
        assert(isinstance(self.num_stages,int) and (num_stages>=2))
        assert(isinstance(self.delay_per_stage,int))
        assert(isinstance(self.start_time, int))

        # create input and output buffers
        # corresponding to the first and last stages
        self.input_buf=simpy.Store(env,capacity=1)
        self.output_buf=simpy.Store(env,capacity=1)

        # a list to model stages
        self.stages=[None for i in range(num_stages)]
        
        #states
        self.define_states(["empty", "moving", "stalled"],start_state="empty")

        # start behavior
        self.process=env.process(self.behavior())


    def __str__(self):
        return self.name
    
    #A blocking methods to get/put jobs.
    #to be called with "yield"
    def get(self):
        return self.output_buf.get()
    
    def put(self,job):
        return self.input_buf.put(job)
    
    #Non-blocking methods to get state of the belt
    def can_put(self):
        if(len(self.input_buf.items)==0):
            return True
        else:
            return False
    
    def can_get(self):
        if(len(self.output_buf.items)!=0):
            return True
        else:
            return False
    
    # A non-blocking methods that 
    # returns a reference to the job
    # that would have been returned by get()
    def get_copy(self):
        assert(self.can_get())
        x = self.output_buf.items[0]
        return x


    # a method that returns a string 
    # with a pictorial representation 
    # of the occupancy of the conveyor belt.
    def show_occupancy(self):
        s = "|"
        s+=  "*|" if(len(self.input_buf.items)!=0 and self.input_buf.items[0]!=None) else " |"
        s+= "".join(["*|" if(self.stages[i]!=None) else " |" for i in range(1,self.num_stages-1)])
        s+= "*|" if(len(self.output_buf.items)!=0 and self.output_buf.items[0]!=None) else " |"
        return s
      
    def empty(self):
        if (len(self.input_buf.items)!=0):
            return False
        if (len(self.output_buf.items)!=0):
            return False
        for i in range(self.num_stages):
            if self.stages[i]!=None:
                return False
        return True

            
    def behavior(self):
        
        self.change_state("empty")

        #wait until the start_time
        yield (self.env.timeout(self.start_time))
        
        while True:
            
            # if the conveyor belt is empty, do nothing.
            if (self.empty()):
                self.change_state("empty")
                yield (self.env.timeout(self.delay_per_stage))

            # else, check if the conveyor belt is stalled
            elif (len(self.output_buf.items)!=0):
                self.change_state("stalled")
                print("T=",self.env.now+0.0, self.name, "Stalled", self.show_occupancy())
                yield (self.env.timeout(self.delay_per_stage))
            
            # else check if the conveyor belt can be moved.
            else:
                self.change_state("moving")
                
                #pick up the object from input_buf if present
                if(len(self.input_buf.items)==0):
                    obj=None
                else:
                    obj=yield self.input_buf.get()
                self.stages[0]=obj
            
                #shift right
                self.stages = [None] + self.stages[0:-1]

                # delay
                yield (self.env.timeout(self.delay_per_stage-1))
                # wait until the middle of the time-slot
                yield (self.env.timeout(0.5))

                #put the last object in output_buf
                obj=self.stages[-1]
                if(obj!=None):
                    yield self.output_buf.put(self.stages[-1])
                print("T=",self.env.now+0.0, self.name, "Shift-right", self.show_occupancy())
                # wait until an integer time instant
                yield (self.env.timeout(0.5))

#testbench function for the ConveyorBelt:
def test_ConveyorBelt():
    class Sender():
        def __init__(self,env,delay_per_stage,output,start_time):
            self.env=env
            self.delay_per_stage=delay_per_stage
            self.start_time=start_time
            
            #pointer to output (conveyor belt)
            self.output=output

            #start behavior
            self.process=env.process(self.behavior())

        def behavior(self):
            
            #offset
            yield (self.env.timeout(self.start_time))
            count=0
            while True:
                
                #delay
                yield (self.env.timeout(self.delay_per_stage))

                #try to place an object in the output  if its empty
                if (self.output.can_put()):
                    obj = "job_"+str(count)
                    yield self.output.put(obj)
                    count+=1
                    print("T=",self.env.now, "Sender placed", obj,"on conveyor belt", self.output.show_occupancy())


    class Receiver():
        def __init__(self,env,inp,start_time):
            self.env=env
            
            #pointer to input (conveyor belt)
            self.inp = inp
            self.start_time=start_time

            #start behavior
            self.process=env.process(self.behavior())

        def behavior(self):
            
            #offset
            yield (self.env.timeout(self.start_time))
            while True:
                #random delay
                yield (env.timeout(1+random.randint(1,13)))
                
                #try to input an object from the conveyor belt
                if (self.inp.can_get()):
                    obj = yield self.inp.get()
                    print("T=",self.env.now,"Receiver picked up", obj,"from conveyor belt",self.inp.show_occupancy())


    env=simpy.Environment()
    conveyor_belt=ConveyorBelt(env, name="ConveyorBelt", num_stages=3, delay_per_stage=1)
    conveyor_belt.start_time=0.5

    sender = Sender(env, delay_per_stage=1, output=conveyor_belt,start_time=0)
    receiver = Receiver(env, inp = conveyor_belt,start_time=0)
    env.run(until=60)

#Uncomment the following to run test:
#test_ConveyorBelt()
