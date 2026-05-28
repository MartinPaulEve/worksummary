# worksummary

A command-line tool for logging daily work items and producing a Microsoft Teams-ready summary.

## Install

```bash
uv sync
```

## Usage

```bash
uv run worksummary add "Fixed bug 128 https://github.com/example/repo/issues/128"
uv run worksummary ls
uv run worksummary summary
```

See `docs/superpowers/specs/` for design details.
