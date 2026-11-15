# FRED-2: Write the hooks

## Goal

The `factory` CLI is the only writer of stage state. The CLI rules are not sufficient, because a session can go around the CLI. The hooks stop the two known paths:

1. A session writes a `stage:*` label, a `factory:*` label or a `factory:event` marker directly on GitHub. The rule reads a stage change that `factory` did not make as a human event. Thus a direct write lets an agent make a false human event.
2. A work session runs a human command (`go`, `approve`, `verified`, `move`, `rework`, `unblock`). Only the owner gives these directives.

## Design

One `PreToolUse` hook on the `Bash` tool. The hook runs `factory hook`. All the rules stay in `bin/factory` (*Model the Domain*), and no second script is necessary (*Laziness Protocol*).

```
hooks/hooks.json     PreToolUse, matcher "Bash" → "${CLAUDE_PLUGIN_ROOT}/bin/factory" hook
bin/factory hook     reads the hook JSON from stdin
                     exit 0 = permit; exit 2 + reason on stderr = stop
```

### Rule 1: no direct write of factory state

Stop the command when it contains a protected name **and** a GitHub write.

- Protected names: `stage:<x>`, `factory:<x>` (the labels and the `factory:event` marker).
- GitHub writes:
  - `gh issue|pr edit|create|comment`
  - `gh label create|edit|delete|clone`
  - `gh api` with a method (`-X`, `--method`), a field (`-f`, `-F`, `--field`, `--raw-field`) or `--input`
  - `curl`

A read stays permitted, for example `gh issue list --label stage:dev`.

### Rule 2: no human commands in work sessions

Stop `factory go|approve|verified|move|rework|unblock` when one of these conditions is true:

- The session folder is a linked git worktree. Work sessions run in worktrees. The foreman session runs in the fixed `main` checkout.
- A subagent makes the call (the hook input has `agent_id`).

The session folder is `CLAUDE_PROJECT_DIR`. If that is not set, it is `cwd` from the hook input. A `cd` in the command does not change `CLAUDE_PROJECT_DIR`.

### Failure mode

If `factory hook` cannot read its input, it stops the command (exit 2). An exit code of 1 would permit the command.

## Options that were compared (rule 2: how to know a work session)

| Option | Result |
|---|---|
| A. The session folder is a worktree | **Selected.** Local, no state, no network. It agrees with the rule "the plugin runs from the fixed `main` checkout". |
| B. The session holds a claim | Not selected. It needs a GitHub read, and a session that does not claim is not found. |
| C. The last owner prompt contains the directive | Not selected. The start prompt of a work session comes from the foreman, and the hook cannot tell it from an owner prompt. |

## Limits

- The hook is a guard against agent drift. It is not a sandbox. A command that builds the label name from variables can pass. `factory audit` stays necessary.
- The hook sees only the `Bash` tool. A GitHub MCP tool is not covered. No such tool is installed now.
- A work session that does not run in a worktree is not found. The foreman skill (step 4) must start each work session in a worktree.
- The foreman session can run a human command in a turn that no human started. Step 4 must handle this case.
- Rule 1 also stops text that only mentions a protected name in a write, for example `gh issue comment --body "stage:dev is late"`. This is acceptable.
- The hook has an effect only after the plugin is installed (step 6).

## Proof

- Tests call `bin/factory hook` with the same JSON that Claude Code sends, and assert the exit code and the message.
- A real Claude Code session with the hook: `gh issue edit --add-label stage:dev` is stopped.
