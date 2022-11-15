import json
import logging
import os
import textwrap

import requests
import tweepy

from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_notes():
    since = datetime.now() - timedelta(minutes=15)

    url = os.getenv("MISSKEY_BASE_URL") + "/api/users/notes"
    resp = requests.post(
        url,
        json={
            "i": os.getenv("MISSKEY_ACCESS_TOKEN"),
            "userId": "97h10bgv4q",
            "includeReplies": False,
            # Multiplying by 1000 because Python counts seconds, but the MissKey
            # API written in JS counts in milliseconds - AAAAAAARGH
            "sinceDate": int(since.timestamp()) * 1000,
            "includeMyRenotes": False,
        },
    )
    return [p["text"] for p in resp.json()]


def post_tweet(client, text):
    if len(text) < 280:
        client.create_tweet(text=text)
    else:
        thread = textwrap.wrap(
            text, 272, break_long_words=False
        )  # 272 allows appending " (xx/yy)"
        previous = None

        for i, block in enumerate(thread):
            tweet_text = block + f" ({i+1}/{len(thread)})"
            if previous:
                previous = client.create_tweet(
                    text=tweet_text, in_reply_to_tweet_id=previous.data["id"]
                )
            else:
                previous = client.create_tweet(text=tweet_text)


def main():
    logger.info("Starting the program")
    bearer_token = os.getenv("BEARER_TOKEN")
    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    logger.info("Getting the MissKey notes posted in the last 1 hour")
    try:
        posts = get_notes()
    except:
        logger.exception("Failed to get notes from Misskey")
        return

    client = tweepy.Client(
        bearer_token, consumer_key, consumer_secret, access_token, access_token_secret
    )
    for i, post in enumerate(posts):
        try:
            logger.info("Posting note (%d/%d)", i + 1, len(posts))
            post_tweet(client, post)
        except Exception:
            logger.exception("Failed to post tweet: %s", post)
            continue

    logger.info("Completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
