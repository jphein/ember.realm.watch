---
name: slack
description: >-
  How to send a Slack message — to a channel, to JP's dad Stephen, or as a
  note-to-self for JP — and what this house can and cannot do on Slack.
---

# Slack

The house runs a Slack bridge. You can SEND messages through it; you cannot
read or search Slack history.

## Sending

Run the script `script.slack_send` with two fields:

- `message` — the text to send, exactly as it should appear.
- `target` — where it goes:
  - `"#channel-name"` for a channel, e.g. `"#general"`.
  - `"@handle"` for a person's DM. `"@calsurvstephen"` is JP's dad Stephen.
    `"@jp"` is JP's own note-to-self DM — use it when JP says "send me",
    "note on slack", or "remind me on slack".

The service call, concretely: domain `script`, service `slack_send`,
service data `{"message": "Dinner at six", "target": "@calsurvstephen"}`.

## The honest limits, which matter here

- **Only routed destinations exist.** The bridge refuses channels and people
  JP has not configured. If a send is refused, say so plainly — never claim a
  message went out that didn't.
- **Success is silent by design.** The bridge speaks up at the hearth only on
  failure; no complaint means delivered.
- **You post as JP** (or as whoever a hearth is mapped to). Write the message
  the way JP would want to be represented — his words, no signature, no
  flourish.
- You cannot read replies. If asked whether someone answered, say that Slack
  replies arrive as announcements at the hearths, not as something you can
  look up.

## Related, so you don't reinvent it

Messages FROM Slack already speak at the hearths (Stephen's DMs and chosen
channels at Dad's house, mentions at the desk). Voice replies are the
tap-to-reply flow on the hearth screens — that path is not this skill.
