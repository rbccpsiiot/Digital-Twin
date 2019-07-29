# AssemblyLine.py
#
# SimPy model of the SMT PCB manufacturing line
# The system consists of a set of machines
# connected over conveyor belts in a sequence.
#
# We use the following timing convention:
#   All machines operate at integer time-instants n = 0, 1, 2, 3,...
#   All conveyor belts move in the middle of the integer instants t = 0.5, 1.5, 2.5, ...


# Author: Neha Karanjkar
# Last Updated: 10 Nov 2017

import random
import simpy

# Model components:
from PCB import *           


# Create an Environment:
env=simpy.Environment()

# Instantiate conveyor belts
# (a conveyor belt carries individual PCBs)
from ConveyorBelt import *
belt_1 = ConveyorBelt(env=env, name="belt_1", capacity=3)
belt_2 = ConveyorBelt(env=env, name="belt_2", capacity=3)
belt_3 = ConveyorBelt(env=env, name="belt_3", capacity=3)
belt_4 = ConveyorBelt(env=env, name="belt_4", capacity=3)
belt_5 = ConveyorBelt(env=env, name="belt_5", capacity=3)

belts = [belt_1, belt_2, belt_3, belt_4, belt_5]


# Instantiate buffers
# (a buffer holds a stack of PCBs)
from Buffer import *
buff_11=Buffer(env, name="buff_11", capacity=1)
buff_12=Buffer(env, name="buff_12", capacity=1)

buff_21=Buffer(env, name="buff_21", capacity=1)
buff_22=Buffer(env, name="buff_22", capacity=1)

buff_3=Buffer(env, name="buff_3", capacity=1)
buff_4=Buffer(env, name="buff_4", capacity=1)
buff_5=Buffer(env, name="buff_5", capacity=1)
buff_6=Buffer(env, name="buff_6", capacity=1)


# Instantiate machines and connect them using conveyor belts/buffers

from Source import *
source_1         = Source (env=env, name="source_1", outp=buff_11)
source_2         = Source (env=env, name="source_2", outp=buff_12)

from BakingOven import *
baking_oven_1    = BakingOven (env=env, name="baking_oven_1", inp=buff_11, outp=buff_21)
baking_oven_2    = BakingOven (env=env, name="baking_oven_2", inp=buff_12, outp=buff_22)

from HumanLoader import *
human_loader     = HumanLoader (env=env, name="human_loader", inp_list=[buff_21,buff_22], outp=buff_3 )

from LineLoader import *
line_loader      = LineLoader (env=env, name="line_loader", inp=buff_3, outp=belt_1 )

from ScreenPrinter import *
screen_printer   = ScreenPrinter (env=env, name="screen_printer", inp=belt_1, outp=belt_2 )


from PickAndPlace import *
pick_and_place_1 = PickAndPlace (env=env, name="pick_and_place_1", inp=belt_2, outp=belt_3 )
pick_and_place_2 = PickAndPlace (env=env, name="pick_and_place_2", inp=belt_3, outp=belt_4 )

from ReflowOven import *
reflow_oven      = ReflowOven (env=env, name="reflow_oven", inp=belt_4, outp=belt_5 )

from LineDownloader import *
line_downloader  = LineDownloader (env=env, name="line_downloader", inp=belt_5, outp=buff_6 )

from Sink import *
sink_1             = Sink (env=env, name="sink_1", inp=buff_6)
sink_1.delay=0

machines= [line_loader, screen_printer, pick_and_place_1, pick_and_place_2, reflow_oven, line_downloader]


# human operators
from HumanOperator import *
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
baking_oven_1.delay = 10
baking_oven_2.delay = 20

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
line_loader.delay=1

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

screen_printer.delay=10


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
pick_and_place_1.delay=0.1
pick_and_place_2.delay=0.1

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
reflow_oven.num_stages=4
reflow_oven.delay=1

# LineDownloader.py
#
# Collects PCBS one by one from the conveyor belt
# and loads them into a stack
# Parameters:
line_downloader.PCB_stack_size=source_1.PCB_stack_size 


# Run simulation, 
T =1000
print("Running simulation for", T," seconds")


#print the activity log to a file.
import sys 
import datetime

original_stdout = sys.stdout
activity_log_file = open("activity_log.txt","w")
sys.stdout = activity_log_file

current_time = datetime.datetime.now()
current_time_str = current_time.strftime("%Y-%m-%d %H:%M")
print("Activity Log generated on ",current_time_str)
env.run(until=1000)
sys.stdout = original_stdout

print("Activity log generated in file: activity_log.txt")

# Print usage statistics:
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


