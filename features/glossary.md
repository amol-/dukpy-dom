# Glossary

Canonical product vocabulary used by the feature files.

## Terms

- Virtual DOM: an in-memory tree of nodes representing a web page; JavaScript mutates it and Python reads it as HTML.
- Interpreter: the Python object (`VirtualDomInterpreter`) that hosts a persistent JavaScript engine plus one virtual DOM.
- evaljs: a Python call that runs a snippet of JavaScript inside the interpreter's persistent context.
- html(): a Python call that serializes the current virtual DOM as an HTML string.
- Mount: attach a framework component (Vue 3 for now) to an element in the virtual DOM and render it.
- Reactivity: a framework's automatic re-render of the virtual DOM when application state changes.
- Interaction helper: a Python method that simulates a user action (click, type, select, check, trigger) on the virtual DOM.
- Inline style: an element's CSS declarations accessed through its style object and serialized as a style attribute.
- Namespace attribute: an attribute qualified by an XML namespace URI, such as SVG xlink:href.
- Keyboard event: a keydown, keypress, or keyup event carrying the pressed key.
- React: a framework whose components mount through ReactDOM.createRoot and render into the virtual DOM.
- Svelte: a framework whose components are compiled to JavaScript before testing and mount into the virtual DOM without a runtime template compiler.
- Offline: operating without any network access at runtime.
- CSS selector: a string pattern that locates an element in the virtual DOM.
- Class list: an element's whitespace-separated list of classes, manipulated through its classList object and serialized as a class attribute.
- Data attribute: a data-* attribute exposing application data to JavaScript, read and written through an element's dataset property.
- Assertion helper: a Python method that verifies virtual DOM state and raises when the expectation is not met.
- Polling: repeatedly re-checking the virtual DOM until a condition holds or a timeout expires.
- Timeout: the maximum time a wait polls before failing.
- Asynchronous update: a DOM change that happens after a delay rather than synchronously.
