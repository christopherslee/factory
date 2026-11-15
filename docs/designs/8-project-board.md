# FACTORY-8: Use a GitHub Project as the board

## Goal

The owner sees all issues of a foreman by stage, on the laptop and on the phone, with no custom board. A card that the owner drags to a different column is a human move.

## Design

Each foreman has one GitHub Project (v2). The **Status** field of the Project is the stage store. The `stage:*` labels go away. No code reads both stores (*Outcome-Oriented Execution*).

### Config

```toml
name = "fred"
prefix = "factory"
github = "christopherslee/factory"
project = 1          # number of the Project of the same owner
```

### Types first

The backend interface changes from labels to stages and flags. The operations do not know where a stage is stored (*Boundary Discipline*).

| Now | After |
|---|---|
| `issue(n)` → `labels` | `issue(n)` → `stage` (one key or none) and `flags` |
| `add_labels`, `remove_label` for stages | `set_stage(n, stage)` |
| `add_labels`, `remove_label` for flags | `set_flag(n, flag, on)` |
| `create_issue(title, body, labels)` | `create_issue(title, body)`, then `set_stage(n, "backlog")`. `set_stage` puts the issue on the board if it is not there. |
| `ensure_label` and `factory labels` | `setup()` and `factory setup`: the six Status options, the Board view, the repo link and the three flag labels |

Status is a single-select field. Thus an issue with two stages is not possible, and that audit check goes away (*Type System Discipline*). The audit keeps one check: an open issue with no stage (not on the board).

The Status options are the `status` names that the stage table already holds: Backlog, In Design, Ready for Dev, In Dev, Waiting for Verification, Done.

The flags (`factory:claimed`, `factory:blocked`, `factory:rework`) stay as labels. The cards show them. The event markers stay as issue comments.

### GitHub calls

`GhBackend` uses `gh api graphql`: one query reads all items of the Project with their Status, and one mutation sets a Status. The backend reads the IDs of the Project, the field and the options once for each run.

### A drag is a human move

No new rule is necessary. `check_advance` already reads a stage that the last agent move did not set as a human event.

| The owner drags | Effect |
|---|---|
| Backlog → In Design | The same as `go` |
| Ready for Dev → In Dev | The same as `approve` |
| A move back | The same as `move`; the agent can move again |
| Waiting for Verification → Done | The owner closes the issue by hand. The agent does not merge. |

`verified` is not a stage. The owner still says `fred verified N`.

### Hook

An agent that edits the Status directly makes a false human move. `factory hook` must also stop:

- `gh project item-edit`, `item-add`, `item-delete`, `item-archive`, `field-create`, `field-delete`, `delete`, `edit`
- `gh api graphql` with a mutation that names `ProjectV2`

### Setup and migration

1. The owner adds the `project` scope: `gh auth refresh -s project`.
2. Make the Project one time (`gh project create --owner OWNER --title TITLE`) and set `project = N` in `foreman.toml`.
3. `factory setup fred` makes the Status options, changes the first view to a Board view, links the repo and makes the flag labels. It is idempotent. Dev confirmed that the API can do all of this.
4. One-time migration for this repo, by hand: add the issues to the Project with their stage, then delete the six `stage:*` labels. No migration code stays in the repo.

FACTORY-8 itself moves between the stores. After the merge, the ship step sets it to Waiting for Verification on the board before the last `advance`.

## Options that were compared

| Option | Result |
|---|---|
| A. Status is the stage store | **Selected by the owner.** One store. A drag is a human move. |
| B. Labels stay, the CLI copies each move to Status | Not selected. Two stores can drift, and a drag does nothing. |
| C. Labels only, and a saved issue search for each stage | Not selected. It is a list, not a board. |

## Limits

- A drag does not start a work session, because no Claude turn runs. The work starts at the owner's next message to the foreman.
- A drag leaves no event marker. The history on the issue shows the agent moves and the directives only.
- A drag to Done does not close the issue. `factory audit` reports an issue that is in Done and open.
- An issue that someone makes in the GitHub UI is not on the board until `factory move N backlog`. The audit reports it.
- A new Project is private. The owner decides if the board of a public repo becomes public.
- The hook does not see a mutation that a command reads from a file.
- Each foreman needs its own Project. A Project of a private foreman must be private.

## Proof

- Tests with the fake backend: the old lifecycle tests pass with stages in place of labels; a stage change outside `factory` permits the next agent move; the hook stops `gh project item-edit` and a `ProjectV2` mutation.
- Real: `factory go` on a real issue moves its card, and a drag from Ready for Dev to In Dev permits `factory advance`.
