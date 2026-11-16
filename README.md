# factory

Claude Code plugin for a laptop-first software factory.
This repo is also the home repo of foreman **fred** (named for Fred Flintstone). Its issues are `FACTORY-1`, `FACTORY-2`, and so on: the issue prefix is the project name, and `fred` is only the name of the foreman.
Each project has a **foreman**: a home repo with `foreman.toml`, issues, docs, mockups and data.
Issue IDs use the form `CC-42`: the prefix, then the issue number of the home repo. The prefix is the foreman name, or `prefix` in `foreman.toml` if it is set.
A project can keep its designs, mockups and delivery docs in a separate **project home** repo: set `home = "../project-home"` in `foreman.toml` (relative to that file). Then the foreman briefs and `factory status --json` (`home`, `designs`, `mockups`) point to that folder. When `home` is not set, the folder of `foreman.toml` is the project home.

## The `factory` CLI

`bin/factory` is the only writer of stage state. The stage of an issue is its **Status** on the GitHub Project of the foreman (`project = N` in `foreman.toml`). That Project is the board. A card that the owner drags to a different column is a human move. The flags (`factory:claimed`, `factory:blocked`, `factory:rework`) are labels.

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
factory audit [foreman]        # find illegal states
factory setup [foreman]        # make the Project board and the flag labels ready
factory hook                   # Claude Code PreToolUse guard (hooks/hooks.json)
```

REF can be `CC-42`, `cc#42`, `"cc 42"`, or `42` inside a foreman folder.

**Rule:** an agent move needs a human event after the last agent move.

Set `FACTORY_FAKE=/path/state.json` to use a local JSON file in place of GitHub.

## Layout

- `bin/factory` — CLI; all stage rules are in this file
- `hooks/hooks.json` — runs `factory hook` before each Bash call: stops direct writes of the Project board and of `factory:*` state, and stops human commands in work sessions (design: `docs/designs/2-hooks.md`)
- `skills/foreman/` — the skill that runs an owner directive such as `fred go 4`: records it, starts the work sessions and reports (design: `docs/designs/4-foreman-skill.md`)
- `skills/work/` — the skill that a work session runs (`/work ID`): it does the stage that `next_action` names, `design`, `develop`, `ship` or `rework` (design: `docs/designs/12-stage-skills.md`)
- `tests/` — behavior tests (`python3 -m unittest discover -s tests -v`)
- `templates/home/` — template for a new foreman home repo
- `foreman.toml` — config of foreman `fred` (this repo)


## Install the skills

Link each skill folder of the fixed `main` checkout into `~/.claude/skills/`:

```
for s in foreman work; do ln -sfn ~/projects/factory/skills/$s ~/.claude/skills/$s; done
```

## Smoke test (real GitHub)

`tests/smoke.sh` tests the factory against real GitHub. It uses only the sandbox foreman `sandy`: a private repo, its own Project board and the issue "Smoke test". It never writes to a live board.
It takes that issue through every stage (human commands with `--note 'smoke test'`), checks `factory status --json` and `factory audit` at each step, and ends in Done. It is idempotent: each run resets the same issue to Backlog first, so a second run gives the same end state.

Run it when you change the GitHub backend (`GhBackend`), the hook or the skills:

```
tests/smoke.sh          # about 2 minutes; prints PASS at the end
```

It runs `bin/factory` of the checkout that holds the script (set `FACTORY` to test another CLI). It needs `gh` with the `repo` and `project` scopes, and `sandy` in the registry.
The hook does not stop it: the hook reads only the command of the Bash call (`tests/smoke.sh`), not the commands in the script. You can run it from a worktree.

To make a sandbox from zero: make a repo with a `foreman.toml` (leave out `project`), then run `factory register FOLDER` and `factory setup NAME`. `factory setup` makes the Project board (or finds an open Project with the same title) and writes `project = N` in `foreman.toml`.

## Foreman registry

The registry maps each foreman name to its home repo folder. It is **not** in this repo, because it names your private projects.
Default path: `~/.config/factory/foremen.toml`. Set `FACTORY_REGISTRY` to use another file, for example a clone of a private registry repo.
