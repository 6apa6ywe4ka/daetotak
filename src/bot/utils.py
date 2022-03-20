from datetime import datetime

from src.config.config import DUPLICATE, SLOW_DOWN, TWEET_URL


def handle_printing_request_details(response, message, method):
    tweet_url = TWEET_URL.format(message_id=message['id'])
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not response:
        print(f"{timestamp} OK {method} to {tweet_url}")
    elif response == SLOW_DOWN:
        print(f"{timestamp} ERROR Too many requests {method} {tweet_url}")
    elif response == DUPLICATE:
        print(f"{timestamp} ERROR Duplicate {method} to : {tweet_url}")
    else:
        print(f"{timestamp} ERROR {method} : {tweet_url}")


def request_failed(response):
    if response.status_code in [403] and \
            response.json().get("detail", "") == "You are not allowed to create a Tweet with duplicate content.":
        return DUPLICATE
    if response.status_code in [429]:
        return SLOW_DOWN
    return response.status_code not in [200, 201]

