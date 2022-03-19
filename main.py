from time import sleep

from src.bot.run import queue_requests, process_queue, init_bot, fetch_messages
from src.config.config import REQUEST_QUEUE_SIZE
from src.config.secret import BEARER_TOKEN
from src.twitter.api import TwitterAPI

twitter = TwitterAPI()

init_bot(twitter)

while True and BEARER_TOKEN:
    if len(twitter.requests_queue) < REQUEST_QUEUE_SIZE:
        messages = fetch_messages(twitter)
        queue_requests(twitter=twitter, messages=messages)
    process_queue(twitter)
    sleep(1)

