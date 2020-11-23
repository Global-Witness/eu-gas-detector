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
        'In the {}, {} is meeting with {} today' \
        .format(
            event['queryStringParameters']['institution'],
            event['queryStringParameters']['host'],
            event['queryStringParameters']['guest']))
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': 'Tweet posted!'
    }
