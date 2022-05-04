import smbus

# for testing only
import random

bus = smbus.SMBus(1)


class DFR0528:
    def __init__(self):
        self.addr = 0x10  # main addr
        self.cellH_addr = 0x03  # cell high check addr
        self.cellL_addr = 0x04  # cell low check addr

        # bus registers
        self.r_cellH = bus.read_byte_data(self.addr, self.cellH_addr)
        self.r_cellL = bus.read_byte_data(self.addr, self.cellL_addr)

        self.charged_capacity = None
        self.total_capacity = 4400
        self.capacity_percent = None

    def update_capacity(self):
        vcellH = self.r_cellH
        vcellL = self.r_cellL

        self.charged_capacity = (((vcellH & 0x0F) << 8) + vcellL) * 1.25  # capacity
        self.capacity_percent = (self.charged_capacity/self.total_capacity)*100

        # see below for testing
        # self.capacity = random.randint(0, 100)
        return