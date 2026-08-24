# AGENTS.md

## Environment

- The project venv is `.venv/` (Python 3.14). It ships no pip binary; bootstrap with `.venv/bin/python -m ensurepip` if missing.
- `pip install .` works and installs `dukpy==0.6.0` from a cp314 wheel plus `dukpy-dom`.
- Build artifacts (`build/`, `*.egg-info/`) are gitignored and must be removed after local installs.
- `runtime.js` is shipped as package data and loaded by `interpreter.py` from the package directory.
- Verify installed behavior from outside the source tree (e.g. `/tmp`) so the source checkout is not on `sys.path`.
- The venv holds a stale non-editable `pip install .` copy of dukpy-dom in `site-packages`; edits to source files do not affect it. To test edited code, load `runtime.js` from source directly via `dukpy.JSInterpreter`, or reinstall and remove `build/` and `*.egg-info/` afterwards.
- Run pytest as `.venv/bin/python -m pytest` from the repo root (source wins via `sys.path[0]`); a bare `pytest`/`PYTHONPATH`-less run from elsewhere imports the stale `site-packages` copy and fails on new symbols.

## dukpy runtime boundary

- `evaljs(code, **kwargs)` exposes kwargs to JS as the `dukpy` global (`dukpy.label`), not as bare identifiers.
- dukpy cannot marshal cyclic JS objects: an evaljs call whose last expression returns a DOM node raises `JSRuntimeError: circular reference`. Have scripts end with a primitive or `undefined;` and read DOM state via `html()`.
- dukpy drains the promise microtask queue at every evaljs call boundary: microtasks scheduled in one call run before the next evaljs body executes, so Vue's Promise-based updates need no manual flushing.

## Development

- Verify the whole workflow of .github/workflows/ci.yml before considering any task completed
