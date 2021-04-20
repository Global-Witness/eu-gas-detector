import os, tweepy, urllib.parse, requests, json
from lxml import etree

auth = tweepy.OAuthHandler(
    os.environ['TWITTER_CONSUMER_KEY'],
    os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(
    os.environ['TWITTER_ACCESS_TOKEN'],
    os.environ['TWITTER_ACCESS_SECRET'])
twitter = tweepy.API(auth)

def lambda_handler(event, context):
    # Send tweet
    tweet = os.environ['TWEET_TEMPLATE'].format(**event['queryStringParameters'])
    
    if len(tweet) > 280:
        tweet = tweet.split('\n')[0] 
    
    status = twitter.update_status(tweet)

    # Log in to AskTheEU
    domain = 'https://www.asktheeu.org'
    s = requests.Session()
    r = s.get(domain + '/en/profile/sign_in')
    login_page = etree.HTML(r.text)
    r = s.post(
        url = domain + '/en/profile/sign_in',
        data = {
            'utf8': '✓',
            'authenticity_token': '',
            'user_signin[email]': os.environ['ASKTHEEU_EMAIL'],
            'user_signin[password]': os.environ['ASKTHEEU_PASSWORD'],
            'token': login_page.xpath('//input[@id="signin_token"]/@value')[0],
            'modal': '',
            'commit': 'Sign+in'
        })

    # Draft request
    r = s.get(domain + '/en/alaveteli_pro/info_requests/new')
    request_page = etree.HTML(r.text)
    r = s.post(
        url = domain + '/en/alaveteli_pro/draft_info_requests',
        data = {
            'utf8': '✓',
            'authenticity_token': request_page.xpath('//input[@name="authenticity_token"]/@value')[0],
            'info_request[public_body_id]': event['queryStringParameters']['public_body_id'],
            'info_request[title]': os.environ['FOI_SUBJECT_TEMPLATE'].format(**event['queryStringParameters']),
            'outgoing_message[body]': os.environ['FOI_BODY_TEMPLATE'].format(**event['queryStringParameters']),
            'embargo[embargo_duration]': '',
            'preview': 'true'
        })

    # Send request
    draft_page = etree.HTML(r.text)
    #r = s.post(
    #    url = domain + '/en/alaveteli_pro/draft_info_requests',
    #    data = {
    #        'utf8': '✓',
    #        'authenticity_token': draft_page.xpath('//input[@name="authenticity_token"]/@value')[0],
    #        'draft_id': draft_page.xpath('//input[@id="draft_id"]/@value')[0],
    #        'commit': 'Send+request'
    #    })

    #return {
    #    'statusCode': 200,
    #    'body': {
    #        'twitter_response': status._json,
    #        'asktheeu_response': {
    #            'text': r.text,
    #            'headers': dict(r.headers),
    #            'status_code': r.status_code,
    #            'request': {
    #                'url': r.request.url,
    #                'method': r.request.method,
    #                'headers': dict(r.request.headers),
    #            }
    #        }
    #    }
    #}

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': 'Success!'
    }
