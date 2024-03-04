import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import unquote
from time import sleep
from base64 import b64decode
from random import uniform
from re import match, sub
from datetime import datetime
import logging
from logging.handlers import QueueHandler
from multiprocessing import Pool, Queue, cpu_count
from sys import stdout
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[logging.StreamHandler(stdout)],
)

log_queue = Queue()
log_handler = QueueHandler(log_queue)
root_logger = logging.getLogger()
root_logger.addHandler(log_handler)

valid_filters = [
    "nativeretweets",
    "media",
    "videos",
    "news",
    "verified",
    "native_video",
    "replies",
    "links",
    "images",
    "safe",
    "quote",
    "pro_video",
]


class Nitter:
    def __init__(self, instances=None, log_level=1, skip_instance_check=False):
        """
        Nitter scraper
        :param instances: accepts a list of instances or a single instance in this format: "https://{host}:{port}", e.g. "http://localhost:8080
        :param log_level: logging level
        :param skip_instance_check: True if the health check of all instances and the instance change during execution should be skipped
        """
        if instances:
            # check instances type is list or str
            if isinstance(instances, list):
                self.instances = instances
            elif isinstance(instances, str):
                self.instances = [instances]
            else:
                raise ValueError("Instances type not supported, only list and str are supported")
        else:
            self.instances = self._get_instances()
        if self.instances is None:
            raise ValueError("Could not fetch instances")
        self.working_instances = []
        self.skip_instance_check = skip_instance_check
        if skip_instance_check:
            self.working_instances = self.instances
        else:
            self._test_all_instances("/x", no_print=True)
        if log_level == 0:
            log_level = logging.WARNING
        elif log_level == 1:
            log_level = logging.INFO
        elif log_level:
            raise ValueError("Invalid log level")

        logger = logging.getLogger()
        logger.setLevel(log_level)

        self.retry_count = 0
        self.cooldown_count = 0
        self.session_reset = False
        self.instance = ""
        self.r = None

    def _initialize_session(self, instance):
        """
        Initialize the requests session
        """
        if instance is None:
            if self.skip_instance_check:
                raise ValueError("No instance specified and instance check skipped")
            self.instance = self.get_random_instance()
            logging.info(
                f"No instance specified, using random instance {self.instance}"
            )
        else:
            self.instance = instance
        self.r = requests.Session()
        self.r.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
                "Host": self.instance.split("://")[1],
            }
        )

    def _is_instance_encrypted(self):
        """
        Check if the current instance uses encrypted media

        :return: True if encrypted, False otherwise
        """
        soup = self._get_page("/x")

        if soup is None:
            raise ValueError("Invalid instance")

        if (
            soup.find("a", class_="profile-card-avatar").find("img")
            and "/enc/"
            in soup.find("a", class_="profile-card-avatar").find("img")["src"]
        ):
            return True
        else:
            return False

    def _get_instances(self):
        """
        Fetch the list of clear web Nitter instances.

        :return: list of Nitter instances, or None if lookup failed
        """
        r = requests.get("https://raw.githubusercontent.com/libredirect/instances/main/data.json")
        if r.ok:
            return r.json()["nitter"]["clearnet"]
        else:
            return None

    def _test_all_instances(self, endpoint, no_print=False):
        """
        Test all Nitter instances when a high number of retries is detected

        :param endpoint: endpoint to use
        :param no_print: True if no output should be printed
        """
        if not no_print:
            print("High number of retries detected. Testing all instances...")
        working_instances = []

        for instance in tqdm(self.instances, desc="Testing instances"):
            self._initialize_session(instance)
            req_session = requests.Session()
            req_session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
                }
            )
            try:
                r = req_session.get(
                    instance + endpoint,
                    cookies={"hlsPlayback": "on"},
                    timeout=10,
                )
                if r.ok:
                    soup = BeautifulSoup(r.text, "lxml")
                    if soup is not None and len(
                        soup.find_all("div", class_="timeline-item")
                    ):
                        working_instances.append(instance)
            except:
                pass
        if not no_print:
            print("New working instances:", ", ".join(working_instances))
        self.working_instances = working_instances

    def _get_new_instance(self, message):
        instance = self.get_random_instance()
        logging.warning(f"{message}. Trying {instance}")
        return instance

    def _check_error_page(self, soup):
        """
        Check if the page contains an error. If so, print the error and return None

        :param soup: page to check
        :return: None if error is found, soup otherwise
        """
        if not soup.find(
            lambda tag: tag.name == "div"
            and (
                tag.get("class") == ["timeline-item"]
                or tag.get("class") == ["timeline-item", "thread"]
            )
        ):
            if soup.find("div", class_="error-panel"):
                message = (
                    f"Fetching error: "
                    + soup.find("div", class_="error-panel").find("span").text.strip()
                )
            else:
                if soup.find("div", class_="timeline-header timeline-protected"):
                    message = "Account is protected"
                else:
                    message = f"Empty page on {self.instance}"
            logging.warning(message)
            soup = None
        return soup

    def _get_page(self, endpoint, max_retries=5):
        """
        Download page from Nitter instance

        :param endpoint: endpoint to use
        :param max_retries: max number of retries, default 5
        :return: page content, or None if max retries reached
        """
        keep_trying = True
        soup = None
        while keep_trying and (self.retry_count < max_retries):
            try:
                r = self.r.get(
                    self.instance + endpoint,
                    cookies={"hlsPlayback": "on", "infiniteScroll": ""},
                    timeout=10,
                )
            except:
                if self.retry_count == max_retries // 2:
                    if not self.skip_instance_check:
                        self._test_all_instances(endpoint)
                        if not self.working_instances:
                            logging.warning(
                                "All instances are unreachable. Check your request and try again."
                            )
                            return None
                if not self.skip_instance_check:
                    self._initialize_session(
                        instance=self._get_new_instance(f"{self.instance} unreachable")
                    )
                self.retry_count += 1
                self.cooldown_count = 0
                self.session_reset = True
                sleep(1)
                continue
            soup = BeautifulSoup(r.text, "lxml")
            if r.ok:
                self.session_reset = False
                soup = self._check_error_page(soup)
                keep_trying = False
            else:
                soup = self._check_error_page(soup)
                if soup is None:
                    keep_trying = False
                else:
                    if self.retry_count == max_retries // 2:
                        if not self.skip_instance_check:
                            self._test_all_instances(endpoint)
                            if not self.working_instances:
                                logging.warning(
                                    "All instances are unreachable. Check your request and try again."
                                )
                                soup = None
                                keep_trying = False
                        else:
                            self.retry_count += 1
                    else:
                        if "cursor" in endpoint:
                            if not self.session_reset:
                                logging.warning(
                                    "Cooldown reached, trying again in 20 seconds"
                                )
                                self.cooldown_count += 1
                                sleep(20)
                            if self.cooldown_count >= 5 and not self.session_reset:
                                if not self.skip_instance_check:
                                    self._initialize_session()
                                else:
                                    self._initialize_session(self.instance)
                                self.session_reset = True
                                self.cooldown_count = 0
                            elif self.session_reset:
                                if not self.skip_instance_check:
                                    self._initialize_session(
                                        self._get_new_instance(
                                            f"Error fetching {self.instance}"
                                        )
                                    )
                        else:
                            self.cooldown_count = 0
                            if not self.skip_instance_check:
                                self._initialize_session(
                                    self._get_new_instance(
                                        f"Error fetching {self.instance}"
                                    )
                                )
                        self.retry_count += 1
            sleep(2)

        if self.retry_count >= max_retries:
            logging.warning("Max retries reached. Check your request and try again.")
            soup = None
        self.retry_count = 0

        return soup

    def _get_quoted_media(self, quoted_tweet, is_encrypted):
        """
        Extract media from a quoted tweet

        :param quoted_tweet: tweet to extract media from
        :param is_encrypted: True if instance uses encrypted media
        :return: lists of images, videos and gifs, or empty lists if no media is found
        """
        quoted_pictures, quoted_videos, quoted_gifs = [], [], []
        if quoted_tweet.find("div", class_="attachments"):
            if is_encrypted:
                quoted_pictures = [
                    "https://pbs.twimg.com/"
                    + b64decode(img["src"].split("/")[-1].encode("utf-8"))
                    .decode("utf-8")
                    .split("?")[0]
                    for img in quoted_tweet.find("div", class_="attachments").find_all(
                        "img"
                    )
                ]
                quoted_videos = [
                    b64decode(video["data-url"].split("/")[-1].encode("utf-8")).decode(
                        "utf-8"
                    )
                    if "data-url" in video.attrs
                    else video.find("source")["src"]
                    for video in quoted_tweet.find(
                        "div", class_="attachments"
                    ).find_all("video", class_="")
                ]
                quoted_gifs = [
                    "https://"
                    + b64decode(
                        gif.source["src"].split("/")[-1].encode("utf-8")
                    ).decode("utf-8")
                    for gif in quoted_tweet.find("div", class_="attachments").find_all(
                        "video", class_="gif"
                    )
                ]
            else:
                quoted_pictures = [
                    "https://pbs.twimg.com"
                    + unquote(img["src"].split("/pic")[1]).split("?")[0]
                    for img in quoted_tweet.find("div", class_="attachments").find_all(
                        "img"
                    )
                ]
                quoted_videos = [
                    unquote("https" + video["data-url"].split("https")[1])
                    if "data-url" in video.attrs
                    else unquote(video.find("source")["src"])
                    for video in quoted_tweet.find(
                        "div", class_="attachments"
                    ).find_all("video", class_="")
                ]
                quoted_gifs = [
                    unquote("https://" + gif.source["src"].split("/pic/")[1])
                    for gif in quoted_tweet.find("div", class_="attachments").find_all(
                        "video", class_="gif"
                    )
                ]
        return quoted_pictures, quoted_videos, quoted_gifs

    def _get_tweet_media(self, tweet, is_encrypted):
        """
        Extract media from a tweet

        :param tweet: tweet to extract media from
        :param is_encrypted: True if instance uses encrypted media
        :return: lists of images, videos and gifs, or empty lists if no media is found
        """
        pictures, videos, gifs = [], [], []
        if tweet.find("div", class_="tweet-body").find(
            "div", class_="attachments", recursive=False
        ):
            if is_encrypted:
                pictures = [
                    "https://pbs.twimg.com/"
                    + b64decode(img["src"].split("/")[-1].encode("utf-8"))
                    .decode("utf-8")
                    .split("?")[0]
                    for img in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("img")
                ]
                videos = [
                    b64decode(video["data-url"].split("/")[-1].encode("utf-8")).decode(
                        "utf-8"
                    )
                    if "data-url" in video.attrs
                    else video.find("source")["src"]
                    for video in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("video", class_="")
                ]
                gifs = [
                    "https://"
                    + b64decode(
                        gif.source["src"].split("/")[-1].encode("utf-8")
                    ).decode("utf-8")
                    for gif in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("video", class_="gif")
                ]
            else:
                pictures = [
                    "https://pbs.twimg.com"
                    + unquote(img["src"].split("/pic")[1]).split("?")[0]
                    for img in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("img")
                ]
                videos = [
                    unquote("https" + video["data-url"].split("https")[1])
                    if "data-url" in video.attrs
                    else video.find("source")["src"]
                    for video in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("video", class_="")
                ]
                gifs = [
                    unquote("https://" + gif.source["src"].split("/pic/")[1])
                    for gif in tweet.find("div", class_="tweet-body")
                    .find("div", class_="attachments", recursive=False)
                    .find_all("video", class_="gif")
                ]
        return pictures, videos, gifs

    def _get_tweet_stats(self, tweet):
        """
        Extract stats from a tweet

        :param tweet: tweet to extract stats from
        :return: dictionary of stats. If a stat is not found, it is set to 0
        """
        return {
            "comments": int(
                tweet.find_all("span", class_="tweet-stat")[0]
                .find("div")
                .text.strip()
                .replace(",", "")
                or 0
            ),
            "retweets": int(
                tweet.find_all("span", class_="tweet-stat")[1]
                .find("div")
                .text.strip()
                .replace(",", "")
                or 0
            ),
            "quotes": int(
                tweet.find_all("span", class_="tweet-stat")[2]
                .find("div")
                .text.strip()
                .replace(",", "")
                or 0
            ),
            "likes": int(
                tweet.find_all("span", class_="tweet-stat")[3]
                .find("div")
                .text.strip()
                .replace(",", "")
                or 0
            ),
        }

    def _get_user(self, tweet, is_encrypted):
        """
        Extract user from a tweet

        :param tweet: tweet to extract user from
        :param is_encrypted: True if instance uses encrypted media
        :return: dictionary of user
        """
        avatar = ""
        profile_id = ""
        if is_encrypted:
            try:
                avatar = "https://pbs.twimg.com/" + b64decode(
                    tweet.find("img", class_="avatar")["src"]
                    .split("/")[-1]
                    .encode("utf-8")
                ).decode("utf-8")
            except:
                avatar = ""

            if tweet.find("img", class_="avatar"):
                profile_id = (
                    b64decode(
                        tweet.find("img", class_="avatar")["src"]
                        .split("/enc/")[1]
                        .encode("utf-8")
                    )
                    .decode("utf-8")
                    .split("/profile_images/")[1]
                    .split("/")[0]
                )
        else:
            avatar = "https://pbs.twimg.com" + unquote(
                tweet.find("img", class_="avatar")["src"].split("/pic")[1]
            )

            if tweet.find("img", class_="avatar"):
                profile_id = (
                    unquote(tweet.find("img", class_="avatar")["src"])
                    .split("profile_images/")[1]
                    .split("/")[0]
                )
        return {
            "name": tweet.find("a", class_="fullname").text.strip(),
            "username": tweet.find("a", class_="username").text.strip(),
            "profile_id": profile_id,
            "avatar": avatar,
        }

    def _get_tweet_date(self, tweet):
        """
        Extract date from a tweet

        :param tweet: tweet to extract date from
        :return: date of tweet
        """
        return (
            tweet.find("span", class_="tweet-date")
            .find("a")["title"]
            .split("/")[-1]
            .split("#")[0]
            if tweet.find("span", class_="tweet-date")
            else ""
        )

    def _get_tweet_text(self, tweet):
        """
        Extract text from a tweet

        :param tweet: tweet to extract text from
        :return: text of tweet
        """
        return (
            tweet.find("div", class_="tweet-content media-body")
            .text.strip()
            .replace("\n", " ")
            if tweet.find("div", class_="tweet-content media-body")
            else tweet.find("div", class_="quote-text").text.strip().replace("\n", " ")
            if tweet.find("div", class_="quote-text")
            else ""
        )

    def _get_tweet_link(self, tweet):
        """
        Extract link from a tweet

        :param tweet: tweet to extract link from
        :return: link of tweet
        """
        return (
            "https://twitter.com" + tweet.find("a")["href"] if tweet.find("a") else ""
        )

    def _get_external_link(self, tweet):
        """
        Extract external link from a tweet

        :param tweet: tweet to extract external link from
        :return: external link of tweet
        """
        return (
            tweet.find("a", class_="card-container")["href"]
            if tweet.find("a", class_="card-container")
            else ""
        )

    def _get_replied_to(self, tweet):
        """
        Extract the users a tweet is replying to. If the tweet is not a reply,
        return an empty list.

        :param tweet: tweet to extract replies from
        :return: list of users the tweet is replying to
        """
        return (
            [
                user.text.strip()
                for user in tweet.find("div", class_="replying-to").find_all("a")
            ]
            if tweet.find("div", class_="replying-to")
            else []
        )

    def _extract_tweet(self, tweet, is_encrypted):
        """
        Extract content from a tweet

        :param tweet: tweet to extract content from
        :param is_encrypted: True if instance uses encrypted media
        :return: dictionary of content for the tweet
        """
        # Replace link text with link
        if tweet.find_all("a"):
            for link in tweet.find_all("a"):
                if "https" in link["href"]:
                    link.replace_with(link["href"])

        # Extract the quoted tweet
        quoted_tweet = (
            tweet.find("div", class_="quote")
            if tweet.find("div", class_="quote")
            else None
        )

        # Extract media from the quoted tweet
        if quoted_tweet:
            deleted = False
            if quoted_tweet["class"] == ["quote", "unavailable"]:
                deleted = True
            (
                quoted_pictures,
                quoted_videos,
                quoted_gifs,
            ) = self._get_quoted_media(quoted_tweet, is_encrypted)

        # Extract media from the tweet
        pictures, videos, gifs = self._get_tweet_media(tweet, is_encrypted)

        return {
            "link": self._get_tweet_link(tweet),
            "text": self._get_tweet_text(tweet),
            "user": self._get_user(tweet, is_encrypted),
            "date": self._get_tweet_date(tweet),
            "is-retweet": tweet.find("div", class_="retweet-header") is not None,
            "is-pinned": tweet.find("div", class_="pinned") is not None,
            "external-link": self._get_external_link(tweet),
            "replying-to": self._get_replied_to(tweet),
            "quoted-post": {
                "link": self._get_tweet_link(quoted_tweet) if not deleted else "",
                "text": self._get_tweet_text(quoted_tweet) if not deleted else "",
                "user": self._get_user(quoted_tweet, is_encrypted)
                if not deleted
                else {},
                "date": self._get_tweet_date(quoted_tweet) if not deleted else "",
                "pictures": quoted_pictures,
                "videos": quoted_videos,
                "gifs": quoted_gifs,
            }
            if quoted_tweet
            else {},
            "stats": self._get_tweet_stats(tweet),
            "pictures": pictures,
            "videos": videos,
            "gifs": gifs,
        }

    def _check_date_validity(self, date):
        """
        Check if a date is valid

        :param date: date to check
        :return: True if date is valid
        """
        to_return = True
        if not match(r"^\d{4}-\d{2}-\d{2}$", date):
            to_return = False
        try:
            year, month, day = [int(number) for number in date.split("-")]
            datetime(year=year, month=month, day=day)
        except:
            to_return = False

        if not (
            datetime(year=2006, month=3, day=21)
            < datetime(year=year, month=month, day=day)
            <= datetime.now()
        ):
            to_return = False

        return to_return

    def _search(
        self,
        term,
        mode,
        number,
        since,
        until,
        near,
        language,
        to,
        filters,
        exclude,
        max_retries,
        instance,
    ):
        """
        Scrape the specified search terms from Nitter

        :param term: term to seach for
        :param mode: search mode.
        :param number: number of tweets to scrape.
        :param since: date to start scraping from.
        :param until: date to stop scraping at.
        :param near: location to search near.
        :param language: language of the tweets.
        :param to: user to which the tweets are directed.
        :param filters: list of filters to apply.
        :param exclude: list of filters to exclude.
        :param max_retries: max retries to scrape a page.
        :param instance: Nitter instance to use.
        :return: dictionary of tweets and threads for the term.
        """
        tweets = {"tweets": [], "threads": []}
        if mode == "hashtag":
            endpoint = "/search?f=tweets&q=%23" + term
        elif mode == "term":
            endpoint = "/search?f=tweets&q=" + term
        elif mode == "user":
            if since or until:
                endpoint = f"/{term}/search?f=tweets&q="
            else:
                endpoint = f"/{term}"
        else:
            raise ValueError("Invalid mode. Use 'term', 'hashtag', or 'user'.")

        self._initialize_session(instance)

        if language:
            endpoint += f"+lang%3A{language}"

        if to:
            endpoint += f"+to%3A{to}"

        if since:
            if self._check_date_validity(since):
                endpoint += f"&since={since}"
            else:
                raise ValueError(
                    "Invalid 'since' date. Use the YYYY-MM-DD format and make sure the date is valid."
                )

        if until:
            if self._check_date_validity(until):
                endpoint += f"&until={until}"
            else:
                raise ValueError(
                    "Invalid 'until' date. Use the YYYY-MM-DD format and make sure the date is valid."
                )

        if near:
            endpoint += f"&near={near}"

        if filters:
            for f in filters:
                if f not in valid_filters:
                    raise ValueError(
                        f"Invalid filter '{f}'. Valid filters are: {', '.join(valid_filters)}"
                    )
                endpoint += f"&f-{f}=on"

        if exclude:
            for e in exclude:
                if e not in valid_filters:
                    raise ValueError(
                        f"Invalid exclusion filter '{e}'. Valid filters are: {', '.join(valid_filters)}"
                    )
                endpoint += f"&e-{e}=on"

        if mode != "user":
            if "?" in endpoint:
                endpoint += "&scroll=false"
            else:
                endpoint += "?scroll=false"

        soup = self._get_page(endpoint, max_retries)

        if soup is None:
            return tweets

        is_encrypted = self._is_instance_encrypted()

        already_scraped = set()

        number = float("inf") if number == -1 else number
        keep_scraping = True
        while keep_scraping:
            thread = []

            for tweet in soup.find_all("div", class_="timeline-item"):
                if len(tweet["class"]) == 1:
                    to_append = self._extract_tweet(tweet, is_encrypted)
                    # Extract tweets
                    if len(tweets["tweets"]) + len(tweets["threads"]) < number:
                        if self._get_tweet_link(tweet) not in already_scraped:
                            tweets["tweets"].append(to_append)
                            already_scraped.add(self._get_tweet_link(tweet))
                    else:
                        keep_scraping = False
                        break
                else:
                    if "thread" in tweet["class"]:
                        to_append = self._extract_tweet(tweet, is_encrypted)
                        # Extract threads
                        if self._get_tweet_link(tweet) not in already_scraped:
                            thread.append(to_append)
                            already_scraped.add(self._get_tweet_link(tweet))

                        if len(tweet["class"]) == 3:
                            tweets["threads"].append(thread)
                            thread = []

            logging.info(
                f"Current stats for {term}: {len(tweets['tweets'])} tweets, {len(tweets['threads'])} threads..."
            )
            if (
                not (since and until)
                and not (since)
                and len(tweets["tweets"]) + len(tweets["threads"]) >= number
            ):
                keep_scraping = False
            else:
                sleep(uniform(1, 2))

                # Go to the next page
                show_more_buttons = soup.find_all("div", class_="show-more")
                if soup.find_all("div", class_="show-more"):
                    if mode == "user":
                        if since or until:
                            next_page = (
                                f"/{term}/search?"
                                + show_more_buttons[-1].find("a")["href"].split("?")[-1]
                            )
                        else:
                            next_page = (
                                f"/{term}?"
                                + show_more_buttons[-1].find("a")["href"].split("?")[-1]
                            )
                    else:
                        next_page = "/search" + show_more_buttons[-1].find("a")["href"]
                    soup = self._get_page(next_page, max_retries)
                    if soup is None:
                        keep_scraping = False
                else:
                    keep_scraping = False
        return tweets

    def _search_dispatch(self, args):
        return self._search(*args)

    def get_random_instance(self):
        """
        Get a random Nitter instance

        :return: URL of random Nitter instance
        """
        return random.choice(self.working_instances)

    def get_tweets(
        self,
        terms,
        mode="term",
        number=-1,
        since=None,
        until=None,
        near=None,
        language=None,
        to=None,
        filters=None,
        exclude=None,
        max_retries=5,
        instance=None,
    ):
        """
        Scrape the specified term from Nitter

        :param terms: string/s to search for
        :param mode: search mode. Default is 'term', can also be 'hashtag' or 'user'
        :param number: number of tweets to scrape. Default is -1 (to not set a limit).
        :param since: date to start scraping from, formatted as YYYY-MM-DD. Default is None
        :param until: date to stop scraping at, formatted as YYYY-MM-DD. Default is None
        :param near: near location of the tweets. Default is None (anywhere)
        :param language: language of the tweets. Default is None (any language)
        :param to: user to which the tweets are directed. Default is None (any user)
        :param filters: list of filters to apply. Default is None
        :param exclude: list of filters to exclude. Default is None
        :param max_retries: max retries to scrape a page. Default is 5
        :param instance: Nitter instance to use. Default is None
        :return: dictionary or array with dictionaries (in case of multiple terms) of the tweets and threads for the provided terms
        """
        if type(terms) == str:
            term = terms.strip()

            return self._search(
                term,
                mode,
                number,
                since,
                until,
                near,
                language,
                to,
                filters,
                exclude,
                max_retries,
                instance,
            )
        elif len(terms) == 1:
            term = terms[0].strip()

            return self._search(
                term,
                mode,
                number,
                since,
                until,
                near,
                language,
                to,
                filters,
                exclude,
                max_retries,
                instance,
            )
        else:
            if len(terms) > cpu_count():
                raise ValueError(
                    f"Too many terms. You can search at most {cpu_count()} terms."
                )

            args = [
                (
                    term.strip(),
                    mode,
                    number,
                    since,
                    until,
                    near,
                    language,
                    to,
                    filters,
                    exclude,
                    max_retries,
                    instance,
                )
                for term in terms
            ]
            with Pool(len(terms)) as p:
                results = list(p.map(self._search_dispatch, args))

            return results

    def _profile_info(self, username, max_retries, instance):
        """
        Gets the profile information for a user.

        :param username: username of the page to scrape
        :param max_retries: max retries to scrape a page. Default is 5
        :param instance: Nitter instance to use. Default is None
        :return: dictionary of the profile's information
        """
        self._initialize_session(instance)
        username = sub(r"[^A-Za-z0-9_+-:]", "", username)
        soup = self._get_page(f"/{username}", max_retries)
        if soup is None:
            return None

        is_encrypted = self._is_instance_encrypted()
        # Extract id if the banner exists, no matter if the instance uses base64 or not
        if soup.find("div", class_="profile-banner").find("img") and is_encrypted:
            profile_id = (
                b64decode(
                    soup.find("div", class_="profile-banner")
                    .find("img")["src"]
                    .split("/enc/")[1]
                    .encode("utf-8")
                )
                .decode("utf-8")
                .split("/profile_banners/")[1]
                .split("/")[0]
            )
        elif soup.find("div", class_="profile-banner").find("img"):
            profile_id = (
                unquote(soup.find("div", class_="profile-banner").find("img")["src"])
                .split("profile_banners/")[1]
                .split("/")[0]
            )
        else:
            profile_id = ""

        # Extract profile image, no matter if the instance uses base64 or not
        if soup.find("a", class_="profile-card-avatar").find("img") and is_encrypted:
            profile_image = "https://" + b64decode(
                soup.find("a", class_="profile-card-avatar")
                .find("img")["src"]
                .split("/enc/")[1]
                .encode("utf-8")
            ).decode("utf-8")
        elif soup.find("a", class_="profile-card-avatar").find("img"):
            profile_image = (
                "https://"
                + unquote(
                    soup.find("a", class_="profile-card-avatar").find("img")["src"]
                ).split("/pic/")[1]
            )
        else:
            profile_image = ""

        icon_container = (
            soup.find("div", class_="photo-rail-header").find(
                "div", class_="icon-container"
            )
            if soup.find("div", class_="photo-rail-header")
            else None
        )

        return {
            "image": profile_image,
            "name": soup.find("a", class_="profile-card-fullname").text.strip(),
            "username": soup.find("a", class_="profile-card-username").text.strip(),
            "id": profile_id,
            "bio": soup.find("div", class_="profile-bio").p.text.strip()
            if soup.find("div", class_="profile-bio")
            else "",
            "location": soup.find("div", class_="profile-location")
            .find_all("span")[-1]
            .text.strip()
            if soup.find("div", class_="profile-location")
            else "",
            "website": soup.find("div", class_="profile-website").find("a")["href"]
            if soup.find("div", class_="profile-website")
            else "",
            "joined": soup.find("div", class_="profile-joindate").find("span")["title"],
            "stats": {
                "tweets": int(
                    soup.find("ul", class_="profile-statlist")
                    .find("li", class_="posts")
                    .find_all("span")[1]
                    .text.strip()
                    .replace(",", "")
                ),
                "following": int(
                    soup.find("ul", class_="profile-statlist")
                    .find("li", class_="following")
                    .find_all("span")[1]
                    .text.strip()
                    .replace(",", "")
                ),
                "followers": int(
                    soup.find("ul", class_="profile-statlist")
                    .find("li", class_="followers")
                    .find_all("span")[1]
                    .text.strip()
                    .replace(",", "")
                ),
                "likes": int(
                    soup.find("ul", class_="profile-statlist")
                    .find("li", class_="likes")
                    .find_all("span")[1]
                    .text.strip()
                    .replace(",", "")
                ),
                "media": int(
                    icon_container.text.strip().replace(",", "").split(" ")[0]
                    if icon_container
                    else 0
                ),
            },
        }

    def _search_profile_dispatch(self, args):
        return self._profile_info(*args)

    def get_profile_info(self, username, max_retries=5, instance=None):
        """
        Get profile information for a user

        :param username: username/s of the page to scrape
        :param max_retries: max retries to scrape a page. Default is 5
        :param instance: Nitter instance to use. Default is None
        :return: dictionary of the profile's information
        """

        if type(username) == str:
            username = username.strip()

            return self._profile_info(username, max_retries, instance)
        elif len(username) == 1:
            username = username[0].strip()

            return self._profile_info(username, max_retries, instance)
        else:
            if len(username) > cpu_count():
                raise ValueError(
                    f"Too many usernames. You can use at most {cpu_count()} usernames."
                )

            args = [
                (
                    user.strip(),
                    max_retries,
                    instance,
                )
                for user in username
            ]
            with Pool(len(username)) as p:
                results = list(p.map(self._search_profile_dispatch, args))

            return results
