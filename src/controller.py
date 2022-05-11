import dfr0528 as ups
import datetime
import subprocess
import re
import smbus2
import bme280
import tabulate
import pytz
import time
import pathlib
from email_handler import GMailAcc, DriveAcc, SheetsAcc
from httplib2.error import ServerNotFoundError
import os
from screen import Screen

# data storage globals
DATA_FILE_NAME = 'data.txt'
DATA_FILEPATH = pathlib.Path(__file__).parent.resolve().joinpath(DATA_FILE_NAME)

# required spreadsheets globals
ALERTS_MEMBERS = 'Alerts - Members'
DEFAULT_ALERTS_MEMBERS = ['daniel.js.campbell@gmail.com']

ALERTS_TRACKING = 'Alerts - Tracking'
ENV_LIMITS = 'Environment - Limits'
OPERATING_PARAMETERS = 'Operating - Parameters'
DEFAULT_MEASUREMENT_FREQ = 3600

DEFAULT_SHEET_INFO = dict()

DEFAULT_MIN_TEMP = -10
DEFAULT_MAX_TEMP = 30
DEFAULT_MIN_HUM = 0
DEFAULT_MAX_HUM = 100
DEFAULT_MIN_PRESS = 90
DEFAULT_MAX_PRESS = 110

values = [
    ['Measurement Frequency [s]', DEFAULT_MEASUREMENT_FREQ],
]
body = {
    'values': values
}
DEFAULT_SHEET_INFO[OPERATING_PARAMETERS] = dict()
DEFAULT_SHEET_INFO[OPERATING_PARAMETERS]['body'] = body
DEFAULT_SHEET_INFO[OPERATING_PARAMETERS]['range'] = 'Sheet1!A1:B1'

values = [
    ['', 'Min.', 'Max.'],
    ['Temperature [C]', DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP],
    ['Pressure [kPa]', DEFAULT_MIN_PRESS, DEFAULT_MAX_PRESS],
    ['Humidity [%]', DEFAULT_MIN_HUM, DEFAULT_MAX_HUM]
]
body = {
    'values': values
}
DEFAULT_SHEET_INFO[ENV_LIMITS] = dict()
DEFAULT_SHEET_INFO[ENV_LIMITS]['body'] = body
DEFAULT_SHEET_INFO[ENV_LIMITS]['range'] = 'Sheet1!A1:D4'

values = [
    ['Members'],
    DEFAULT_ALERTS_MEMBERS,
]
body = {
    'values': values
}
DEFAULT_SHEET_INFO[ALERTS_MEMBERS] = dict()
DEFAULT_SHEET_INFO[ALERTS_MEMBERS]['body'] = body
DEFAULT_SHEET_INFO[ALERTS_MEMBERS]['range'] = 'Sheet1!A1:A2'


class Controller:
    def __init__(self):
        print("Initializing Controller...")

        # messages to send once initialized
        self.warnings = list()
        self.alerts = list()

        self.bus_addrs = self.init_bus_vars()
        # self.check_bus()

        self.bme_sensors = self.init_temp_sensors()
        self.ups = ups.DFR0528()
        self.screen = self.init_screen()

        self.meas_freq = None

        self.T1 = None
        self.T2 = None
        self.TAvg = None

        self.H1 = None
        self.H2 = None
        self.HAvg = None

        self.P1 = None
        self.P2 = None
        self.PAvg = None

        self.gmail = GMailAcc()
        self.gmail.clear_inbox()  # clear inbox on init to deal with old alerts

        self.gdrive = DriveAcc()
        self.gsheets = SheetsAcc()

        self.check_sheets()

        self.alerts_members = self.get_alerts_members()
        self.env_limits = self.get_env_limits()
        self.meas_freq = self.get_frequency()

        self.deliver_warnings()
        self.deliver_alerts()

    def run(self, freq=None):
        """ typical controller run sequence - frequency in seconds [s]"""

        freq_external = True
        if not freq:
            freq = self.meas_freq
            freq_external = False

        while True:
            self.update_status(freq)
            self.check_data_requests()
            self.env_limits = self.get_env_limits()

            if not freq_external:  # if no external freq passed, use sheet freq in operating params
                freq = self.get_frequency()

            self.init_temp_sensors()
            self.update_controller()
            self.update_data_records(to_console=True)

            # try displaying to screen
            try:
                lines = ['T1: {}C, T2: {}C'.format(round(self.T1, 1), round(self.T2, 1)),
                         'H1: {}%, H2: {}%'.format(round(self.H1, 1), round(self.H2, 1)),
                         'P1: {}kPa, P2: {}kPa'.format(round(self.P1, 1), round(self.P2, 1))]
                self.screen.display(lines=lines)

            except ValueError:
                error_message = "Screen disconnected or cannot be initialized!"
                self.log_peripheral_issue(error_message)
            pass

            self.deliver_warnings()
            self.deliver_alerts()

            time.sleep(freq)

    def deliver_warnings(self):
        """ send and clear all accumulated warning messages - controller will proceed despite warnings """

        if self.warnings:
            print('Sending warning messages to alerts members')
            for warning_message in self.warnings:
                self.gmail.send_message(self.gmail.address, warning_message)

        self.warnings = list()
        return

    def deliver_alerts(self):
        """ send and clear all accumulated alert messages - controller will not proceed without addressing alerts """

        if self.alerts:
            print('Sending alerts messages to alerts members')
            for alert_message in self.alerts:
                self.gmail.send_message(self.gmail.address, alert_message)

        self.alerts = list()
        return

    def check_data_requests(self):
        """ check for data requests and reply with data if desired """
        try:
            messages = self.gmail.service.users().messages().list(userId='me', labelIds=['INBOX']).execute()['messages']
            messages_ids = [x['id'] for x in messages]

            for mId in messages_ids:
                check = self.gmail.service.users().messages().get(userId="me", id=mId).execute()
                headers = check['payload']['headers']
                subject = [i['value'] for i in headers if i["name"].lower() == 'subject'][0]

                if 'data' in subject.lower():
                    data_from = self.gmail.address
                    data_to = [i['value'] for i in headers if i["name"].lower() == 'from'][0]
                    data_subject = subject
                    data_body = "See up to date measurement data attached."
                    att_fp = DATA_FILEPATH
                    data_response_email = self.gmail.create_message_wAttachment(data_from,
                                                                                data_to,
                                                                                data_subject,
                                                                                data_body,
                                                                                att_fp)
                    self.gmail.send_message(data_from, data_response_email)
                    self.gmail.service.users().messages().delete(userId="me", id=mId).execute()

        except KeyError:
            return

        except ServerNotFoundError:
            return

        return

    def get_alerts_members(self):
        """ get list of alerts - members from column A of sheet """
        print("Fetching Alerts Members...")

        all_sheets = self.gdrive.get_sheets()
        alerts_list = []

        for sheet in all_sheets:
            csheet = self.gsheets.get_sheet(sheet['id'])
            title = csheet['properties']['title']
            if title == ALERTS_MEMBERS:
                try:
                    sheet_temp = self.gsheets.service.spreadsheets().values().get(spreadsheetId=sheet['id'],
                                                                                  range='Sheet1!A:A').execute()['values']
                    # range returns rows as lists, parse into single list
                    alerts_list = [x[0] for x in sheet_temp]

                    # remove non-emails from list
                    for member in alerts_list:
                        if '@' and '.c' not in member:
                            alerts_list.remove(member)
                except KeyError: # case where alerts - members sheet is empty
                    error_message = "No valid alerts members found in Alerts - Members sheet, please enter valid emails in column A of Alerts - Members. Alerts will only be sent to defaults!"
                    self.log_init_issue(error_message)
                    alerts_list = DEFAULT_ALERTS_MEMBERS

                if len(alerts_list) == 0:  # case where no valid email addresses are found
                    error_message = "No valid alerts members found in Alerts - Members sheet, please enter valid emails in column A of Alerts - Members. Alerts will only be sent to defaults!"
                    self.log_init_issue(error_message)
                    alerts_list = DEFAULT_ALERTS_MEMBERS


        return alerts_list

    def get_env_limits(self):
        """ get default environment limits from sheet """
        print("Fetching Environment Limits...")

        all_sheets = self.gdrive.get_sheets()
        env_limits = dict()

        for sheet in all_sheets:
            csheet = self.gsheets.get_sheet(sheet['id'])
            title = csheet['properties']['title']
            if title == ENV_LIMITS:
                sheet_temp = self.gsheets.service.spreadsheets().values().get(spreadsheetId=sheet['id'],
                                                                              range='Sheet1!A1:D4').execute()['values']

                env_limits['temp'] = dict()
                env_limits['hum'] = dict()
                env_limits['press'] = dict()

                # set temperature limits
                try:
                    env_limits['temp']['min'] = int(sheet_temp[1][1])
                except (ValueError, IndexError):
                    env_limits['temp']['min'] = DEFAULT_MIN_TEMP
                    error_message = "Temperature Min. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MIN_TEMP)
                    self.log_init_issue(error_message)
                try:
                    env_limits['temp']['max'] = int(sheet_temp[1][2])
                except (ValueError, IndexError):
                    env_limits['temp']['max'] = DEFAULT_MAX_TEMP
                    error_message = "Temperature Max. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MAX_TEMP)
                    self.log_init_issue(error_message)

                # set pressure limits
                try:
                    env_limits['press']['min'] = int(sheet_temp[2][1])
                except (ValueError, IndexError):
                    env_limits['press']['min'] = DEFAULT_MIN_PRESS
                    error_message = "Pressure Min. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MIN_PRESS)
                    self.log_init_issue(error_message)
                try:
                    env_limits['press']['max'] = int(sheet_temp[2][2])
                except (ValueError, IndexError):
                    env_limits['press']['max'] = DEFAULT_MAX_PRESS
                    error_message = "Pressure Max. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MAX_PRESS)
                    self.log_init_issue(error_message)

                # set pressure limits
                try:
                    env_limits['hum']['min'] = int(sheet_temp[3][1])
                except (ValueError, IndexError):
                    env_limits['hum']['min'] = DEFAULT_MIN_HUM
                    error_message = "Humidity Min. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MIN_HUM)
                    self.log_init_issue(error_message)
                try:
                    env_limits['hum']['max'] = int(sheet_temp[3][2])
                except (ValueError, IndexError):
                    env_limits['hum']['max'] = DEFAULT_MAX_HUM
                    error_message = "Humidity Max. in Environment Limits is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MAX_HUM)
                    self.log_init_issue(error_message)

        return env_limits

    def get_frequency(self):
        """ get measurement frequency from sheet """
        print("Fetching Measurement Frequency...")

        all_sheets = self.gdrive.get_sheets()
        meas_freq = None

        for sheet in all_sheets:
            csheet = self.gsheets.get_sheet(sheet['id'])
            title = csheet['properties']['title']
            if title == OPERATING_PARAMETERS:
                sheet_temp = self.gsheets.service.spreadsheets().values().get(spreadsheetId=sheet['id'],
                                                                              range='Sheet1!A1:D4').execute()['values']

                # set temperature limits
                try:
                    meas_freq = int(sheet_temp[0][1])
                except (ValueError, IndexError):
                    meas_freq = DEFAULT_MEASUREMENT_FREQ
                    error_message = "Measurement Frequency in Operating - Parameters is non-numeric and cannot be parsed, " \
                                    "initialized using default value: {}C".format(DEFAULT_MEASUREMENT_FREQ)
                    self.log_init_issue(error_message)

        return meas_freq

    def log_init_issue(self, message):
        """ log initialization issues """

        init_from = self.gmail.address
        init_subject = "Initialization Warning"
        message_body = message

        for member in self.alerts_members:
            init_to = member
            init_email = self.gmail.create_message(init_from, init_to, init_subject, message_body)
            self.warnings.append(init_email)

    def log_env_issue(self, message):
        """ log environment issues """

        env_from = self.gmail.address
        env_subject = "Environment Warning"
        message_body = message

        for member in self.alerts_members:
            env_to = member
            env_email = self.gmail.create_message(env_from, env_to, env_subject, message_body)
            self.warnings.append(env_email)

    def log_peripheral_issue(self, message):
        """ log peripheral issues """

        per_from = self.gmail.address
        per_subject = "Peripheral/Sensor Warning"
        message_body = message

        for member in self.alerts_members:
            per_to = member
            per_email = self.gmail.create_message(per_from, per_to, per_subject, message_body)
            self.warnings.append(per_email)

    def check_sheets(self):
        """ check if all sheets present for alerts system """
        print("Checking for required sheets and parameters... ")

        all_sheets = self.gdrive.get_sheets()
        # required info for alerts to work properly
        required_titles = [ALERTS_MEMBERS, ALERTS_TRACKING, ENV_LIMITS, OPERATING_PARAMETERS]

        titles = []
        for sheet in all_sheets:
            csheet = self.gsheets.get_sheet(sheet['id'])
            titles.append(csheet['properties']['title'])

        for sheet in required_titles:
            if sheet not in titles:
                print(sheet + ' missing!')
                # create shete if missing
                new_sheet_id = self.gsheets.create_sheet(sheet)
                # update sheet to reflect defaults set above, only params required ofr operation are set as default
                if sheet in DEFAULT_SHEET_INFO.keys():  # only create defaults if set above
                    self.gsheets.edit_sheet(new_sheet_id, DEFAULT_SHEET_INFO[sheet]['range'],
                                            DEFAULT_SHEET_INFO[sheet]['body'])
            else:
                print(sheet + ' confirmed')

    def update_status(self, interval):
        """ update controller status via email"""

        status_to = self.gmail.address
        status_from = self.gmail.address
        status_subject = "Status"
        status_body = str(interval)

        status_email = self.gmail.create_message(status_from, status_to, status_subject, status_body)
        self.gmail.send_message(self.gmail.address, status_email)

        return

    def init_temp_sensors(self):
        """ init bme sensors and BME objects -> dict containing BME objects """

        bmes = dict()
        try:
            bmes['bme1'] = self.sample_bme(self.bus_addrs['bme1'])
        except OSError:
            error_message = "Sensor 1 disconnected or cannot be initialized!"
            self.log_peripheral_issue(error_message)
            pass
        try:
            bmes['bme2'] = self.sample_bme(self.bus_addrs['bme2'])
        except OSError:
            error_message = "Sensor 2 disconnected or cannot be initialized!"
            self.log_peripheral_issue(error_message)
            pass

        return bmes

    def init_screen(self):
        """ init screen - warn if disconnected """
        try:
            screen = Screen()
            return screen

        except ValueError:
            error_message = "Screen disconnected or cannot be initialized!"
            self.log_peripheral_issue(error_message)
        return

    def sample_bme(self, addr):
        port = 1
        bus = smbus2.SMBus(port)

        calibration_params = bme280.load_calibration_params(bus, addr)

        # the sample method will take a single reading and return a
        # compensated_reading object
        data = bme280.sample(bus, addr, calibration_params)
        bus.close()

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
        header = ['timestamp', 'temp1', 'temp2', 'avg_temp', 'hum1', 'hum2', 'avg_hum', 'press1', 'press2', 'press_avg']
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
                data_file.write(header_str + '\n')
            data_file.write(x)
        data_file.close()

        # debugging
        if to_console:
            print(tabulate.tabulate([to_store], header))

        return

    def update_controller(self):
        """ update state of all peripherals connected to controller """

        for bme in self.bme_sensors.keys():
            self.bme_sensors[bme] = self.sample_bme(self.bus_addrs[bme])

        self.ups.update_capacity()

        return

    def process_inputs(self):
        """ process sensor inputs and ensure all are within limits """

        timestamp = datetime.datetime.now()
        timestamp = timestamp.replace(tzinfo=pytz.timezone('Canada/Yukon'))

        # data processing
        # process temp given possible disconnects
        try:
            self.T1 = self.bme_sensors['bme1'].temperature
        except:
            self.T1 = None

        try:
            self.T2 = self.bme_sensors['bme2'].temperature
        except:
            self.T2 = None

        if self.T1 and self.T2:
            self.TAvg = (self.T1 + self.T2)/2
        elif self.T1:
            self.TAvg = self.T1
        elif self.T2:
            self.TAvg = self.T2
        else:
            self.TAvg = 'error'

        # process humidity given possible disconnects
        try:
            self.H1 = self.bme_sensors['bme1'].humidity
        except:
            self.H1 = None

        try:
            self.H2 = self.bme_sensors['bme2'].humidity
        except:
            self.H2 = None

        if self.H1 and self.H2:
            self.HAvg = (self.H1 + self.H2)/2
        elif self.H1:
            self.HAvg = self.H1
        elif self.H2:
            self.HAvg = self.H2
        else:
            self.HAvg = 'error'

        # process press given possible disconnects
        try:
            self.P1 = self.bme_sensors['bme1'].pressure
        except:
            self.P1 = None

        try:
            self.P2 = self.bme_sensors['bme2'].pressure
        except:
            self.P2 = None

        if self.P1 and self.P2:
            self.PAvg = (self.P1 + self.P2)/2
        elif self.P1:
            self.PAvg = self.P1
        elif self.P2:
            self.PAvg = self.P2
        else:
            self.PAvg = 'error'

        # check temp limits and warn if outside limits
        if self.env_limits['temp']['min'] >= self.TAvg:
            error_message = "Average temperature below minimum! Average Temperature [C]: " + str(self.TAvg)
            self.log_env_issue(error_message)
        if self.env_limits['temp']['max'] <= self.TAvg:
            error_message = "Average temperature above maximum! Average Temperature [C]: " + str(self.TAvg)
            self.log_env_issue(error_message)

        # check pressure limits and warn if outside limits
        if self.env_limits['press']['min'] >= self.PAvg:
            error_message = "Average pressure below minimum! Average Pressure [kPa]: " + str(self.PAvg)
            self.log_env_issue(error_message)
        if self.env_limits['press']['max'] <= self.PAvg:
            error_message = "Average pressure above maximum! Average Pressure [kPa]: " + str(self.PAvg)
            self.log_env_issue(error_message)

        # check humidity limits and warn if outside limits
        if self.env_limits['hum']['min'] >= self.HAvg:
            error_message = "Average humidity below minimum! Average Humidity [%]: " + str(self.HAvg)
            self.log_env_issue(error_message)
        if self.env_limits['hum']['max'] <= self.HAvg:
            error_message = "Average humidity above maximum! Average Humidity [%]: " + str(self.HAvg)
            self.log_env_issue(error_message)

        # STORAGE HEADER - timestamp, temp1, temp2, avg_temp, hum1, hum2, avg_hum, press1, press2, avg_press,
        to_store = [timestamp, self.T1, self.T2, self.TAvg, self.H1, self.H2, self.HAvg]

        return to_store


class EnvError(Exception):
    """ issue with one or more env variables """
    pass


class SensorError(Exception):
    """ issue with one or more env variables """
    pass


if __name__ == '__main__':
    contoller = Controller()
    contoller.run()