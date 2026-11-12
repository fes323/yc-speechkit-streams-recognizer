# Live translation + stage subtitles (MVP)

This fork adds Russian ⇄ English translation to the original Yandex SpeechKit streaming recognizer.

## Quick start

Requires **Python 3.11 or 3.12** (the upstream example uses `audioop`, removed in Python 3.13).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r src/requirements.txt
$env:API_KEY="YOUR_SPEECHKIT_API_KEY"
$env:TRANSLATE_API_KEY="YOUR_TRANSLATE_API_KEY"
$env:YANDEX_FOLDER_ID="YOUR_FOLDER_ID"
python src/web_app.py --port 8080
```

Open:
- http://localhost:8080 — microphone capture and operator controls
- http://localhost:8080/screen — full-screen black stage subtitles
- http://localhost:8080/screen?transparent=1 — transparent overlay for OBS Browser Source
- http://localhost:8080/screen?transparent=1&size=64&bottom=8 — configured overlay

Create a Yandex Cloud service account with `ai.speechkit-stt.user` and `ai.translate.user` permissions and authorized API keys. **Never commit credentials to git.** Use a direct AUX/MATRIX audio feed from the venue console connected as a Windows input.

## Operator procedure

1. Select the Windows audio input (microphone or USB audio interface).
2. Select RU → EN or EN → RU before speaking.
3. Click **Start recording**; the original recognition stream is forwarded to SpeechKit.
4. The server translates **final** recognition phrases in sequence and publishes the latest translated phrase to `/api/state`.
5. Show `/screen` on the LED screen, or add the transparent URL to OBS/vMix as a browser source.
6. Use **Hide**, **Show**, **Clear**, and **Demo** in the operator panel.

For local use, server binds to `127.0.0.1` by default. If remote AV hardware needs the URL, introduce authenticated network access and TLS before binding to any public network interface. The control endpoints have no authentication in this MVP.

## Limitations — do not use untested on a live conference

- The upstream SpeechKit gRPC stream has a **5-minute limit**. This MVP does not yet implement seamless stream rotation. Restart recording manually after a session, or add automatic rotation before production.
- Browser `getUserMedia` needs localhost or HTTPS; a remote client may require TLS.
- Audio input and API reliability require a full AV rehearsal.
- Only final recognition results are translated. Latency is network- and speech-dependent.
- Only the latest translated phrase appears; history stays in process memory. No speaker diarization.
- Reloading the program clears state. Use a secure operator access design before deployment on a shared network.
- Translation may fail due to permissions, keys, quota, or network. Errors appear in operator panel; stage does not show errors.
- Open-source prototype, not a production interpreter or a substitute for human verification of safety-critical content.
