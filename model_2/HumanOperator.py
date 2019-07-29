# HumanOperator.py
#
# A human operator can be assigned several tasks.
# The operator maintains a list of the tasks assigned,
# the machine on which it is to be performed. 
#
# The operator performs the appropriate task
# whenever interrupted.
#
# Author: Neha Karanjkar
# Date:   20 Nov 2017


import random,math
import simpy

from BaseOperator import BaseOperator

# Information about an assigned task
# is stored as a tuple:
from collections import namedtuple
Task  = namedtuple('Task', 'task_name machine_name task_ptr machine_ptr delay')


class HumanOperator(BaseOperator):
    
    def __init__(self, env, name):
        BaseOperator.__init__(self,env,name)
        
        # list of tasks assigned 
        # to this operator
        self.assigned_tasks_list=[]
        
        # start behavior
        self.behavior=env.process(self.behavior())
        self.define_states(states=["idle","busy"], start_state="idle")
        
        #queued-up tasks to be performed.
        self.pending_tasks_queue = []

    # function to assign a new task
    # to this operator
    def assign_task(self, task_name, machine_name, task_ptr, machine_ptr, delay):
        
        self.assigned_tasks_list.append(Task(task_name, machine_name, task_ptr, machine_ptr, delay))
        #checks:
        assert(isinstance(delay, int))
  

    def behavior(self):
        
        self.task_is_ongoing = False
        self.current_task=None
        self.current_task_delay = 0
        self.current_task_start_time = 0

        
        while True:

            try:
                
                # if a task was ongoing before we were interrupted,
                # resume and finish the task.
                if(self.task_is_ongoing):
                    print("T=",self.env.now+0.0,self.name,"resuming task",self.current_task.task_name)
                    self.current_task_start_time = self.env.now
                    yield self.env.timeout(self.current_task_delay)
                    # execute the functionality corresponding to this task
                    self.current_task.task_ptr(machine=self.current_task.machine_ptr)
                    self.task_is_ongoing = False
                    print("T=",self.env.now+0.0,self.name,"finished task",self.current_task.task_name)
                    self.change_state("idle")
                
                # if there are any pending tasks, 
                # perform the first task in the list.
                if(len(self.pending_tasks_queue)>=1):
                    self.current_task = self.pending_tasks_queue.pop(0)
                    
                    # start the task
                    self.current_task_delay = self.current_task.delay
                    self.current_task_start_time = self.env.now
                    self.task_is_ongoing = True
                    self.change_state("busy")
                    print("T=",self.env.now+0.0,self.name,"starting task",self.current_task.task_name)
                    yield self.env.timeout(self.current_task_delay)
                    
                    # finished the task without any interruption
                    # execute the functionality corresponding to this task
                    self.current_task.task_ptr(machine=self.current_task.machine_ptr)
                    self.task_is_ongoing = False
                    print("T=",self.env.now+0.0,self.name,"finished task",self.current_task.task_name)
                    self.change_state("idle")
                
                # else, there are no ongoing or pending tasks.
                # do some low priority idle work until interrupted.
                else:
                    self.change_state("idle")
                    yield self.env.timeout(100)
                
            
            except simpy.Interrupt as i:
                
                # the human operator was interrupted by a machine.
                # check the cause and the source of the interruption
                machine_name, cause = i.cause.split(":")
                print("T=", self.env.now+0.0, self.name, "was interrupted by",machine_name,"for",cause)
                
                # check if this task was indeed assigned to me.
                task = [t for t in self.assigned_tasks_list if ( t.task_name==cause and t.machine_name==machine_name )]
                if len(task)==0:
                    print("ERROR!! no such task assigned to operator",self.name)
                assert(len(task)==1)
                task=task[0]

                # add the requested task to the pending_tasks_queue
                # to be performed later.
                self.pending_tasks_queue.append(task)

                # if there was a task ongoing when this interrupt happened,
                # note down the remaining time for this task.
                if(self.task_is_ongoing):
                    self.current_task_delay = self.current_task_delay - (self.env.now - self.current_task_start_time) 
                

