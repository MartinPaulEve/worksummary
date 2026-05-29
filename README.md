# worksummary

A command-line tool for logging daily work items and producing a Microsoft Teams-ready summary. Disclaimer/warning: produced with AI as a personal tool. Tested on Ubuntu Linux and nowhere else yet. Testing on Mac soon.

## Install

For development (from a clone of this repo):

```bash
uv sync
uv run pre-commit install
```

To install `worksummary` as a system-wide command (so you can run it without `uv run`):

```bash
uv tool install .                                          # from a local clone
uv tool install git+https://github.com/MartinPaulEve/worksummary.git   # from GitHub
```

The first `worksummary` invocation creates an SQLite database under `$XDG_DATA_HOME/worksummary/work.db` (or `~/.local/share/worksummary/work.db` if `XDG_DATA_HOME` is unset).

## Commands

```bash
# Add an item (defaults to today)
worksummary add "Fixed bug 128 https://github.com/example/repo/issues/128"
worksummary add "Reviewed yesterday's PR" --date 2026-05-27

# List items for a date (full hash; shortest globally-unique prefix highlighted in [red])
worksummary ls
worksummary ls --date 2026-05-27

# Remove an item by id prefix (shortest unique prefix or any longer one)
worksummary remove 6
worksummary remove 640ab2

# Replace an item (delete + add on the same date)
worksummary replace 6 "Fixed bug 128 and added regression test"

# Render a Teams-ready summary
worksummary summary
worksummary summary --date 2026-05-27
```

## Output

### `summary`

`summary` produces text that pastes cleanly into a Teams channel. Bold headers use Unicode Mathematical Bold characters (Teams does not render markdown bold on paste, so `**...**` would otherwise appear as literal asterisks). URL footnotes use Unicode superscript digits.

```
𝐖𝐨𝐫𝐤 — 𝐓𝐡𝐮 𝟐𝟖 𝐌𝐚𝐲 𝟐𝟎𝟐𝟔

- Fixed bug 128 [¹]
- Reviewed PR for new menu items [²][³]
- Pair-programmed on auth refactor

𝐑𝐞𝐟𝐞𝐫𝐞𝐧𝐜𝐞𝐬
1. https://github.com/example/repo/issues/128
2. https://github.com/example/repo/pull/42
3. https://github.com/example/repo/issues/88
```

### `ls`

`ls` shows each item's full SHA-1 hash with the shortest unique prefix wrapped in `[brackets]` and coloured red (when stdout is a TTY). The prefix is computed against every item in the database, so any prefix shown is safe to pass to `remove` or `replace`.

```
[6]4108de3b22ad344e8f074689ac0b01cc7042d81  2026-05-29 09:59  Today's task
[e]92c53fc94aa4302832746fc03b509bddd6472d5  2026-05-27 09:59  First yesterday item
[b]358859db34624f809dcfdf5c69383d6f457e1c5  2026-05-27 09:59  Second yesterday item
```

## Shell completion

`worksummary` supports tab completion for commands (`add`, `ls`, `remove`, …) and options (`--date`, …) in fish, bash, and zsh. You must have `worksummary` on your `$PATH` for completion to work — see [Install](#install) above to put it there.

### fish

The fish completion script Click 8.4 generates is broken (the parser indexes fields that aren't there, so nothing ever completes). This repo ships a working hand-written version at `completions/worksummary.fish` — copy it into your fish completions directory:

```fish
mkdir -p ~/.config/fish/completions
cp completions/worksummary.fish ~/.config/fish/completions/
```

Open a new shell. Then `worksummary a<TAB>` completes to `add`, and `worksummary add --d<TAB>` completes to `--date`.

### bash

```bash
mkdir -p ~/.local/share/bash-completion/completions
_WORKSUMMARY_COMPLETE=bash_source worksummary > ~/.local/share/bash-completion/completions/worksummary
```

Or, to load on demand, add this to your `~/.bashrc`:

```bash
eval "$(_WORKSUMMARY_COMPLETE=bash_source worksummary)"
```

### zsh

```zsh
mkdir -p ~/.zsh/completions
_WORKSUMMARY_COMPLETE=zsh_source worksummary > ~/.zsh/completions/_worksummary
```

Then ensure `~/.zsh/completions` is in your `$fpath` and `compinit` has been called — typically by adding to `~/.zshrc`:

```zsh
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit
```

## Development

```bash
uv run pytest
uv run ruff check
uv run ruff format
```

See `docs/superpowers/specs/` for the design document and `docs/superpowers/plans/` for the implementation plan.
