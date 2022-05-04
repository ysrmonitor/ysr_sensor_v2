import smbus

# for testing only
import random


class DFR0528:
    def __init__(self):
        self.addr = '0x10'  # main addr
        self.cellH_addr = '0x03'  # cell high check addr
        self.cellL_addr = '0x04'  # cell low check addr

        # bus registers
        self.r_cellH = smbus.bus.read_byte(self.addr, self.cellH_addr)
        self.r_cellL = smbus.bus.read_byte(self.addr, self.cellL_addr)

        self.capacity = None

    def update_capacity(self):
        vcellH = self.r_cellH
        vcellL = self.r_cellL

        self.capacity = (((vcellH&0x0F) << 8)+vcellL)*1.25  # capacity

        # see below for testing
        # self.capacity = random.randint(0, 100)
        return