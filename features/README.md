# Features

This directory contains the canonical product behavior specification.

The `.feature` files are:

- product documentation
- executable BDD scenarios
- stable contracts between product intent and implementation

They are not:

- test implementation files
- implementation instructions
- execution plans or progress trackers

## Layout

```text
features/
├── README.md
├── glossary.md
├── dom/
│   ├── dom-manipulation.feature
│   ├── element-api.feature
│   ├── namespaces.feature
│   ├── selectors.feature
│   └── style.feature
├── frameworks/
│   ├── react.feature
│   └── svelte.feature
├── interpreter/
│   └── python-api.feature
├── vue/
│   └── vue-component-rendering.feature
└── testing/
    ├── assertions.feature
    ├── interactions.feature
    └── waiting.feature
```

## Authoring rules

- One feature per file.
- One externally visible behavior per scenario.
- Every feature file has a stable `@feature:<FEATURE-ID>` tag.
- Every scenario has a stable `@id:<SCENARIO-ID>` tag.
- IDs must not change after they are referenced by plans, tests, or documentation.
- Step wording is part of the spec API.
- Prefer concrete examples over abstract prose.
- Prefer product vocabulary from `glossary.md`.
- Do not track implementation status here.
