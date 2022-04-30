from datetime import datetime, timedelta

from src.bot.utils import handle_printing_request_details, request_failed
from src.config.config import TEXT_TO_REPLY, INTERVAL_TO_SEARCH_HOURS, INITIAL_TWEET, \
    WORKER_TIMEOUT, DAYS_BEFORE_NOW, INITIAL_TWEET_OPTIONS, WORK_MODE, WORK_MODES


def init_bot(twitter):
    if WORK_MODE == WORK_MODES.get(1):
        if INITIAL_TWEET == INITIAL_TWEET_OPTIONS.get(2):
            last_tweets = twitter.last_tweets()
            for tweet in last_tweets:
                referenced_tweets = tweet.get("referenced_tweets", [])
                if len(referenced_tweets):
                    last_tweet_id = referenced_tweets[0].get("id", None)
                    tweet_info = twitter.tweet(tweet_id=last_tweet_id)
                    twitter.API_RPS["TWEET"].append(datetime.now())
                    twitter.start_time = (
                        datetime.strptime(
                            tweet_info["created_at"],
                            "%Y-%m-%dT%H:%M:%S.%fZ"))
                    twitter.end_time = twitter.start_time + \
                        timedelta(hours=INTERVAL_TO_SEARCH_HOURS)
        elif INITIAL_TWEET == INITIAL_TWEET_OPTIONS.get(1):
            twitter.start_time = datetime.now() - timedelta(days=DAYS_BEFORE_NOW)
            twitter.end_time = twitter.start_time + \
                timedelta(hours=INTERVAL_TO_SEARCH_HOURS)
    elif WORK_MODE == WORK_MODES.get(2):
        twitter.start_time = datetime.utcnow() - timedelta(minutes=30)
        twitter.end_time = datetime.utcnow() - timedelta(minutes=1)


def fetch_messages(twitter):
    if WORK_MODE == WORK_MODES.get(2):
        if twitter.last_fetched is not None and twitter.last_fetched + \
                timedelta(minutes=WORKER_TIMEOUT) > datetime.now():
            return []
        else:
            twitter.start_time = datetime.utcnow() - timedelta(minutes=30)
            twitter.end_time = datetime.utcnow() - timedelta(minutes=1)

    response = twitter.search_tweets(
        start_time=twitter.start_time,
        end_time=twitter.end_time)
    twitter.last_fetched = datetime.now()

    error_locator = "\'start_time\' must be on or after "
    if response.status_code in [400] and error_locator in response.text:
        twitter.start_time = datetime.strptime(response.text.split(error_locator)[1].split(
            "Z")[0] + ":59Z", "%Y-%m-%dT%H:%M:%SZ") + timedelta(minutes=10)
        twitter.end_time = twitter.start_time + \
            timedelta(hours=INTERVAL_TO_SEARCH_HOURS)
        response = twitter.search_tweets(
            start_time=twitter.start_time,
            end_time=twitter.end_time)

    if response.json().get("meta", {}).get("next_token"):
        twitter.next_token = response.json().get("meta", {}).get("next_token")
    else:
        twitter.next_token = None
        twitter.start_time = twitter.end_time
        twitter.end_time = twitter.start_time + \
            timedelta(hours=INTERVAL_TO_SEARCH_HOURS)

    messages = response.json().get("data", [])
    messages_filtered = filter(
        lambda x: not x["text"].startswith("RT @"), messages)
    return messages_filtered


def queue_requests(twitter, messages):
    for message in messages:
        if (not message["id"] in twitter.tweet_processed) and (
                not message["id"] in [i.message["id"] for i in twitter.requests_queue]):
            twitter.queue_reply(message)
            twitter.queue_like(message)
            twitter.queue_quote(message)


def is_request_allowed(twitter, request):
    allowed = False
    if request.method_name == "like":
        allowed = twitter.ready_to_like
    elif request.method_name in ["quote", "reply"]:
        allowed = twitter.ready_to_reply
    return allowed


def is_any_request_allowed(twitter):
    return twitter.ready_to_like or twitter.ready_to_reply


def process_queue(twitter):
    # chunked, twitter.requests_queue = twitter.requests_queue[:10], twitter.requests_queue[10:]
    if is_any_request_allowed(twitter):
        for request in twitter.requests_queue:
            if (request.method_name == "like" and twitter.ready_to_like) or (
                    request.method_name in ["quote", "reply"] and twitter.ready_to_reply):
                response = request.http_method(
                    url=request.url,
                    json=request.json,
                    auth=request.auth,
                    headers=request.headers,
                    params=request.params)
                if request.message["id"] not in twitter.tweet_processed:
                    twitter.tweet_processed.append(request.message["id"])
                request_fail = request_failed(response)
                handle_printing_request_details(
                    response=request_fail,
                    message=request.message,
                    method=request.method_name)
                twitter.requests_queue.remove(request)
                request.time_sent = datetime.now()
                twitter.requests_sent.append(request)
                if not request_fail:
                    if request.method_name == "like":
                        twitter.last_like_sent = datetime.now()
                    elif request.method_name in ["quote", "reply"]:
                        twitter.last_reply_sent = datetime.now()
                    break
