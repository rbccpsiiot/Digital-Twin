# PCB_types.py
# 
# Routines to obtain info such as dimensions, 
# number of components, amount of solder required etc.
# from the type_ID of a PCB.
#
#
# Author: Neha Karanjkar 
# Date: 30 Oct 2017


from collections import namedtuple
PCB_info = namedtuple('PCB_info', 'width height num_components solder_amt adhesive_amt')

PCB_types={\
#------------------------------------------------------------------------------------------------
#type_ID:(    width(cm), height(cm), num_components, solder_amount(gm), adhesive_amount(gm) )
 1       :   PCB_info( 5,          5,             28,               5.0,                5.0  ),\
 2       :   PCB_info( 6,          5,             28,               5.0,                5.0  ),\
 3       :   PCB_info( 7,          5,             23,               5.0,                5.0  ),\
 4       :   PCB_info( 5,         10,             48,               5.0,                5.0  ),\
 5       :   PCB_info( 5,         15,             70,               5.0,                5.0  )\
#------------------------------------------------------------------------------------------------
}



#routines:
def get_PCB_width(type_ID):
    return PCB_types[type_ID].width

def get_PCB_height(type_ID):
    return PCB_types[type_ID].height

def get_PCB_num_components(type_ID):
    return PCB_types[type_ID].num_components

def get_PCB_solder_amt(type_ID):
    return PCB_types[type_ID].solder_amt

def get_PCB_adhesive_amt(type_ID):
    return PCB_types[type_ID].adhesive_amt
