
# TODO rconcile requiremtnes
# todo implement screen stuff
# todo alerts
# todo scan for request emails

import time
from controller import Controller

# frequency of sensor update in seconds
UPDATE_FREQ = 1


def main():

    controller = Controller()

    controller.update_controller()
    controller.update_data_records(to_console=True)


if __name__ == '__main__':
    x = 2
    while x > 1:
        main()
        time.sleep(UPDATE_FREQ)