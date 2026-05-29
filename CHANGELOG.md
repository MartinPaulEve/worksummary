## 1.2.0 (2026-05-29)

### Feat

- **add**: support --before <prefix> to insert before an existing item

## 1.1.3 (2026-05-29)

### Fix

- **completion**: bypass env subprocess in fish completion

## 1.1.2 (2026-05-29)

### Fix

- **completion**: ship working fish completion script

## 1.1.1 (2026-05-29)

### Fix

- **ls**: compute prefix globally and wrap it in [brackets]

## 1.1.0 (2026-05-28)

### Feat

- **formatting**: use Unicode bold for headers and show date in ls
- **urls**: render footnote markers as Unicode superscript digits
- **cli**: wire add/ls/remove/replace/summary commands
- **formatting**: render Teams summary and colored ls output
- **storage**: add SQLite CRUD for work items
- **ids**: generate SHA-1 ids and resolve shortest unique prefixes
- **urls**: extract URLs and rewrite descriptions with [N] footnotes
- **dates**: parse and format ISO YYYY-MM-DD dates
- **paths**: resolve XDG-compliant database path
