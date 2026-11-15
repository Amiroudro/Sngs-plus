import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from step1_collect import parse_plain_sitemap  # noqa: E402


class CollectionPolicyTests(unittest.TestCase):
    def test_editorial_sections_are_not_silently_excluded(self):
        xml = """<urlset>
          <url><loc>https://example.com/sports/cricket-final-1</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
          <url><loc>https://example.com/entertainment/film-awards-2</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
          <url><loc>https://example.com/lifestyle/public-health-3</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
          <url><loc>https://example.com/videos/interview-4</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
          <url><loc>https://example.com/author/reporter-5</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
        </urlset>"""
        cutoff = datetime(2026, 11, 12, tzinfo=timezone.utc)
        items = parse_plain_sitemap(
            xml, "Example Publisher", "test", cutoff=cutoff
        )
        urls = {item["url"] for item in items}
        self.assertEqual(len(urls), 3)
        self.assertTrue(any("/sports/" in url for url in urls))
        self.assertTrue(any("/entertainment/" in url for url in urls))
        self.assertTrue(any("/lifestyle/" in url for url in urls))
        self.assertFalse(any("/videos/" in url for url in urls))
        self.assertFalse(any("/author/" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
