# Voice Turn Trace

See transcription, inference, synthesis, and playback on one timeline and measure an interrupted turn separately.

[Source](project.py) · [Demo evidence](evidence/demo.html) · [Verification](evidence/checks.json)

## Run locally

Requires Python 3.11+.

```sh
python project.py --html trace.html
python -m unittest discover -v
```

## Engineering decision

Use wall-clock boundaries for first-audio latency and stage durations for diagnosis. Keep interrupted turns separate from completed-turn percentiles.

Synthetic traces with overlapping stages. No provider, microphone, carrier, or handset timings are represented.



[Technology or project reference](https://github.com/pipecat-ai/pipecat)
