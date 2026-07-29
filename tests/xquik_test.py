import unittest

from ntscraper import Xquik


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    def get(self, url, headers, params, timeout):
        self.requests.append(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        return FakeResponse(self.payload)


class TestXquik(unittest.TestCase):
    def test_requires_api_key(self):
        with self.assertRaises(ValueError):
            Xquik(api_key="", session=FakeSession({}))

    def test_get_tweets_maps_nitter_shape(self):
        session = FakeSession(
            {
                "tweets": [
                    {
                        "id": "123",
                        "text": "hello",
                        "createdAt": "2026-06-30T00:00:00.000Z",
                        "likeCount": 4,
                        "retweetCount": 3,
                        "replyCount": 2,
                        "quoteCount": 1,
                        "author": {
                            "id": "42",
                            "username": "xquik",
                            "name": "Xquik",
                            "profilePicture": "https://example.com/avatar.png",
                        },
                    }
                ],
                "has_next_page": True,
                "next_cursor": "cursor-1",
            }
        )

        result = Xquik(api_key="test-key", session=session).get_tweets(
            "xquik",
            mode="user",
            number=5,
        )

        self.assertEqual(len(result["tweets"]), 1)
        self.assertEqual(result["tweets"][0]["id"], "123")
        self.assertEqual(result["tweets"][0]["user"]["username"], "xquik")
        self.assertEqual(
            result["tweets"][0]["user"]["avatar"],
            "https://example.com/avatar.png",
        )
        self.assertEqual(result["tweets"][0]["stats"]["likes"], 4)
        self.assertEqual(result["tweets"][0]["stats"]["retweets"], 3)
        self.assertEqual(result["threads"], [])
        self.assertTrue(result["has_next_page"])
        self.assertEqual(result["next_cursor"], "cursor-1")
        self.assertEqual(session.requests[0]["params"]["q"], "from:xquik")
        self.assertEqual(session.requests[0]["params"]["limit"], 5)
        self.assertEqual(session.requests[0]["headers"]["x-api-key"], "test-key")

    def test_hashtag_query_normalizes_hash(self):
        session = FakeSession({"tweets": []})

        Xquik(api_key="test-key", session=session).get_tweets("#ai", mode="hashtag")

        self.assertEqual(session.requests[0]["params"]["q"], "#ai")

    def test_rejects_invalid_query_type_without_request(self):
        session = FakeSession({"tweets": []})

        with self.assertRaisesRegex(ValueError, "query_type"):
            Xquik(api_key="test-key", session=session).get_tweets(
                "ai", query_type="Relevance"
            )

        self.assertEqual(session.requests, [])

    def test_rejects_invalid_number_without_request(self):
        session = FakeSession({"tweets": []})

        for number in (True, 0, 201, 1.5):
            with self.subTest(number=number):
                with self.assertRaisesRegex(ValueError, "number"):
                    Xquik(api_key="test-key", session=session).get_tweets(
                        "ai", number=number
                    )

        self.assertEqual(session.requests, [])


if __name__ == "__main__":
    unittest.main()
