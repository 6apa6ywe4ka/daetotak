import json
import uuid
from datetime import datetime, timedelta
from urllib import parse
from urllib.parse import urljoin

import requests as requests
from requests_oauthlib import OAuth1

from src.config.config import TWITTER_URL, SEARCH_TWEETS_ENDPOINT, TEXT_TO_FIND, DAYS_TO_FIND, \
    HOURS_TO_FIND, LIKE_TWEET_ENDPOINT, REPLY_TWEET_ENDPOINT, QUOTE_TWEET_ENDPOINT, TEXT_TO_REPLY, \
    FAVORITES_ENDPOINT, ME_ENDPOINT, TWEETS_ENDPOINT, TWEET_ENDPOINT, INTERVAL_TO_SEARCH_HOURS, DUPLICATE, SLOW_DOWN
from src.config.secret import OUATH_CONSUMER_SECRET, OAUTH_SERVER_KEY, OAUTH_SERVER_SECRET, BEARER_TOKEN, \
    OAUTH_CONSUMER_KEY


class TwitterAPI(object):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    oauth = None
    user_id = None

    def __init__(self):
        self.set_oauth_v1_token()

    def set_oauth_v1_token(self):
        self.oauth = OAuth1(
            client_key=OAUTH_CONSUMER_KEY, client_secret=OUATH_CONSUMER_SECRET,
            resource_owner_key=OAUTH_SERVER_KEY,
            resource_owner_secret=OAUTH_SERVER_SECRET
        )
        self.user_id = self.oauth.client.resource_owner_key.split('-')[0]
        return self.oauth

    def me(self):
        url = urljoin(TWITTER_URL, ME_ENDPOINT)
        response = requests.get(url=url, auth=self.oauth)
        return response.json()["data"]

    def tweet(self, tweet_id):
        url = urljoin(TWITTER_URL, TWEET_ENDPOINT.format(tweet_id=tweet_id))
        params = {"tweet.fields": "author_id,created_at"}
        response = requests.get(url=url, auth=self.oauth, params=params)
        return response.json()["data"]

    def last_tweets(self):
        url = urljoin(TWITTER_URL, TWEETS_ENDPOINT.format(user_id=self.user_id))
        params = {"tweet.fields": "author_id,created_at", "expansions": "referenced_tweets.id"}
        response = requests.get(url=url, auth=self.oauth, params=params)
        return response.json()["data"]

    def favorites(self):
        # TODO: Possible broken and unused
        url = urljoin(TWITTER_URL, FAVORITES_ENDPOINT)
        response = requests.get(url=url, auth=self.oauth)
        return response.json()["data"]

    def search_tweets(self, start_time=None, end_time=None):
        url = urljoin(TWITTER_URL, SEARCH_TWEETS_ENDPOINT)

        if start_time is None:
            start_time = (
                    datetime.now() - timedelta(days=DAYS_TO_FIND, hours=HOURS_TO_FIND))
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time is None:
            end_time = (datetime.strptime(
                start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(
                hours=INTERVAL_TO_SEARCH_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"query": TEXT_TO_FIND,
                  "start_time": start_time,
                  "end_time": end_time,
                  "tweet.fields": "author_id,created_at",
                  "user.fields": "username"}
        response = requests.get(url=url, headers=self.headers, params=params)
        error_locator = "\'start_time\' must be on or after "
        if response.status_code in [400] and error_locator in response.text:
            start_time = response.text.split(error_locator)[1].split("Z")[0] + ":59Z"
            end_time = (datetime.strptime(
                start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(
                hours=INTERVAL_TO_SEARCH_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
            params = {"query": TEXT_TO_FIND,
                      "start_time": start_time,
                      "end_time": end_time,
                      "tweet.fields": "author_id,created_at",
                      "user.fields": "created_at"}
            response = requests.get(url=url, headers=self.headers, params=params)
        return response.json()["data"]

    @staticmethod
    def handle_post_action(response):
        if response.status_code in [403] and response.json().get("detail", "") == "You are not allowed to create a Tweet with duplicate content.":
            return DUPLICATE
        if response.status_code in [429]:
            return SLOW_DOWN
        return response.status_code in [200, 201]

    def reply(self, message):
        url = urljoin(TWITTER_URL, REPLY_TWEET_ENDPOINT.format(message))
        data = {"reply": {"in_reply_to_tweet_id": message["id"]},
                "text": TEXT_TO_REPLY}
        response = requests.post(url=url, json=data, auth=self.oauth)
        return self.handle_post_action(response=response)

    def quote(self, message):
        url = urljoin(TWITTER_URL, QUOTE_TWEET_ENDPOINT.format(message))
        data = {"quote_tweet_id": message["id"],
                "text": TEXT_TO_REPLY}
        response = requests.post(url=url, json=data, auth=self.oauth)
        return self.handle_post_action(response=response)

    def like(self, message):
        url = urljoin(TWITTER_URL,
                      LIKE_TWEET_ENDPOINT.format(partition=self.oauth.client.resource_owner_key.split('-')[0]))
        data = {"tweet_id": message["id"]}
        response = requests.post(url=url, json=data, auth=self.oauth)
        return self.handle_post_action(response=response)
