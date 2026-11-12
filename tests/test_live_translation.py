"""Offline tests. Run: PYTHONPATH=src python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from live_translation import LiveSubtitles


class LiveSubtitleTests(unittest.TestCase):
    def setUp(self):
        self.subs = LiveSubtitles()

    def test_initial_state(self):
        state = self.subs.snapshot()
        self.assertEqual(state["language"], "ru-en")
        self.assertTrue(state["visible"])

    def test_direction_switch_clears_output(self):
        self.subs.demo()
        state = self.subs.configure(language="en-ru")
        self.assertEqual(state["language"], "en-ru")
        self.assertEqual(state["text"], "")

    def test_visibility(self):
        self.assertFalse(self.subs.configure(visible=False)["visible"])
        self.assertTrue(self.subs.configure(visible=True)["visible"])

    def test_reject_invalid_controls(self):
        with self.assertRaises(ValueError):
            self.subs.configure(language="fr-de")
        with self.assertRaises(ValueError):
            self.subs.configure(visible="false")

    def test_demo_no_cloud(self):
        state = self.subs.demo()
        self.assertEqual(state["status"], "demo")
        self.assertIn("Good afternoon", state["text"])

    def test_translate_request(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"translations":[{"text":"Hello"}]}'
        with patch.dict("os.environ", {"TRANSLATE_API_KEY":"test", "YANDEX_FOLDER_ID":"test"}):
            with patch("urllib.request.urlopen", return_value=FakeResponse()) as request:
                value = LiveSubtitles._translate("Привет", "ru-en")
                self.assertEqual(value, "Hello")
                body = __import__("json").loads(request.call_args[0][0].data)
                self.assertEqual(body["sourceLanguageCode"], "ru")
                self.assertEqual(body["targetLanguageCode"], "en")


if __name__ == "__main__":
    unittest.main()
