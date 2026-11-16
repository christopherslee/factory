---
name: design
description: Write the design of one factory issue in the In Design stage. Use only when a factory work session brief says `/design <ID>`, or when the owner runs `/design` with a factory issue ID such as FACTORY-12.
---

# Design

You are a work session of the software factory. Run this skill as `/design <ID>`, for example `/design FACTORY-12`. `<N>` is the issue number, `<prefix>` is the issue prefix in lowercase, and `<slug>` is a short name from the issue title. Do only this issue.

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

## End

Run the stage command of the last step, then `factory release <ID>`. If the CLI refuses, report the refusal and stop. Then write the report in ASD-STE100 Simplified Technical English, with the result in the first line:

- **Did:** one to three lines.
- **Proof:** what was run or delivered, and the result.
- **Not done:** each item, or "nothing".
- **Follow-ups:** possible issue titles, or "none".
- **Links:** the design file, the PR, the mockups.
