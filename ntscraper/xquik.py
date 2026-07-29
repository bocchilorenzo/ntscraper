import os

import requests


class Xquik:
    DEFAULT_BASE_URL = "https://xquik.com"
    VALID_QUERY_TYPES = ("Latest", "Top")

    def __init__(self, api_key=None, base_url=DEFAULT_BASE_URL, session=None, timeout=10):
        self.api_key = api_key or os.environ.get("XQUIK_API_KEY")
        if not self.api_key:
            raise ValueError("Set api_key or XQUIK_API_KEY before searching with Xquik.")
        self.base_url = base_url.rstrip("/")
        self.session = session if session is not None else requests.Session()
        self.timeout = timeout

    def get_tweets(
        self,
        term,
        mode="term",
        number=20,
        since=None,
        until=None,
        query_type="Latest",
        cursor=None,
    ):
        if query_type not in self.VALID_QUERY_TYPES:
            raise ValueError("Invalid query_type. Use 'Latest' or 'Top'.")
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or not 1 <= number <= 200
        ):
            raise ValueError("number must be an integer between 1 and 200.")

        params = {
            "q": self._query(term, mode),
            "queryType": query_type,
            "limit": number,
        }
        if since:
            params["sinceTime"] = since
        if until:
            params["untilTime"] = until
        if cursor:
            params["cursor"] = cursor

        response = self.session.get(
            f"{self.base_url}/api/v1/x/tweets/search",
            headers={"x-api-key": self.api_key},
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "tweets": [self._tweet(tweet) for tweet in payload.get("tweets", [])],
            "threads": [],
            "has_next_page": bool(payload.get("has_next_page")),
            "next_cursor": payload.get("next_cursor"),
            "raw": payload,
        }

    def _query(self, term, mode):
        if mode == "term":
            return term
        if mode == "hashtag":
            return "#" + term.lstrip("#")
        if mode == "user":
            return "from:" + term.lstrip("@")
        raise ValueError("Invalid mode. Use 'term', 'hashtag', or 'user'.")

    def _tweet(self, tweet):
        author = tweet.get("author") or {}
        tweet_id = str(tweet.get("id", ""))
        username = author.get("username") or ""
        return {
            "id": tweet_id,
            "link": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else "",
            "text": tweet.get("text") or "",
            "user": {
                "name": author.get("name") or "",
                "username": username,
                "profile_id": str(author.get("id", "")),
                "avatar": author.get("profilePicture") or "",
            },
            "date": tweet.get("createdAt") or "",
            "is-retweet": False,
            "is-pinned": False,
            "external-link": "",
            "replying-to": [],
            "quoted-post": {},
            "stats": {
                "comments": self._int_value(tweet.get("replyCount")),
                "retweets": self._int_value(tweet.get("retweetCount")),
                "quotes": self._int_value(tweet.get("quoteCount")),
                "likes": self._int_value(tweet.get("likeCount")),
            },
            "pictures": [],
            "videos": [],
            "gifs": [],
            "raw": tweet,
        }

    def _int_value(self, value):
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0
