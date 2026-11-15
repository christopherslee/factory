# factory

Claude Code plugin for a laptop-first software factory.
This repo is also the home repo of foreman **fred** (named for Fred Flintstone). Its issues are `FRED-1`, `FRED-2`, and so on.
Each project has a **foreman**: a home repo with `foreman.toml`, issues, docs, mockups and data.
Issue IDs use the form `CC-42`.

## The `factory` CLI

`bin/factory` is the only writer of stage state. Stages are `stage:*` labels on the home repo issues.

```
factory stages                 # the stage table
factory foremen                # registered foremen
factory register FOLDER        # add a home repo folder to the registry
factory status [foreman]       # issues by stage, and what the tick must start (--json)
factory go|approve|verified REF    # human directives
factory move REF STAGE         # human: any stage
factory rework REF "note"      # human: ask for a revision
factory advance REF            # agent: one stage forward, if the rule permits
factory claim REF SESSION | release REF | block REF "question" | reworked REF
factory new "title" [--foreman cc]
factory audit | labels [foreman]
```

REF can be `CC-42`, `cc#42`, `"cc 42"`, or `42` inside a foreman folder.

**Rule:** an agent move needs a human event after the last agent move.

Set `FACTORY_FAKE=/path/state.json` to use a local JSON file in place of GitHub.

## Layout

- `bin/factory` — CLI; all stage rules are in this file
- `tests/` — behavior tests (`python3 -m unittest discover -s tests -v`)
- `templates/home/` — template for a new foreman home repo
- `foreman.toml` — config of foreman `fred` (this repo)


## Foreman registry

The registry maps each foreman name to its home repo folder. It is **not** in this repo, because it names your private projects.
Default path: `~/.config/factory/foremen.toml`. Set `FACTORY_REGISTRY` to use another file, for example a clone of a private registry repo.
