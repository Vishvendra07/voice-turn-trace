"""Separate voice turn wall time from overlapping stage durations."""

import argparse
import html
import json
import math
from pathlib import Path

STAGES = ("transcript", "inference", "synthesis", "playback")


def summarize(turn):
    ranges = {}
    for stage, start, end in turn["spans"]:
        if stage not in STAGES or stage in ranges or not 0 <= start < end:
            raise ValueError(f"Invalid span in {turn['id']}")
        ranges[stage] = (start, end)
    if not ranges or turn["terminal"] not in ("completed", "interrupted"):
        raise ValueError("Unsupported turn")
    if "playback" not in ranges and turn["terminal"] == "completed":
        raise ValueError("A completed turn must show playback")
    stages = {stage: end - start for stage, (start, end) in ranges.items()}
    begin = min(start for start, _ in ranges.values())
    end = max(end for _, end in ranges.values())
    boundary = turn.get("interrupt_ms")
    if turn["terminal"] == "interrupted" and (boundary is None or not begin <= boundary <= end):
        raise ValueError("Interruption needs a timestamp inside its turn")
    return {
        "id": turn["id"],
        "locale": turn["locale"],
        "terminal": turn["terminal"],
        "wall_ms": end - begin,
        "stages_ms": stages,
        "longest_stage": max(stages, key=stages.get),
        "first_audio_ms": ranges["playback"][0] - begin if "playback" in ranges else None,
        "post_interrupt_playback_ms": max(
            0, ranges["playback"][1] - max(boundary, ranges["playback"][0])
        )
        if boundary is not None and "playback" in ranges
        else None,
    }


def report(turns):
    rows = [summarize(turn) for turn in turns]
    completed = sorted(row["first_audio_ms"] for row in rows if row["terminal"] == "completed")
    return {
        "turns": rows,
        "completed_only": {
            "n": len(completed),
            "first_audio_p95_ms": completed[math.ceil(0.95 * len(completed)) - 1]
            if completed
            else None,
        },
    }


def render(turns):
    colors = dict(zip(STAGES, ["#538e9b", "#a45523", "#6f8553", "#604b92"], strict=True))
    upper = max(end for turn in turns for _, _, end in turn["spans"])
    rows = "".join(
        "<section><h2>"
        + html.escape(turn["id"])
        + " · "
        + html.escape(turn["terminal"])
        + "</h2>"
        + "".join(
            f'<div class="track"><span>{stage} · {start}–{end} ms</span><i style="margin-left:{100 * start / upper:.3f}%;width:{100 * (end - start) / upper:.3f}%;background:{colors[stage]}"></i></div>'
            for stage, start, end in turn["spans"]
        )
        + "</section>"
        for turn in turns
    )
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Voice Turn Trace</title><style>body{{font:16px system-ui;background:#edf0eb;color:#162821;max-width:940px;margin:auto;padding:3rem 1rem}}section{{border-top:1px solid #a8b8aa;padding:.6rem 0 1rem}}.track{{margin:.55rem 0}}.track i{{height:.42rem;display:block;border-radius:.2rem;margin-top:.2rem}}h1{{font-size:clamp(2rem,5vw,3.5rem)}}h2{{font-size:1rem}}</style><h1>Voice Turn Trace</h1><p>Synthetic spans on a shared {upper} ms timeline. Overlap indicates concurrent stages.</p>{rows}</html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    turns = json.loads(Path(__file__).with_name("fixtures.json").read_text())
    result = report(turns)
    if args.html:
        args.html.write_text(render(turns), encoding="utf-8")
    print(json.dumps(result, indent=2))
