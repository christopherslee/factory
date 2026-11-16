# FACTORY-32: The `try` directive and the Verify stage

## Summary

- The owner says `<name> try N`, in In Dev or Verify. The agent builds the issue branch and puts it in front of the owner (the `## Verify` section of the project home). The stage does not change. The owner can say it again at any time.
- A new agent command, `factory ready-to-try <ID> <sha> [--where <device or URL>]`, records which build the owner can try now. `factory status` shows one line: `Ready to try: ZZ-14 @ abc1234 · <device or URL>`. The part after `·` is optional.
- The stage "Waiting for Verification" becomes "Verify". `factory setup` renames the board option and keeps the cards in the column.
- `factory audit` warns when an issue in Verify has no build on the device that matches its last revision.
- No new stage. The review device (or the preview URL) is one shared thing, so one record tells what is on it.

## Goal

Before verification, the owner must use the real artifact: a running app, an installed build, an app on a test phone. Today the develop step installs the build one time. It records nothing. Thus:

1. The owner cannot ask for the build again after a rework, or after they tried a different issue.
2. When two issues wait in the stage, the owner cannot see which build is on the phone. The last install wins.
3. The stage name "Waiting for Verification" sounds like the owner waits for someone. The owner is the one who must act.

The word "deploy" is not used. It sounds like a release to production. In the factory, only `ship` sends a build out, from the main branch.

## Design

### Words

| Word | Who | What it does | Stage change |
|---|---|---|---|
| `try` | owner | Put the issue branch in front of the owner. Permitted in In Dev and Verify. Can repeat. | none |
| `ready-to-try` | agent | Record that the build of commit `<sha>` is ready to try, with an optional device or URL. | none |
| `verified` | owner | Accept what the owner tried. Permits `ship`. | none (as today) |
| `ship` | agent | Merge to main, run `## Ship`, close. | Verify → Done (as today) |

### CLI (`bin/factory`)

1. `STAGES`: `Stage("verify", "Verify", "ORANGE", old=("Waiting for Verification",))`. The new field `old` holds earlier names of the status option.
   - `GhBackend.setup` uses the option ID of an old name when it sets the options. GitHub then renames the option, and the cards stay in it. Without the ID, GitHub makes a new option and the cards lose their stage.
   - `STATUS_STAGE` also maps each old name, so that a board that has not had `factory setup` yet still reads correctly.
2. `HUMAN_COMMANDS` gets `try`. `factory try <ID> --note ...` is permitted in In Dev and Verify. It writes a human event `try`. The hook stops it in a work session, as the other human commands.
3. `Event` gets two optional fields, `sha` and `where`. `factory ready-to-try <ID> <sha> [--where <device or URL>]` is an agent command. It is permitted in In Dev and Verify. It writes an agent event `ready-to-try` with the sha and, if given, the device or URL.
4. `next_action` gets one new row, after `rework` and before `develop` and `ship`: In Dev or Verify, and a `try` event comes after the last `ready-to-try` event → `try`.
5. `check_advance` does not change. A `try` event is a human event, but Verify → Done still needs `verified`.
6. `op_status` adds `ready_to_try`: the `ready-to-try` event with the latest time across the open issues of the foreman, as `{"id", "sha", "where", "at"}` or `null`. `format_status` prints `Ready to try: <ID> @ <sha 7 characters>`, then ` · <where>` if it is set, above `start now`.
7. `op_audit` adds one problem: an issue in Verify with no `ready-to-try` event, or with a `reworked` event after its last `ready-to-try` event. Text: `ZZ-14: in Verify, but the build to try is older than the last revision; say "<name> try 14"`. In In Dev the audit is silent: the work is not complete.

### Skills

- `skills/work`:
  - The action table gets the row `try`.
  - New Steps section `try`: (1) Find the worktree of the issue. If the branch has no commits of its own, run `factory block <ID> "nothing to try yet: the branch has no commits"` and stop. (2) In In Dev, commit the work that the tests pass; do not merge main. In Verify, merge main into the branch. (3) Do `## Verify`. (4) Run `factory ready-to-try <ID> <sha of HEAD> --where <device or URL>`. The report starts with **Ready to try** (ID, sha, device or URL) and **What to check** (from the PR, or "work not complete" in In Dev).
  - Develop step 6 and rework step 4 run `factory ready-to-try <ID> <sha>` after `## Verify`.
  - In In Dev, a `try` that comes while a develop session holds the claim waits. When develop ends, `next_action` gives `try` if develop did not record a newer `ready-to-try`.
  - The stage name "Waiting for Verification" becomes "Verify" in the text.
- `skills/foreman`: the directive table gets `<name> try N` → `factory try <NAME>-N`, with `--note`. The report gives the `Ready to try` line.
- `templates/home/CLAUDE.md`: `## Verify` must give the commands, the device name or URL for `--where`, and output that shows the build is ready (for example, the install command prints the bundle ID, or the server prints its URL).

### Ship

After the merge, `bin/install-skills`, then `factory setup` for each registered foreman, so that each board renames the column.

## Options that were compared

| | A. `try` is a human event (recommended) | B. `try` is a foreman word only | C. No `try`; develop always installs |
|---|---|---|---|
| How | `factory try` writes an event. `next_action` returns `try`. The foreman runs `/work`. | The foreman runs the `## Verify` commands. The CLI records only `ready-to-try`. | `ready-to-try` is recorded. The owner cannot ask again. |
| Record of the request | yes, on the issue | no | — |
| Works with `factory status` → `start` | yes | no; the foreman needs its own rule | — |
| Reinstall after a different issue | yes | yes | no |
| Size | one event, one row, one Steps section | smaller CLI, but a rule outside the CLI | smallest |

A keeps all stage and action rules in the CLI, as `bin/factory` requires. B puts a rule in the foreman skill. C does not solve problem 1.

## Decisions for the owner

Decided in the rework note of the owner:

1. The stage name is "Verify". Decided: yes.
2. The status line says "Ready to try", with an optional device or URL. Decided. (The default was "On device".)
3. `verified` is permitted when the build ready to try is a different issue. Decided: yes; only the audit warns.
4. `try` is permitted in In Dev and Verify. Decided. (The default was Verify only.)

## Out of scope

- More than one review device or preview URL for each foreman.
- The build on the device after `ship`. If `## Ship` installs the main build, the record does not show it. `Ready to try` shows only open issues.
- A sha check against the remote branch. The audit uses the events (`reworked` after `ready-to-try`). It does not read git.
- The `## Verify` section of each project. Each project adds its own (for example, a separate issue).

## Limits

- If a session installs a build without `factory ready-to-try`, the record is wrong. The skills tell each session to run it.
- `Ready to try` reads only open issues. After the last issue closes, the line is empty.
- A board that has not had `factory setup` after the update shows the old column name. The CLI still reads it.
- A `try` in In Dev builds the branch as it is. The build can be incomplete or broken. The report says so.

## Proof

1. `python3 -m unittest discover -s tests -v`: new tests for `try` in In Dev and Verify, `ready-to-try` with and without `--where`, `next_action` = `try` before `develop` and `ship`, the `Ready to try` line, the audit rule, the old status name, and the hook stop of `factory try`.
2. `tests/smoke.sh` on the sandbox board: `factory setup sandy` renames the column, and the smoke issue stays in it. The smoke test adds `try` in In Dev, then `try` → `ready-to-try` → `verified` → `advance` in Verify.
3. The owner runs `factory status <name>` on a live board after `factory setup`. The column is "Verify", and the `Ready to try` line names the issue and the device or URL.
