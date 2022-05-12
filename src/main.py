from controller import Controller
from httplib2 import ServerNotFoundError


def main():
    while True:
        try:
            controller = Controller()
            controller.run()
        except ServerNotFoundError:
            print("Initialization failed - Retrying...")
            pass


if __name__ == '__main__':
    main()

