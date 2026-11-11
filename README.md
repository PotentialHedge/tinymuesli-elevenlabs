# ElevenLabs Scribe for tinyMuesli

A [tinyMuesli](https://tinymuesli.potentialhedge.com) plugin that transcribes your meetings with
[ElevenLabs Scribe](https://elevenlabs.io/speech-to-text) instead of Apple's on-device engine.

- **When:** each track (you, and everyone else) is uploaded once the meeting ends, so the transcript
  appears then, not during the call.
- **Speakers:** still worked out on your Mac by tinyMuesli, so recognising voices from earlier meetings
  keeps working.
- **Language:** with the language on System Default, Scribe detects it itself, including meetings that
  change language partway through.

Your meeting audio goes to ElevenLabs. See their [privacy policy](https://elevenlabs.io/privacy-policy).

## Install

In tinyMuesli: Settings › Plugins › Find Plugins, or Install a Plugin with `PotentialHedge/tinymuesli-elevenlabs`.
Or in Terminal:

```sh
tinymuesli plugin install PotentialHedge/tinymuesli-elevenlabs
tinymuesli plugin config elevenlabs apiKey YOUR_KEY
```

Then choose **ElevenLabs Scribe** under Settings › Recording › Transcription. Needs `python3`
(it comes with Xcode's command line tools: `xcode-select --install`).

## Settings

| Setting | |
|---|---|
| `elevenlabs.apiKey` | From elevenlabs.io › Developers › API Keys. Kept in your keychain. |
| `elevenlabs.model` | `scribe_v2` (default) or `scribe_v1` |
| `elevenlabs.keyterms` | Names and terms to listen for, separated by commas. ElevenLabs charges 20% more when any are set. |

## How it works

`main.py` is a complete tinyMuesli transcription plugin in about 120 lines of standard-library Python,
so it's a good starting point for your own: see [Writing a tinyMuesli plugin](https://github.com/PotentialHedge/tinymuesli/blob/main/docs/plugins.md).
To try a change, link your copy: `tinymuesli plugin install ./tinymuesli-elevenlabs`.
