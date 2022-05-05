
# TODO rconcile requiremtnes
# todo implement screen stuff
# todo alerts
# todo scan for request emails

import time
from controller import Controller
from screen import Screen

# frequency of sensor update in seconds
UPDATE_FREQ = 1


def main():

    controller = Controller()

    controller.update_controller()
    controller.update_data_records(to_console=True)

    screen = Screen()
    lines = ['T1: %, T2: %'.format(controller.T1, controller.T2), 'H1: %, H2: %'.format(controller.H1, controller.H2)]
    screen.display(lines=lines)


if __name__ == '__main__':
    x = 2
    while x > 1:
        main()
        time.sleep(UPDATE_FREQ)