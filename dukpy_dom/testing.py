# DONE(EVO-016): DOM inspection methods
# Why:
# - Python needs to read and verify DOM state for testing
# Done:
# - Methods to get HTML, text, attributes from Python
# - Can inspect any element in the DOM
# Non-Goals:
# - Do not implement full browser DevTools API
# - Do not add debugging utilities yet

# DONE(EVO-017): Interaction helpers
# Why:
# - UI tests need to simulate user interactions
# Done:
# - click, type_text, fill_in, select_option helpers implemented
# - Helpers dispatch appropriate DOM events
# Non-Goals:
# - Do not implement complex interaction sequences
# - Do not simulate keyboard shortcuts

# DONE(EVO-018): Assertion helpers
# Why:
# - Tests need to verify DOM state and content
# Done:
# - assert_html, assert_text, assert_attribute, assert_has_class implemented
# - Helpers provide clear error messages
# Non-Goals:
# - Do not implement full testing framework
# - Do not add matchers for complex selectors

# DONE(EVO-019): Waiting utilities
# Why:
# - Async UI updates need to be waited for
# Done:
# - wait_for, wait_for_element, wait_for_text implemented
# - Utilities use polling with configurable timeout
# Non-Goals:
# - Do not implement async/await based waiting
# - Do not add retry logic for flaky tests

import time


class DomInspector:
    """Read-only DOM inspection for UI tests: HTML, text, and attributes.

    Wraps a :class:`~dukpy_dom.interpreter.VirtualDomInterpreter` and locates
    elements with the JS-side querySelector engine. Methods return None when
    the selector matches no element.
    """

    def __init__(self, interpreter):
        self._interpreter = interpreter

    def html(self, selector=None):
        """Return serialized HTML of the whole page, or of the first element matching ``selector``.

        :param str selector: Optional CSS selector locating one element.
        """
        if selector is None:
            return self._interpreter.html()
        # IIFE keeps `el` out of the shared global scope so user scripts can
        # declare their own `el` without clashing.
        return self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector); return el ? el.toHTML() : null; })();",
            selector=selector,
        )

    def text(self, selector):
        """Return the text content of the first element matching ``selector``.

        :param str selector: CSS selector locating one element.
        """
        return self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector); return el ? el.textContent : null; })();",
            selector=selector,
        )

    def attribute(self, selector, name):
        """Return one attribute value of the first element matching ``selector``.

        :param str selector: CSS selector locating one element.
        :param str name: Attribute to read.
        """
        return self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector); return el ? el.getAttribute(dukpy.name) : null; })();",
            selector=selector,
            name=name,
        )

    def attributes(self, selector):
        """Return all attributes of the first element matching ``selector`` as a dict.

        :param str selector: CSS selector locating one element.
        """
        return self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector); return el ? el.attributes : null; })();",
            selector=selector,
        )


class DomInteractor:
    """Simulate user actions (click, type, select) on the virtual DOM.

    Wraps a :class:`~dukpy_dom.interpreter.VirtualDomInterpreter` and locates
    elements with the JS-side querySelector engine. Each action dispatches the
    DOM event a real user action would fire, so mounted components handle it.
    """

    def __init__(self, interpreter):
        self._interpreter = interpreter

    def click(self, selector):
        """Click the first element matching ``selector``.

        Dispatches a bubbling ``click`` MouseEvent on the element.

        :param str selector: CSS selector locating one element.
        """
        self._act(selector, "el.dispatchEvent(new MouseEvent('click', {bubbles: true}));")

    def type_text(self, selector, text):
        """Type ``text`` into the input or textarea matching ``selector``.

        Dispatches a keydown, keypress, and keyup per character (each carrying
        the character as ``key``), then sets the control's value and dispatches
        an ``input`` event, so keyboard handlers, v-model bindings, and later
        assertions all observe the typing.

        :param str selector: CSS selector locating one element.
        :param str text: Text to type.
        """
        self._act(
            selector,
            "for (var i = 0; i < dukpy.text.length; i++) {"
            " var key = dukpy.text.charAt(i);"
            " el.dispatchEvent(new KeyboardEvent('keydown', {key: key, bubbles: true}));"
            " el.dispatchEvent(new KeyboardEvent('keypress', {key: key, bubbles: true}));"
            " el.dispatchEvent(new KeyboardEvent('keyup', {key: key, bubbles: true}));"
            " }"
            " el.value = dukpy.text;"
            " el.dispatchEvent(new Event('input', {bubbles: true}));",
            text=text,
        )

    def fill_in(self, selector, value):
        """Set the value of the input or textarea matching ``selector``.

        Same effect as :meth:`type_text`: sets the control's value and
        dispatches an ``input`` event.

        :param str selector: CSS selector locating one element.
        :param str value: Value to set.
        """
        self.type_text(selector, value)

    def select_option(self, selector, value):
        """Select the option with ``value`` in the select matching ``selector``.

        Sets the select's value and dispatches a bubbling ``change`` event.

        :param str selector: CSS selector locating one element.
        :param str value: Option value to select.
        """
        self._act(
            selector,
            "el.value = dukpy.value; el.dispatchEvent(new Event('change', {bubbles: true}));",
            value=value,
        )

    def check(self, selector):
        """Check the checkbox or radio input matching ``selector``.

        Sets the control's checked state to true and dispatches a bubbling
        ``change`` event.

        :param str selector: CSS selector locating one element.
        """
        self._act(
            selector,
            "el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true}));",
        )

    def uncheck(self, selector):
        """Uncheck the checkbox or radio input matching ``selector``.

        Sets the control's checked state to false and dispatches a bubbling
        ``change`` event.

        :param str selector: CSS selector locating one element.
        """
        self._act(
            selector,
            "el.checked = false; el.dispatchEvent(new Event('change', {bubbles: true}));",
        )

    def trigger_event(self, selector, event_type):
        """Dispatch an event of type ``event_type`` on the first element matching ``selector``.

        Dispatches a bubbling event on the element, so any handler — a framework
        event binding or a plain ``addEventListener`` — observes it, like the
        other interaction helpers.

        :param str selector: CSS selector locating one element.
        :param str event_type: Event type to dispatch, e.g. ``"submit"``.
        """
        self._act(
            selector,
            "el.dispatchEvent(new Event(dukpy.event_type, {bubbles: true}));",
            event_type=event_type,
        )

    def _act(self, selector, action, **kwargs):
        """Run ``action`` on the first element matching ``selector``.

        ``action`` is a JS statement using ``el`` as the element; the IIFE
        keeps ``el`` out of the shared global scope, matching DomInspector.
        Raises ValueError when no element matches.
        """
        missing = self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector);"
            " if (!el) { return true; }"
            + action
            + " return false; })();",
            selector=selector,
            **kwargs,
        )
        if missing:
            raise ValueError(f"No element matches selector {selector!r}")


class DomAsserter:
    """Verify DOM state matches expectations, raising AssertionError on mismatch.

    Wraps a :class:`~dukpy_dom.interpreter.VirtualDomInterpreter` and locates
    elements with the JS-side querySelector engine, like DomInspector.
    Failures raise :class:`AssertionError` naming the selector, the expected
    value, and the actual value.
    """

    def __init__(self, interpreter):
        self._interpreter = interpreter

    def assert_html(self, expected, selector=None):
        """Assert the page HTML, or the element matching ``selector``, equals ``expected``.

        :param str expected: Expected serialized HTML.
        :param str selector: Optional CSS selector locating one element; the
            whole page is asserted when omitted.
        """
        if selector is None:
            actual = self._interpreter.html()
            if actual != expected:
                raise AssertionError(f"expected page HTML {expected!r}, got {actual!r}")
            return
        found, actual = self._read(selector, "el.toHTML()")
        self._expect(found, actual, expected, "to serialize to", selector)

    def assert_text(self, expected, selector=None):
        """Assert the page text, or the element matching ``selector``'s text, equals ``expected``.

        :param str expected: Expected text content.
        :param str selector: Optional CSS selector locating one element; the
            text of the whole page (``document.body``) is asserted when omitted.
        """
        if selector is None:
            actual = self._interpreter.evaljs("document.body.textContent;")
            if actual != expected:
                raise AssertionError(f"expected page text {expected!r}, got {actual!r}")
            return
        found, actual = self._read(selector, "el.textContent")
        self._expect(found, actual, expected, "to have text", selector)

    def assert_attribute(self, selector, name, expected):
        """Assert the ``name`` attribute of the element matching ``selector`` equals ``expected``.

        :param str selector: CSS selector locating one element.
        :param str name: Attribute to check.
        :param str expected: Expected attribute value.
        """
        found, actual = self._read(selector, "el.getAttribute(dukpy.name)", name=name)
        self._expect(found, actual, expected, f"attribute {name!r} to be", selector)

    def assert_has_class(self, selector, class_name):
        """Assert the element matching ``selector`` has ``class_name`` in its class list.

        :param str selector: CSS selector locating one element.
        :param str class_name: Class to check for.
        """
        found, actual = self._read(selector, "el.className")
        if not found:
            raise AssertionError(f"no element matches selector {selector!r}")
        if class_name not in actual.split():
            raise AssertionError(
                f"expected element {selector!r} to have class {class_name!r}, got {actual!r}"
            )

    def _read(self, selector, expr, **kwargs):
        """Evaluate ``expr`` (using ``el``) on the first element matching ``selector``.

        Returns ``(found, value)``: ``found`` is False when no element matches;
        ``value`` is the expression's result otherwise (None when an attribute
        is absent). The IIFE keeps ``el`` out of the shared global scope,
        matching DomInspector and DomInteractor.
        """
        return self._interpreter.evaljs(
            "(function(){ var el = document.querySelector(dukpy.selector);"
            " if (!el) { return [false, null]; }"
            " return [true, (" + expr + ")]; })();",
            selector=selector,
            **kwargs,
        )

    def _expect(self, found, actual, expected, description, selector):
        """Raise AssertionError unless the element exists and ``actual`` equals ``expected``.

        ``description`` completes the failure message, e.g. ``"to have text"``.
        """
        if not found:
            raise AssertionError(f"no element matches selector {selector!r}")
        if actual != expected:
            raise AssertionError(
                f"expected element {selector!r} {description} {expected!r}, got {actual!r}"
            )


class DomWaiter:
    """Wait for the virtual DOM to reach an expected state.

    Wraps a :class:`~dukpy_dom.interpreter.VirtualDomInterpreter` like the
    other helpers and polls the DOM until the condition holds or the timeout
    expires. A timed-out wait raises :class:`TimeoutError` naming the wait and
    the timeout.
    """

    # Poll interval; short enough that waits feel immediate, long enough that
    # polling stays cheap.
    _INTERVAL = 0.05

    def __init__(self, interpreter, timeout=5.0):
        self._interpreter = interpreter
        self._timeout = timeout

    def wait_for(self, condition, timeout=None, description="condition"):
        """Poll ``condition`` until it returns a truthy value.

        ``condition`` is a zero-argument callable checked on every poll.
        ``timeout`` (seconds) overrides the waiter's default. Returns as soon
        as the condition holds; raises :class:`TimeoutError` after the timeout
        expires, naming ``description`` so the failure identifies the wait.

        :param callable condition: Polled repeatedly until truthy.
        :param float timeout: Seconds to poll before failing.
        :param str description: Named in the timeout error.
        """
        limit = self._timeout if timeout is None else timeout
        deadline = time.monotonic() + limit
        while True:
            if condition():
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"timed out after {limit:g}s waiting for {description}"
                )
            time.sleep(self._INTERVAL)

    def wait_for_element(self, selector, timeout=None):
        """Wait until an element matching ``selector`` exists in the DOM.

        :param str selector: CSS selector locating the awaited element.
        :param float timeout: Seconds to poll before failing.
        """
        self.wait_for(
            lambda: self._interpreter.evaljs(
                "(function(){ return !!document.querySelector(dukpy.selector); })();",
                selector=selector,
            ),
            timeout=timeout,
            description=f"element {selector!r} to appear",
        )

    def wait_for_text(self, selector, expected, timeout=None):
        """Wait until the first element matching ``selector`` has text ``expected``.

        :param str selector: CSS selector locating the awaited element.
        :param str expected: Text the element must have.
        :param float timeout: Seconds to poll before failing.
        """
        self.wait_for(
            lambda: self._interpreter.evaljs(
                "(function(){ var el = document.querySelector(dukpy.selector);"
                " return el && el.textContent === dukpy.expected; })();",
                selector=selector,
                expected=expected,
            ),
            timeout=timeout,
            description=f"text of {selector!r} to equal {expected!r}",
        )

# DONE(EVO-171): Make type_text dispatch keydown keypress and keyup events before the input event
# Why:
# - The BDD spec (F-TESTING-INTERACTIONS-S007) expects typing to fire keydown, keypress,
#   and keyup events carrying the pressed key before the input event, so keyboard handlers
#   observe the typing; KeyboardEvent (EVO-161) exists as this unit's dependency.
# Done:
# - DomInteractor.type_text dispatches a bubbling keydown, keypress, and keyup per character
#   (each carrying the character as key), then sets the control's value and dispatches the
#   single input event, so v-model bindings and value assertions keep working and keyboard
#   handlers see every pressed key.
# Non-Goals:
# - Do not simulate key auto-repeat, keyboard shortcuts, focus, or input method
#   composition (isComposing); EVO-161 already scoped those out.

# DONE(EVO-181): Add check and uncheck interaction helpers for checkbox and radio inputs
# Why:
# - The BDD spec (F-TESTING-INTERACTIONS-S004/S005) checks and unchecks a checkbox
#   and expects the checked state to change with a change event dispatched; the
#   checked property (EVO-121) exists as this unit's dependency.
# Done:
# - DomInteractor.check and DomInteractor.uncheck set the control's checked state
#   to true/false and dispatch a bubbling change Event, reusing the _act IIFE
#   pattern shared with select_option.
# Non-Goals:
# - Do not dispatch click events, toggle state, or validate that the matched
#   element is a checkbox or radio input.

# DONE(EVO-191): Add a generic trigger_event helper that dispatches a named event on a matching element
# Why:
# - The BDD spec (F-TESTING-INTERACTIONS-S006) triggers a submit event on a form
#   and expects the form's handler to observe it; the React and Svelte evolutions
#   (EVO-221, EVO-223) also need Python-side dispatch of named events to drive
#   framework event handlers.
# Done:
# - DomInteractor.trigger_event(selector, event_type) dispatches a bubbling Event
#   of the given type on the first element matching the selector, reusing the
#   _act IIFE pattern shared with click/type_text/select_option.
# - Raises ValueError naming the selector when no element matches, like the other
#   interaction helpers.
# Non-Goals:
# - Do not add event-options parameters (detail, cancelable, ...); the BDD spec
#   needs only a named bubbling event.
