import boto3, os, csv, requests, re, json, urllib.parse
from datetime import datetime
from lxml import etree

def join_with_and(l):
    return ' and '.join([', '.join(l[:-1]), l[-1]] if len(l) > 2 else l)

def get_meetings_data(url, host_type):
    meetings = []
    r = requests.get(url)
    
    if r.status_code == 200:
        meeting_table = etree.HTML(r.text).xpath('//table[@id="listMeetingsTable"]/tbody/tr')
        for meeting in meeting_table:
            if host_type == 'Commissioner':
                hosts = [h.strip() for h in etree.HTML(r.text).xpath('(//nav/ol//li//a)[3]/text()')]
                column_indices = {'date': '1', 'guests': '3'}
            elif host_type == 'Cabinet':
                hosts = [h.strip() for h in meeting.xpath('.//td[1]/text()')][:-1]
                column_indices = {'date': '2', 'guests': '4'}

            guests = []
            for guest in meeting.xpath('.//td[{guests}]/comment()'.format(**column_indices)):
                guest = etree.HTML('<' + str(guest).replace('<!-- ', '').replace('-->', ''))
                guests.append({
                    'name': guest.xpath('.//a/text()')[0],
                    'id': urllib.parse.parse_qs(urllib.parse.urlsplit(guest.xpath('.//a/@href')[0]).query)['id'][0]
                })

            meetings.append({
                'date': meeting.xpath('.//td[{date}]/text()'.format(**column_indices))[0].strip(),
                'hosts': hosts,
                'guests': guests,
                'public_body_id': '576'
            })
   
    return meetings

def send_confirmation_email(subject, body):
    response = boto3.client('ses').send_email(
        Source = os.environ['SOURCE_EMAIL'],
        Destination = {'ToAddresses': [os.environ['RECIPIENT_EMAIL']]},
        Message = {
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body} } })
    
    return response

def lambda_handler(event, context):
    r = requests.get('https://ec.europa.eu/commission/commissioners/2019-2024_en')
    commissioner_urls = etree.HTML(r.text).xpath('//h3[@class="listing__title"]/a/@href')
    for url in commissioner_urls:
        meetings = []
        r = requests.get(url)
        meetings += get_meetings_data(etree.HTML(r.text).xpath('//div[@id="transparency"]//a/@href')[0], 'Commissioner')
        meetings += get_meetings_data(etree.HTML(r.text).xpath('//div[@id="transparency"]//a/@href')[1], 'Cabinet')

        with open('data/entities.csv', 'r') as i:
            entity_rows = list(csv.reader(i.readlines()))
            entities = {}
            for row in entity_rows:
                entities[row[0]] = row[1]

        for meeting in meetings:
            hit = False
            # Using a combined list of hosts and guests here is a bit hacky
            for entity in entities.keys():
                if entity in [g['id'] for g in meeting['guests']] and meeting['date'] == datetime.today().strftime('%d/%m/%Y'):
                    hit = True
        
            if hit == True:
                meeting['guests_string'] = join_with_and([g['name'] for g in meeting['guests']])
                meeting['guests_string_twitter'] = join_with_and([entities.get(g['id']) for g in meeting['guests'] if entities.get(g['id']) is not None])
                meeting['hosts_string'] = join_with_and(meeting['hosts'])
                meeting['hosts_string_twitter'] = join_with_and([entities.get(h) if entities.get(h) is not None else h for h in meeting['hosts']])
                
                send_confirmation_email(
                    subject = 'New meeting with {guests_string}'.format(**meeting),
                    body =
                        '<html><body>' + \
                        os.environ['TWEET_TEMPLATE'].format(**meeting) + \
                        '<br/><br/>' + \
                        '<a href="https://' + os.environ['API_ID'] + '.execute-api.eu-west-1.amazonaws.com/dev?' + \
                        urllib.parse.urlencode(meeting) + '">' + \
                        'Click here to send this Tweet and submit an FOI request!</a> If you don\'t think it\'s right, just ignore this email.' + \
                        '</body></html>')
