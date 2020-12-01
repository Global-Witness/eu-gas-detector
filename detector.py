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

    if r.status_code == 200:
        meetings = csv.reader(r.text.splitlines())
        for row in meetings:
            if institution == 'European Commission':
                meeting = {
                    'date'           : row[3],
                    'institution'    : institution,
                    'host'           : row[1],
                    'public_body_id' : '576',
                    'guest'          : row[7],
                    'url'            : 'https://www.integritywatch.eu/'
                }
            elif institution == 'European Parliament':
                meeting = {
                    'date'           : row[10],
                    'institution'    : institution,
                    'host'           : row[0],
                    'public_body_id' : '546',
                    'guest'          : row[4],
                    'url'            : 'https://www.integritywatch.eu/mepmeetings'
                }

            if meeting['date'] == datetime.today().strftime('%d/%m/%Y') and re.search(r'ga(s|z)', meeting['guest'].lower()):
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
