import smbus2


class DFR0528:
    def __init__(self):
        self.addr = 0x10  # main addr
        self.cellH_addr = 0x03  # cell high check addr
        self.cellL_addr = 0x04  # cell low check addr

        self.charged_capacity = None
        self.total_capacity = 4400
        self.capacity_percent = None

    def update_capacity(self):
        """ update charged and percentage capacity """
        # init and read bus
        bus = smbus2.SMBus(1)
        vcellH = bus.read_byte_data(self.addr, self.cellH_addr)
        vcellL = bus.read_byte_data(self.addr, self.cellL_addr)

        # update props
        self.charged_capacity = (((vcellH & 0x0F) << 8) + vcellL) * 1.25  # total charged capacity [mAh]
        self.capacity_percent = (self.charged_capacity/self.total_capacity)*100  # capacity as percentage
        bus.close()

        return
