from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests as requests
from requests_oauthlib import OAuth1

from src.bot.utils import request_failed
from src.config.config import TWITTER_URL, SEARCH_TWEETS_ENDPOINT, TEXT_TO_FIND, LIKE_TWEET_ENDPOINT, \
    REPLY_TWEET_ENDPOINT, QUOTE_TWEET_ENDPOINT, TEXT_TO_REPLY, \
    FAVORITES_ENDPOINT, ME_ENDPOINT, TWEETS_ENDPOINT, TWEET_ENDPOINT, \
    LIKE_TIMEDELTA, QUOTE_TIMEDELTA, REPLY_TIMEDELTA, LIKE_SECONDS_TIMEOUT, REPLY_SECONDS_TIMEOUT
from src.config.secret import OUATH_CONSUMER_SECRET, OAUTH_SERVER_KEY, OAUTH_SERVER_SECRET, BEARER_TOKEN, \
    OAUTH_CONSUMER_KEY


class Request:
    http_method = None
    headers = None
    auth = None
    params = None
    json = None
    time_sent = None
    time_to_send = None
    message = None
    method_name = None

    def __init__(
            self,
            method,
            url,
            headers=None,
            auth=None,
            params=None,
            json=None,
            time_to_send=None,
            message=None,
            method_name=None):
        self.http_method = method
        self.method_name = method_name
        self.url = url
        self.headers = headers
        self.auth = auth
        self.params = params
        self.json = json
        self.time_to_send = time_to_send
        self.message = message


class TwitterAPI(object):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    oauth = None
    user_id = None
    API_RPS = {}

    start_time = None
    end_time = None

    requests_queue = []
    requests_sent = []

    last_like_sent = None
    last_reply_sent = None

    next_token = None

    last_fetched = None

    tweet_processed = []

    @property
    def ready_to_like(self):
        if self.last_like_sent is None:
            return True
        return self.last_like_sent + \
            timedelta(seconds=LIKE_SECONDS_TIMEOUT) < datetime.now()

    @property
    def ready_to_reply(self):
        if self.last_reply_sent is None:
            return True
        return self.last_reply_sent + \
            timedelta(seconds=REPLY_SECONDS_TIMEOUT) < datetime.now()

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

    def queue_request(
            self,
            method,
            url,
            headers=None,
            auth=None,
            params=None,
            json=None):
        self.requests_queue.append(Request(method=method,
                                           url=url,
                                           headers=headers,
                                           auth=auth,
                                           params=params,
                                           json=json))

    def queue_GET_request(
            self,
            url,
            method_name,
            headers=None,
            auth=None,
            params=None,
            json=None,
            time_to_send=None,
            message=None):
        self.requests_queue.append(Request(method=requests.get,
                                           url=url,
                                           headers=headers,
                                           auth=auth,
                                           params=params,
                                           json=json,
                                           time_to_send=time_to_send,
                                           message=message,
                                           method_name=method_name))

    def queue_POST_request(
            self,
            url,
            method_name,
            headers=None,
            auth=None,
            params=None,
            json=None,
            time_to_send=None,
            message=None):
        self.requests_queue.append(Request(method=requests.post,
                                           url=url,
                                           headers=headers,
                                           auth=auth,
                                           params=params,
                                           json=json,
                                           time_to_send=time_to_send,
                                           message=message,
                                           method_name=method_name))

    def queue_PUT_request(
            self,
            url,
            method_name,
            headers=None,
            auth=None,
            params=None,
            json=None,
            time_to_send=None,
            message=None):
        self.requests_queue.append(Request(method=requests.put,
                                           url=url,
                                           headers=headers,
                                           auth=auth,
                                           params=params,
                                           json=json,
                                           time_to_send=time_to_send,
                                           message=message,
                                           method_name=method_name))

    def me(self):
        url = urljoin(TWITTER_URL, ME_ENDPOINT)
        self.queue_GET_request(url=url, auth=self.oauth)
        response = requests.get(url=url, auth=self.oauth)
        self.API_RPS.setdefault(self.me.__name__, [])
        self.API_RPS[self.me.__name__].append(datetime.now())
        return response.json()["data"]

    def tweet(self, tweet_id):
        url = urljoin(TWITTER_URL, TWEET_ENDPOINT.format(tweet_id=tweet_id))
        params = {"tweet.fields": "author_id,created_at"}
        response = requests.get(url=url, auth=self.oauth, params=params)
        self.API_RPS.setdefault(self.tweet.__name__, [])
        self.API_RPS[self.tweet.__name__].append(datetime.now())
        return response.json()["data"]

    def last_tweets(self):
        url = urljoin(
            TWITTER_URL,
            TWEETS_ENDPOINT.format(
                user_id=self.user_id))
        params = {
            "tweet.fields": "author_id,created_at",
            "expansions": "referenced_tweets.id"}
        response = requests.get(url=url, auth=self.oauth, params=params)
        self.API_RPS.setdefault(self.last_tweets.__name__, [])
        self.API_RPS[self.last_tweets.__name__].append(datetime.now())
        return response.json()["data"]

    def favorites(self):
        # TODO: Possible broken and unused
        url = urljoin(TWITTER_URL, FAVORITES_ENDPOINT)
        response = requests.get(url=url, auth=self.oauth)
        self.API_RPS.setdefault(self.favorites.__name__, [])
        self.API_RPS[self.favorites.__name__].append(datetime.now())
        return response.json()["data"]

    def search_tweets(self, start_time=None, end_time=None):
        url = urljoin(TWITTER_URL, SEARCH_TWEETS_ENDPOINT)

        params = {"query": TEXT_TO_FIND,
                  "tweet.fields": "author_id,created_at",
                  "user.fields": "username"}
        if start_time is not None:
            params.update(
                {"start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        if end_time is not None:
            params.update(
                {"end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        if self.next_token is not None:
            params.update({"next_token": self.next_token})
        response = requests.get(url=url, headers=self.headers, params=params)
        self.API_RPS.setdefault(self.search_tweets.__name__, [])
        self.API_RPS[self.search_tweets.__name__].append(datetime.now())

        return response

    def reply(self, message):
        url = urljoin(TWITTER_URL, REPLY_TWEET_ENDPOINT.format(message))
        data = {"reply": {"in_reply_to_tweet_id": message["id"]},
                "text": TEXT_TO_REPLY}
        response = requests.post(url=url, json=data, auth=self.oauth)
        self.API_RPS.setdefault(self.reply.__name__, [])
        self.API_RPS[self.reply.__name__].append(datetime.now())
        return request_failed(response=response)

    def queue_reply(self, message):
        url = urljoin(TWITTER_URL, REPLY_TWEET_ENDPOINT.format(message))
        data = {"reply": {"in_reply_to_tweet_id": message["id"]},
                "text": TEXT_TO_REPLY}
        time_to_send = datetime.now() + timedelta(seconds=REPLY_TIMEDELTA)
        self.queue_POST_request(
            url=url,
            json=data,
            auth=self.oauth,
            time_to_send=time_to_send,
            message=message,
            method_name="reply")

    def quote(self, message):
        url = urljoin(TWITTER_URL, QUOTE_TWEET_ENDPOINT.format(message))
        data = {"quote_tweet_id": message["id"],
                "text": TEXT_TO_REPLY}
        response = requests.post(url=url, json=data, auth=self.oauth)
        self.API_RPS.setdefault(self.quote.__name__, [])
        self.API_RPS[self.quote.__name__].append(datetime.now())
        return request_failed(response=response)

    def queue_quote(self, message):
        url = urljoin(TWITTER_URL, QUOTE_TWEET_ENDPOINT.format(message))
        data = {"quote_tweet_id": message["id"],
                "text": TEXT_TO_REPLY}
        time_to_send = datetime.now() + timedelta(seconds=QUOTE_TIMEDELTA)
        self.queue_POST_request(
            url=url,
            json=data,
            auth=self.oauth,
            time_to_send=time_to_send,
            message=message,
            method_name="quote")

    def like(self, message):
        url = urljoin(TWITTER_URL, LIKE_TWEET_ENDPOINT.format(
            partition=self.oauth.client.resource_owner_key.split('-')[0]))
        data = {"tweet_id": message["id"]}
        response = requests.post(url=url, json=data, auth=self.oauth)
        self.API_RPS.setdefault(self.like.__name__, [])
        self.API_RPS[self.like.__name__].append(datetime.now())
        return request_failed(response=response)

    def queue_like(self, message):
        url = urljoin(TWITTER_URL, LIKE_TWEET_ENDPOINT.format(
            partition=self.oauth.client.resource_owner_key.split('-')[0]))
        data = {"tweet_id": message["id"]}
        time_to_send = datetime.now() + timedelta(seconds=LIKE_TIMEDELTA)
        self.queue_POST_request(
            url=url,
            json=data,
            auth=self.oauth,
            time_to_send=time_to_send,
            message=message,
            method_name="like")
