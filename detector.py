import boto3, os, csv, requests, re, json, urllib.parse
from datetime import datetime

def lambda_handler(event, context):
    check_meetings('European Commission')
    check_meetings('European Parliament')

def check_meetings(institution):
    if institution == 'European Commission':
        r = requests.get('https://www.integritywatch.eu/data/meetings.csv')
    elif institution == 'European Parliament':
        r = requests.get('https://www.integritywatch.eu/data/mepmeetings/mepmeetings.csv')

    r.encoding = 'utf-8'

    with open('data/guests.csv', 'r') as i:
        guests = list(csv.reader(i.readlines()))

    if r.status_code == 200:
        meetings = csv.reader(r.text.splitlines())
        for meeting_row in meetings:
            for guest_row in guests:
                if meeting_row[6] == guest_row[1] and meeting_row[3] == datetime.today().strftime('%d/%m/%Y'):

                    if institution == 'European Commission':
                        meeting = {
                            'date'           : meeting_row[3],
                            'institution'    : institution,
                            'host'           : meeting_row[1],
                            'public_body_id' : '576',
                            'guest'          : guest_row[2] if guest_row[2] != '' else meeting_row[7],
                            'url'            : 'https://www.integritywatch.eu/'
                        }
            
                    elif institution == 'European Parliament':
                        meeting = {
                            'date'           : meeting_row[10],
                            'institution'    : institution,
                            'host'           : meeting_row[0],
                            'public_body_id' : '546',
                            'guest'          : meeting_row[4],
                            'url'            : 'https://www.integritywatch.eu/mepmeetings'
                        }

                    send_confirmation_email(
                        subject = 'New meeting with {guest}'.format(**meeting),
                        body =
                            '<html><body>' + \
                            os.environ['TWEET_TEMPLATE'].format(**meeting) + \
                            '<br/><br/>' + \
                            '<a href="https://' + os.environ['API_ID'] + '.execute-api.eu-west-1.amazonaws.com/dev?' + \
                            urllib.parse.urlencode(meeting) + '">' + \
                            'Click here to send this Tweet and submit an FOI request!</a> If you don\'t think it\'s right, just ignore this email.' + \
                            '</body></html>')

def send_confirmation_email(subject, body):
    response = boto3.client('ses').send_email(
        Source = os.environ['SOURCE_EMAIL'],
        Destination = {'ToAddresses': [os.environ['RECIPIENT_EMAIL']]},
        Message = {
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body} } })

    return response
