import random
import bme280
# use pip install pimoroni-bme280 smbus for real setup

# class BME280:
#     def __init__(self, address):
#         self.address = address
#         self.temperature = None
#         self.pressure = None
#         self.humidity = None
#
#     def update_sensor(self):
#         self.temperature = random.randint(-20, 10)
#         self.pressure = random.randint(95, 105)
#         self.humidity = random.randint(0, 100)
#

bme1 = bme280.BME280(i2c_addr=0x77)
print(bme1.get_temperature())