# TODO get data
# TODO check data
# TODO store data comma delim
# TODO email infrastruct
# TODO boot
# TODO other peripherals

# short term todo
# todo implement screen stuff

# for testing
# from tests import BME280
import dfr0528 as ups

from bme280 import BME280
import datetime
import time
import pathlib
import subprocess
import re

DATA_FILE_NAME = 'data.txt'
DATA_FILEPATH = pathlib.Path(__file__).parent.resolve().joinpath(DATA_FILE_NAME)


class Controller:
    def __init__(self):
        self.bus_addrs = self.init_bus_vars()
        self.temp_sensors = self.init_temp_sensors()
        self.ups = ups.DFR0528()

    def init_temp_sensors(self):
        """ init bme sensors and BME objects -> dict containing BME objects """

        bmes = dict()

        bmes['bme1'] = BME280(self.bus_addrs['bme1'])
        bmes['bme2'] = BME280(self.bus_addrs['bme2'])

        return bmes

    def init_bus_vars(self):
        """ init all bus addresses for expected devices"""

        bus_addrs = dict()

        bus_addrs['bme1'] = '0x76'
        bus_addrs['bme2'] = '0x77'
        bus_addrs['screen'] = '0x3c'
        bus_addrs['ups'] = '0x10'

        self.check_bus()

        return bus_addrs

    def check_bus(self):
        """ check all requested buses are available/connected """

        p = subprocess.Popen(['i2cdetect', '-y', '1'], stdout=subprocess.PIPE,)
        # cmdout = str(p.communicate())

        for i in range(0, 9):
            line = str(p.stdout.readline())

            for match in re.finditer("[0-9][0-9]:.*[0-9][0-9]", line):
                print(match.group())
        return

    def update_data_records(self):
        """ store sensing variables and timestamp """

        timestamp = datetime.datetime.now()

        # data processing
        temp1 = self.temp_sensors['bme1'].temperature
        temp2 = self.temp_sensors['bme2'].temperature
        avg_temp = (temp1 + temp2)/2

        # STORAGE HEADER - timestamp, temp1, temp2, avgtemp, batt_capacity
        to_store = [timestamp, temp1, temp2, avg_temp, self.ups.capacity]

        # setup cdl
        x = ','.join(map(str, to_store))
        x += '\n'

        # write to txt
        data_file = open(DATA_FILEPATH, 'a')
        data_file.write(x)
        data_file.close()

        # debuggin
        print(x)
        print('avg: ' + str(avg_temp))
        if avg_temp >= -10:
            print('fucked')

        return

    def update_controller(self):
        """ update state of all peripherals connected to controller """

        for bme in self.temp_sensors:
            self.temp_sensors[bme].update_sensor()

        self.ups.update_capacity()


def main():
    # bme1 = BME280(0x76)
    # bme2 = BME280(0x77)
    #
    # timestamp = datetime.datetime.now()
    # bme1.update_sensor()
    # bme2.update_sensor()
    #
    # avg_temp = (bme1.temperature + bme2.temperature)/2
    #
    # # STORAGE HEADER - timestamp, temp1, temp2, avgtemp
    # to_store = [timestamp, bme1.temperature, bme2.temperature, avg_temp]
    #
    # # setup cdl
    # x = ','.join(map(str, to_store))
    # x += '\n'
    # print(x)
    # print('avg: ' + str(avg_temp))
    # if avg_temp >= -10:
    #     print('fucked')
    #
    # # write to txt
    # data_file = open(DATA_FILEPATH, 'a')
    # data_file.write(x)
    # data_file.close()

    controller = Controller()
    controller.update_controller()
    controller.update_data_records()

    print()


if __name__ == '__main__':
    x = 2
    while x > 1:
        main()
        time.sleep(1)