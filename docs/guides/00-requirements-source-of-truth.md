# Requirements Source of Truth

To avoid drift between implementation and product intent, this repository expects the original product requirements to be versioned in Git.

## Required artifact

- `docs/specs/original-spec.md` (or a folder under `docs/specs/original-spec/`)

## Why this is required

- Cloud-mode implementation includes behavior-sensitive decisions (session bootstrap shape, proxy trust, CORS policy, and LLM structured output contracts).
- These must map to explicit, reviewable requirements rather than inferred assumptions.

## How to add the missing spec docs

From your local machine (where the docs currently exist), copy your spec into this repository and commit:

```bash
mkdir -p docs/specs
cp /path/to/original-spec docs/specs/original-spec.md
# or: cp -R /path/to/original-spec docs/specs/original-spec

git add docs/specs/original-spec.md docs/specs/original-spec
# add whichever path you used

git commit -m "docs: add original product requirements spec"
```

## Implementation gate

Before shipping additional cloud-mode behavior changes, confirm:

- [ ] All MUST/SHOULD requirements are extracted from original spec.
- [ ] A traceability matrix exists from requirement -> file(s)/tests.
- [ ] Acceptance tests map 1:1 to spec success criteria.
