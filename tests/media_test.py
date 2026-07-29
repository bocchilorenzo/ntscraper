import unittest

from bs4 import BeautifulSoup

from ntscraper import Nitter


class TestTweetMedia(unittest.TestCase):
    def test_missing_tweet_body_has_no_media(self):
        tweet = BeautifulSoup(
            '<div class="timeline-item"><div class="unavailable">Restricted</div></div>',
            "lxml",
        )

        media = Nitter.__new__(Nitter)._get_tweet_media(tweet, is_encrypted=False)

        self.assertEqual(media, ([], [], []))

    def test_unencrypted_picture_is_extracted(self):
        tweet = BeautifulSoup(
            """
            <div class="timeline-item">
              <div class="tweet-body">
                <div class="attachments">
                  <img src="/pic/media%2Fexample.jpg?name=small">
                </div>
              </div>
            </div>
            """,
            "lxml",
        )

        pictures, videos, gifs = Nitter.__new__(Nitter)._get_tweet_media(
            tweet, is_encrypted=False
        )

        self.assertEqual(pictures, ["https://pbs.twimg.com/media/example.jpg"])
        self.assertEqual(videos, [])
        self.assertEqual(gifs, [])


if __name__ == "__main__":
    unittest.main()
