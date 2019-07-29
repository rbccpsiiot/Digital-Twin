# PCB.py
#
#
# Author: Neha Karanjkar 
# Date: 18 Oct 2017


class PCB:
    creation_timestamp=0.0
    
    def __init__(self, type_ID, serial_ID, creation_timestamp=0.0):

        #A PCB has the following attributes:
        self.type_ID=type_ID        # type (used to infer dimensions, num of components etc)
        self.serial_ID=serial_ID    # a unique identifier for each PCB instance
        self.creation_timestamp=creation_timestamp

    def __str__(self):
        return"PCB <type_ID="+str(self.type_ID)+", serial_ID="+str(self.serial_ID)+">"


