---
name: tree
description: List directory structure as a tree with frontmatter summaries
category: builtin
tags: [file, directory, navigation]
---

# tree

List directory structure with frontmatter summaries.

## Arguments

| Arg | Type | Description |
|-----|------|-------------|
| path | string | Directory to list (default: cwd) |
| depth | integer | Max recursion depth (default: 3) |
| hidden | boolean | Show hidden files (default: false) |

## Frontmatter Extraction

For markdown files, extracts and displays inline summaries from YAML frontmatter:
- `summary`: Brief description (preferred)
- `title`: File title (fallback)
- `description`: Description (fallback)
- `protected`: Shows [protected] marker

## WHEN TO USE

- Exploring project structure
- Understanding folder organization
- Finding files before reading them
- Getting overview of a directory
- Discovering memory structure (markdown files with frontmatter)

## WHEN NOT TO USE

- Searching file contents (use grep)
- Finding files by pattern (use glob)
- Reading file contents (use read)

## Output

Tree-formatted directory listing with connectors. Directories are listed
before files. Markdown files show extracted frontmatter summaries inline.

```
project/
├── src/
│   ├── main.py
│   └── utils.py
├── memory/
│   ├── character.md - Agent persona definition
│   └── rules.md [protected] - Immutable behavior rules
└── README.md
```

## LIMITATIONS

- Large directories may produce very long output
- Hidden files excluded by default (use hidden=true to include)
- Symbolic links handled per platform

## TIPS

- Use before `read` to discover file paths
- Combine with `glob` for pattern matching
- Use `depth` to limit output for large directories
