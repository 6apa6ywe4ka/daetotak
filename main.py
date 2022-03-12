from src.bot.run import run_bot
from src.config.secret import BEARER_TOKEN
from src.twitter.api import TwitterAPI

twitter = TwitterAPI()

while True and BEARER_TOKEN:
    run_bot(twitter)

