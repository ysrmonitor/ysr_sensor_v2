
# TODO rconcile requiremtnes
# todo implement screen stuff
# todo alerts
# todo scan for request emails

import time
from controller import Controller, EnvError, SensorError
from screen import Screen

# frequency of sensor update in seconds
UPDATE_FREQ = 1


def main(controller, screen=None):
    x = 2
    while x > 1:
        try:
            time.sleep(UPDATE_FREQ)
            controller.update_controller()
            controller.update_data_records(to_console=True)
        except SensorError:
            print("Sensor disconnected")
            # todo send sensor disconnected message
            pass

        except EnvError:
            print("Environment Issue!")
            # todo send env alert message
            pass

        except OSError:
            print('Sensor disconnected!')
            # todo send env alert message
            pass

        try:
            lines = ['T1: {}C, T2: {}C'.format(round(controller.T1, 1), round(controller.T2, 1)),
                     'H1: {}%, H2: {}%'.format(round(controller.H1, 1), round(controller.H2, 1)),
                     'Battery: {}/{}'.format(controller.batt_charge, controller.batt_capacity)]
            screen.display(lines=lines)

        except ValueError:
            print("Screen disconnected")
            # todo send screen disconnected message
            pass


if __name__ == '__main__':
    try:
        controller = Controller()
        try:
            screen = Screen()
            main(controller, screen)

        except ValueError:
            main(controller)
            print("Screen disconnected")
            # todo send screen disconnected message
            pass

    except SensorError:
        print("Sensor disconnected")
        # todo send sensor disconnected message
        pass

    except EnvError:
        print("Environment Issue!")
        # todo send env alert message
        pass



