---
name: printer-watch
description: >-
  How to answer questions about the 3D printer and running prints, and what to do
  when a print looks stuck. Use for anything about the printer, a print, how far
  along it is, when it will finish, or whether it has gone wrong.
---

# Printer watch

The printer is an OctoPrint machine called serialhub. `check_print` is your only
source of truth about it. Never state a percentage, a filename or a finish time
that did not come from a `check_print` call in this conversation.

## Answering the ordinary question

Call `check_print`, then say the useful part in one sentence.

- `state=Printing` — say what it is printing, roughly how far along, and how long
  is left. Round for speech: "about two thirds through, roughly an hour left" is
  better than "60 percent, 1 hour 10 minutes". Never read the filename's hash or
  the `.gcode` extension; the tool has already stripped them.
- `state=Operational` and `nothing is printing` — the printer is on and idle. Say
  it is idle, not that it is "operational".
- `printer_unreachable=true` — say you cannot reach the printer, and that you
  therefore do not know whether it is printing. Do not soften this into "nothing
  is printing"; those are different facts and JP acts on them differently.

If asked only "is it done?", answer yes or no first, then the detail.

## When a print looks stuck

You cannot see a stall in a single reading — a percentage is a snapshot, and one
snapshot never proves that nothing is moving. So:

1. Treat these as real trouble on the spot, no second look needed:
   - `state=Paused` — the print is stopped and waiting for a person.
   - `printer_unreachable=true` while JP believes a print is running.
   - `state=Error` or anything else that is not Printing, Paused or Operational.
2. If JP suspects a stall and the state is still `Printing`, call `check_print`
   again after a short pause in the conversation and compare the percentage. Say
   plainly which you did: "it has not moved since I last looked" is a measurement;
   "it seems stuck" is a guess.
3. `time_left=unknown` on its own is not a stall. OctoPrint reports that early in
   a print before its estimate settles.

## Escalating

When something is genuinely wrong, do these in order and stop as soon as JP has
what he needs:

1. Say what is wrong in one sentence, with the number that shows it.
2. Offer the camera: `look_at_camera` with `camera=printer` for the nozzle, or
   `camera=printroom` for the wider view. Remember you cannot see the picture —
   put it up, say you have, and let JP look. Never describe the image.
3. If the printer is unreachable, `realm_status` will not help: serialhub is not
   one of the machines Home Assistant watches, and the tool will say so honestly.
   Say the printer is not answering rather than implying the host is down.

Do not pause, cancel or resume a print. Never offer to. A print is JP's to stop,
and the bed being clear is a thing only he can confirm.
