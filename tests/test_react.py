"""The pinned React bundles load offline, expose usable globals, and mount."""

import os
import shutil

from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.testing import DomInteractor


def _mounted(component_js):
    """Return an interpreter with React loaded and ``component_js`` rendered into #root.

    ``component_js`` runs with a ``root`` div (id "root") already in the body
    and must end with ``undefined;`` like any script whose last expression
    must not be a DOM node.
    """
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("react", "react-dom")
    interpreter.evaljs(
        "var root = document.createElement('div'); root.id = 'root';"
        "document.body.appendChild(root);" + component_js
    )
    return interpreter


def test_load_framework_react_exposes_react_globals():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("react", "react-dom")
    assert interpreter.evaljs("typeof React;") == "object"
    assert interpreter.evaljs("typeof ReactDOM;") == "object"
    assert interpreter.evaljs("typeof ReactDOM.createRoot;") == "function"


def test_load_framework_react_leaves_element_style_intact():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("react", "react-dom")
    assert interpreter.evaljs(
        "typeof document.createElement('div').style;"
    ) == "object"


def test_create_root_renders_element_markup():
    interpreter = _mounted(
        "var el = React.createElement('div', {id: 'hello'}, 'Hello React');"
        "ReactDOM.createRoot(root).render(el); undefined;"
    )
    assert interpreter.html() == (
        '<html><body><div id="root"><div id="hello">Hello React</div>'
        '</div></body></html>'
    )


def test_create_root_renders_into_get_element_by_id_container():
    # Mirrors the mount scenario: the container is located with
    # document.getElementById before createRoot mounts into it.
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("react", "react-dom")
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"root\"></div>';"
        "var el = React.createElement('div', null, 'Hello React');"
        "ReactDOM.createRoot(document.getElementById('root')).render(el); undefined;"
    )
    assert "<div>Hello React</div>" in interpreter.html()


def test_create_root_renders_stateful_component_initial_state():
    interpreter = _mounted(
        "function Counter() {"
        "  var s = React.useState(0);"
        "  return React.createElement('div', null, 'Count: ' + s[0]);"
        "}"
        "ReactDOM.createRoot(root).render(React.createElement(Counter, null)); undefined;"
    )
    assert "<div>Count: 0</div>" in interpreter.html()


def test_later_set_state_rerenders_mounted_component():
    # The setter is captured in useLayoutEffect, which runs after the commit
    # (the same capture pattern as Vue's mounted() hook), so a later evaljs
    # call can drive the component's state.
    interpreter = _mounted(
        "function Counter() {"
        "  var s = React.useState(0);"
        "  React.useLayoutEffect(function() { window.__setCount = s[1]; });"
        "  return React.createElement('div', null, 'Count: ' + s[0]);"
        "}"
        "ReactDOM.createRoot(root).render(React.createElement(Counter, null)); undefined;"
    )
    assert "Count: 0" in interpreter.html()
    interpreter.evaljs("window.__setCount(42); undefined;")
    assert "Count: 42" in interpreter.html()


def test_load_framework_react_loads_user_provided_bundles(tmp_path):
    # User-provided builds replace the pinned ones.
    react_bundle = tmp_path / "react.production.min.js"
    react_bundle.write_text("var React = {version: '9.9.9'};", encoding="utf-8")
    react_dom_bundle = tmp_path / "react-dom.production.min.js"
    react_dom_bundle.write_text("var ReactDOM = {version: '9.9.9'};", encoding="utf-8")
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework(str(react_bundle), str(react_dom_bundle))
    assert interpreter.evaljs("React.version;") == "9.9.9"
    assert interpreter.evaljs("ReactDOM.version;") == "9.9.9"


def test_user_provided_bundles_mount_component(tmp_path):
    # The real builds loaded from user paths (not the internal pinned defaults)
    # still mount and render into html().
    react_bundle = tmp_path / "react.production.min.js"
    react_source = os.path.join(os.path.dirname(__file__), "..", "dukpy_dom", "vendor", "react.production.min.js")
    shutil.copyfile(react_source, react_bundle)
    react_dom_bundle = tmp_path / "react-dom.production.min.js"
    react_dom_source = os.path.join(os.path.dirname(__file__), "..", "dukpy_dom", "vendor", "react-dom.production.min.js")
    shutil.copyfile(react_dom_source, react_dom_bundle)
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework(str(react_bundle), str(react_dom_bundle))
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"root\"></div>';"
        "var el = React.createElement('div', null, 'Hello React');"
        "ReactDOM.createRoot(document.getElementById('root')).render(el); undefined;"
    )
    assert "<div>Hello React</div>" in interpreter.html()


def test_click_helper_updates_mounted_react_component():
    # F-FRAMEWORK-REACT-S003: the click helper drives the component's event
    # handler (React's onClick) and the re-rendered output shows in html().
    interpreter = _mounted(
        "function Counter() {"
        "  var s = React.useState(0);"
        "  return React.createElement('button',"
        "    {onClick: function() { s[1](s[0] + 1); }}, 'Count: ' + s[0]);"
        "}"
        "ReactDOM.createRoot(root).render(React.createElement(Counter, null)); undefined;"
    )
    DomInteractor(interpreter).click("#root button")
    assert "<button>Count: 1</button>" in interpreter.html()
