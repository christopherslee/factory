# FACTORY-6: Give each foreman an issue prefix

## Goal

The issue ID names the project, and the foreman keeps its own name. For this repo: the issues are `FACTORY-6`, and the owner still says `fred go 6`.

## Design

`foreman.toml` gets one optional key, `prefix`. It has the same form as `name` (2-8 lowercase letters or digits, first a letter). Without the key, the prefix is the name, so other foremen do not change.

```toml
name = "fred"        # the owner says: fred go 6
prefix = "factory"   # the issue IDs are: FACTORY-6
```

- `Foreman.ref()` builds the ID from the prefix. This is the only place that builds an ID.
- A reference resolves by the name or by the prefix: `fred 6`, `fred-6` and `FACTORY-6` are the same issue.
- If a name or prefix belongs to more than one foreman, the CLI gives an error. It does not guess.
- The issue numbers do not change. The ID is not stored on GitHub, so issues 1, 2 and 4 also show as `FACTORY-1`, `FACTORY-2` and `FACTORY-4`. `FRED-4` still resolves, because `fred` is the foreman name. No compatibility code is necessary (*Outcome-Oriented Execution*).
- Branches use the prefix: `factory-6-issue-prefix`.

## Options that were compared

| Option | Result |
|---|---|
| A. Optional `prefix` key | **Selected.** One key, one changed line in `ref()`. |
| B. Rename the foreman to `factory` | Not selected. The owner wants the foreman name `fred`. |
| C. Use the repo name as the prefix | Not selected. A repo name can be longer than 8 characters or have a `-home` suffix. |

## Limits

- Old texts (commit messages, the titles of designs 2 and 4, old comments) still say `FRED-N`. They stay as they are.

## Proof

Tests: with a prefix, `factory new` prints the prefixed ID, all reference forms resolve to it, a bad prefix is an error, and a shared prefix is an error. In this repo: `factory resolve fred-6` and `factory resolve FACTORY-6` give `FACTORY-6`.
