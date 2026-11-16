# FACTORY-12: Write the stage skills: design, develop, ship, rework

## Summary

- Four skills replace the four briefs in the foreman skill: `design`, `develop`, `ship`, `rework`. Each skill name is equal to a `next_action` value of the CLI.
- Each skill keeps the work session inside the issue. A new idea goes into the report as a follow-up. It does not go into the work.
- Each skill follows how the owner works: options to pick by letter, the real artifact in front of the owner before verification, and a short report that states the end state.
- A project can have a separate project home (FACTORY-26). The skills take each folder from `factory status --json` and contain no fixed path.
- Four decisions wait for the owner. Each has a default. See "Decisions for the owner".

## Goal

A work session gets its procedure from a skill, not from a one-sentence brief. The procedure is the same for each issue of each project, and it matches the habits of the owner at each stage.

The test of the foreman skill found one defect: a design session added a feature that the issue did not ask for. The skills must prevent this.

## Evidence: how the owner works

The source is the owner's own messages in approximately 40 recent Claude Code sessions (approximately 370 messages). Only general patterns are written here.

| Stage | Habit of the owner | Effect on the skill |
|---|---|---|
| Design | Asks for options before a build ("mock it up first"). Selects by letter, and frequently mixes two options or changes one detail. | The design gives 2–3 labeled options (A, B, C) and one recommendation. For a change that a user sees, the options are mockup images. |
| Design | Asks for the approach first on logic work ("tell me how you want to solve it, then we implement it"). | For work that a user does not see, the options are a short table, not images. |
| Design | Answers numbered questions with numbered short answers ("1. yes 2. B"). | Open questions are numbered, and each has a default. |
| Design | Wants the agent to decide and continue, not to stop. Wants a stop only for a decision that is hard to undo. | The session uses the default and continues. It uses `factory block` only for a decision that is hard to undo. |
| Design | Removes scope ("leave it for now", "not a real use case yet"). Backs out a feature that makes the product more complicated. | The design has an "Out of scope" list. The smallest design is the default. |
| Develop | Gives one small request at a time. Asks for a commit after each step that works. | Small commits, one for each unit that is verified. |
| Develop | Reviews the real artifact on the real device, not a description. Asks for the new build before each review. Asks "what am I reviewing?". | The develop skill delivers the build to the place where the owner reviews it, and the PR has a "What to check" list. |
| Develop | Asks for an update from the main branch before the review of a branch. | The skill merges the main branch into the issue branch before the tests and the delivery. |
| Develop | Sends ideas that come during work to the backlog ("add a todo"). | Follow-ups go into the report. They are not built. |
| Develop | Asks "commit, if it is safe to commit". | The skill looks at the diff for secrets and private data before each push. |
| Ship | Gives a short approval ("looks good, merge and close"). Later asks if the code is merged and the issue is closed. | The ship report states each end state in one line: merged, tests on main, issue closed, stage. |
| Ship | Is frequently away from the laptop and reads on a phone. | Reports are short, and the first lines contain the result. |
| Rework | Gives one short and specific note, usually one visible change. Does many fast rounds. | The rework skill does only what the note says and makes the round fast: revise, deliver again, report. |
| Rework | Puts a new idea in the same message as an approval ("we will iterate on this later, make a backlog item, merge for now"). | An idea for later becomes a follow-up, not work in this round. |
| Rework | Sometimes says "back it out". | The rework skill can revert the change and keep the issue. |

## Design

### Files

```
skills/design/SKILL.md
skills/develop/SKILL.md
skills/ship/SKILL.md
skills/rework/SKILL.md
```

The name of each skill is the `next_action` value that `factory status` prints. Thus the foreman skill needs no table from action to brief (*Model the Domain*).

Each skill takes one argument: the issue ID (`/design FACTORY-12`).

### Folders

A project can have three different places (FACTORY-26). No skill contains a fixed path. Each skill takes the folders from `factory status <foreman> --json`:

| Field | What it is | What a skill does there |
|---|---|---|
| `root` | The folder of `foreman.toml`. Its GitHub repo holds the issues. | Reads `CLAUDE.md`. |
| `home` | The project home. The default is `root`. | Reads `CLAUDE.md` (with `## Verify` and `## Ship`). |
| `designs`, `mockups` | Folders in the project home. | `design` and `rework` write here. `develop` reads here. |
| `repos[].path` | The code repos. | `develop`, `ship` and `rework` change code here, in the worktree of the session. |

One rule tells where a design is committed. It has two cases, and the skill finds the case with `git rev-parse --show-toplevel` in `home` and in the worktree:

- **The project home is in the repo of the worktree** (the factory itself, and each project without a `home` field whose code is in the folder of `foreman.toml`). The session writes to the same relative path in its worktree, not in the fixed checkout, and commits on branch `<prefix>-<N>-<slug>`. The design goes to the main branch with the code PR.
- **The project home is a different repo.** The session writes to `designs` and `mockups` directly and commits only its own files on the default branch of that repo, then pushes. No branch and no PR are made there.

Reason for the second case: the next session reads `designs` from the checkout of the project home. A design on a branch of that checkout is not visible there, and two sessions cannot have two branches in one checkout. Each issue writes only its own files (`<N>-<slug>.md`, `mockups/<N>-<slug>/`), so sessions do not write the same file (*Separate Before Serializing Shared State*). The stage on the board tells if a design is approved, not the branch.

### Change to the foreman skill

The table of four briefs is deleted (*Subtract Before You Add*). The brief of a work session becomes:

> You are the work session for `<ID>` (`<title>`) of foreman `<name>`. Run the skill `/<next_action> <ID>`. Do only this issue.

The other rules of the brief on `main` (the folders, never run a human command, `factory block` for a question, the form of the report) move into the skills. The paragraph that tells the foreman session to take the folders from `factory status` is also deleted from the foreman skill: the skills do this.

### Common part of each skill

Each skill has the same three blocks. A test makes sure that the text of these blocks is the same in the four files (*Encode Lessons in Structure*).

**Start**

1. Run `factory show <ID>` and `factory status <foreman> --json`. Take `root`, `home`, `designs`, `mockups` and `repos` from the output. Read `CLAUDE.md` in `root`, and in `home` if it is a different folder.
2. Check the precondition of the skill (table below). If it is not true, change nothing, report, and stop. A second start of the same skill is thus safe (*Make Operations Idempotent*).

| Skill | Precondition |
|---|---|
| `design` | The stage is In Design. The `rework` flag is not set. |
| `develop` | The stage is In Dev. The `rework` flag is not set. The file `<designs>/<N>-*.md` is there. |
| `ship` | The stage is Waiting for Verification. A `verified` event comes after the last agent move. |
| `rework` | The `rework` flag is set. |

**Rules**

- Do only what the issue asks (for `rework`: only what the note asks). When you find a different idea, a different defect or a possible improvement, do not build it and do not design it. Write it in the report below "Follow-ups", as a possible issue title.
- Never run `factory go|approve|verified|move|rework|unblock`. Do not run `factory new`: the owner decides what goes into the backlog.
- When a question has no answer in the issue, select the simplest option, write the decision down, and continue. Run `factory block <ID> "question"` and stop only if the decision is hard to undo.
- Write designs only in `designs` and mockups only in `mockups`. Change code only in the worktree of the session.
- Never write details of a different project in this repo, its issues or its PRs.
- Never write `Closes`, `Fixes` or `Resolves` with an issue number.

**End**

Run the stage command, then `factory release <ID>`. If the CLI refuses, report the refusal and stop. Then write the report in Simplified Technical English, with the result in the first line:

- **Did:** one to three lines.
- **Proof:** what was run or delivered, and the result.
- **Not done:** each item, or "nothing".
- **Follow-ups:** possible issue titles, or "none".
- **Links:** the design file, the PR, the mockups.

### `design`

1. Decide if the issue changes something that a user sees.
   - **Yes:** make 2–3 mockup images, labeled A, B and C, in `<mockups>/<N>-<slug>/`. Recommend one.
   - **No:** compare 2–3 approaches in a table. Recommend one.
2. Write `<designs>/<N>-<slug>.md` with these sections: summary (five lines maximum), goal, design, options that were compared, decisions for the owner, out of scope, limits, proof.
   - "Decisions for the owner" is a numbered list. Each item has a default. The design uses the defaults.
   - "Out of scope" lists what the design leaves out on purpose.
   - "Proof" states what the owner will look at on the real artifact to verify the work.
3. Commit as the rule in "Folders" tells.
4. Run `factory advance <ID>`.

The owner then says `approve` (the recommendation and the defaults are accepted) or `rework` with a short note ("B, with the colors of A"; "1. yes 2. no").

### `develop`

1. Read the design file in `designs` and each event after it. An owner note is stronger than the design text.
2. Work on branch `<prefix>-<N>-<slug>` of the code repo. Merge the main branch into it first.
3. Build in small units. For each unit: write the behavior test, write the code, run the tests, commit. Write the test first for logic that has no user interface.
4. Merge the main branch again. Run all the tests.
5. Look at the full diff for secrets and private data.
6. Do the `## Verify` section of `CLAUDE.md` in the project home. This section tells the session how to put the real artifact in front of the owner (for example: install the build on the review device, or start the app and make screenshots). If the section is not there, use the product as a user does and keep the output as proof.
7. Push the branch. Open a PR that names the issue as `Refs #<N>`. The PR body contains "What to check": three to five steps that the owner can do in two minutes, each with the expected result.
8. Run `factory advance <ID>`.

### `ship`

1. Merge the main branch into the issue branch. If there is a conflict that changes behavior, run `factory block` with a summary and stop.
2. Run all the tests on the branch.
3. Merge the PR. Delete the branch on the remote.
4. Run all the tests on the main branch. If they fail, run `factory block <ID> "the tests fail on main: <summary>"` and stop. Do not revert without the owner.
5. Do the `## Ship` section of `CLAUDE.md` in the project home, if it is there (for example: deliver the build from the main branch).
6. Run `factory advance <ID>`. This closes the issue.

The report starts with four lines: **Merged** (commit), **Tests on main** (result), **Issue** (closed or open), **Stage**.

### `rework`

1. Read the last `rework` note. The stage tells what to revise:

   | Stage | Revise |
   |---|---|
   | In Design, Ready for Dev | The design file and the mockups, in the place and on the branch that the rule in "Folders" tells. |
   | In Dev, Waiting for Verification | The code and the tests, on the same branch and the same PR of the code repo. If the note changes the design, also the design file. |

2. Do only what the note says. If the note has two possible meanings, use the smaller one and state it in the report.
3. Special notes:
   - A selection ("B", or "A with one part of B"): make the one result. Move the options that were not selected to "Options that were compared".
   - Numbered answers: write each answer into "Decisions for the owner" as decided.
   - "Back it out": revert the change. Keep the issue and its branch.
   - An idea "for later": write it as a follow-up. Do not build it.
4. For code: run all the tests, push, do the `## Verify` section again, and update "What to check" in the PR.
5. Run `factory reworked <ID>`. The stage does not change.

The report gives one line for each item of the note: what it was before, and what it is now.

### Change to the home template

`templates/home/CLAUDE.md` gets two empty sections, `## Verify` and `## Ship`, each with one line that explains its purpose. A project with a separate project home puts these two sections in the `CLAUDE.md` of the project home. The private details of a project (devices, commands, accounts) stay in the repos of that project. The skills contain none.

### Installation

`~/.claude/skills/` has one link for each skill folder. The README gets the four new `ln -s` lines next to the line for `foreman`. The links point to the fixed `main` checkout, so the skills are available after this issue is shipped.

## Options that were compared

| Option | Result |
|---|---|
| A. Four skills, one for each `next_action`, with a common part that a test keeps equal | **Selected.** A session loads only the procedure of its stage. The names come from the CLI, so the foreman skill holds no table. |
| B. One `work` skill with four sections | Not selected. No repeated text, but each session reads three procedures that it must not do. This is a risk for the scope defect. |
| C. Keep the briefs in the foreman skill and make them longer | Not selected. The foreman session carries all the text in each directive turn, and the owner cannot run a stage directly. |
| D. A shared rules file that the four skills refer to | Not selected. A session can fail to read the second file. Repeated text plus a test is more reliable (*Minimize Reader Load*). |

For the design of a project with a separate project home:

| Option | Result |
|---|---|
| Commit on the default branch of the project home | **Selected.** The design is at one fixed path for the owner and for the next session. |
| A branch in the project home (the brief on `main` says this) | Not selected. The `develop` session reads `designs` from the checkout and does not find the design. Nothing merges the branch. |
| A branch and a PR in the project home, and `ship` merges two PRs | Not selected. Two merges for one issue, and the owner must look in two places. |
| Keep each design in the code repo | Not selected. This removes what FACTORY-26 added. |

For the source of the folders:

| Option | Result |
|---|---|
| The skill reads `factory status <foreman> --json` | **Selected.** One source, no CLI change, and the owner can run a skill directly. |
| The foreman session writes the folders into each brief | Not selected. The paths are then in two places, and a skill that the owner starts has none. |
| `factory show` prints the folders | Not selected now. It is a CLI change, and this issue makes none. |

For follow-ups:

| Option | Result |
|---|---|
| The work session lists follow-ups in the report | **Selected.** The owner decides what goes into the backlog. |
| The work session runs `factory new` for each idea | Not selected. Agents can fill the backlog with issues that nobody asked for. |

## Decisions for the owner

1. **Skill names.** Default: `design`, `develop`, `ship`, `rework`, as the issue says. The risk: the owner says "ship it" in sessions that are not factory sessions, and a global skill named `ship` can start there. The precondition check stops it with no change. Alternative: `factory-design`, `factory-develop`, `factory-ship`, `factory-rework`.
2. **Follow-ups.** Default: the report lists them and the owner says `<name> new "title"`. Alternative: the work session creates the Backlog issues.
3. **Tests fail on main after the merge.** Default: block and wait for the owner. Alternative: the session reverts the merge commit, then blocks.

4. **Design of a project with a separate project home.** Default: the design is committed on the default branch of the project home, with no branch and no PR. Alternative: a branch and a PR in the project home, and `ship` merges both PRs.

## Out of scope

- No change to stages, transitions or `check_advance`.
- No new CLI command.
- No skill for the Backlog or for the Ready for Dev stage: no agent action is there.
- No automatic cleanup of worktrees after ship.
- No change to the hook. It continues to stop human commands in work sessions.

## Limits

- The scope rule is an instruction, not a check. The proof below shows if it holds for one issue. If a session adds scope again, the next step is a check of the diff against the design file.
- The quality of the delivery step depends on the `## Verify` section of each project. An empty section gives a weaker proof.
- A skill that is linked into `~/.claude/skills/` is visible in all sessions of the owner, also outside the factory. See decision 1.
- With a separate project home, a design is on the default branch of that repo before the owner approves it. The stage on the board is the only sign that it is approved.
- With a separate project home, two sessions can commit in one checkout at the same time. They write different files, but one `git commit` or `git push` can fail and must be tried again.
- The path with a separate project home is tested only with the first such project.
- The mockups of a private project are in its private project home. The skills never copy them into this repo.

## Proof

1. **Tests** (`tests/test_skills.py`):
   - For each `next_action` value that the CLI can print, `skills/<value>/SKILL.md` is there and its `name` is equal to the value.
   - The Rules block is the same text in the four skills.
   - The foreman skill does not contain the old brief table.
   - No skill contains the text `home repo` or a path that starts with `docs/designs` or `mockups/`: each path comes from the `designs` and `mockups` fields.
2. **Real run:** after this issue is shipped, one new issue goes from Backlog to Done. Its events show a `design` session, a `develop` session and a `ship` session, and one `rework` round. Each session report names the skill that it ran. The diff of that issue contains nothing that the issue did not ask for.
3. **Separate project home:** the first issue of a project with a `home` field has its design file in `designs` on the default branch of the project home, and its code PR contains no design file.
