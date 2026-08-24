# DONE(EVO-201): Ship pinned React 18 and ReactDOM client UMD builds and load them offline into the interpreter
# Why:
# - Tests must mount React components reproducibly and offline. Loading from a CDN breaks air-gapped runs and version pinning.
# Done:
# - The package ships pinned React 18 UMD builds (react and react-dom client) as package data, loaded with no network access.
# - load_react(interpreter) exposes React and ReactDOM globals, including ReactDOM.createRoot, in the interpreter's JS context.
# Non-Goals:
# - Do not wire createRoot mounting into the virtual DOM; that is EVO-211.

# DONE(EVO-211): Make ReactDOM createRoot render mount a component into the virtual DOM so html shows the rendered markup
# Why:
# - The BDD spec (F-FRAMEWORK-REACT-S002) mounts a component with
#   ReactDOM.createRoot(...).render(...) and expects html() to show the rendered
#   markup; mounting needed three runtime gaps filled.
# Done:
# - ReactDOM.createRoot(root).render(element) mounts into the virtual DOM: initial
#   renders, stateful components (useState), and re-renders from a later evaljs
#   call all show in html().
# - runtime.js exposes Document.addEventListener/removeEventListener/dispatchEvent
#   (aliased to Element's methods) because react-dom attaches a "selectionchange"
#   listener to the root container's ownerDocument.
# - runtime.js defines setTimeout/clearTimeout backed by queueMicrotask: react's
#   scheduler (no setImmediate/MessageChannel in dukpy) falls back to setTimeout,
#   and dukpy's evaljs-boundary microtask drain (EVO-091) commits the render
#   before the next evaljs body runs. The callback must not run synchronously:
#   react-dom assigns root.callbackNode after scheduleCallback returns, so a sync
#   timer leaves a stale completed task and ensureRootIsScheduled drops all later
#   updates.
# - runtime.js defines an empty HTMLIFrameElement constructor: react-dom's commit
#   phase checks `b instanceof window.HTMLIFrameElement` (getActiveElementDeep),
#   which throws "invalid 'instanceof' right operand" without it.
# - runtime.js adds document.getElementById (a querySelector('#id') wrapper), which
#   the mount scenario uses to locate the container.
# Non-Goals:
# - Do not wire the Python interaction helpers to React events; that is EVO-221.

"""React integration for dukpy-dom."""

import os

from dukpy_dom.interpreter import VirtualDomInterpreter

# Pinned React 18.3.1 UMD builds, vendored so tests run offline.
# Sources:
#   https://unpkg.com/react@18.3.1/umd/react.production.min.js
#   https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js
# sha256 (react): d949f1c3687aedadcedac85261865f29b17cd273997e7f6b2bfc53b2f9d4c4dd
# sha256 (react-dom): 35f4f974f4b2bcd44da73963347f8952e341f83909e4498227d4e26b98f66f0d
# The react-dom UMD build is React 18's client build: it exposes ReactDOM.createRoot.
_REACT = os.path.join(os.path.dirname(__file__), "vendor", "react.production.min.js")
_REACT_DOM_CLIENT = os.path.join(os.path.dirname(__file__), "vendor", "react-dom.production.min.js")

# React's UMD wrapper falls back to the `self` global when CommonJS/AMD are
# absent; dukpy only provides globalThis. Define it before loading the bundles.
_UMD_SHIM = "var self = globalThis;"


def load_react(interpreter, react_bundle=None, react_dom_bundle=None):
    """Load React browser builds into ``interpreter``.

    Reads the vendored bundles (react and react-dom client) from package data
    by default, so no network access is needed. Pass ``react_bundle`` and/or
    ``react_dom_bundle`` to load user-provided builds from paths instead, so a
    component is tested against the framework versions its application uses.
    Afterwards the interpreter's JS context exposes ``React`` and ``ReactDOM``
    globals usable with ``ReactDOM.createRoot(...).render(...)``.

    :param VirtualDomInterpreter interpreter: Interpreter to load React into.
    :param str react_bundle: Optional path to a user-provided React browser build.
    :param str react_dom_bundle: Optional path to a user-provided react-dom browser build.
    """
    if react_bundle is None:
        react_bundle = _REACT
    if react_dom_bundle is None:
        react_dom_bundle = _REACT_DOM_CLIENT
    return interpreter.load_framework(react_bundle, react_dom_bundle)

# DONE(EVO-221): Make interaction helpers drive React event handlers so the click helper updates a mounted React component's rendered HTML
# Why:
# - The BDD spec (F-FRAMEWORK-REACT-S003) clicks a button on a mounted React
#   counter component and expects html() to show the incremented counter, the
#   React analogue of the Svelte scenario EVO-223 already covers.
# Done:
# - DomInteractor.click on a mounted React component's button runs its onClick
#   handler and the re-rendered output shows in html(): the dispatched bubbling
#   click reaches react-dom's delegated listener at the root container, and
#   React 18 discrete events flush synchronously at the end of dispatch, so the
#   click helper needed no runtime changes. The test in tests/test_react.py
#   proves the wiring end-to-end.
# Non-Goals:
# - Do not add React-specific interaction helpers: the shared DomInteractor
#   (click/type_text/fill_in/select_option/trigger_event) is the intended
#   surface, the same one Svelte and Vue use.

# DONE(EVO-225): Allow load_react to load user-provided React and ReactDOM browser bundles instead of the pinned ones
# Why:
# - A component should be testable against the React version its application
#   uses, not only the pinned vendored build; this is the React analogue of
#   EVO-224's load_vue(bundle=...). The pinned bundles stay the default for
#   offline tests.
# Done:
# - load_react(interpreter, react_bundle=..., react_dom_bundle=...) accepts
#   optional paths to user-provided React and react-dom browser builds; when
#   omitted, the pinned vendored bundles load as before.
# - A fresh interpreter loading user-provided builds exposes React and ReactDOM
#   globals, and mounting a component into the document shows its rendered
#   markup in html().
# Non-Goals:
# - Do not validate the bundles' React versions or structure.
# - Do not add a plugin or multi-version system.
