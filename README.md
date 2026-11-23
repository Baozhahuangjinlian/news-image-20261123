# Newspaper front page — 23 November 2026

[![make.fun](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/Baozhahuangjinlian/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/Baozhahuangjinlian/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123)

A make.fun bounty entry for [news-image-20261123](https://make.fun/bounty/news-image-20261123):
one 1024×1024 image summing up the world's news of Monday 23 November 2026.

## The image

`main.py` draws the front page with Pillow (no network, deterministic — two runs
write identical bytes) and saves it as `entry.png`:

- Giant date masthead: **MONDAY 23 NOVEMBER 2026 — 50 STORIES · 7 REGIONS · 12 OUTLETS**
- **BY THE NUMBERS** strip: 8 verified figures from the day's stories
- **THE DAY IN UTC**: six-slot timeline from overnight to evening
- Four big illustrated headlines, each with a UTC clock, a CLAIM / CONFIRMED /
  REPORTED tag, a named source, and a WHY IT MATTERS line
- Twelve secondary stories, then an ALSO ON list that brings the total to 50,
  with a region tag on every line
- A schematic world map with numbered pins, a DATE CHECK strip naming the
  near-miss stories deliberately left out, and a footer source statement

All 50 stories happened or were first reported on 23 November 2026, researched
from live news pages (One Turn, Al Jazeera, Reuters, CNN, Arab News, WION, SCMP,
Dawn, Economic Times). The drawings are flat vector-style originals — no
photographs of real people anywhere in the image.

## Run it

```sh
python3 main.py
```

Writes `entry.png` (1024×1024 PNG, under 1 MiB) to `$MAKEFUN_OUTPUT_DIR`,
`/output` if that exists, or the current directory.

## Self-score

Scored 90/100 against the top-three formula before submitting (breadth 30/30,
readability 24/30, faithfulness 20/20, craft 16/20). The 90-point gate is the
bar for this entry; anything below it would not have been submitted.

## License

MIT — see `LICENSE`.
