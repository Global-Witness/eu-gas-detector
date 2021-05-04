import boto3, os, tweepy, csv, requests, re, json, urllib.parse, html
from datetime import datetime
from lxml import etree

auth = tweepy.OAuthHandler(
    os.environ['TWITTER_CONSUMER_KEY'],
    os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(
    os.environ['TWITTER_ACCESS_TOKEN'],
    os.environ['TWITTER_ACCESS_SECRET'])
twitter = tweepy.API(auth)

def join_with_and(l):
    return ' and '.join([', '.join(l[:-1]), l[-1]] if len(l) > 2 else l)

def get_meetings_data(url, host_type, public_body_id):
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
                    'id': urllib.parse.parse_qs(
                        urllib.parse.urlsplit(
                            guest.xpath('.//a/@href')[0]).query)['id'][0]
                })

            date = datetime.strptime(
                meeting.xpath('.//td[{date}]/text()'.format(**column_indices))[0].strip(),
                '%d/%m/%Y')

            meetings.append({
                'date': datetime.strftime(date, '%B %-d'),
                'hosts': hosts,
                'guests': guests,
                'public_body_id': public_body_id
            })
   
    return meetings

def send_confirmation_email(subject, body):

    for address in os.environ['RECIPIENT_EMAILS'].split(','):
        print('Sending email to {}...'.format(address))

    response = boto3.client('ses').send_email(
        Source = os.environ['SOURCE_EMAIL'],
        Destinatiot = {'ToAddresses': os.environ['RECIPIENT_EMAILS'].split(',')},
        Message = {
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body} } })
    
    return response

def lambda_handler(event, context):
    latest_tweets = [
        html.unescape(t.full_text) for t in
        twitter.user_timeline(count = 100, tweet_mode = 'extended')
    ]

    with open('data/entities.csv', 'r') as i:
        entity_rows = list(csv.reader(i.readlines()))
        entities = {}
        for row in entity_rows:
            entities[row[0]] = row[1]

    with open('data/public-bodies.csv', 'r') as i:
        public_body_rows = list(csv.reader(i.readlines()))
        public_bodies = {}
        for row in public_body_rows:
            public_bodies[row[0]] = row[1]

    for url in public_bodies.keys():
        meetings = []
        r = requests.get(url)

        meetings += get_meetings_data(
            etree.HTML(r.text).xpath('//div[@id="transparency"]//a/@href')[0],
            'Commissioner',
            public_bodies[url])

        meetings += get_meetings_data(etree.HTML(r.text).xpath(
            '//div[@id="transparency"]//a/@href')[1],
            'Cabinet',
            public_bodies[url])

        for meeting in meetings:
            hit = False
            # Using a combined list of hosts and guests here is a bit hacky
            for entity in entities.keys():
                if entity in [g['id'] for g in meeting['guests']]:
                    hit = True
        
            if hit == True:
                meeting['guests_string'] = join_with_and([g['name'] for g in meeting['guests']])
                meeting['guests_string_twitter'] = join_with_and(
                    [g['name'] + ' (' + entities.get(g['id']) + ')' for g in meeting['guests'] if entities.get(g['id']) is not None])
                meeting['hosts_string'] = join_with_and(meeting['hosts'])
                meeting['hosts_string_twitter'] = join_with_and(
                    [h + ' (' + entities.get(h) + ')' if entities.get(h) is not None else h for h in meeting['hosts']])
                
                tweet = os.environ['TWEET_TEMPLATE'].format(**meeting)

                if len(tweet) > 280:
                    tweet = tweet.split('\n')[0]

                print(meeting)

                if tweet not in latest_tweets:
                    response = send_confirmation_email(
                        subject = 'New meeting with {guests_string_twitter}'.format(**meeting),
                        body =
                            '<html><body>' + \
                            tweet + \
                            '<br/><br/>' + \
                            '<a href="https://' + os.environ['API_ID'] + '.execute-api.eu-west-1.amazonaws.com/dev?' + \
                            urllib.parse.urlencode(meeting) + '">' + \
                            'Click here to send this Tweet and submit an FOI request!</a> If you don\'t think it\'s right, just ignore this email.' + \
                            '</body></html>')
                    
                    print(response)
