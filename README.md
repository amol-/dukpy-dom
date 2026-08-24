# dukpy-dom

A virtual DOM and browserless UI-testing library for dukpy. It runs Vue 3,
React 18, and Svelte components in a persistent JavaScript interpreter so
Python can read DOM state as HTML and simulate user interactions — a
Cypress-like experience without a browser.

## Quick start

Every test follows the same journey: create a `VirtualDomInterpreter` (a
persistent JS engine with one virtual DOM), load a framework, mount a
component, and drive it with interaction helpers.

Scripts passed to `evaljs` must end with `undefined;` when their last
expression could be a DOM node — dukpy cannot marshal DOM nodes back to Python.

### Vue

```python
from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.testing import DomInteractor
from dukpy_dom.vue import load_vue

interpreter = VirtualDomInterpreter()
load_vue(interpreter)  # pinned Vue 3.5.13 browser build, offline

interpreter.evaljs(
    'document.body.innerHTML = \'<div id="app"></div>\';'
    'var app = Vue.createApp({'
    '  data: function() { return { count: 0 }; },'
    '  template: \'<button @click="count++">Count: {{ count }}</button>\''
    '});'
    'app.mount(\'#app\'); undefined;'
)
assert "Count: 0" in interpreter.html()

DomInteractor(interpreter).click("#app button")
assert "Count: 1" in interpreter.html()
```

### React

```python
from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.react import load_react
from dukpy_dom.testing import DomInteractor

interpreter = VirtualDomInterpreter()
load_react(interpreter)  # pinned React 18.3.1 builds, offline

interpreter.evaljs(
    'document.body.innerHTML = \'<div id="root"></div>\';'
    'function Counter() {'
    '  var s = React.useState(0);'
    '  return React.createElement(\'button\','
    '    {onClick: function() { s[1](s[0] + 1); }}, \'Count: \' + s[0]);'
    '}'
    'ReactDOM.createRoot(document.getElementById(\'root\'))'
    '  .render(React.createElement(Counter, null)); undefined;'
)
assert "Count: 0" in interpreter.html()

DomInteractor(interpreter).click("#root button")
assert "Count: 1" in interpreter.html()
```

### Svelte

The package ships no Svelte runtime: components are compiled with your own
Svelte version before the test, then the bundle loads like any script.

```python
from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.testing import DomInteractor

interpreter = VirtualDomInterpreter()
with open("counter.bundle.js", encoding="utf-8") as bundle:
    interpreter.evaljs(bundle.read())

interpreter.evaljs(
    "new CounterBundle.default({ target: document.body }); undefined;"
)
assert "Count: 0" in interpreter.html()

DomInteractor(interpreter).click("#counter")
assert "Count: 1" in interpreter.html()
```

Compile a component with your own Svelte version and bundle it as an IIFE that
exposes the component class (here as `CounterBundle.default`):

```js
// build.mjs — compile Counter.svelte with svelte@4, bundle with esbuild
import { compile } from "svelte/compiler";
import { build } from "esbuild";
import { readFileSync } from "node:fs";

const { js } = compile(readFileSync("Counter.svelte", "utf8"), {
  filename: "Counter.svelte",
});

await build({
  stdin: { contents: js.code, resolveDir: "." },
  bundle: true,  // inlines svelte/internal
  format: "iife",
  globalName: "CounterBundle",
  outfile: "counter.bundle.js",
});
```

`tests/fixtures/svelte-counter.bundle.js` is such a build (svelte@4.2.20,
esbuild 0.28.2), and `tests/test_svelte.py` shows the full mount-and-interact
journey.

## Testing with your own framework version

By default the pinned vendored builds load. To test against the framework
version your application uses, point the loader at your own browser builds
instead:

- Vue: `load_vue(interpreter, bundle="/path/to/vue.global.prod.js")`
- React: `load_react(interpreter, react_bundle="...", react_dom_bundle="...")`
  — `react-dom`'s UMD client build (React 18 exposes `createRoot`)
- Svelte: always your own version — the compile recipe above uses whatever
  `svelte/compiler` you install

The pinned defaults stay available for offline tests; `tests/test_vue.py` and
`tests/test_react.py` cover both paths.

## Interaction and assertion helpers

Beyond `DomInteractor` (click, type, fill, select, check, trigger), the package
ships `DomInspector` (read HTML, text, attributes), `DomAsserter` (assertions
with clear failure messages), and `DomWaiter` (poll until an element or text
appears). All wrap the same `VirtualDomInterpreter`.

## Product behavior

Canonical product behavior is described in [`features/`](features/).

The `.feature` files are the source of truth for what the software does. They are product specifications first and executable BDD scenarios second.

Implementation and delivery tracking belongs outside this directory. Stable feature and scenario IDs let other workflows refer back to the product behavior without making the spec a status surface.
