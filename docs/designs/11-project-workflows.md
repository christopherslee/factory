# FACTORY-11: Keep the Project workflows from moving a card to Done

## Problem

At the ship step of FACTORY-8, the merge of a PR that said `Closes #8` closed the issue. The built-in Project workflow "Item closed" then set the card to Done. The card was in Done before the tests on `main` ran, `factory advance` was refused, and the issue has no event marker for the move to Done.

The cause is a second writer of the Status. The agent's merge started it, so an agent action moved a card without `factory`.

## Design

Remove the second writer (*Separate Before Serializing Shared State*), and stop the agent from closing an issue through a PR.

1. **`factory setup` deletes the workflow "Item closed"** from the Project of the foreman. After that, only `factory` and the owner write the Status. The step is idempotent: if the workflow is not there, nothing changes.
2. **PRs say `Refs #N`, not `Closes #N`.** This goes in the `develop` brief of the foreman skill. The issue stays open until `factory advance` closes it, after the tests on `main` pass.

The ship order does not change: merge, test `main`, `factory advance`. With these two changes, the card is in Waiting for Verification until the `advance`.

### Workflows that stay

| Workflow | Effect | Decision |
|---|---|---|
| Auto-close issue | The Status becomes Done → the issue closes | Stays. A drag to Done by the owner then closes the issue. |
| Pull request merged | A PR card → Done | Stays. PRs are not cards on the board, and `factory` does not read PR cards. |
| Auto-add sub-issues | Adds sub-issues to the Project | Stays. It does not write a Status. |
| Item added to project, Pull request linked to issue | Off | They are already off: `factory setup` removed the options that they used. |

## Spike result

On a scratch Project, the mutation `deleteProjectV2Workflow` removed "Item closed", and the workflow list no longer showed it. The API has no mutation that turns a workflow off or makes one. Thus the delete is the only way through the API, and I found no way to undo it through the API. The owner can also turn the workflow off by hand in the Project settings; then `factory setup` has nothing to delete.

## Options that were compared

| Option | Result |
|---|---|
| A. Delete the workflow in `factory setup`, and `Refs #N` in the brief | **Selected.** It removes the cause, and each new foreman gets it with no manual step. |
| B. `Refs #N` only | Not selected. It is an instruction only. One PR or commit message with `Fixes #N` gives the fault again. |
| C. Run the tests before the merge | Not selected. The card still moves to Done without `factory advance`, so the marker is still missing. |
| D. `factory advance` accepts a card that is already in Done | Not selected. It hides the second writer. |

## Limits

- If a merge closes an issue because of a closing word, the issue is closed while its card is not in Done. `factory advance` then moves the card and writes the marker, so the end state is correct. If the tests fail, a human must open the issue again.
- If the owner closes an issue by hand in the GitHub UI, the card does not move. The owner must drag the card to Done instead, which also closes the issue.
- `factory audit` reads only open issues, so it does not find a closed issue whose card is not in Done.

## Correction of the FACTORY-8 design

That design says that a drag to Done does not close the issue. This is wrong: "Auto-close issue" closes it.

## Proof

Real, on the Project of this repo: after `factory setup fred`, the workflow list has no "Item closed". A test issue in Waiting for Verification is closed through the API, and its card stays in Waiting for Verification. Then `factory advance` moves it to Done and writes the marker.
