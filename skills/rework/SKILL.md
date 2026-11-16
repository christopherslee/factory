---
name: rework
description: Revise the work of one factory issue after an owner rework note. Use only when a factory work session brief says `/rework <ID>`, or when the owner runs `/rework` with a factory issue ID such as FACTORY-12.
---

# Rework

You are a work session of the software factory. Run this skill as `/rework <ID>`, for example `/rework FACTORY-12`. `<N>` is the issue number, `<prefix>` is the issue prefix in lowercase, and `<slug>` is a short name from the issue title. Do only this issue.

## Start

1. Run `factory show <ID>` and `factory resolve <ID>`. The output of `resolve` gives the foreman name.
2. Run `factory status <foreman> --json`. Take `root`, `home`, `designs`, `mockups` and `repos` from the output. Read `CLAUDE.md` in `root`, and in `home` if it is a different folder.
3. List `<home>/.claude/skills/`. Read each `SKILL.md` whose description applies to this stage, and follow it. Use the tools in `<home>/bin` and the data in `<home>/data` as `CLAUDE.md` in the project home tells.
4. Check the precondition of this skill (table below). If it is not true, change nothing, report, and stop. A second start of the same skill is thus safe.

| Skill | Precondition |
|---|---|
| `design` | The stage is In Design. The `rework` flag is not set. |
| `develop` | The stage is In Dev. The `rework` flag is not set. The file `<designs>/<N>-*.md` is there. |
| `ship` | The stage is Waiting for Verification. A `verified` event comes after the last agent move. |
| `rework` | The `rework` flag is set. |

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
