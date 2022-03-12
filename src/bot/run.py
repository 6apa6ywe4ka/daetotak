from datetime import datetime, timedelta
from time import sleep

from src.bot.utils import handle_printing_request_details
from src.config.config import TEXT_TO_REPLY, INTERVAL_TO_SEARCH_HOURS, INITIAL_TWEET, SLOW_DOWN, DUPLICATE, \
    WORKER_TIMEOUT, REST_START_TIMEOUT


def run_bot(twitter):
    last_tweets = twitter.last_tweets()
    start_time = None
    end_time = None
    if len(last_tweets) and INITIAL_TWEET == 2:
        for tweet in last_tweets:
            referenced_tweets = tweet.get("referenced_tweets", [])
            if len(referenced_tweets):
                last_tweet_id = referenced_tweets[0].get("id", None)
                tweet_info = twitter.tweet(tweet_id=last_tweet_id)
                start_time = tweet_info["created_at"]
                end_time = (datetime.strptime(
                    start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(
                    hours=INTERVAL_TO_SEARCH_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
                break
    elif INITIAL_TWEET == 1:
        pass
    messages = twitter.search_tweets(start_time=start_time, end_time=end_time)
    for message in messages:
        replied = twitter.reply(message)
        if replied == SLOW_DOWN:
            time_to_sleep = 1
            while replied == SLOW_DOWN:
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                replied = twitter.reply(message)
        handle_printing_request_details(response=replied, message=message, text_to_reply=TEXT_TO_REPLY, method="reply")

        liked = twitter.like(message)
        if liked == SLOW_DOWN:
            time_to_sleep = REST_START_TIMEOUT
            while liked == SLOW_DOWN:
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                liked = twitter.like(message)
        handle_printing_request_details(response=liked, message=message, text_to_reply=TEXT_TO_REPLY, method="reply")

        quoted = twitter.quote(message)
        if quoted == SLOW_DOWN:
            time_to_sleep = 5
            while quoted == SLOW_DOWN:
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                quoted = twitter.quote(message)
        handle_printing_request_details(response=quoted, message=message, text_to_reply=TEXT_TO_REPLY, method="reply")

        sleep(WORKER_TIMEOUT)
