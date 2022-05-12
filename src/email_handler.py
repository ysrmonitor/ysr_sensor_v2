from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
import mimetypes

import base64

# required spreadsheets globals
ALERTS_MEMBERS = 'Alerts - Members'
ALERTS_TRACKING = 'Alerts - Tracking'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://mail.google.com/',
          'https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.compose',
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


class GoogAcc:
    def __init__(self):
        self.creds = None
        self.address = 'ysr.monitor@gmail.com'
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())


class GMailAcc(GoogAcc):
    def __init__(self):
        super().__init__()

        self.service = build('gmail', 'v1', credentials=self.creds)

    def get_labels(self):
        try:
            # Call the Gmail API
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            if not labels:
                print('No labels found.')
                return
            print('Labels:')
            for label in labels:
                print(label['name'])

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred: {error}')

    def create_message(self, sender, to, subject, message_text):
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8"))

        return {'raw': raw_message.decode("utf-8")}

    def create_message_wAttachment(self, sender, to, subject, message_text, file):
        """Create a message for an email.

        Args:
          sender: Email address of the sender.
          to: Email address of the receiver.
          subject: The subject of the email message.
          message_text: The text of the email message.
          file: The path to the file to be attached.

        Returns:
          An object containing a base64url encoded email object.
        """
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)

        if main_type == 'text':
            fp = open(file, 'rb')
            # news = str(fp.read())
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(file, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(file, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(file, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8"))
        return {'raw': raw_message.decode("utf-8")}

        # return {'raw': base64.urlsafe_b64encode(message.as_string())}
        # return {'raw': base64.urlsafe_b64encode(message.as_bytes())}

    def send_message(self, user_id, message):

        try:
            message = self.service.users().messages().send(userId=user_id, body=message).execute()
            print('Message Id: %s' % message['id'])
            return message
        except Exception as e:
            print('An error occurred: %s' % e)
            return None

    def clear_inbox(self):
        messages = self.service.users().messages().list(userId='me', labelIds=['INBOX']).execute().get('messages', [])

        for message in messages:
            message_id = message['id']
            self.service.users().messages().delete(userId="me", id=message_id).execute()

        return


class DriveAcc(GoogAcc):
    def __init__(self):
        super().__init__()

        self.service = build('drive', 'v3', credentials=self.creds)

    def get_all_files(self):
        all_files = self.service.files().list().execute()

        return all_files

    def get_sheets(self):
        all_files = self.get_all_files()
        sheets = [f for f in all_files['files'] if 'spreadsheet' in f['mimeType']]

        return sheets


class SheetsAcc(GoogAcc):
    def __init__(self):
        super().__init__()

        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_sheet(self, id):
        sheet = self.service.spreadsheets().get(spreadsheetId=id).execute()

        return sheet

    def create_sheet(self, title):
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = self.service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        print('Spreadsheet ID: {0}'.format(spreadsheet.get('spreadsheetId')))

        return spreadsheet.get('spreadsheetId')

    def edit_sheet(self, spreadsheet_id, range_name, body):
        value_input_option = "RAW"

        result = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))


if __name__ == '__main__':
    gmail = GMailAcc()
    drive = DriveAcc()
    sheets = SheetsAcc()

    all_sheets = drive.get_sheets()
    for sheet in all_sheets:
        csheet = sheets.get_sheet(sheet['id'])
        title = csheet['properties']['title']
        print(title)

    for sheet in all_sheets:
        csheet = sheets.get_sheet(sheet['id'])
        title = csheet['properties']['title']
        if title == ALERTS_MEMBERS:
            sheet_temp = sheets.service.spreadsheets().values().get(spreadsheetId=sheet['id'], range='Sheet1!A:A').execute()['values']
            alerts_list = [x[0] for x in sheet_temp]
            print()
