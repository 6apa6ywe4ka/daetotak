from src.config.config import DUPLICATE, SLOW_DOWN, TWEET_URL


def handle_printing_request_details(response, message, text_to_reply, method):
    tweet_url = TWEET_URL.format(message_id=message['id'])
    if response == DUPLICATE:
        print(f"Duplicate {method} to @ {message['created_at']} id: {tweet_url}: {text_to_reply}")
    if response and response != SLOW_DOWN:
        print(f"Successful {method} to @ {message['created_at']} id: {tweet_url}: {text_to_reply}")
    if response == SLOW_DOWN:
        print(f"Too many requests {method} @ {message['created_at']} id: {tweet_url}: {text_to_reply}")
    if not response:
        print(f"Error {method} @ {message['created_at']} id: {tweet_url}: {text_to_reply}")