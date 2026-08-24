"""Element property behavior in the virtual DOM."""

import pytest

from dukpy_dom.interpreter import VirtualDomInterpreter


@pytest.fixture
def interpreter():
    return VirtualDomInterpreter()


def test_class_name_reads_class_attribute(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('class', 'note active');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.className;") == 'note active'


def test_class_name_setter_writes_class_attribute(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.className = 'note active';
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.getAttribute('class');") == 'note active'


def test_class_name_defaults_to_empty_string(interpreter):
    assert interpreter.evaljs("document.createElement('div').className;") == ''


def test_element_constructor_is_global(interpreter):
    assert interpreter.evaljs("typeof Element;") == 'function'
    assert interpreter.evaljs("document.createElement('div') instanceof Element;") is True


def test_svg_element_global_defined_but_plain_elements_are_not_svg(interpreter):
    assert interpreter.evaljs("typeof SVGElement;") == 'function'
    assert interpreter.evaljs("document.createElement('div') instanceof SVGElement;") is False


def test_create_element_ns_creates_svg_element_in_svg_namespace(interpreter):
    interpreter.evaljs("""
        var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        document.body.appendChild(rect);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild instanceof SVGElement;"
    ) is True
    assert interpreter.evaljs(
        "document.body.firstChild.namespaceURI;"
    ) == 'http://www.w3.org/2000/svg'


def test_set_attribute_ns_stores_qualified_name_for_serialization(interpreter):
    interpreter.evaljs("""
        var el = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        el.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', '#icon');
        document.body.appendChild(el);
        undefined;
    """)
    assert 'xlink:href="#icon"' in interpreter.html()


def test_get_attribute_ns_round_trips_with_matching_namespace(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', '#icon');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.getAttributeNS("
        "'http://www.w3.org/1999/xlink', 'href');"
    ) == '#icon'


def test_get_attribute_ns_requires_matching_namespace(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', '#icon');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.getAttributeNS("
        "'http://example.com/other', 'href');"
    ) is None


def test_get_attribute_ns_reads_plain_attributes_with_null_namespace(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('a');
        el.setAttribute('href', '#plain');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.getAttributeNS(null, 'href');"
    ) == '#plain'


def test_remove_attribute_ns_drops_namespaced_attribute(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', '#icon');
        document.body.appendChild(el);
        el.removeAttributeNS('http://www.w3.org/1999/xlink', 'href');
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.getAttributeNS("
        "'http://www.w3.org/1999/xlink', 'href');"
    ) is None
    assert 'xlink:href' not in interpreter.html()


def test_style_property_round_trips_through_dom(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.style.color = 'red';
        el.style.fontSize = '16px';
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.style.color;") == 'red'
    assert interpreter.evaljs("document.body.firstChild.style.fontSize;") == '16px'
    assert 'style="color: red; font-size: 16px;"' in interpreter.html()


def test_style_set_property_and_get_property_value(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.style.setProperty('--brand', 'acme');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.style.getPropertyValue('--brand');"
    ) == 'acme'
    assert 'style="--brand: acme;"' in interpreter.html()


def test_style_reads_existing_style_attribute(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('style', 'color: blue');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.style.color;") == 'blue'


def test_style_remove_property_drops_declaration(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.style.color = 'red';
        el.style.removeProperty('color');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "document.body.firstChild.getAttribute('style');"
    ) is None


def test_style_undefined_property_reads_empty_string(interpreter):
    assert interpreter.evaljs(
        "document.createElement('div').style.background;"
    ) == ''


def test_keyboard_event_is_global_and_ui_event_subclass(interpreter):
    assert interpreter.evaljs("typeof KeyboardEvent;") == 'function'
    assert interpreter.evaljs(
        "new KeyboardEvent('keydown') instanceof UIEvent;"
    ) is True
    assert interpreter.evaljs(
        "new KeyboardEvent('keydown') instanceof Event;"
    ) is True


def test_keyboard_event_defaults(interpreter):
    assert interpreter.evaljs(
        "var e = new KeyboardEvent('keyup');"
        " [e.key, e.code, e.keyCode, e.repeat, e.ctrlKey, e.shiftKey, e.altKey, e.metaKey];"
    ) == ['', '', 0, False, False, False, False, False]


def test_keyboard_event_exposes_key_code_and_modifiers(interpreter):
    assert interpreter.evaljs(
        "var e = new KeyboardEvent('keydown', {key: 'a', code: 'KeyA',"
        " keyCode: 65, shiftKey: true});"
        " [e.key, e.code, e.keyCode, e.shiftKey, e.ctrlKey];"
    ) == ['a', 'KeyA', 65, True, False]


def test_keyboard_event_get_modifier_state(interpreter):
    assert interpreter.evaljs(
        "var e = new KeyboardEvent('keydown', {ctrlKey: true, metaKey: true});"
        " [e.getModifierState('Control'), e.getModifierState('Ctrl'),"
        " e.getModifierState('Shift'), e.getModifierState('Meta')];"
    ) == [True, True, False, True]


def test_keyboard_event_dispatch_reaches_listener(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('input');
        window.__keys = [];
        el.addEventListener('keydown', function(e) {
            window.__keys.push([e.type, e.key, e.shiftKey]);
        });
        document.body.appendChild(el);
        el.dispatchEvent(new KeyboardEvent('keydown', {key: 'a', shiftKey: true, bubbles: true}));
        undefined;
    """)
    assert interpreter.evaljs("window.__keys;") == [['keydown', 'a', True]]


def test_class_list_add_and_contains_round_trip_through_html(interpreter):
    interpreter.evaljs("""
        var button = document.createElement('button');
        document.body.appendChild(button);
        button.classList.add('active');
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.classList.contains('active');") is True
    assert 'class="active"' in interpreter.html()


def test_class_list_remove_and_toggle_update_class_list(interpreter):
    interpreter.evaljs("""
        var div = document.createElement('div');
        div.className = 'a b';
        document.body.appendChild(div);
        div.classList.remove('a');
        div.classList.toggle('c');
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.classList.contains('b');") is True
    assert interpreter.evaljs("document.body.firstChild.classList.contains('c');") is True
    assert 'class="b c"' in interpreter.html()


def test_class_list_toggle_returns_whether_token_is_present(interpreter):
    interpreter.evaljs("""
        var div = document.createElement('div');
        div.className = 'a';
        document.body.appendChild(div);
        undefined;
    """)
    assert interpreter.evaljs(
        "var c = document.body.firstChild.classList; c.toggle('a');"
    ) is False
    assert interpreter.evaljs(
        "var c = document.body.firstChild.classList; c.toggle('b');"
    ) is True


def test_class_list_item_and_length_reflect_class_attribute(interpreter):
    interpreter.evaljs("""
        var div = document.createElement('div');
        div.className = 'a b';
        document.body.appendChild(div);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.classList.length;") == 2
    assert interpreter.evaljs("document.body.firstChild.classList.item(0);") == 'a'
    assert interpreter.evaljs("document.body.firstChild.classList.item(1);") == 'b'
    assert interpreter.evaljs("document.body.firstChild.classList.item(2);") is None


def test_class_list_is_live_view_of_class_attribute(interpreter):
    interpreter.evaljs("""
        var div = document.createElement('div');
        document.body.appendChild(div);
        div.classList.add('note');
        undefined;
    """)
    # classList mutations serialize to the class attribute, and className
    # writes are visible to a fresh classList access.
    assert interpreter.evaljs("document.body.firstChild.className;") == 'note'
    interpreter.evaljs("document.body.firstChild.className = 'other'; undefined;")
    assert interpreter.evaljs("document.body.firstChild.classList.contains('note');") is False
    assert interpreter.evaljs("document.body.firstChild.classList.contains('other');") is True


def test_class_list_add_ignores_duplicate_and_blank_tokens(interpreter):
    interpreter.evaljs("""
        var div = document.createElement('div');
        document.body.appendChild(div);
        div.classList.add('a');
        div.classList.add('a', '', 'b');
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.className;") == 'a b'


def test_matches_true_for_class_selector(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('id', 'card');
        el.className = 'note active';
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.matches('.note');") is True
    assert interpreter.evaljs("document.body.firstChild.matches('#card');") is True
    assert interpreter.evaljs("document.body.firstChild.matches('div');") is True
    assert interpreter.evaljs("document.body.firstChild.matches('[id=card]');") is True


def test_matches_false_for_non_matching_selector(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('id', 'card');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.matches('#missing');") is False
    assert interpreter.evaljs("document.body.firstChild.matches('.note');") is False
    assert interpreter.evaljs("document.body.firstChild.matches('span');") is False


def test_matches_complex_selector_checks_parent_chain(interpreter):
    interpreter.evaljs("""
        var outer = document.createElement('div');
        var inner = document.createElement('p');
        outer.appendChild(inner);
        document.body.appendChild(outer);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.firstChild.matches('div > p');") is True
    assert interpreter.evaljs("document.body.firstChild.firstChild.matches('div p');") is True
    assert interpreter.evaljs("document.body.firstChild.matches('div > p');") is False


def test_matches_empty_or_blank_selector_is_false(interpreter):
    assert interpreter.evaljs("document.createElement('div').matches('');") is False
    assert interpreter.evaljs("document.createElement('div').matches('   ');") is False


def test_closest_returns_self_when_self_matches(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('id', 'card');
        el.className = 'note active';
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs(
        "var el = document.body.firstChild; el.closest('.note') === el;"
    ) is True
    assert interpreter.evaljs(
        "var el = document.body.firstChild; el.closest('div') === el;"
    ) is True


def test_closest_returns_nearest_matching_ancestor(interpreter):
    interpreter.evaljs("""
        var outer = document.createElement('div');
        outer.setAttribute('id', 'outer');
        outer.className = 'card';
        var inner = document.createElement('p');
        outer.appendChild(inner);
        document.body.appendChild(outer);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.firstChild.closest('.card').getAttribute('id');") == 'outer'
    assert interpreter.evaljs("document.body.firstChild.firstChild.closest('div') === document.body.firstChild;") is True


def test_closest_returns_null_when_no_ancestor_matches(interpreter):
    interpreter.evaljs("""
        var outer = document.createElement('div');
        outer.setAttribute('id', 'outer');
        var inner = document.createElement('p');
        outer.appendChild(inner);
        document.body.appendChild(outer);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.firstChild.closest('.missing');") is None


def test_closest_stops_at_non_element_ancestor(interpreter):
    interpreter.evaljs("""
        var tpl = document.createElement('template');
        tpl.content.appendChild(document.createElement('span'));
        document.body.appendChild(tpl);
        undefined;
    """)
    # The span's parent is the DocumentFragment behind <template>.content,
    # which has no matches method; closest must end the walk instead of throwing.
    assert interpreter.evaljs(
        "document.body.firstChild.content.childNodes[0].closest('.missing') === null;"
    ) is True


def test_closest_empty_selector_is_null(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.closest('');") is None
    assert interpreter.evaljs("document.body.firstChild.closest('   ');") is None


def test_dataset_reads_data_attributes_as_camelcase_properties(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('data-user-id', '42');
        el.setAttribute('data-count', '3');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.dataset.userId;") == '42'
    assert interpreter.evaljs("document.body.firstChild.dataset.count;") == '3'


def test_dataset_missing_property_is_undefined(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.dataset.missing;") is None


def test_dataset_write_serializes_to_attribute_and_html(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.dataset.userId = '42';
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.getAttribute('data-user-id');") == '42'
    assert 'data-user-id="42"' in interpreter.html()


def test_dataset_delete_removes_attribute(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('data-user-id', '42');
        document.body.appendChild(el);
        delete el.dataset.userId;
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.hasAttribute('data-user-id');") is False
    assert 'data-user-id' not in interpreter.html()


def test_dataset_in_operator_tests_presence(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        el.setAttribute('data-user-id', '42');
        document.body.appendChild(el);
        undefined;
    """)
    assert interpreter.evaljs("'userId' in document.body.firstChild.dataset;") is True
    assert interpreter.evaljs("'missing' in document.body.firstChild.dataset;") is False


def test_dataset_dashed_property_names_map_straight(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        document.body.appendChild(el);
        el.dataset['foo-bar'] = 'x';
        undefined;
    """)
    assert interpreter.evaljs("document.body.firstChild.getAttribute('data-foo-bar');") == 'x'


def test_dataset_is_live_view_of_attributes(interpreter):
    interpreter.evaljs("""
        var el = document.createElement('div');
        document.body.appendChild(el);
        el.dataset.userId = '42';
        undefined;
    """)
    # dataset mutations write the attribute, and setAttribute writes are
    # visible to a fresh dataset access.
    interpreter.evaljs("document.body.firstChild.setAttribute('data-role', 'admin'); undefined;")
    assert interpreter.evaljs("document.body.firstChild.dataset.role;") == 'admin'
    assert interpreter.evaljs("document.body.firstChild.dataset.userId;") == '42'
