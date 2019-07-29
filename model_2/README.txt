This is a simple model of an SMT PCB assembly line.
See documentation/ for the list of components in the assembly line.

REQUIREMENTS:
	Python3
	SimPy (version >3.10)

TO RUN THE SIMULATION IN TERMINAL:
	$ python3 AssemblyLine.py

AUTHOR:
	Neha Karanjkar

ASSUMPTIONS:
	1. All machine delays are specified in seconds 
	and can only be integral multiples of seconds.
	
	2. All power ratings are specified in watts.
	
	3. Successive machines in the assembly line are connected to each other
	via a single unit of buffering. Exactly one machine can 'put' an
	item/job into the buffer and the next machine can 'get' the item from
	the buffer. 

	4. IMPORTANT: to make the execution deterministic, the following
	convention has been adopted: For all machines, the 'get' operation (to
	pick an item from the input buffer) takes place at integer time
	instants only {t=1,2,3,...} whereas the 'put' operation (to place an
	item in the output buffer) takes place at time instants: {0.5, 1.5,
	2.5, 3.5, ...}. Thus the minimum delay that can be modelled for
	transfer of an item between two modules is 1s. 

	These are reasonable assumptions for modelling the SMT PCB assembly
	line. The time granularity of a second is acceptable.

