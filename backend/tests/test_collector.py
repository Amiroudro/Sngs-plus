import socket
import unittest
from unittest.mock import patch
from urllib.request import Request

from app import collector


class CollectorSafetyTests(unittest.TestCase):
    def test_feed_url_requires_https(self):
        with self.assertRaises(ValueError):
            collector.validate_public_feed_url("http://example.com/rss")

    def test_feed_url_rejects_credentials_and_nonstandard_ports(self):
        with self.assertRaises(ValueError):
            collector.validate_public_feed_url("https://user:pass@example.com/rss")
        with self.assertRaises(ValueError):
            collector.validate_public_feed_url("https://example.com:8443/rss")

    @patch.object(collector.socket, "getaddrinfo")
    def test_feed_url_rejects_private_dns_addresses(self, getaddrinfo):
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ]
        with self.assertRaises(ValueError):
            collector.validate_public_feed_url("https://feeds.example.com/rss")

    @patch.object(collector, "validate_public_feed_url")
    def test_redirect_target_is_revalidated(self, validate):
        handler = collector.SafeRedirectHandler()
        request = Request("https://feeds.example.com/rss")
        handler.redirect_request(
            request, None, 302, "Found", {}, "https://other.example.com/feed"
        )
        validate.assert_called_once_with("https://other.example.com/feed")

    @patch.object(collector, "validate_public_feed_url")
    def test_redirect_to_private_target_is_rejected(self, validate):
        validate.side_effect = ValueError("private address")
        handler = collector.SafeRedirectHandler()
        request = Request("https://feeds.example.com/rss")
        with self.assertRaises(ValueError):
            handler.redirect_request(
                request, None, 302, "Found", {}, "https://127.0.0.1/admin"
            )

    def test_article_links_must_be_safe_https_urls(self):
        self.assertTrue(collector.validate_article_url("https://news.example.com/story"))
        self.assertFalse(collector.validate_article_url("http://news.example.com/story"))
        self.assertFalse(collector.validate_article_url("javascript:alert(1)"))
        self.assertFalse(collector.validate_article_url("https://user@news.example.com/story"))
        self.assertFalse(collector.validate_article_url("https://news.example.com:8443/story"))

    def test_feed_html_is_reduced_to_plain_text(self):
        value = "<p>Good <b>news</b></p><script>alert(1)</script><style>.x{}</style>"
        self.assertEqual(collector.clean_text(value), "Good news")

    def test_clean_text_respects_limit(self):
        self.assertEqual(collector.clean_text("abcdefgh", limit=4), "abcd")


if __name__ == "__main__":
    unittest.main()
