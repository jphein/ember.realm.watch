# Ember's system prompt — the source of truth

`ember-system.md.j2` is Ember's conversation system prompt.

**Why this directory exists.** Until 2026-07-31 this prompt existed *only* inside Home
Assistant's `.storage/core_config_entries` — not in this repo, not in any backup this repo
knew about, and not in HA's YAML config either. A measured prompt-cache fix was made against
it once, its reasoning was written into `docs/home-assistant.md` §6.3, and the prompt itself
was never captured. Nothing in the repo contained the string `You are Ember`. That is the
whole reason [#37](https://github.com/jphein/ember.realm.watch/issues/37) had to
re-derive from scratch what §6.3 already half-knew.

This file is now the source of truth. **Edit here, deploy with the tool, never hand-edit
`.storage`.**

## Deploy

```bash
../tools/ember-prompt.py --diff      # show repo vs live
../tools/ember-prompt.py --deploy    # push this file into HA, live, no restart
../tools/ember-prompt.py --extract   # pull live back into this file
```

Deploy drives HA's **config-subentry reconfigure flow** over the REST API. That matters:

> ⚠ **Editing `.storage/core.config_entries` on disk does not work.** HA loads that store
> into memory once at startup and rewrites it from memory on every save, so a disk edit is
> both ignored *and* liable to be silently clobbered. There is no "reload config entries"
> for it either — a disk edit needs a full HA restart to take effect. The reconfigure flow
> applies immediately with no restart, which is why the tool uses it.

The flow **replaces the subentry's data wholesale**, so the tool resubmits every field
(`chat_model`, `max_tokens`, `functions`, `context_threshold`, …) and only substitutes
`prompt`. It refuses to run if any field would be dropped.

## The one rule

The prompt's **prefix must be byte-stable between turns**. llama.cpp's prefix cache
truncates at the first differing token, and everything after it — including the whole
conversation history — is re-prefilled. Anything that renders differently per request
(a timestamp with sub-hour precision, a live entity *state*, a reordered list) costs real
seconds on every turn. Measured numbers and the method are in `docs/home-assistant.md` §6.3.

The device CSV deliberately carries `entity_id,name,area_id` and **no state column** for
exactly this reason.
