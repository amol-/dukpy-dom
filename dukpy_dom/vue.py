# DONE(EVO-010): Vue 3 template compilation support
# Why:
# - dukpy-dom should support compiling Vue templates
# Done:
# - Vue 3 runtime can be loaded and used
# - Templates compile to render functions
# Non-Goals:
# - Do not bundle the Vue runtime here; runtime provisioning is EVO-101.
# - Do not implement Vue-specific optimizations yet

# DONE(EVO-011): Vue reactivity support
# Why:
# - Vue components need to react to state changes
# Done:
# - DOM mutations trigger Vue reactivity
# - Vue can track and update component state
# Non-Goals:
# - Do not implement Vue's reactivity system (use Vue's own)
# - Do not add Vue-specific debugging

"""Vue integration for dukpy-dom."""

# DONE(EVO-101): Ship a pinned Vue 3 browser build and load it offline
# Why:
# - Tests must mount Vue components reproducibly and offline. Loading from a CDN breaks air-gapped runs and version pinning.
# Done:
# - The package ships a pinned Vue 3 browser bundle (runtime plus template compiler) as package data.
# - A documented API loads it into the interpreter with no network access and exposes a Vue global usable with createApp/mount.
# Non-Goals:
# - Do not add React or Svelte bundles yet.
# - Do not add a plugin or multi-version system.

import os

from dukpy_dom.interpreter import VirtualDomInterpreter

# Pinned Vue 3.5.13 browser build (runtime + template compiler), vendored so
# tests run offline. Source: https://unpkg.com/vue@3.5.13/dist/vue.global.prod.js
# sha256: c459ba7cc8db65c982589fa5d64c7ff478877e8e5b0fd75683207cec6a4e89e8
_VUE_RUNTIME = os.path.join(os.path.dirname(__file__), "vendor", "vue.global.prod.js")


def load_vue(interpreter, bundle=None):
    """Load a Vue 3 browser build into ``interpreter``.

    Reads the vendored bundle (runtime plus template compiler) from package
    data by default, so no network access is needed. Pass ``bundle`` to load a
    user-provided Vue 3 browser build from a path instead, so a component is
    tested against the framework version its application uses. Afterwards the
    interpreter's JS context exposes a ``Vue`` global usable with
    ``Vue.createApp(...).mount(...)``.

    :param VirtualDomInterpreter interpreter: Interpreter to load Vue into.
    :param str bundle: Optional path to a user-provided Vue 3 browser build.
    """
    return interpreter.load_framework(bundle or _VUE_RUNTIME)

# DONE(EVO-224): Allow load_vue to load a user-provided Vue 3 browser bundle instead of the pinned one
# Why:
# - The BDD spec (F-VUE-RENDER-S004) loads Vue from a path to the user's own
#   browser bundle so a component is tested against the framework version its
#   application uses; the pinned bundle stays the default for offline tests.
# Done:
# - load_vue(interpreter, bundle=...) accepts an optional path to a user-provided
#   Vue 3 browser build; when omitted, the pinned vendored bundle loads as before.
# - A fresh interpreter loading a user-provided build exposes a Vue global
#   (typeof Vue is "object") and mounting a counter component into the document
#   body shows its rendered markup in html().
# Non-Goals:
# - Do not validate the bundle's Vue version or structure.
# - Do not add a plugin or multi-version system.
# - Do not change load_react; user-provided React bundles are EVO-225.
