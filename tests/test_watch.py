import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("watch", ROOT / "scripts" / "watch_sources.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)

RSS = """<rss><channel>
<item><title>Run long tasks</title><link>https://developers.openai.com/blog/long</link><pubDate>Mon</pubDate></item>
<item><title>A guide</title><link>https://platform.openai.com/docs/guides/x</link></item>
</channel></rss>"""
ATOM = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>v3.18.0</title>
<link href="https://github.com/mlflow/mlflow/releases/tag/v3.18.0"/><updated>2026-11-01</updated></entry></feed>"""


class TestWatch(unittest.TestCase):
    def test_parses_rss_and_atom(self):
        self.assertEqual([i["title"] for i in watch.parse_feed(RSS)], ["Run long tasks", "A guide"])
        self.assertEqual(watch.parse_feed(ATOM)[0]["link"], "https://github.com/mlflow/mlflow/releases/tag/v3.18.0")

    def test_filters_and_skips_seen(self):
        items = watch.parse_feed(RSS)
        src = {"include": r"developers\.openai\.com/blog/"}
        self.assertEqual(len(watch.new_items(src, items, set())), 1)
        self.assertEqual(watch.new_items(src, items, {"https://developers.openai.com/blog/long"}), [])

    def test_sources_config_is_valid(self):
        import json
        for s in json.loads((ROOT / "watch/sources.json").read_text())["sources"]:
            self.assertTrue(s["feed"].startswith("https://"))
            re.compile(s.get("include") or ".*")
            self.assertTrue((ROOT / s["update"]).exists(), s["update"])


if __name__ == "__main__":
    unittest.main()
