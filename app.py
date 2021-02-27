from flask import Flask, jsonify
import tweepy, configparser

config = configparser.ConfigParser()
config.read("config.ini")

consumer_key = config['twitter']['twitter_key']
consumer_secret = config['twitter']['twitter_secret']

app = Flask(__name__)

colours = [
    {
        'id': 1,
        'colour': 'blue'
    },
    {
        'id': 2,
        'colour': 'red'
    }
]

auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
twitter_api = tweepy.API(auth)

@app.route('/', methods=['GET'])
def index():
    return "Welcome to Jacket Server, turn back or suffer your DOOM"

@app.route('/api/v1.0/get_tweets', methods=['GET'])
def get_tasks():
    return jsonify({'colours': colours[0]})

if __name__ == '__main__':
    app.run(debug=True)
