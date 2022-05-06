import dfr0528 as ups
import datetime
import pathlib
import subprocess
import re
import smbus2
import bme280
import tabulate
import os
# from alert import AlertFactory

DATA_FILE_NAME = 'data.txt'
DATA_FILEPATH = pathlib.Path(__file__).parent.resolve().joinpath(DATA_FILE_NAME)


class Controller:
    def __init__(self):
        self.alerts = list()
        self.bus_addrs = self.init_bus_vars()
        self.check_bus()

        self.bme_sensors = self.init_temp_sensors()
        self.ups = ups.DFR0528()

        self.T1 = None
        self.T2 = None
        self.TAvg = None

        self.H1 = None
        self.H2 = None
        self.HAvg = None

        self.batt_charge = None
        self.batt_capacity = self.ups.total_capacity

    def update_status(self):
        # todo send status email - delete old status email
        return

    def init_temp_sensors(self):
        """ init bme sensors and BME objects -> dict containing BME objects """

        bmes = dict()
        try:
            bmes['bme1'] = self.sample_bme(self.bus_addrs['bme1'])
        except OSError:
            raise SensorError
        try:
            bmes['bme2'] = self.sample_bme(self.bus_addrs['bme2'])
        except OSError:
            raise SensorError

        return bmes

    def sample_bme(self, addr):
        port = 1
        bus = smbus2.SMBus(port)

        calibration_params = bme280.load_calibration_params(bus, addr)

        # the sample method will take a single reading and return a
        # compensated_reading object
        data = bme280.sample(bus, addr, calibration_params)

        return data

    def init_bus_vars(self):
        """ init all bus addresses for expected devices"""

        bus_addrs = dict()

        bus_addrs['bme1'] = 0x76
        bus_addrs['bme2'] = 0x77
        bus_addrs['screen'] = 0x3c
        bus_addrs['ups'] = 0x10

        # self.check_bus()

        return bus_addrs

    def check_bus(self):
        """ check all requested buses are available/connected """

        p = subprocess.Popen(['i2cdetect', '-y', '1'], stdout=subprocess.PIPE,)
        match_rows = list()

        for i in range(0, 9):
            line = str(p.stdout.readline())

            for match in re.finditer("[0-9][0-9]:.*[0-9][0-9, 'a-g']", line):
                # print(match.group())
                split1 = match.group().split()
                match_rows += split1

        # remove unwanted entries from matches
        match_rows = [x for x in match_rows if '-' not in x]
        match_rows = [x for x in match_rows if ':' not in x]

        # compare to bus_addrs
        for key in self.bus_addrs.keys():
            addr = self.bus_addrs[key]
            addr = str(addr)  # only compare last two addr elements as string
            addr = addr[-2:]

            if addr not in match_rows:
                raise OSError
            else:
                print(key + " connected!")

        return

    def update_data_records(self, to_console=False):
        """ store sensing variables and timestamp """
        to_store = self.process_inputs()
        header = ['timestamp', 'temp1', 'temp2', 'avg_temp', 'hum1', 'hum2', 'avg_hum', 'batt_capacity']
        # convert header list to string for txt data
        header_str = ""
        for item in header:
            header_str += item
            header_str += ', '

        # setup comma delimited string
        x = ','.join(map(str, to_store))
        x += '\n'

        # write to txt
        with open(DATA_FILEPATH, 'a') as data_file:
            # write header to file if empty
            if os.stat(DATA_FILEPATH).st_size == 0:
                data_file.write(header_str)
            data_file.write(x)
        data_file.close()

        # debugging
        if to_console:
            print(tabulate.tabulate([to_store], header))

        return

    def update_controller(self):
        """ update state of all peripherals connected to controller """

        for bme in self.bme_sensors.keys():
            # self.temp_sensors[bme].update_sensor()
            self.bme_sensors[bme] = self.sample_bme(self.bus_addrs[bme])

        self.ups.update_capacity()

    def process_inputs(self):
        """ process sensor inputs and ensure all are within limits """

        # desired limits set by user
        temp_max_allowable = 0
        humidity_max_allowable = 20

        timestamp = datetime.datetime.now()

        # data processing
        self.T1 = self.bme_sensors['bme1'].temperature
        self.T2 = self.bme_sensors['bme2'].temperature
        self.TAvg = (self.T1 + self.T2)/2

        self.H1 = self.bme_sensors['bme1'].humidity
        self.H2 = self.bme_sensors['bme2'].humidity
        self.HAvg = (self.H1 + self.H2)/2

        self.batt_charge = self.ups.charged_capacity
        # todo determine capacity and raise batterror when low

        if self.TAvg >= temp_max_allowable:
            raise EnvError
        if self.HAvg >= humidity_max_allowable:
            raise EnvError

        # STORAGE HEADER - timestamp, temp1, temp2, avg_temp, hum1, hum2, avg_hum, batt_capacity
        to_store = [timestamp, self.T1, self.T2, self.TAvg, self.H1, self.H2, self.HAvg, self.batt_charge]

        return to_store


class EnvError(Exception):
    """ issue with one or more env variables """
    pass


class SensorError(Exception):
    """ issue with one or more env variables """
    pass