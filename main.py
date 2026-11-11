#!/usr/bin/env python3
"""tinyMuesli plugin: transcribes a track with ElevenLabs Scribe.

tinyMuesli sends one JSON request on stdin:
    {"method": "transcribe", "file": "/tmp/….m4a", "language": "de-DE", "detectLanguage": false,
     "settings": {"elevenlabs.apiKey": "…", "elevenlabs.model": "scribe_v2"}, "apiVersion": 1}
and expects {"phrases": [{"start", "end", "text", "words": [{"text", "start", "end", "confidence"}]}]}
on stdout. Errors go to stderr with a non-zero exit; tinyMuesli shows them.

Standard library only, so it runs with any python3.
"""
import json
import math
import os
import sys
import urllib.error
import urllib.request
import uuid

ENDPOINT = "https://api.elevenlabs.io/v1/speech-to-text"
PAUSE = 1.0  # seconds of silence that start a new phrase


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def multipart(fields, file_path, boundary):
    """Yields the request body in pieces, so a long meeting isn't read into memory twice."""
    for name, value in fields:
        yield (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode()
    name = os.path.basename(file_path)
    yield (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
           "Content-Type: audio/mp4\r\n\r\n").encode()
    with open(file_path, "rb") as f:
        while chunk := f.read(1 << 20):
            yield chunk
    yield f"\r\n--{boundary}--\r\n".encode()


def transcribe(request):
    settings = request.get("settings", {})
    key = settings.get("elevenlabs.apiKey")
    if not key:
        fail("No ElevenLabs API key. Add one in tinyMuesli's Settings › Plugins, "
             "or run: tinymuesli plugin config elevenlabs apiKey YOUR_KEY")
    fields = [
        ("model_id", settings.get("elevenlabs.model", "scribe_v2")),
        ("timestamps_granularity", "word"),
        ("diarize", "false"),  # tinyMuesli identifies speakers itself
        ("tag_audio_events", "false"),
    ]
    if not request.get("detectLanguage", True) and request.get("language"):
        fields.append(("language_code", request["language"].split("-")[0]))
    for term in (settings.get("elevenlabs.keyterms") or "").split(","):
        if term.strip():
            fields.append(("keyterms", term.strip()))

    boundary = f"tinymuesli-{uuid.uuid4()}"
    body = b"".join(multipart(fields, request["file"], boundary))
    http = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "xi-api-key": key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "tinyMuesli-elevenlabs-plugin",
    })
    try:
        with urllib.request.urlopen(http, timeout=30 * 60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        fail(f"ElevenLabs answered {error.code}: {error.read().decode(errors='replace')[:300]}")
    except urllib.error.URLError as error:
        fail(f"Couldn't reach ElevenLabs: {error.reason}")
    return phrases(result.get("words", []))


def ends_sentence(text):
    return text.rstrip()[-1:] in ".?!。？！"


def phrases(words):
    """Scribe's words (with separate "spacing" items) as sentence-sized phrases. Each word keeps
    its leading space, so the words' texts join to the phrase's text."""
    out, current, space_before = [], [], False

    def flush():
        if current:
            out.append({"start": current[0]["start"], "end": current[-1]["end"],
                        "text": "".join(w["text"] for w in current), "words": list(current)})
            current.clear()

    for item in words:
        kind = item.get("type")
        if kind == "spacing":
            space_before = True
            continue
        if kind != "word" or item.get("start") is None or item.get("end") is None:
            continue  # audio events like (laughter)
        if current and (item["start"] - current[-1]["end"] >= PAUSE or ends_sentence(current[-1]["text"])):
            flush()
        word = {"text": (" " if space_before and current else "") + item["text"],
                "start": item["start"], "end": item["end"]}
        if item.get("logprob") is not None:
            word["confidence"] = math.exp(item["logprob"])
        current.append(word)
        space_before = False
    flush()
    return out


def main():
    try:
        request = json.loads(sys.stdin.readline())
    except json.JSONDecodeError as error:
        fail(f"Bad request from tinyMuesli: {error}")
    if request.get("method") != "transcribe":
        fail(f"Unknown method {request.get('method')!r}")
    json.dump({"phrases": transcribe(request)}, sys.stdout)


if __name__ == "__main__":
    main()
