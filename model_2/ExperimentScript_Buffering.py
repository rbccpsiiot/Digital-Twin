# Script for running the buffering-related experiment
# Author: Neha Karanjkar

import random
import simpy
import os
import sys 
import datetime

import AssemblyLine as AL


#===============================================
# Simulation parameters:
#===============================================
# The simulation is run until <batch_size> number of PCBs
# have finished processing or max_simulation_time_in_hours is elapsed,
# whichever occurs earlier.
# Note that the batch size should be an integer multiple of stack_size and buffering_size.

AL.batch_size = 1024 #simulation stops after <batch_size> PCBs have been processed.
AL.stack_size = 16 # number of PCBs that can be held at a time in a stack (at the Line Loader's input)

# Max simulation time:
AL.max_simulation_time_in_hours = 500

# Whether an activity log needs to be created..
# Warning: the log file can get very large.
AL.print_activity_log = False

# Buffering-related parameters:
AL.buffering_enabled = True  #whether buffering is enabled
AL.double_buffering_enabled = True #use single buffering or double?
AL.reflow_oven_turn_on_margin_k =0 #turn RFO on after capacity-k items have accumulated
AL.buffering_mode = "FIFO" #can be either "LIFO" or "FIFO"

results=[]
buffer_sizes= [4,8,16,32,64,128,256,512,1024]

results.insert(0,["k","N", "avg_throughput", "avg_cycle_time_hrs", "max_cycle_time_hrs", "avg_energy_per_PCB", "RFO_OFF", "RFO_setup", "RFO_ON_empty", "RFO_ON_occupied"])
for i in buffer_sizes:
    AL.buffer_capacity_per_stage = i
    result = AL.RunSimulation()
    results.append(result)

# write the results into a csv file
import csv

with open("results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(results)
