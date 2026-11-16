# {{title}} — foreman `{{name}}`

This is the home repo for foreman `{{name}}`. It holds the issues, docs, mockups and data.
The code is in the repos that `foreman.toml` lists.

## Rules for every session
- Refer to issues as `{{NAME}}-42`. Branches: `{{name}}-42-short-slug`.
- Change stages only with the `factory` CLI. Never edit the Project board or the `factory:*` labels directly.
- An agent can make one forward move after each human event. If `factory advance` refuses, stop and report.
- Designs go in `docs/designs/<number>-<slug>.md` and mockups go in `mockups/` of the project home: the `home` folder in `foreman.toml`, or this folder when `home` is not set. Data goes in `data/`.
- The project home is the workspace of the foreman: `docs/designs/`, `mockups/`, `data/`, `bin/` (tools), `.claude/skills/` (project skills). Code repos get only code.

## Project context
(Describe the product, users and constraints here.)

## Verify
(How a session puts the real artifact in front of the owner, for `try` and before verification. Give the commands, the device name or URL for `factory ready-to-try --where`, and the output that shows the build is ready: for example, the install command prints the bundle ID, or the server prints its URL.)

## Ship
(What a session does after the merge to main: for example, deliver the build from the main branch. Leave empty if nothing.)
