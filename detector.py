import boto3, os, csv, requests, json
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
                    'date'  : row[3],
                    'host'  : row[1],
                    'guest' : row[7]
                }
            elif institution == 'European Parliament':
                meeting = {
                    'date'  : row[10],
                    'host'  : row[0],
                    'guest' : row[4]
                }

            meeting['institution'] = institution

            if meeting['date'] == datetime.today().strftime('%d/%m/%Y'):
                send_confirmation_email(
                    subject = 'New meeting with {guest}'.format(**meeting),
                    body =
                        '<html><body>' + \
                        'In the {institution}, {host} is meeting with {guest} today'.format(**meeting) + \
                        '<br/><br/>' + \
                        '<a href="https://' + os.environ['API_ID'] + '.execute-api.eu-west-1.amazonaws.com/dev/tweet?' + \
                        'institution={institution}&host={host}&guest={guest}'.format(**meeting) + '">' + \
                        'Click here to send this Tweet!</a> If you don\'t think it\'s right, just ignore this email.' + \
                        '</body></html>')

def send_confirmation_email(subject, body):
    response = boto3.client('ses').send_email(
        Source = os.environ['SOURCE_EMAIL'],
        Destination = {'ToAddresses': [os.environ['RECIPIENT_EMAIL']]},
        Message = {
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body} } })

    return response