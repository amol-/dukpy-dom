"""The pinned Vue 3 bundle loads offline and exposes a usable Vue global."""

import shutil

from dukpy_dom.interpreter import VirtualDomInterpreter


def test_load_framework_vue_exposes_vue_global():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    assert interpreter.evaljs("typeof Vue;") == "object"


def test_load_framework_vue_is_pinned_version():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    assert interpreter.evaljs("Vue.version;") == "3.5.13"


def test_create_app_returns_mountable_app():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    assert interpreter.evaljs(
        "typeof Vue.createApp; var app = Vue.createApp({ template: '<div>hi</div>' }); "
        "typeof app.mount;"
    ) == "function"


def test_mount_renders_component_without_reference_error():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"app\"></div>'; "
        "var app = Vue.createApp({ template: '<div>hi</div>' }); "
        "app.mount('#app'); undefined;"
    )
    assert "<div>hi</div>" in interpreter.html()


def test_mount_renders_svg_component():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"app\"></div>'; "
        "var app = Vue.createApp({ template: '<svg><rect width=\"10\" height=\"5\"></rect></svg>' }); "
        "app.mount('#app'); undefined;"
    )
    html = interpreter.html()
    assert "<svg>" in html
    assert "<rect" in html and 'width="10"' in html and 'height="5"' in html


def test_mount_renders_xlink_href_attribute():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"app\"></div>'; "
        "var app = Vue.createApp({ template: '<svg><use xlink:href=\"#icon\"></use></svg>' }); "
        "app.mount('#app'); undefined;"
    )
    assert 'xlink:href="#icon"' in interpreter.html()


def test_mount_renders_static_style_attribute():
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework("vue")
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"app\"></div>'; "
        "var app = Vue.createApp({ template: '<div style=\"color: red\">hi</div>' }); "
        "app.mount('#app'); undefined;"
    )
    assert 'style="color: red;"' in interpreter.html()


def test_load_framework_vue_loads_user_provided_bundle(tmp_path):
    # F-VUE-RENDER-S004: a user-provided build replaces the pinned one.
    bundle = tmp_path / "vue.global.prod.js"
    bundle.write_text("var Vue = {version: '9.9.9'};", encoding="utf-8")
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework(str(bundle))
    assert interpreter.evaljs("typeof Vue;") == "object"
    assert interpreter.evaljs("Vue.version;") == "9.9.9"


def test_user_provided_bundle_mounts_component(tmp_path):
    # F-VUE-RENDER-S004: loading the real Vue build from a user path (not the
    # internal pinned default) still mounts and renders into html().
    import os
    bundle = tmp_path / "vue.global.prod.js"
    source = os.path.join(os.path.dirname(__file__), "..", "dukpy_dom", "vendor", "vue.global.prod.js")
    shutil.copyfile(source, bundle)
    interpreter = VirtualDomInterpreter()
    interpreter.load_framework(str(bundle))
    interpreter.evaljs(
        "document.body.innerHTML = '<div id=\"app\"></div>'; "
        "var app = Vue.createApp({ template: '<div>hi</div>' }); "
        "app.mount('#app'); undefined;"
    )
    assert "<div>hi</div>" in interpreter.html()
