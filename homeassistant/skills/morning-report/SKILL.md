---
name: morning-report
description: >-
  How to compose the spoken morning summary: weather, the printer, whether any
  machines are down, and who is about. Use when asked for the morning report, a
  briefing, a rundown, "how are things", or what JP needs to know today.
---

# Morning report

A briefing spoken aloud at the hearth. It is **four short sentences at most**, and
fewer when there is nothing to say. This is the one place you may go past the
usual one-sentence rule — but a report nobody can hold in their head is worse
than no report.

## Gather, in this order

1. `weather_now` — what it is doing outside, today's high and low, rain.
2. `check_print` — only mention the printer if something is actually printing, or
   if it is unreachable while a print was expected. An idle printer is not news.
3. `realm_status` — call it with no host. Mention machines only if something is
   **down**. "Everything is up" is worth at most three words, and usually none.
4. `whos_home` — mention only if it is surprising, for example the house is empty.

## Compose

Lead with the weather, because it is the one thing that is always true and always
useful. Then anything that is *unusual*. Then stop.

Good:

> Cold start, forty-three out, up to sixty-nine later with no rain. The midframe
> print is about two thirds done, roughly an hour left. Everything else is up.

Bad — this is a status dump, not a report:

> Weather is clear night, temperature 55F, high 69F, low 34F, rain 0mm. Print job
> ember mobile midframe r10 at 60 percent with 1 hour 10 minutes remaining. Eight
> machines watched, all up. Tracked people 1, jp home.

## Rules

- **Round every number for speech.** "Forty-three" not "43F". "About an hour" not
  "1 hour 10 minutes". Nobody needs a decimal at breakfast.
- **Never invent a calendar.** This house has no personal calendar exposed to you
  — the only calendars are game-shop freebies and a lighting schedule. If asked
  about the day's plans, say you do not have his calendar. Do not read out Epic
  Games Store entries as if they were appointments.
- **Report failures as failures.** If `weather_now` says `forecast_unavailable` or
  `check_print` says `printer_unreachable`, name the gap in a few words. A report
  that quietly omits what it could not fetch is a report that lies by shape.
- Do not offer to do things. This is a briefing, not a menu.
