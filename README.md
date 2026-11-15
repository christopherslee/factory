# factory

Claude Code plugin for a laptop-first software factory.
This repo is also the home repo of foreman **fred** (named for Fred Flintstone). Its issues are `FACTORY-1`, `FACTORY-2`, and so on: the issue prefix is the project name, and `fred` is only the name of the foreman.
Each project has a **foreman**: a home repo with `foreman.toml`, issues, docs, mockups and data.
Issue IDs use the form `CC-42`: the prefix, then the issue number of the home repo. The prefix is the foreman name, or `prefix` in `foreman.toml` if it is set.

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
factory hook                   # Claude Code PreToolUse guard (hooks/hooks.json)
```

REF can be `CC-42`, `cc#42`, `"cc 42"`, or `42` inside a foreman folder.

**Rule:** an agent move needs a human event after the last agent move.

Set `FACTORY_FAKE=/path/state.json` to use a local JSON file in place of GitHub.

## Layout

- `bin/factory` — CLI; all stage rules are in this file
- `hooks/hooks.json` — runs `factory hook` before each Bash call: stops direct writes of `stage:*` and `factory:*` state, and stops human commands in work sessions (design: `docs/designs/2-hooks.md`)
- `skills/foreman/` — the skill that runs an owner directive such as `fred go 4`: records it, starts the work sessions and reports (design: `docs/designs/4-foreman-skill.md`)
- `tests/` — behavior tests (`python3 -m unittest discover -s tests -v`)
- `templates/home/` — template for a new foreman home repo
- `foreman.toml` — config of foreman `fred` (this repo)


## Foreman registry

The registry maps each foreman name to its home repo folder. It is **not** in this repo, because it names your private projects.
Default path: `~/.config/factory/foremen.toml`. Set `FACTORY_REGISTRY` to use another file, for example a clone of a private registry repo.
