# {{title}} — foreman `{{name}}`

This is the home repo for foreman `{{name}}`. It holds the issues, docs, mockups and data.
The code is in the repos that `foreman.toml` lists.

## Rules for every session
- Refer to issues as `{{NAME}}-42`. Branches: `{{name}}-42-short-slug`.
- Change stages only with the `factory` CLI. Never edit the Project board or the `factory:*` labels directly.
- An agent can make one forward move after each human event. If `factory advance` refuses, stop and report.
- Designs go in `docs/designs/<number>-<slug>.md`. Mockups go in `mockups/`. Data goes in `data/`.

## Project context
(Describe the product, users and constraints here.)
