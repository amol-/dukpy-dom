"""A compiled Svelte component mounts into the virtual DOM and renders."""

import os

from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.testing import DomInteractor

# Real Svelte 4.2.20 compile of a counter component (svelte.compile), bundled
# by esbuild 0.28.2 into an IIFE exposing the component class as
# CounterBundle.default. Generated offline with node tooling; the banner
# comment in the fixture records provenance, and the fixture must not be
# edited by hand.
_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "svelte-counter.bundle.js"
)


def _with_compiled_component():
    """Return an interpreter with the compiled Svelte counter component loaded.

    The component class is exposed as ``CounterBundle.default``; mounting it
    with a target element is a separate evaljs call, like a real test would do.
    """
    interpreter = VirtualDomInterpreter()
    with open(_FIXTURE, encoding="utf-8") as bundle:
        interpreter.evaljs(bundle.read())
    return interpreter


def test_compiled_svelte_component_mounts_and_renders():
    interpreter = _with_compiled_component()
    interpreter.evaljs(
        "new CounterBundle.default({ target: document.body }); undefined;"
    )
    assert interpreter.html() == (
        '<html><body><button id="counter">Count: 0</button></body></html>'
    )


def test_click_helper_updates_mounted_svelte_component():
    # F-FRAMEWORK-SVELTE-S002: the click helper drives the component's event
    # handler (Svelte's listen/inc) and the re-rendered output shows in html().
    interpreter = _with_compiled_component()
    interpreter.evaljs(
        "new CounterBundle.default({ target: document.body }); undefined;"
    )
    DomInteractor(interpreter).click("#counter")
    assert interpreter.html() == (
        '<html><body><button id="counter">Count: 1</button></body></html>'
    )
