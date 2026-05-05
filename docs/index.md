# ISCO Documentation Hub

Welcome to the central documentation hub for the DCCA ISCO team. This site aggregates curated documentation from across our GitHub repositories and standalone sources into one searchable place.

## How this works

- Each documented system maintains its source-of-truth documentation in its own GitHub repository.
- This hub pulls **selected** files from those repositories on a schedule (and on demand).
- The Git source repo remains the canonical version. This site is a read-only, rendered, redacted view for stakeholders.

If you spot an issue or have a correction, please open a pull request against the source repository (linked at the top of each document) — not against `isco-docs-hub` itself.

## Currently published

- **WordPress (cca.hawaii.gov)** — architecture reference, security review

## Adding more documentation

If you maintain a system at DCCA ISCO and want its docs included here, open a pull request to [`isco-docs-hub`](https://github.com/DCCA-ISCO/isco-docs-hub) updating `config/sources.yaml` with the repository, branch, and files you want pulled.

## Privacy and redaction

This site is publicly accessible. Documents pulled from source repositories are filtered through `config/redactions.yaml` before publishing — AWS account IDs, resource identifiers, and ARNs are replaced with placeholders. CIDR ranges and high-level architecture content are preserved. The Git source remains unredacted for operators.
