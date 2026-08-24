"""DomInspector reads virtual-DOM state as plain Python values."""

import pytest

from dukpy_dom.interpreter import VirtualDomInterpreter
from dukpy_dom.testing import DomAsserter, DomInspector, DomInteractor, DomWaiter
from dukpy_dom.vue import load_vue


@pytest.fixture
def interpreter():
    interpreter = VirtualDomInterpreter()
    interpreter.evaljs("""
        var div = document.createElement('div');
        div.setAttribute('id', 'greeting');
        div.setAttribute('data-kind', 'button');
        div.textContent = 'hello';
        document.body.appendChild(div);
        undefined;
    """)
    return interpreter


@pytest.fixture
def inspector(interpreter):
    return DomInspector(interpreter)


def test_read_text_of_element(inspector):
    assert inspector.text('#greeting') == 'hello'


def test_read_attributes_as_dict(inspector):
    assert inspector.attributes('#greeting') == {'id': 'greeting', 'data-kind': 'button'}


def test_read_single_attribute(inspector):
    assert inspector.attribute('#greeting', 'data-kind') == 'button'
    assert inspector.attribute('#greeting', 'class') is None


def test_read_element_html(inspector):
    assert inspector.html('#greeting') == '<div data-kind="button" id="greeting">hello</div>'


def test_read_page_html(inspector):
    assert inspector.html() == '<html><body><div data-kind="button" id="greeting">hello</div></body></html>'


def test_missing_element_returns_none(inspector):
    assert inspector.text('#missing') is None
    assert inspector.attributes('#missing') is None
    assert inspector.attribute('#missing', 'data-kind') is None
    assert inspector.html('#missing') is None


def test_inspector_does_not_clobber_user_global_el(interpreter):
    inspector = DomInspector(interpreter)
    interpreter.evaljs("var el = 'user-value'; undefined;")
    assert inspector.html('#greeting') == '<div data-kind="button" id="greeting">hello</div>'
    assert inspector.text('#greeting') == 'hello'
    assert interpreter.evaljs("el;") == 'user-value'


def test_inspector_snippets_coexist_with_user_top_level_let_el(interpreter):
    inspector = DomInspector(interpreter)
    interpreter.evaljs("let el = 'user-value'; undefined;")
    assert inspector.attribute('#greeting', 'id') == 'greeting'
    assert inspector.attributes('#greeting') == {'id': 'greeting', 'data-kind': 'button'}
    assert interpreter.evaljs("el;") == 'user-value'


@pytest.fixture
def actor(interpreter):
    return DomInteractor(interpreter)


def test_click_dispatches_click_event(interpreter, actor):
    interpreter.evaljs("""
        var btn = document.createElement('button');
        btn.id = 'btn';
        btn.addEventListener('click', function() { btn.textContent = 'clicked'; });
        document.body.appendChild(btn);
        undefined;
    """)
    actor.click('#btn')
    assert interpreter.evaljs("document.querySelector('#btn').textContent;") == 'clicked'


def test_click_missing_element_raises(actor):
    with pytest.raises(ValueError, match="'#missing'"):
        actor.click('#missing')


def test_type_text_sets_value_and_dispatches_input(interpreter, actor):
    interpreter.evaljs("""
        var input = document.createElement('input');
        input.id = 'field';
        window.__inputEvents = 0;
        input.addEventListener('input', function() { window.__inputEvents++; });
        document.body.appendChild(input);
        undefined;
    """)
    actor.type_text('#field', 'hello')
    assert interpreter.evaljs("document.querySelector('#field').value;") == 'hello'
    assert interpreter.evaljs("window.__inputEvents;") == 1


def test_type_text_dispatches_keyboard_events_before_input(interpreter, actor):
    interpreter.evaljs("""
        var input = document.createElement('input');
        input.id = 'field';
        window.__events = [];
        ['keydown', 'keypress', 'keyup', 'input'].forEach(function(type) {
            input.addEventListener(type, function(event) {
                window.__events.push(type + ':' + (event.key || ''));
            });
        });
        document.body.appendChild(input);
        undefined;
    """)
    actor.type_text('#field', 'a')
    assert interpreter.evaljs("window.__events;") == [
        'keydown:a', 'keypress:a', 'keyup:a', 'input:'
    ]
    assert interpreter.evaljs("document.querySelector('#field').value;") == 'a'


def test_fill_in_sets_value(interpreter, actor):
    interpreter.evaljs("""
        var input = document.createElement('input');
        input.id = 'field';
        document.body.appendChild(input);
        undefined;
    """)
    actor.fill_in('#field', 'filled')
    assert interpreter.evaljs("document.querySelector('#field').value;") == 'filled'


def test_select_option_sets_value_and_dispatches_change(interpreter, actor):
    interpreter.evaljs("""
        var select = document.createElement('select');
        select.id = 'pick';
        window.__changeEvents = 0;
        select.addEventListener('change', function() { window.__changeEvents++; });
        ['a', 'b'].forEach(function(value) {
            var opt = document.createElement('option');
            opt.value = value;
            opt.textContent = value;
            select.appendChild(opt);
        });
        document.body.appendChild(select);
        undefined;
    """)
    actor.select_option('#pick', 'b')
    assert interpreter.evaljs("document.querySelector('#pick').value;") == 'b'
    assert interpreter.evaljs("window.__changeEvents;") == 1


def test_check_sets_checked_and_dispatches_change(interpreter, actor):
    interpreter.evaljs("""
        var input = document.createElement('input');
        input.id = 'agree';
        input.type = 'checkbox';
        window.__changeEvents = 0;
        input.addEventListener('change', function() { window.__changeEvents++; });
        document.body.appendChild(input);
        undefined;
    """)
    actor.check('#agree')
    assert interpreter.evaljs("document.querySelector('#agree').checked;") is True
    assert interpreter.evaljs("window.__changeEvents;") == 1


def test_uncheck_clears_checked_and_dispatches_change(interpreter, actor):
    interpreter.evaljs("""
        var input = document.createElement('input');
        input.id = 'agree';
        input.type = 'checkbox';
        input.checked = true;
        window.__changeEvents = 0;
        input.addEventListener('change', function() { window.__changeEvents++; });
        document.body.appendChild(input);
        undefined;
    """)
    actor.uncheck('#agree')
    assert interpreter.evaljs("document.querySelector('#agree').checked;") is False
    assert interpreter.evaljs("window.__changeEvents;") == 1


def test_check_works_on_radio_input(interpreter, actor):
    interpreter.evaljs("""
        var radio = document.createElement('input');
        radio.id = 'choice';
        radio.type = 'radio';
        document.body.appendChild(radio);
        undefined;
    """)
    actor.check('#choice')
    assert interpreter.evaljs("document.querySelector('#choice').checked;") is True


def test_trigger_event_dispatches_named_event(interpreter, actor):
    interpreter.evaljs("""
        var form = document.createElement('form');
        form.id = 'login';
        window.__submitEvents = 0;
        form.addEventListener('submit', function() { window.__submitEvents++; });
        document.body.appendChild(form);
        undefined;
    """)
    actor.trigger_event('#login', 'submit')
    assert interpreter.evaljs("window.__submitEvents;") == 1


def test_trigger_event_missing_element_raises(actor):
    with pytest.raises(ValueError, match="'#missing'"):
        actor.trigger_event('#missing', 'submit')


def test_click_updates_mounted_vue_component():
    interpreter = VirtualDomInterpreter()
    load_vue(interpreter)
    actor = DomInteractor(interpreter)
    interpreter.evaljs("""
        document.body.innerHTML = '<div id="app"></div>';
        var app = Vue.createApp({
            template: '<button id="counter" @click="count++">{{ count }}</button>',
            data() { return { count: 0 }; }
        });
        app.mount('#app');
        undefined;
    """)
    actor.click('#counter')
    assert '<button id="counter">1</button>' in interpreter.html()


@pytest.fixture
def asserter(interpreter):
    return DomAsserter(interpreter)


def test_assert_html_element_matches(asserter):
    asserter.assert_html('<div data-kind="button" id="greeting">hello</div>', '#greeting')


def test_assert_html_page_matches(asserter):
    asserter.assert_html('<html><body><div data-kind="button" id="greeting">hello</div></body></html>')


def test_assert_html_mismatch_reports_actual(asserter):
    with pytest.raises(AssertionError, match="expected element '#greeting' to serialize to"):
        asserter.assert_html('<div>other</div>', '#greeting')


def test_assert_text_element_matches(asserter):
    asserter.assert_text('hello', '#greeting')


def test_assert_text_page_matches(asserter):
    asserter.assert_text('hello')


def test_assert_text_mismatch_reports_actual(asserter):
    with pytest.raises(AssertionError, match="expected element '#greeting' to have text"):
        asserter.assert_text('goodbye', '#greeting')


def test_assert_attribute_matches(asserter):
    asserter.assert_attribute('#greeting', 'data-kind', 'button')


def test_assert_attribute_absent_reports_actual(asserter):
    with pytest.raises(AssertionError, match="attribute 'class' to be 'big'"):
        asserter.assert_attribute('#greeting', 'class', 'big')


def test_assert_has_class_matches(interpreter, asserter):
    interpreter.evaljs(
        "document.querySelector('#greeting').setAttribute('class', 'a big'); undefined;"
    )
    asserter.assert_has_class('#greeting', 'big')


def test_assert_has_class_missing_reports_class_list(asserter):
    with pytest.raises(AssertionError, match="to have class 'big'"):
        asserter.assert_has_class('#greeting', 'big')


def test_assert_missing_element_reports_selector(asserter):
    with pytest.raises(AssertionError, match="no element matches selector '#missing'"):
        asserter.assert_text('hello', '#missing')


@pytest.fixture
def waiter(interpreter):
    return DomWaiter(interpreter)


def test_wait_for_returns_once_condition_holds(waiter):
    polls = []

    def condition():
        polls.append(1)
        return len(polls) > 2

    waiter.wait_for(condition)
    assert len(polls) == 3


def test_wait_for_times_out_naming_description_and_timeout(waiter):
    with pytest.raises(TimeoutError, match="timed out after 0.05s waiting for condition"):
        waiter.wait_for(lambda: False, timeout=0.05)


def test_wait_for_element_succeeds_after_async_update(interpreter, waiter):
    interpreter.evaljs(
        "Promise.resolve().then(function(){"
        " var late = document.createElement('div'); late.id = 'late';"
        " document.body.appendChild(late); }); undefined;"
    )
    waiter.wait_for_element('#late')


def test_wait_for_element_times_out_naming_selector_and_timeout(waiter):
    with pytest.raises(
        TimeoutError, match="timed out after 0.05s waiting for element '#missing' to appear"
    ):
        waiter.wait_for_element('#missing', timeout=0.05)


def test_wait_for_text_succeeds_after_async_update(interpreter, waiter):
    interpreter.evaljs(
        "Promise.resolve().then(function(){"
        " document.querySelector('#greeting').textContent = 'done'; }); undefined;"
    )
    waiter.wait_for_text('#greeting', 'done')


def test_wait_for_text_times_out_naming_selector_and_expected(waiter):
    with pytest.raises(TimeoutError, match="text of '#greeting' to equal 'done'"):
        waiter.wait_for_text('#greeting', 'done', timeout=0.05)


def test_waiter_default_timeout_is_configurable(interpreter):
    waiter = DomWaiter(interpreter, timeout=0.05)
    with pytest.raises(TimeoutError, match="timed out after 0.05s"):
        waiter.wait_for_element('#missing')
