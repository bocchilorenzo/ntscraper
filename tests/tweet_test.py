import unittest
from ntscraper import Nitter


class TestGetTweetById(unittest.TestCase):
    def test_get_tweet_by_id(self):
        """
        Test fetching a tweet by its ID.
        """
        nitter = Nitter()
        tweet = nitter.get_tweet_by_id("X", "1824507305389592885", instance="https://nt.vern.cc")
        self.assertIsNotNone(tweet, "Tweet should note be None")
        self.assertEqual(tweet['user']['username'], "@X", "Username should match the expected username")
        self.assertEqual(tweet['text'], "since it’s friday, let’s have some fun!  comment with a @grok generated pic"
                                        " that describes your entire personality 👹")
        self.assertEqual(tweet['date'], "Aug 16, 2024 · 6:03 PM UTC", "Date should match the expected date")
        self.assertGreaterEqual(tweet['stats']['likes'], 3471, "Likes count should be greater than or equal to 297")
        self.assertGreaterEqual(tweet['stats']['retweets'], 303, "Retweets count should be greater than or equal to 82")
        self.assertGreaterEqual(tweet['stats']['comments'], 2000, "Comments count should be greater than or equal to 18"
                                )


if __name__ == '__main__':
    unittest.main()
