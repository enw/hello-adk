# Issue tracker: Local Markdown

Specs and tickets live in `.scratch/`, tracked in Git.

- One feature per directory: `.scratch/<feature-slug>/`.
- Spec: `spec.md`.
- Tickets: `issues/<NN>-<slug>.md`, numbered from `01`.
  One file per ticket, never a combined tickets file.
- Triage state: `Status:` near the top, using triage-labels.md.
- Dependencies: `Blocked by: NN, NN` near the top.
- Comments: append under `## Comments`.

"Publish to the issue tracker" means create the appropriate file.
"Fetch a ticket" means read its referenced file.

## Wayfinding

- Map: `.scratch/<effort>/map.md`, containing Notes,
  Decisions-so-far, and Fog sections.
- Child tickets: `issues/<NN>-<slug>.md`.
- `Type:` is research, prototype, grilling, or task.
- Wayfinding statuses use open, claimed, or resolved.
- Frontier: first numbered open, unclaimed ticket whose
  dependencies are all resolved.
- Claim: save `Status: claimed` before working.
- Resolve: append `## Answer`, set `Status: resolved`,
  and add a summary and link to the map's Decisions-so-far.
