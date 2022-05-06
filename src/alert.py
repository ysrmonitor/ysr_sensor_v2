import datetime
import pytz
from email_handler import GMailAcc


def main():
    print(pytz.all_timezones)

    dt = datetime.datetime.now()
    dt = dt.replace(tzinfo=pytz.timezone('Canada/Yukon'))
    print(dt)


def test():
    gmail_acc = GMailAcc()  # init gmail account

    # send status email with Status as subject line, and response interval in seconds with s appended
    email = gmail_acc.create_message(gmail_acc.address, gmail_acc.address, 'Status', str(3600))
    gmail_acc.send_message(gmail_acc.address, email)

    return


if __name__ == '__main__':
    test()