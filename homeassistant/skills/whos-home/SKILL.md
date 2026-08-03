---
name: whos-home
description: >-
  How to answer who is at home, whether someone is back, and whether the house is
  empty. Covers what this house can and cannot actually tell about people.
---

# Who's home

Call `whos_home`. It returns one entry per tracked person, each `home` or `out`.

## Answering

Say it in one sentence, using names as a person would: "JP is home", not
"jp=home". If nobody is home, say the house is empty.

## The honest limit, which matters here

**This house tracks exactly one person: JP.** `tracked_people=1` is the normal
reading, not a fault.

So:

- "Is anyone home?" — answer about JP, because he is all Home Assistant knows.
- "Is anyone *else* home?" or a question about a named person who is not JP —
  say plainly that JP is the only person the house tracks, so you cannot say.
  Do not answer "no", which sounds like knowledge of an empty house.
- Never infer a person from a device. There are phones, tablets, watches and
  Bluetooth key tags in this house, and a tag that is home tells you where the
  tag is. If asked to be more specific than the person entities allow, say what
  you actually have.

## When the reading is neither home nor out

A person can read `unknown` or `unavailable` when their phone has not reported
recently. Say the tracking has gone quiet rather than guessing they are out —
"out" is a claim, and silence is not.
