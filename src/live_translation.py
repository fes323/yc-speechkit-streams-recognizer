"""Server-side subtitle state and ordered Yandex Translate processing."""
import json
import logging
import os
import queue
import threading
import time
import urllib.error
import urllib.request

LOG = logging.getLogger(__name__)
URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"


class LiveSubtitles:
    def __init__(self):
        self.lock = threading.RLock()
        self.queue = queue.Queue(maxsize=100)
        self.language = "ru-en"
        self.visible = True
        self.sequence = 0
        self.generation = 0
        self.text = ""
        self.original = ""
        self.status = "ready"
        self.error = ""
        self.changed = time.time()
        self.history = []
        self.worker = threading.Thread(target=self._run, name="translate", daemon=True)
        self.worker.start()

    def snapshot(self):
        with self.lock:
            return {
                "sequence": self.sequence, "language": self.language,
                "visible": self.visible, "text": self.text,
                "original": self.original, "status": self.status,
                "error": self.error, "changed": self.changed,
                "history": list(self.history[-30:]),
            }

    def _touch(self):
        self.sequence += 1
        self.changed = time.time()

    def configure(self, *, language=None, visible=None, clear=False):
        with self.lock:
            if language is not None:
                if language not in ("ru-en", "en-ru"):
                    raise ValueError("Language must be ru-en or en-ru")
                if language != self.language:
                    self.language = language
                    self.generation += 1
                    self.text = ""
                    self.original = ""
            if visible is not None:
                if not isinstance(visible, bool):
                    raise ValueError("visible must be boolean")
                self.visible = visible
            if clear:
                self.text = ""
                self.original = ""
                self.error = ""
            self._touch()
            return self.snapshot()

    def publish(self, text):
        text = str(text or "").strip()[:1500]
        if not text:
            return
        with self.lock:
            self.status = "translating"
            self.original = text
            self.error = ""
            generation = self.generation
            direction = self.language
            self._touch()
        try:
            self.queue.put_nowait((generation, direction, text))
        except queue.Full:
            with self.lock:
                self.status = "error"
                self.error = "Translation queue is full"
                self._touch()

    def demo(self):
        with self.lock:
            ru = self.language == "ru-en"
            self.original = ("Добрый день, коллеги! Добро пожаловать на конференцию."
                             if ru else "Good afternoon, colleagues! Welcome to the conference.")
            self.text = ("Good afternoon, colleagues! Welcome to the conference."
                         if ru else "Добрый день, коллеги! Добро пожаловать на конференцию.")
            self.status = "demo"
            self.error = ""
            self._touch()
            return self.snapshot()

    def _run(self):
        while True:
            generation, direction, source = self.queue.get()
            try:
                translated = self._translate(source, direction)
                with self.lock:
                    if generation == self.generation:
                        self.text = translated
                        self.original = source
                        self.status = "ready"
                        self.error = ""
                        self.history.append({"original": source, "translated": translated,
                                             "language": direction, "time": time.time()})
                        self.history = self.history[-100:]
                        self._touch()
            except Exception as exc:
                LOG.exception("Translate error")
                with self.lock:
                    if generation == self.generation:
                        self.status = "error"
                        self.error = str(exc)[:240]
                        self._touch()
            finally:
                self.queue.task_done()

    @staticmethod
    def _translate(source, direction):
        key = os.environ.get("TRANSLATE_API_KEY") or os.environ.get("API_KEY")
        folder = os.environ.get("YANDEX_FOLDER_ID")
        if not key or not folder:
            raise RuntimeError("Set TRANSLATE_API_KEY (or API_KEY) and YANDEX_FOLDER_ID")
        source_lang, target_lang = direction.split("-")
        payload = json.dumps({
            "folderId": folder, "sourceLanguageCode": source_lang,
            "targetLanguageCode": target_lang, "texts": [source],
        }).encode("utf-8")
        req = urllib.request.Request(
            URL, data=payload, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Api-Key " + key},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                result = json.load(res)
        except urllib.error.HTTPError as exc:
            raise RuntimeError("Translate HTTP " + str(exc.code)) from exc
        translations = result.get("translations", [])
        if not translations or not translations[0].get("text"):
            raise RuntimeError("Translate returned an empty response")
        return translations[0]["text"]


SUBTITLES = LiveSubtitles()
