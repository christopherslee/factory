# FRED-4: Write the foreman skill

## Goal

The owner controls each project with short directives, for example `fred go 4`. One skill, `foreman`, does the same procedure for each directive: it records the directive with the `factory` CLI, starts the work sessions that `factory status` asks for, and reports.

No tick and no scheduled task are necessary. The owner's directive turn is the trigger (*Laziness Protocol*).

## Design

One file: `skills/foreman/SKILL.md`. It contains no rules about stages. The CLI holds the rules and the skill only calls it (*Model the Domain*).

### Directives

| Owner says | Command |
|---|---|
| `<name> go N` | `factory go` |
| `<name> approve N` | `factory approve` |
| `<name> verified N` | `factory verified` |
| `<name> rework N "note"` | `factory rework` |
| `<name> unblock N` | `factory unblock` |
| `<name> move N STAGE` | `factory move` |
| `<name> new "title"` | `factory new` |
| `<name> status` | `factory status` |

`<name>` is a foreman name from the registry. Free text is permitted when the directive and the issue are clear.

### The directive turn

1. **Human check.** A human command is run only when the directive is in the owner's own message of this turn.
2. **Record.** Run the `factory` command with the owner's words as the note. If the CLI refuses, report and stop.
3. **Audit.** Run `factory audit <name>` and report each problem.
4. **Start.** Read `factory status <name> --json`. For each ID in `start`: start a work session in a new git worktree of the code repo, then run `factory claim ID <session id>`.
5. **Report** in STE100: what moved, which sessions started, and what waits for the owner, with the exact directive to say.

### Work sessions

- Each work session runs in a git worktree. This is necessary: the hook from FRED-2 finds a work session by its worktree.
- The brief of a work session comes from `next_action` (`design`, `develop`, `ship`, `rework`). The skill holds one short brief for each action. Build step 5 replaces these briefs with stage skills.
- A work session ends with `factory advance` (or `factory reworked`), then `factory release`, then a report.
- If the tool to start a session is not available (plain CLI), the skill uses a subagent with worktree isolation.

### A turn that no human started

When a work session ends, the app continues the foreman session. No owner message is in that turn. In that turn the skill:

- runs no human command,
- checks the result (`factory show`, the diff or the PR),
- tells the owner what waits, with the exact directive,
- proposes the sessions in `start`, but does not start them.

## Options that were compared

| Option | Result |
|---|---|
| A. One `foreman` skill for all directives | **Selected.** One procedure, one file. |
| B. One skill for each directive (`/approve`, `/go`, …) | Not selected. Six files repeat the same five steps. |
| C. A `factory directive` subcommand that also starts sessions | Not selected. The CLI cannot start app sessions. |

## Limits

- The human check is an instruction, not a hook. The hook cannot yet tell an owner prompt from an app event. A later spike can test whether a `UserPromptSubmit` hook sees the difference.
- The skill is available to sessions only after it is linked into `~/.claude/skills` or the plugin is installed (step 6).
- For a foreman whose code repo is in a different folder than the home repo, the app can refuse the session start. This is tested with the first such project.
- Issues and PRs share one number sequence on GitHub. The skill takes a new ID only from the output of `factory new`.

## Proof

A `go` directive for a real FRED issue, given in a session that has the skill, starts a design session in a worktree, and the issue shows the claim of that session.
