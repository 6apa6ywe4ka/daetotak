from src.config.config import DUPLICATE, SLOW_DOWN, TWEET_URL


def handle_printing_request_details(response, message, text_to_reply, method):
    tweet_url = TWEET_URL.format(message_id=message['id'])

    if not response:
        print(f"Successful {method} to {tweet_url}: {text_to_reply}")
    elif response == SLOW_DOWN:
        print(f"Too many requests {method} {tweet_url}: {text_to_reply}")
    elif response == DUPLICATE:
        print(f"Duplicate {method} to : {tweet_url}: {text_to_reply}")
    else:
        print(f"Error {method} : {tweet_url}: {text_to_reply}")


def request_failed(response):
    if response.status_code in [403] and \
            response.json().get("detail", "") == "You are not allowed to create a Tweet with duplicate content.":
        return DUPLICATE
    if response.status_code in [429]:
        return SLOW_DOWN
    return response.status_code not in [200, 201]

