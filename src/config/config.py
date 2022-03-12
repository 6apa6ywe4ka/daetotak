import sys
from urllib.parse import urljoin

API_KEY = ""
API_SECRET_KEY = ""

TEXT_TO_FIND = "русні пизда"
TEXT_TO_REPLY = "да ето так"

DAYS_TO_FIND = 120
HOURS_TO_FIND = 3
INTERVAL_TO_SEARCH_HOURS = 24
INITIAL_TWEET = {1: "Get by config",
                 2: "Resume last session"}.get(2)

AUTH_CALLBACK_URL = "https://twitter.com"
TWITTER_URL = "https://api.twitter.com"
API_VERSION = 2
SEARCH_TWEETS_ENDPOINT = f"{API_VERSION}/tweets/search/recent"
LIKE_TWEET_ENDPOINT = f"{API_VERSION}/users/{{partition}}/likes"
ME_ENDPOINT = f"{API_VERSION}/users/me"
TWEETS_ENDPOINT = f"{API_VERSION}/users/{{user_id}}/tweets"
TWEET_ENDPOINT = f"{API_VERSION}/tweets/{{tweet_id}}"
FAVORITES_ENDPOINT = f"{API_VERSION}/users/:id/liked_tweets"
REPLY_TWEET_ENDPOINT = f"{API_VERSION}/tweets"
QUOTE_TWEET_ENDPOINT = f"{API_VERSION}/tweets"
REQUEST_TOKEN_ENDPOINT = "oauth/request_token"
