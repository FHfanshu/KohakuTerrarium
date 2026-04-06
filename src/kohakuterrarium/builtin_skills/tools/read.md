---
name: read
description: Read file contents (required before write/edit)
category: builtin
tags: [file, io]
---

# read

Read file contents. Supports text files, images, and PDFs.

## SAFETY

- **You MUST read files before writing or editing them.** The write and edit
  tools will error if you haven't read the file first.
- Text output is capped at 200KB. Use offset/limit for large text files.
- Images are capped at 20MB.
- PDFs: use the `pages` argument to read in chunks. Do NOT use offset/limit
  for PDFs.

## Arguments

| Arg | Type | Applies to | Description |
|-----|------|------------|-------------|
| path | string | ALL | Path to file (required) |
| offset | integer | TEXT ONLY | Line to start from (0-based, default: 0) |
| limit | integer | TEXT ONLY | Max lines to read (default: all) |
| pages | string | PDF ONLY | Page range: "1-5", "3", "10-20" |

## File Type Behavior

**Text files** (source code, config, markdown, etc.):
Returns contents with line numbers (format: `line_num->content`).
Use offset/limit for specific ranges of large files.

**Images** (png, jpg, jpeg, gif, webp, svg, bmp, tiff, ico, heif, heic, avif):
Returns the image for visual inspection by the model. No text extraction;
the model sees the image directly.

**PDFs** (.pdf files):
Returns extracted text + rendered page images. Use the `pages` argument
to specify which pages to read. Do NOT use offset/limit for PDFs --
the tool will error if you try.
For large PDFs (>20 pages), you MUST provide a `pages` range.
Example: `read(path="paper.pdf", pages="1-10")`

**Binary files** (executables, compiled objects, etc.):
Rejected with an error. Use `bash` with `xxd`, `file`, or other tools
to inspect binary files.

## WHEN TO USE

- Examining source code or config files
- Checking file contents before editing
- Reading logs or text data
- Viewing images or screenshots
- Reading PDF documents

## Output Format

Text files:
```
     1->first line content
     2->second line content
     3->...
```

Lines longer than 2000 characters are truncated with a notice.

## LIMITATIONS

- UTF-8 encoding for text files (invalid bytes replaced)
- Very large text files should use offset/limit
- Images must be under 20MB
- PDFs require pymupdf (`pip install pymupdf`) for rendering

## TIPS

- Use `glob` first to find files by pattern, then `read` to examine them.
- Use `grep` to locate relevant lines, then `read` with offset/limit for context.
- For PDFs: `read(path="doc.pdf", pages="1-5")` -- always use pages=, never offset/limit.
- For images: `read(path="screenshot.png")` to see content visually.
- For large text files, read in chunks with offset/limit.
