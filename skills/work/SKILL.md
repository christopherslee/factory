---
name: work
description: Do the next stage of one factory issue (design, develop, ship or rework), as `next_action` of the factory CLI names it. Use only when a factory work session brief says `/work <ID>`, or when the owner runs `/work` with a factory issue ID such as FACTORY-12.
---

# Work

You are a work session of the software factory. Run this skill as `/work <ID>`, for example `/work FACTORY-12`. `<N>` is the issue number, `<prefix>` is the issue prefix in lowercase, and `<slug>` is a short name from the issue title. Do only this issue.

## Start

1. Run `factory show <ID>` and `factory resolve <ID>`. The output of `resolve` gives the foreman name.
2. Run `factory status <foreman> --json`. Take `root`, `home`, `designs`, `mockups` and `repos` from the output. Read `CLAUDE.md` in `root`, and in `home` if it is a different folder.
3. List `<home>/.claude/skills/`. Read each `SKILL.md` whose description applies to this stage, and follow it. Use the tools in `<home>/bin` and the data in `<home>/data` as `CLAUDE.md` in the project home tells.
4. Find the action. `next_action` in `factory status --json` names it, but it is empty while a session holds the claim, and the foreman claims the issue for you. Thus take the action from this table, with the stage and the flags from `factory show <ID>`. The rows are the rules of `next_action` in the CLI, without the claim.

| Stage and flags | Action |
|---|---|
| The `rework` flag is set (any stage) | `rework` |
| In Design | `design` |
| In Dev | `develop` |
| Waiting for Verification, and a `verified` event comes after the last agent move | `ship` |

5. If the `blocked` flag is set, or no row applies, change nothing, report the stage and the flags, and stop. A second start of this skill is thus safe.
6. Do only the Steps section of that action.

## Folders

The project home is the workspace of the foreman. It holds designs, mockups, data (`<home>/data`), tools (`<home>/bin`) and project skills (`<home>/.claude/skills`). The code repos (`repos[].path`) hold only the product code. Take each folder from `factory status`. Never use a fixed path.

1. **A project home is defined** (`home` is a different repo than the code repo). Design and spec work go into the project home: `designs`, `mockups` and the other folders of the project home.
2. **The design or spec work goes into the project repo itself** (`home` is in the code repo). The work must be on a new worktree of that repo, on branch `<prefix>-<N>-<slug>`. If you are not in such a worktree, create one before you write. Never write in the fixed checkout. The design goes to the main branch with the code PR.
3. **The design or spec work goes into the project home.** Commit it directly to that repo, on its default branch, and push. Make no worktree, no branch and no PR there. Write only the files of this issue (`<designs>/<N>-<slug>.md`, `<mockups>/<N>-<slug>/`). If `git commit` or `git push` fails because a different session committed at the same time, pull and try again.
4. **Development starts and no worktree exists yet.** Create a new worktree of the code repo on branch `<prefix>-<N>-<slug>`. If `git worktree list` in the code repo shows a worktree for that branch, use it. If the session started in a new worktree of the code repo with no commits of its own, use that worktree and switch it to the branch.

To find the case, compare `git rev-parse --show-toplevel` in `home` and in the code repo. The same top folder is rule 2. A different one is rules 1 and 3.

## Rules

- Do only what the issue asks (for `rework`: only what the note asks). When you find a different idea, a different defect or a possible improvement, do not build it and do not design it. Write it in the report below "Follow-ups", as a possible issue title.
- Never run `factory go|approve|verified|move|rework|unblock`. Do not run `factory new`: the owner decides what goes into the backlog.
- When a question has no answer in the issue, select the simplest option, write the decision down, and continue. Run `factory block <ID> "question"` and stop only if the decision is hard to undo.
- Write designs only in `designs` and mockups only in `mockups`. Change code only in the worktree of the issue.
- Never copy designs, mockups, data, tools or project skills into a code repo. Link to them.
- Never write details of a different project in a repo, an issue or a PR of this project.
- Never write `Closes`, `Fixes` or `Resolves` with an issue number. Only `factory advance` closes an issue.

## Steps

Do only the section of the action that Start found.

### design

1. Decide if the issue changes something that a user sees.
   - **Yes:** make 2–3 mockup images, labeled A, B and C, in `<mockups>/<N>-<slug>/`. Recommend one.
   - **No:** compare 2–3 approaches in a table. Recommend one.
2. Write `<designs>/<N>-<slug>.md` with these sections: summary (five lines maximum), goal, design, options that were compared, decisions for the owner, out of scope, limits, proof.
   - "Decisions for the owner" is a numbered list. Each item has a default. The design uses the defaults.
   - "Out of scope" lists what the design leaves out on purpose.
   - "Proof" states what the owner will look at on the real artifact to verify the work.
3. Write and commit as rules 1–3 in "Folders" tell: directly to the project home if one is defined, else on a new worktree of the project repo.
4. Run `factory advance <ID>`.

The owner then says `approve` (the recommendation and the defaults are accepted) or `rework` with a short note ("B, with the colors of A"; "1. yes 2. no").

### develop

1. Read the design file in `designs` and each event after it. An owner note is stronger than the design text.
2. Find the worktree of the code repo on branch `<prefix>-<N>-<slug>`. If no worktree exists yet, create one (rule 4 in "Folders"). Work only in it. Merge the main branch into it first.
3. Build in small units. For each unit: write the behavior test, write the code, run the tests, commit. Write the test first for logic that has no user interface.
4. Merge the main branch again. Run all the tests.
5. Look at the full diff for secrets and private data.
6. Do the `## Verify` section of `CLAUDE.md` in the project home. This section tells you how to put the real artifact in front of the owner (for example: install the build on the review device, or start the app and make screenshots). If the section is not there, use the product as a user does and keep the output as proof.
7. Push the branch. Open a PR that names the issue as `Refs #<N>`. The PR body contains "What to check": three to five steps that the owner can do in two minutes, each with the expected result.
8. Run `factory advance <ID>`.

### ship

1. Merge the main branch into the issue branch. If there is a conflict that changes behavior, run `factory block <ID> "summary of the conflict"` and stop.
2. Run all the tests on the branch.
3. Merge the PR. Delete the branch on the remote.
4. Run all the tests on the main branch. If they fail, run `factory block <ID> "the tests fail on main: <summary>"` and stop. Do not revert without the owner.
5. Do the `## Ship` section of `CLAUDE.md` in the project home, if it is there (for example: deliver the build from the main branch).
6. Run `factory advance <ID>`. This closes the issue.

Start the report with four lines: **Merged** (commit), **Tests on main** (result), **Issue** (closed or open), **Stage**.

### rework

1. Read the last `rework` note in `factory show <ID>`. The stage tells what to revise:

   | Stage | Revise |
   |---|---|
   | In Design, Ready for Dev | The design file and the mockups. With a project home: commit directly to it (rule 3). Without: in the worktree of the issue, and create a new one if none exists (rule 2). |
   | In Dev, Waiting for Verification | The code and the tests, in the worktree of the issue, on the same branch and the same PR of the code repo. If no worktree exists, create one on that branch (rule 4). If the note changes the design, also the design file, in the place that rules 1–3 tell. |

2. Do only what the note says. If the note has two possible meanings, use the smaller one and state it in the report.
3. Special notes:
   - A selection ("B", or "A with one part of B"): make the one result. Move the options that were not selected to "Options that were compared".
   - Numbered answers: write each answer into "Decisions for the owner" as decided.
   - "Back it out": revert the change. Keep the issue and its branch.
   - An idea "for later": write it as a follow-up. Do not build it.
4. For code: run all the tests, push, do the `## Verify` section again, and update "What to check" in the PR.
5. Run `factory reworked <ID>`. The stage does not change.

In the report, give one line for each item of the note: what it was before, and what it is now.

## End

Run the stage command of the last step, then `factory release <ID>`. If the CLI refuses, report the refusal and stop. Then write the report in ASD-STE100 Simplified Technical English, with the result in the first line:

- **Did:** one to three lines.
- **Proof:** what was run or delivered, and the result.
- **Not done:** each item, or "nothing".
- **Follow-ups:** possible issue titles, or "none".
- **Links:** the design file, the PR, the mockups.
