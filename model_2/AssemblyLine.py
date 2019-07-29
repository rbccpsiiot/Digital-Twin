# AssemblyLine.py
#
# SimPy model of an SMT PCB assembly line.
# See ./documentation for an illustration of the line. 
# The system consists of a set of machines
# connected over conveyor belts in a sequence.
#
#
# Author: Neha Karanjkar

import random
import simpy
import os
import sys 
import datetime

# Import definitions of machines and other classes
# specific to this assembly line.
from PCB import *           
from Buffer import *
from ConveyorBelt import *
from HumanOperator import *
from Source import *
from LineLoader import *
from ScreenPrinter import *
from PickAndPlace import *
from PCBBufferingModule import *
from PCBDoubleBufferingModule import *
from ReflowOven import *
from Sink import *



#===============================================
# Simulation parameters:
#===============================================
# The simulation is run until <batch_size> number of PCBs
# have finished processing or max_simulation_time_in_hours is elapsed,
# whichever occurs earlier.
# Note that the batch size should be an integer multiple of stack_size and buffering_size.

batch_size = 1024 #simulation stops after <batch_size> PCBs have been processed.
stack_size = 16 # number of PCBs that can be held at a time in a stack (at the Line Loader's input)

# Max simulation time:
max_simulation_time_in_hours = 100

# Whether an activity log needs to be created..
# Warning: the log file can get very large.
print_activity_log = False

# Buffering-related parameters
buffering_enabled = True  #w hether buffering is enabled
double_buffering_enabled = False # use single buffering or double?
buffer_capacity_per_stage = 32 # max number of items that can be buffered per stage.
reflow_oven_turn_on_margin_k = 0 # turn on the reflow oven as soon as (capacity - k) items have accumulated
buffering_mode = "LIFO"  # Can be either "LIFO" or "FIFO"



# Function to run simulation:
def RunSimulation():

    # Create an Environment:
    env=simpy.Environment()

    # Checks on simulation parameters:
    assert(batch_size % stack_size ==0)
    assert(batch_size % (buffer_capacity_per_stage) == 0)


    # Instantiate machines, set their parameters
    #and connect them using conveyor belts/buffers

    # PCB definitions:


    # Succesive machines in the assembly line are connected
    # using buffers(slots). One machine can "put" and the next machine 
    # can "get"  a PCB from the buffer.
    #NOTE: these buffers are just placeholders for a single PCB.
    # These are different from a PCB buffering "module". 
    buff = []
    NUM_BUFFERS = 6
    for i in range (NUM_BUFFERS):
        buff.append(Buffer(env, name="buff_"+str(i), capacity=1))


    # Instantiate conveyor belts
    # the first conveyor belt is between the screen printer to the Pick and place1.
    # the second belt is between the buffering module and the Reflow Oven.
    belt_SP_to_PP1 = ConveyorBelt(env=env, name="belt_SP_to_PP1", num_stages=3, delay_per_stage=1)
    belt_buffering_module_to_RFO = ConveyorBelt(env=env, name="belt_buffering_module_to_RFO", num_stages=3, delay_per_stage=1)


    # Instantiate Human Operators.
    # Human operators can be interrupted by machine
    # for performing tasks such as refilling machine consummables.
    human_operator_1 = HumanOperator (env=env, name="human_operator_1")

    #======================================
    # Machines in the assembly Line:
    #======================================
    #
    #======================================
    # Source:
    #======================================
    # A source creates a PCB stack of a given type 
    # periodically after a certain delay, 
    # and places the stack at its output.
    # The source stalls if there's no place at the output.
    source_1  = Source (env=env, name="source_1", outp=buff[0])
    source_1.delay = 0
    source_1.PCB_type = 1
    source_1.PCB_stack_size=stack_size
    source_1.PCB_batch_size=batch_size #total PCBs to be produced.


    #======================================
    # LineLoader:
    #======================================
    # A line loader waits until there is a stack of PCBs
    # at its input. Then, it picks up PCBs from the stack
    # one at a time and places them on the conveyor belt.
    # parameters: 
    #   delay (for pushing a single PCB into the empty output buffer)
    line_loader      = LineLoader (env=env, name="line_loader", inp=buff[0], outp=buff[1])
    line_loader.delay= 2

    #======================================
    # ScreenPrinter:
    #======================================
    #   The ScreenPrinter performs printing, one PCB at a time.
    #   Each PCB consumes a certain amount of solder and adhesive
    #   and incurs a certain amount of delay.
    #   When the solder or adhesive levels falls below a certain threshold, 
    #   a human operator is informed and the printing is paused 
    #   until a refill is made by the operator.
    #   After every 'n' printing operations, a 'cleaning' operation
    #   is automatically performed. The value of n is the parameter 'num_pcbs_per_cleaning'
    #   Each cleaning takes up a certain time specified as 'cleaning_delay'.
    screen_printer   = ScreenPrinter (env=env, name="screen_printer", inp=buff[1], outp=belt_SP_to_PP1)

    screen_printer.solder_capacity=500 # units: gram
    screen_printer.solder_initial_amount=500

    screen_printer.adhesive_capacity=500
    screen_printer.adhesive_initial_amount=500

    screen_printer.printing_delay=18
    screen_printer.cleaning_delay=28
    screen_printer.num_pcbs_per_cleaning=2

    #  power ratings (in watts) for each state
    # states: ["idle","waiting_for_refill","printing","cleaning","waiting_to_output"]
    screen_printer.set_power_ratings([100.0, 100.0, 500.0, 1000.0, 100.0])


    #======================================
    # PickAndPlace:
    #======================================
    #  The PickAndPlace machine performs component placement one PCB at a time.
    #  The processing for each PCB incurs a certain delay.
    #  After a randomly distributed interval, a reel replacement operation is necessary
    #  and a human operator is interrupted to perform the replacement.
    pick_and_place_1 = PickAndPlace (env=env, name="pick_and_place_1", inp=belt_SP_to_PP1, outp=buff[2] )
    pick_and_place_2 = PickAndPlace (env=env, name="pick_and_place_2", inp=buff[2], outp=buff[3])
    pick_and_place_1.processing_delay=85
    pick_and_place_2.processing_delay=50
    # num of PCBs processed after which reel replacement is required
    pick_and_place_1.reel_replacement_interval = 50
    pick_and_place_2.reel_replacement_interval = 50
    #  power ratings (in watts) for each state
    # states: ["idle","waiting_for_reel_replacement","processing","waiting_to_output"]
    pick_and_place_1.set_power_ratings([100.0, 100.0, 500.0, 100.0])
    pick_and_place_2.set_power_ratings([100.0, 100.0, 500.0, 100.0])


    #======================================
    # PCB Buffering module:
    #======================================

    if(double_buffering_enabled):
        # Double buffering
        buffering_module = PCBDoubleBufferingModule (env=env, name="buffering_module", inp=buff[3], outp=belt_buffering_module_to_RFO )
        buffering_module.capacity_per_stage=buffer_capacity_per_stage
        buffering_module.k = reflow_oven_turn_on_margin_k
        buffering_module.buffering_mode = buffering_mode
        #  set power ratings (in watts) for each state
        #  states: ["bypass","buffering_enabled"]
        buffering_module.set_power_ratings([250,250])
    else:
        # Single buffering
        buffering_module = PCBBufferingModule (env=env, name="buffering_module", inp=buff[3], outp=belt_buffering_module_to_RFO )
        buffering_module.capacity=buffer_capacity_per_stage
        buffering_module.k = reflow_oven_turn_on_margin_k 
        buffering_module.buffering_mode = buffering_mode
        #  set power ratings (in watts) for each state
        #  states: ["bypass","filling", "emptying"]
        buffering_module.set_power_ratings([250,250, 250])

    if (buffering_enabled):
        buffering_module.enable_buffering()
    #=========================================




    #======================================
    # Reflow Oven:
    #======================================
    #  The Reflow Oven is similar to a conveyor belt.
    reflow_oven = ReflowOven (env=env, name="reflow_oven", inp=belt_buffering_module_to_RFO, outp=buff[4] )
    reflow_oven.num_stages = 10
    reflow_oven.delay_per_stage=5
    #reflow_oven.setup_time=900 # setup time is 15 minutes=900 seconds.

    #  power ratings (in watts) for each state
    # states: ["off", "setup", "temperature_maintain_unoccupied", "temperature_maintain_occupied"]
    reflow_oven.set_power_ratings([320.0, 33000.0, 25800.0, 25800.0])

    if (buffering_enabled):
        # Let the buffering module control the turning ON and OFF
        # of the reflow oven:
        buffering_module.set_reflow_oven_control(reflow_oven)
    #=========================================


    #======================================
    # Sink:
    #======================================
    # A sink consumes PCBs or PCB stacks from its input buffer
    # and maintains a count of total PCBs consumed and the average
    # cycle time for each PCB

    sink_1             = Sink (env=env, name="sink_1", inp=buff[4])
    sink_1.delay = 0
    sink_1.batch_size = batch_size # stop simulation after these many PCBs have been processed.

    #======================================
    # Assignment of Tasks to Human Operators:
    #======================================
    # Assign some human operators to 
    # handle refilling tasks in the screen printer and pick and place machines.
    # A human operator remains idle until interrupted
    # by a machine and then performs the assigned task.

    # operator 1: 
    screen_printer.set_refill_operator(human_operator_1)
    human_operator_1.assign_task(task_name="solder_refill",machine_name="screen_printer", task_ptr=solder_refill_task, machine_ptr=screen_printer, delay=60)
    human_operator_1.assign_task(task_name="adhesive_refill",machine_name="screen_printer", task_ptr=adhesive_refill_task, machine_ptr=screen_printer, delay=60)

    pick_and_place_1.set_reel_replacement_operator(human_operator_1)
    pick_and_place_2.set_reel_replacement_operator(human_operator_1)
    human_operator_1.assign_task(task_name="reel_replacement",machine_name="pick_and_place_1", task_ptr=reel_replacement_task, machine_ptr=pick_and_place_1, delay=60)
    human_operator_1.assign_task(task_name="reel_replacement",machine_name="pick_and_place_2", task_ptr=reel_replacement_task, machine_ptr=pick_and_place_2, delay=60)



    # Run simulation, 
    T =3600*max_simulation_time_in_hours
    print("Running simulation for a maximum of ", max_simulation_time_in_hours," hours,")
    print("or until",batch_size,"PCBs have been processed, whichever is earlier.")





    # Creation of an activity log
    original_stdout = sys.stdout
    if(print_activity_log):
        activity_log_file = open("activity_log.txt","w")
        sys.stdout = activity_log_file
    else:
        nowhere = open(os.devnull, 'w')
        sys.stdout = nowhere

    # Run simulation
    current_time = datetime.datetime.now()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M")
    print("Activity Log generated on ",current_time_str)

    env.run(until=simpy.events.AnyOf(env,[sink_1.stop_condition, env.timeout(T)]))


    # Print simulation results:
    sys.stdout = original_stdout

    if(print_activity_log): print("Activity log generated in file: activity_log.txt")
    # Compute stats:
    machines = [line_loader, screen_printer, belt_SP_to_PP1, pick_and_place_1, pick_and_place_2, buffering_module, belt_buffering_module_to_RFO, reflow_oven]
    machines_e = [screen_printer, pick_and_place_1, pick_and_place_2, buffering_module, reflow_oven]
    humans = [human_operator_1]
    total_energy=0.0
    for i in machines_e:
        total_energy+=sum(i.get_energy_consumption())

    
    # Some important stats:
    avg_throughput = sink_1.num_items_finished/float(env.now)*3600  #PCBs per hour
    avg_cycle_time_hrs = sink_1.average_cycle_time/3600.0 #hours
    max_cycle_time_hrs = sink_1.max_cycle_time/3600.0 #hours
    avg_energy_per_PCB = total_energy/(float(sink_1.num_items_finished)*1e3) # kilo Joules per PCB
    RFO_utilization = reflow_oven.get_utilization()

    # Print usage statistics:
    # 
    print("\n================================")
    print("Stats:")
    print("================================")
    print ("Total time elapsed = ",env.now," seconds ( %0.2f hours)"% (env.now/3600.0))
    print ("Total number of PCBs created =",source_1.num_items_created)
    print ("Total number of PCBs finished =",sink_1.num_items_finished)
    print ("Average cycle-time per PCB = %0.2f seconds"%(avg_cycle_time_hrs*3600), "( %0.2f hours)"%(avg_cycle_time_hrs))
    print ("Max cycle-time per PCB = %0.2f"%(max_cycle_time_hrs*3600), "seconds ( %0.2f hours)"%(max_cycle_time_hrs))
    print ("Average throughput = %0.2f"%(avg_throughput)," PCBs per hour.")
    
    print("\n================================")
    print("Utilization Report: ")
    print("================================")
    for i in machines:
        i.print_utilization()
    for i in humans:
        i.print_utilization()
    
    print("\n================================")
    print("Energy Consumption: ")
    print("================================")
    for i in machines_e:
        i.print_energy_consumption()
    print("Total energy consumed = ",total_energy/1e3, "Kilo Joules")
    if(sink_1.num_items_finished==0): sink_1.num_items_finished =1
    print ("Average energy consumed per-PCB = %0.2f" %(avg_energy_per_PCB)," Kilo Joules per PCB.")

    result = [reflow_oven_turn_on_margin_k, buffer_capacity_per_stage, avg_throughput, avg_cycle_time_hrs, max_cycle_time_hrs, avg_energy_per_PCB]
    result.extend(RFO_utilization)

    return result

