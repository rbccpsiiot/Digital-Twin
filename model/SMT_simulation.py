# SMT_simulation.py
#
# Routine to execute the SimPy model
# of the SMT assembly line for a specified time.
#
# Author: Neha Karanjkar
# Last Updated: 20 March 2018

import random
import simpy
import sys 
import datetime
from io import StringIO
import copy
from collections import OrderedDict

# Model components:
from PCB import *
from ConveyorBelt import *
from Buffer import *
from Source import *
from BakingOven import *
from HumanLoader import *
from LineLoader import *
from ScreenPrinter import *
from PickAndPlace import *
from ReflowOven import *
from LineDownloader import *
from Sink import *
from HumanOperator import *


import os
import sys


class SMT_simulation():
    
    # init function 
    def __init__(self):
        #
        #initialize the model parameters
        #to their default values.
        self.model_parameters = self.get_default_model_parameters()


    # Function to run the simulation for
    # a specified amount of time.
    # The values of the model parameters are passed
    # as a dictionary.
    def run_simulation(self,simulation_time, generate_activity_log):
        
        #check arguments:
        assert(simulation_time >= 1)
        assert(isinstance(self.model_parameters,dict))

        # Create a SimPy Environment:
        env=simpy.Environment()

        # We use the following timing convention:
        #   All machines operate at integer time-instants n = 0, 1, 2, 3,...
        #   All conveyor belts move in the middle of the integer instants t = 0.5, 1.5, 2.5, ...


        # Instantiate conveyor belts
        # (a conveyor belt carries individual PCBs)
        belt_1 = ConveyorBelt(env=env, name="belt_1", capacity=3)
        belt_2 = ConveyorBelt(env=env, name="belt_2", capacity=3)
        belt_3 = ConveyorBelt(env=env, name="belt_3", capacity=3)
        belt_4 = ConveyorBelt(env=env, name="belt_4", capacity=3)
        belt_5 = ConveyorBelt(env=env, name="belt_5", capacity=3)

        belts = [belt_1, belt_2, belt_3, belt_4, belt_5]

        # Instantiate buffers
        # (a buffer holds a stack of PCBs)
        buff_11=Buffer(env, name="buff_11", capacity=1)
        buff_12=Buffer(env, name="buff_12", capacity=1)
        buff_21=Buffer(env, name="buff_21", capacity=1)
        buff_22=Buffer(env, name="buff_22", capacity=1)
        buff_3=Buffer(env, name="buff_3", capacity=1)
        buff_4=Buffer(env, name="buff_4", capacity=1)
        buff_5=Buffer(env, name="buff_5", capacity=1)
        buff_6=Buffer(env, name="buff_6", capacity=1)


        # Instantiate machines and connect them using conveyor belts/buffers
        source_1         = Source (env=env, name="source_1", outp=buff_11)
        source_2         = Source (env=env, name="source_2", outp=buff_12)

        baking_oven_1    = BakingOven (env=env, name="baking_oven_1", inp=buff_11, outp=buff_21)
        baking_oven_2    = BakingOven (env=env, name="baking_oven_2", inp=buff_12, outp=buff_22)

        human_loader     = HumanLoader (env=env, name="human_loader", inp_list=[buff_21,buff_22], outp=buff_3 )
        line_loader      = LineLoader (env=env, name="line_loader", inp=buff_3, outp=belt_1 )
        screen_printer   = ScreenPrinter (env=env, name="screen_printer", inp=belt_1, outp=belt_2 )
        pick_and_place_1 = PickAndPlace (env=env, name="pick_and_place_1", inp=belt_2, outp=belt_3 )
        pick_and_place_2 = PickAndPlace (env=env, name="pick_and_place_2", inp=belt_3, outp=belt_4 )
        reflow_oven      = ReflowOven (env=env, name="reflow_oven", inp=belt_4, outp=belt_5 )
        line_downloader  = LineDownloader (env=env, name="line_downloader", inp=belt_5, outp=buff_6 )
        sink_1             = Sink (env=env, name="sink_1", inp=buff_6)
        sink_1.delay=0

        machines= [line_loader, screen_printer, pick_and_place_1, pick_and_place_2, reflow_oven, line_downloader]

        # human operators
        human_operator_1 = HumanOperator (env=env, name="human_operator_1")
        human_operator_2 = HumanOperator (env=env, name="human_operator_2")

        
        
        # Set machine parameters
        #
        # Source:
        # A source creates a PCB stack of a given type 
        # periodically after a certain delay, 
        # and places the stack at its output.
        # The source stalls if there's no place at the output.
        source_1.delay = 100
        source_1.PCB_type = 1
        source_1.PCB_stack_size=10

        source_2.delay = 10
        source_2.PCB_type = 2
        source_2.PCB_stack_size=10

        # BakingOven:
        #
        # A baking oven waits until there is a stack
        # of PCBs at it's input, then bakes the stack
        # for 'delay' time and then places the stack 
        # at its output. 
        baking_oven_1.delay = self.model_parameters["baking_oven_1"]["parameters"]["delay"]["value"]
        baking_oven_1.on_temp = self.model_parameters["baking_oven_1"]["parameters"]["on_temperature"]["value"]
        baking_oven_2.delay = self.model_parameters["baking_oven_2"]["parameters"]["delay"]["value"]
        baking_oven_2.on_temp = self.model_parameters["baking_oven_2"]["parameters"]["on_temperature"]["value"]

        #
        # HumanLoader:
        #
        # The human loader keeps checking
        # if jobs are available in a given list
        # of input buffers, and places them
        # as they arrive at the input of the line loader.
        # delay: time between picking up a job and 
        #placing it near the line loader.
        human_loader.delay = 1 

        # LineLoader:
        # 
        # A line loader waits until there is a stack of PCBs
        # at its input. Then, it picks up PCBs from the stack
        # one at a time and places them on the conveyor belt.
        # parameters: 
        #   delay (between picking up and placing each pcb)
        line_loader.delay= self.model_parameters["line_loader"]["parameters"]["delay"]["value"]

        # ScreenPrinter:
        #
        #   The ScreenPrinter performs printing, one PCB at a time.
        #   Each PCB consumes a certain amount of solder and adhesive
        #   and incurs a certain amount of delay depending on the PCB's type_ID.
        #   When the solder or adhesive levels falls below a certain threshold, 
        #   a human operator is informed and the printing is paused 
        #   until a refill is made by the operator.
        #   Parameters:
        screen_printer.solder_capacity=200
        screen_printer.solder_initial_amount=2

        screen_printer.adhesive_capacity=200
        screen_printer.adhesive_initial_amount=200

        screen_printer.delay= self.model_parameters["screen_printer"]["parameters"]["delay"]["value"]


        # Assign some human operators to 
        # handle refilling tasks in the screen printer.
        # A human operator remains idle until interrupted
        # by a machine and then performs the assigned task.
        screen_printer.set_refill_operator(human_operator_1)

        human_operator_1.assign_task(task_name="solder_refill",machine_name="screen_printer", task_ptr=solder_refill_task, machine_ptr=screen_printer, delay=3)
        human_operator_1.assign_task(task_name="adhesive_refill",machine_name="screen_printer", task_ptr=adhesive_refill_task, machine_ptr=screen_printer, delay=3)



        ## PickAndPlace:
        ##
        ##  The PickAndPlace machine performs component placement one PCB at a time.
        ##  Each PCB consumes a certain number of components from the reels.
        ##  The time required to process a PCB is proportional
        ##  to the number of components in it
        ##   Parameters:
        pick_and_place_1.delay=self.model_parameters["pick_and_place_1"]["parameters"]["delay"]["value"]
        pick_and_place_2.delay=self.model_parameters["pick_and_place_2"]["parameters"]["delay"]["value"]

        # ReflowOven:
        # 
        # The ReflowOven is similar to a conveyor belt.
        # The entire length of the belt is divided into a fixed number of stages, 
        # with each stage representing the placeholder for a single job.
        # After each 'delay' amounts of time, the conveyor belt moves right,
        # (akin to a shift-right operation) and a job that was 
        # in stage i moves to stage i+1.
        # However, unlike a conveyour belt, the ReflowOven's belt
        # does not stall. 
        # Parameters:
        reflow_oven.num_stages= self.model_parameters["reflow_oven"]["parameters"]["num_stages"]["value"]
        reflow_oven.delay=self.model_parameters["reflow_oven"]["parameters"]["delay"]["value"]

        # LineDownloader.py
        #
        # Collects PCBS one by one from the conveyor belt
        # and loads them into a stack
        # Parameters:
        line_downloader.PCB_stack_size=source_1.PCB_stack_size 


        
        # Run simulation, 
        T = int(simulation_time)
        assert(T>1)
        print("Running simulation for", T," seconds")

        #Generate the activity log into a file
        if(generate_activity_log==True):
            activity_log_file = open("activity_log.txt","w")
            sys.stdout = activity_log_file
            current_time = datetime.datetime.now()
            current_time_str = current_time.strftime("%Y-%m-%d %H:%M")
            print("==============================================")
            print("Activity Log generated on ",current_time_str)
            print("Simulation time = ",T)
            print("==============================================")
        else:
            nothing = open(os.devnull, 'w')
            sys.stdout = nothing

        # run the simulation
        env.run(until=T)
        sys.stdout = sys.__stdout__

        if(generate_activity_log==True):
            print("Activity log generated in file: activity_log.txt")
        
        # Generate results into a string object
        results_string = StringIO()
        sys.stdout = results_string

        print("\n================================")
        print("Stats:")
        print("================================")
        print ("Total time elapsed = ",env.now," seconds")
        print ("Total number of stacks processed =",sink_1.num_stacks_completed)
        print ("Average cycle-time per stack = ",sink_1.average_cycle_time, "seconds")
        print ("Average throughput = ",sink_1.num_stacks_completed/float(env.now)*60," stacks per minute")

        machines = [baking_oven_1, baking_oven_2, line_loader, screen_printer, pick_and_place_1, pick_and_place_2,reflow_oven,line_downloader]
        humans = [human_loader, human_operator_1, human_operator_2]

        print("\n================================")
        print("Utilization Report (operators): ")
        print("================================")
        for i in machines:
            i.print_utilization()
        for i in humans:
            i.print_utilization()

        print("\n================================")
        print("Utilization Report (conveyor belts): ")
        print("================================")
        for i in belts:
            i.print_utilization()

        print("\n================================")
        print("Energy Consumption: ")
        print("================================")
        for i in machines:
            i.print_energy_consumption()
        for i in belts:
            i.print_energy_consumption()
        print("================================")
        sys.stdout = sys.__stdout__
        return results_string



    def get_default_model_parameters(self):
        
        # Create a dictionary contaning information about 
        # the model parameters.
        #
        # The format of the dictionary is:
        #
        #   {machine_1_id:{"label":"machine1", "parameters":{machine_1_parameters}},
        #        machine_2_id:{"label":"machine2", "parameters":{machine_2_parameters}}, ...}
        #
        # where {machine_n_parameters} is itself a dictionary of the form:
        #   {"parameter1":{"label":"some name", "default_value":10, "value":20},
        #     "parameter2":{"label":"some name2", "default_value":120, "value":20},
        #      "parameter3":{"label":"some name3", "default_value":123, "value":24}}
        #
        
        
        model_parameters = OrderedDict()
        # Baking Oven 1:
        model_parameters["baking_oven_1"]= {"label":"Baking oven 1", "parameters":{\
                                            "delay":{"label":"Baking time (seconds)", "default_value":360, "value":360, "format":"int"},
                                            "on_temperature":{"label":"ON temperature (degree Celsius)", "default_value":105, "value":105, "format":"int"}
                                            }}
                                            
        model_parameters["baking_oven_2"]= {"label":"Baking oven 2", "parameters":{\
                                            "delay":{"label":"Baking time (seconds)", "default_value":120, "value":120, "format":"int"},
                                            "on_temperature":{"label":"ON temperature (degree Celsius)", "default_value":65, "value":65, "format":"int"}
                                            }}
        # Line Loader:
        model_parameters["line_loader"]=  {"label":"Line Loader", "parameters":{\
                                            "delay":{"label":"Delay per PCB (seconds)", "default_value":1, "value":1, "format":"int"}
                                            }}
        # Screen Printer:
        model_parameters["screen_printer"]= {"label":"Screen Printer", "parameters":{\
                                            "delay":{"label":"Printing time per PCB (seconds)", "default_value":10, "value":10, "format":"int"}
                                            }}
        # Pick and place 1:
        model_parameters["pick_and_place_1"]={"label":"Pick and Place 1", "parameters":{\
                                            "delay":{"label":"Avg delay per component (seconds)", "default_value":0.1, "value":0.1, "format":"float"}
                                            }}
        # Pick and place 2:
        model_parameters["pick_and_place_2"]={"label":"Pick and Place 2", "parameters":{\
                                            "delay":{"label":"Avg delay per component (seconds)", "default_value":0.1, "value":0.1, "format":"float"}
                                            }}
        # Reflow oven:
        model_parameters["reflow_oven"]= {"label":"Reflow Oven", "parameters":{\
                                            "delay":{"label":"Avg delay per stage (seconds)", "default_value":2, "value":2,"format":"int"},
                                            "num_stages":{"label":"Number of stages", "default_value":4, "value":4,"format":"int"}
                                            }}
 
        return model_parameters
    

if __name__ == '__main__':
    S = SMT_simulation()
    simulation_time = 100
    results = S.run_simulation(simulation_time)
    print(results.getvalue())
