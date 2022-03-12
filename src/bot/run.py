from datetime import datetime, timedelta
from time import sleep

from src.config.config import TEXT_TO_REPLY, INTERVAL_TO_SEARCH_HOURS, INITIAL_TWEET


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
        if replied == "SLOW DOWN":
            time_to_sleep = 1
            while replied == "SLOW DOWN":
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                replied = twitter.reply(message)
        if replied and replied != "SLOW DOWN":
            print(f"Replied to @ {message['created_at']} id: {message['id']}: {TEXT_TO_REPLY}")
        if not replied or replied == "SLOW DOWN":
            print(f"Error replying @ {message['created_at']} id: {message['id']}: {TEXT_TO_REPLY}")

        liked = twitter.like(message)
        if liked == "SLOW DOWN":
            time_to_sleep = 1
            while liked == "SLOW DOWN":
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                liked = twitter.like(message)
        if liked and liked != "SLOW DOWN":
            print(f"Liked @ {message['created_at']} id: {message['id']}")
        if not liked or liked == "SLOW DOWN":
            print(f"Can't like @ {message['created_at']} id: {message['id']}: {TEXT_TO_REPLY}")

        quoted = twitter.quote(message)
        if quoted == "SLOW DOWN":
            time_to_sleep = 5
            while quoted == "SLOW DOWN":
                print(f"Slowing down. Waiting for {time_to_sleep}")
                sleep(time_to_sleep)
                time_to_sleep *= 2
                quoted = twitter.quote(message)
        if quoted and quoted != "SLOW DOWN":
            print(f"Quoted @ {message['created_at']} id: {message['id']}: {TEXT_TO_REPLY}")
        if not quoted or quoted == "SLOW DOWN":
            print(f"Can't quote @ {message['created_at']} id: {message['id']}: {TEXT_TO_REPLY}")

        sleep(5)
