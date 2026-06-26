# Layout Rules

## Content Restructuring

- Use the first H1 as the cover title and remove it from the body when it is clearly the document title.
- If the body starts at H2 or H3, shift headings upward so the PDF starts with a readable H1/H2/H3 hierarchy.
- Generate the table of contents from normalized H1/H2/H3 headings.
- Render the table of contents as a consulting-style outline: H1 becomes a chapter band, H2 becomes an indented section row, and H3 becomes a lighter local point. Do not present all TOC levels as identical cards.
- Keep the original content order unless a heading normalization is needed for readability.

## Cover

- A cover should include title, document type, optional author, optional date, and template label.
- The cover should feel like a business report, not a poster.
- Avoid decorative overload. Use whitespace and restrained accent color.
- The cover page should occupy the full first page. Do not let body-page print margins shrink the cover background.

## Body

- H1 marks major sections and may use a divider.
- H2 marks scan-level subsections and should be visually stronger than paragraph text.
- H3 marks local groups and should stay compact.
- Paragraphs should have comfortable Chinese line height.

## Pagination

- Avoid headings stranded at the bottom of a page.
- Avoid splitting callouts, tables, code blocks, and figures across pages when possible.
- Keep table text wrapped; do not depend on horizontal scrolling in print.
- Code blocks should wrap long lines to preserve page width.
- Reserve enough top and bottom page margin for rendered headers and footers.
- Footers should stay minimal: no generator label, no author fallback text, and no `Page` prefix before the page counter.
- Treat Markdown horizontal rules as spacing in polished reports unless the selected template explicitly needs visible section rules.

## Diagrams

- Detect fenced ASCII diagrams and formula blocks before applying code-block styling.
- Use visual cards, matrices, flows, hubs, and layer stacks to preserve the author's structure while improving readability.
- Keep a diagram intact on one page when possible, even if that creates some whitespace before the diagram.

## Images

- Resolve relative images from the Markdown file directory.
- Constrain images to page width.
- Use alt text or image title as the caption when available.
