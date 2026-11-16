# FACTORY-32: The `try` directive and the Verify stage

## Summary

- The owner says `<name> try N`. The agent builds the issue branch and puts it in front of the owner (the `## Verify` section of the project home). The stage does not change. The owner can say it again at any time.
- A new agent command, `factory installed <ID> <sha>`, records which build is on the review device. `factory status` shows one line: `On device: ZZ-14 @ abc1234`.
- The stage "Waiting for Verification" becomes "Verify". `factory setup` renames the board option and keeps the cards in the column.
- `factory audit` warns when an issue in Verify has no build on the device that matches its last revision.
- No new stage. The review device is one shared thing, so one record tells what is on it.

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
| `try` | owner | Put the issue branch in front of the owner. Can repeat. | none |
| `installed` | agent | Record that the build of commit `<sha>` is on the review device. | none |
| `verified` | owner | Accept what the owner tried. Permits `ship`. | none (as today) |
| `ship` | agent | Merge to main, run `## Ship`, close. | Verify → Done (as today) |

### CLI (`bin/factory`)

1. `STAGES`: `Stage("verify", "Verify", "ORANGE", old=("Waiting for Verification",))`. The new field `old` holds earlier names of the status option.
   - `GhBackend.setup` uses the option ID of an old name when it sets the options. GitHub then renames the option, and the cards stay in it. Without the ID, GitHub makes a new option and the cards lose their stage.
   - `STATUS_STAGE` also maps each old name, so that a board that has not had `factory setup` yet still reads correctly.
2. `HUMAN_COMMANDS` gets `try`. `factory try <ID> --note ...` is permitted only in Verify. It writes a human event `try`. The hook stops it in a work session, as the other human commands.
3. `Event` gets an optional field `sha`. `factory installed <ID> <sha>` is an agent command. It is permitted in In Dev and Verify. It writes an agent event `installed` with the sha.
4. `next_action` gets one new row, after `rework` and before `ship`: Verify, and a `try` event comes after the last `installed` event → `try`.
5. `check_advance` does not change. A `try` event is a human event, but Verify → Done still needs `verified`.
6. `op_status` adds `on_device`: the `installed` event with the latest time across the open issues of the foreman, as `{"id", "sha", "at"}` or `null`. `format_status` prints `On device: <ID> @ <sha 7 characters>` above `start now`.
7. `op_audit` adds one problem: an issue in Verify with no `installed` event, or with a `reworked` event after its last `installed` event. Text: `ZZ-14: in Verify, but the build on the device is older than the last revision; say "<name> try 14"`.

### Skills

- `skills/work`:
  - The action table gets the row `try`.
  - New Steps section `try`: (1) In the worktree of the issue, merge main into the branch. (2) Do `## Verify`. (3) Run `factory installed <ID> <sha of HEAD>`. The report starts with **On device** (ID and sha) and **What to check** (copied from the PR).
  - Develop step 6 and rework step 4 run `factory installed <ID> <sha>` after `## Verify`.
  - The stage name "Waiting for Verification" becomes "Verify" in the text.
- `skills/foreman`: the directive table gets `<name> try N` → `factory try <NAME>-N`, with `--note`. The report names the build on the device.
- `templates/home/CLAUDE.md`: `## Verify` must give the commands, and the output of the commands must show that the install worked (for example, the install command prints the bundle ID).

### Ship

After the merge, `bin/install-skills`, then `factory setup` for each registered foreman, so that each board renames the column.

## Options that were compared

| | A. `try` is a human event (recommended) | B. `try` is a foreman word only | C. No `try`; develop always installs |
|---|---|---|---|
| How | `factory try` writes an event. `next_action` returns `try`. The foreman runs `/work`. | The foreman runs the `## Verify` commands. The CLI records only `installed`. | `installed` is recorded. The owner cannot ask again. |
| Record of the request | yes, on the issue | no | — |
| Works with `factory status` → `start` | yes | no; the foreman needs its own rule | — |
| Reinstall after a different issue | yes | yes | no |
| Size | one event, one row, one Steps section | smaller CLI, but a rule outside the CLI | smallest |

A keeps all stage and action rules in the CLI, as `bin/factory` requires. B puts a rule in the foreman skill. C does not solve problem 1.

## Decisions for the owner

1. The stage name is "Verify". Default: yes.
2. The status line says "On device". For a web project it is the same text. Default: yes. Other: "Ready to try".
3. `verified` is permitted when the build on the device is a different issue. Default: yes; only the audit warns. Other: refuse `verified`.
4. `try` is permitted only in Verify. Default: yes. Other: also in In Dev, for a look before the work is complete.

## Out of scope

- More than one review device for each foreman.
- The build on the device after `ship`. If `## Ship` installs the main build, the record does not show it. `On device` shows only open issues.
- A sha check against the remote branch. The audit uses the events (`reworked` after `installed`). It does not read git.
- The `## Verify` section of each project. Each project adds its own (for example, a separate issue).

## Limits

- If a session installs a build without `factory installed`, the record is wrong. The skills tell each session to run it.
- `On device` reads only open issues. After the last issue closes, the line is empty.
- A board that has not had `factory setup` after the update shows the old column name. The CLI still reads it.

## Proof

1. `python3 -m unittest discover -s tests -v`: new tests for `try`, `installed`, `next_action` = `try`, `on_device`, the audit rule, the old status name, and the hook stop of `factory try`.
2. `tests/smoke.sh` on the sandbox board: `factory setup sandy` renames the column, and the smoke issue stays in it. The smoke test adds `try` → `installed` → `verified` → `advance`.
3. The owner runs `factory status <name>` on a live board after `factory setup`. The column is "Verify", and the `On device` line names the issue that is on the phone.
