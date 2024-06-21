from requests_oauthlib import OAuth1Session
import os
import json
import schedule
import time
from flask import Flask, request, redirect
from datetime import datetime, timedelta
import openai
import pytz

app = Flask(__name__)

# Your Twitter API credentials
CONSUMER_KEY = "YOUR_TWITTER_API_KEY"
CONSUMER_SECRET = "YOUR_TWITTER_APIKEY_SECRET"
ACCESS_TOKEN = 'YOUR_TWITTER_ACCESS_TOKEN'
ACCESS_TOKEN_SECRET = 'YOUR_TWITTER_ACCESS_TOKEN_SECRET'

# OpenAI API credentials
openai.api_key = 'YOUR_OPENAI_API_KEY'

# Set the callback URL (must match the URL set in the app settings)
CALLBACK_URL = 'http://YOUR.HOST.IP.ADDRESS:8000/callback'

# Step 1: Get a request token
request_token_url = "https://api.twitter.com/oauth/request_token"
oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET, callback_uri=CALLBACK_URL)

try:
    fetch_response = oauth.fetch_request_token(request_token_url)
except ValueError:
    print("There may have been an issue with the consumer_key or consumer_secret you entered.")
    exit()

resource_owner_key = fetch_response.get("oauth_token")
resource_owner_secret = fetch_response.get("oauth_token_secret")
print("Got OAuth token: %s" % resource_owner_key)

# Step 2: Redirect the user to Twitter for authorization
base_authorization_url = "https://api.twitter.com/oauth/authorize"
authorization_url = oauth.authorization_url(base_authorization_url)
print("Please go here and authorize: %s" % authorization_url)

@app.route('/')
def index():
    return redirect(authorization_url)

# Step 3: Handle the callback from Twitter
@app.route('/callback')
def callback():
    global ACCESS_TOKEN, ACCESS_TOKEN_SECRET

    verifier = request.args.get('oauth_verifier')

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    ACCESS_TOKEN = oauth_tokens["oauth_token"]
    ACCESS_TOKEN_SECRET = oauth_tokens["oauth_token_secret"]

    print("Access Token:", ACCESS_TOKEN)
    print("Access Token Secret:", ACCESS_TOKEN_SECRET)

    # Post a tweet immediately after successful OAuth
    post_tweet()

    return "Authorization successful! You can now close this window."

# Load content plan from file
def load_content_plan():
    with open('content_plan.txt', 'r') as file:
        return file.readlines()

# Save content plan to file
def save_content_plan(content_plan):
    with open('content_plan.txt', 'w') as file:
        file.writelines(content_plan)

# Function to generate a cybersecurity post
def generate_cybersecurity_post(prompt):
    contextual_prompt = (
        f"{prompt}\n\n"
        "Now, generate a new and engaging twitter post 100-200 characters long on the topic stated above. Don't use hashtags, and keep it strictly to 100-200 characters since it's for twitter.."
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a friendly and cool career advisor, who is posting on twitter. You use smiles a bit, and strictly limit your posts to not more than 200 symbols"},
            {"role": "user", "content": contextual_prompt}
        ],
        max_tokens=512,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Function to post a tweet
def post_tweet():
    content_plan = load_content_plan()
    if not content_plan:
        print("Content plan is empty.")
        return

    topic = content_plan.pop(0).strip()
    save_content_plan(content_plan)

    # Generate tweet content using OpenAI
    tweet_content = generate_cybersecurity_post(topic)

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    payload = {"text": tweet_content}
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        print("Failed to post tweet:", response.status_code, response.text)
    else:
        print("Tweet posted successfully!")

# Adjusted function to post a tweet at specified hours
def post_tweet_scheduled():
    # Get current time in CET
    cet = pytz.timezone('CET')
    current_time = datetime.now(cet)

    # Define the hours you want to post the tweets
    posting_hours = list(range(8, 24))  # From 8 AM to 11 PM

    if current_time.hour in posting_hours:
        post_tweet()

# Scheduler to post tweet every hour from 8 AM to 11 PM CET
for hour in range(8, 24):  # From 8 AM to 11 PM
    schedule.every().day.at(f"{hour:02d}:00").do(post_tweet_scheduled)

# Run the Flask app
if __name__ == '__main__':
    # Start the Flask app in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host='YOUR_HOST_IP', port=8000))
    flask_thread.start()

    # Start the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)
