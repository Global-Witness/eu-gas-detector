import os, tweepy

auth = tweepy.OAuthHandler(
    os.environ['TWITTER_CONSUMER_KEY'],
    os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(
    os.environ['TWITTER_ACCESS_TOKEN'],
    os.environ['TWITTER_ACCESS_SECRET'])
twitter = tweepy.API(auth)

def lambda_handler(event, context):
    status = twitter.update_status(
        'In the {institution}, {host} is meeting with {guest} today' \
        .format(event['queryStringParameters']**))
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': 'Tweet posted!'
    }
