from flask import Flask, jsonify
import tweepy, configparser

config = configparser.ConfigParser()
config.read("config.ini")

consumer_key = config['twitter']['twitter_key']
consumer_secret = config['twitter']['twitter_secret']
access_token = config['twitter']['access_token']
access_token_secret = config['twitter']['access_token_secret']

app = Flask(__name__)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
twitter_api = tweepy.API(auth)

colour = ""

def check_tweet(tweet_text):
    tweet_text = tweet_text.lower()
    if "red" in tweet_text:
        return "red"
    elif "orange" in tweet_text:
        return "orange"
    elif "yellow" in tweet_text:
        return "yellow"
    elif "chartreuse" in tweet_text:
        return "chartreuse"
    elif "green" in tweet_text:
        return "green"
    elif "spring" in tweet_text:
        return "spring"
    elif "cyan" in tweet_text:
        return "cyan"
    elif "azure" in tweet_text:
        return "azure"
    elif "blue" in tweet_text:
        return "blue"
    elif "violet" in tweet_text:
        return "violet"
    elif "violet" in tweet_text:
        return "violet"
    elif "magenta" in tweet_text:
        return "magenta"
    elif "rose" in tweet_text:
        return "rose"
    else:
        return "white"

def get_latest_mention():
    tweets = twitter_api.mentions_timeline()
    for tweet in tweets:
        return (tweet.text)


@app.route('/', methods=['GET'])
def index():
    return "Welcome to Jacket Server, turn back or suffer your DOOM"

@app.route('/api/v1.0/get_tweets', methods=['GET'])
def get_tweets():
    if check_tweet(get_latest_mention()) != None:
        colour = check_tweet(get_latest_mention())
    return jsonify({'colour': colour, 'tweets': get_latest_mention()})

if __name__ == '__main__':
    app.run(debug=True)
