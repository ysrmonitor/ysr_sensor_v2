

class AlertFactory:

    def alert_factory(self, a_type, **kwargs):
        if 'bus_disconnect' in a_type:
            return BusAlert(a_type=a_type, **kwargs)


class Alert:
    def __init__(self, a_type, **kwargs):
        self.type = a_type
        self.info = kwargs

    def process(self):
        pass


class BusAlert(Alert):
    def __init__(self, a_type, **kwargs):
        super().__init__(a_type, **kwargs)

    def process(self):
        # todo email all on alets list
        # todo display to screen
        print(self.info['sensor'] + 'disconnected!')
        super().process()
        return


class EnvAlert(Alert):
    def __init__(self, a_type, **kwargs):
        super().__init__(a_type, **kwargs)

    def process(self):
        # todo email all on alets list
        if 'temp' in self.info.keys():
            print("Temperature is: " + self.info['temp'])
        elif 'hum' in self.info.keys():
            print("Humidity is: " + self.info['temp'])
        super().process()
        return
