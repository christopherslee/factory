# factory — home repo of foreman `fred`

This repo is the factory plugin (CLI `factory`) and also the home repo of foreman `fred`. Issue IDs: `FRED-1`.
The project name is `factory`. `fred` is only the name of its foreman. When the owner says "fred", they speak to the foreman of this project.

- `bin/factory` is the only writer of stage state. All stage rules are in `STAGES`, `TRANSITIONS` and `check_advance`.
- Run the tests: `python3 -m unittest discover -s tests -v`
- Write reports for the owner in ASD-STE100 Simplified Technical English.
- Sessions must run the installed plugin from a fixed `main` checkout, never from a worktree.

## This repo is public
- Never write details of a private project (names, code, issues, designs, data) in this repo, in its issues or in its PRs.
- `FRED-*` issues are public. Write only about the factory itself.
- The foreman registry is private. It lives outside this repo (`~/.config/factory/foremen.toml`).
