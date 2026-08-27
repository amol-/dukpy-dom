










(function(global) {
    function TextNode(text) {
        this.nodeType = 3;
        this.nodeName = '#text';
        this.parentNode = null;
        this.ownerDocument = null;
        this.nodeValue = String(text);
    }

    TextNode.prototype.toHTML = function() {
        return escapeText(this.nodeValue);
    };

    Object.defineProperty(TextNode.prototype, 'textContent', {
        get: function() { return this.nodeValue; },
        set: function(value) { this.nodeValue = String(value); }
    });

    // CharacterData data accessor. Svelte's set_data reads and writes
    // text.data, so without this the re-render silently vanishes:
    // toHTML() reads nodeValue but the write lands on a plain 'data'
    // property.
    Object.defineProperty(TextNode.prototype, 'data', {
        get: function() { return this.nodeValue; },
        set: function(value) { this.nodeValue = String(value); }
    });

    // Comment node, a leaf node type like TextNode.
    function Comment(text) {
        this.nodeType = 8;
        this.nodeName = '#comment';
        this.parentNode = null;
        this.ownerDocument = null;
        this.nodeValue = String(text);
    }

    Comment.prototype.toHTML = function() {
        return '<!--' + escapeText(this.nodeValue) + '-->';
    };

    Object.defineProperty(Comment.prototype, 'textContent', {
        get: function() { return this.nodeValue; },
        set: function(value) { this.nodeValue = String(value); }
    });

    // data aliases nodeValue on Comment too, matching CharacterData.
    Object.defineProperty(Comment.prototype, 'data', {
        get: function() { return this.nodeValue; },
        set: function(value) { this.nodeValue = String(value); }
    });

    function Element(tagName) {
        this.nodeType = 1;
        this.nodeName = String(tagName).toUpperCase();
        this.tagName = this.nodeName;
        this.parentNode = null;
        this.ownerDocument = null;
        this.childNodes = [];
        this.attributes = {};
        if (this.nodeName === 'TEMPLATE') {
            this.content = new DocumentFragment();
        }
    }

    Element.prototype.appendChild = function(child) {
        if (child.parentNode) {
            child.parentNode.removeChild(child);
        }
        child.parentNode = this;
        this.childNodes.push(child);
        return child;
    };

    Element.prototype.removeChild = function(child) {
        var index = this.childNodes.indexOf(child);
        if (index < 0) {
            throw new Error('node is not a child');
        }
        this.childNodes.splice(index, 1);
        child.parentNode = null;
        return child;
    };

    Element.prototype.insertBefore = function(child, before) {
        if (before === null || before === undefined) {
            return this.appendChild(child);
        }
        var index = this.childNodes.indexOf(before);
        if (index < 0) {
            throw new Error('reference node is not a child');
        }
        if (child.parentNode) {
            child.parentNode.removeChild(child);
        }
        child.parentNode = this;
        this.childNodes.splice(index, 0, child);
        return child;
    };

    Element.prototype.replaceChild = function(newChild, oldChild) {
        // DOM spec: replacing a node with itself is a no-op.
        if (newChild === oldChild) {
            return oldChild;
        }
        // Remember oldChild's index before any mutation: the new child takes
        // its place even when the new child is moved from this same parent.
        var index = this.childNodes.indexOf(oldChild);
        if (index < 0) {
            throw new Error('node is not a child');
        }
        if (newChild.parentNode) {
            newChild.parentNode.removeChild(newChild);
        }
        this.childNodes.splice(index, 0, newChild);
        newChild.parentNode = this;
        oldChild.parentNode = null;
        this.childNodes.splice(this.childNodes.indexOf(oldChild), 1);
        return oldChild;
    };

    // EventTarget interface.
    Element.prototype.addEventListener = function(type, listener, capture) {
        if (typeof listener !== 'function') {
            return;
        }
        capture = normalizeCapture(capture);
        if (!this.__listeners) {
            this.__listeners = {};
        }
        var list = this.__listeners[type] || (this.__listeners[type] = []);
        var duplicate = list.some(function(entry) {
            return entry.listener === listener && entry.capture === capture;
        });
        if (!duplicate) {
            list.push({listener: listener, capture: capture});
        }
    };

    Element.prototype.removeEventListener = function(type, listener, capture) {
        if (!this.__listeners) {
            return;
        }
        var list = this.__listeners[type];
        if (!list) {
            return;
        }
        capture = normalizeCapture(capture);
        for (var i = 0; i < list.length; i++) {
            if (list[i].listener === listener && list[i].capture === capture) {
                list.splice(i, 1);
                return;
            }
        }
    };

    // Event propagation over the event path (target and its ancestors).
    // Listeners fire root-to-target in the capture phase, all on the target,
    // then target-to-root in the bubble phase when the event bubbles.
    // Dispatch honors the stop flags between phases and between nodes. The
    // flags are reset on each dispatch so an event object can be dispatched
    // again.
    Element.prototype.dispatchEvent = function(event) {
        event.target = event.target || this;
        event.__stopPropagation = false;
        event.__stopImmediate = false;
        var path = [];
        for (var node = this; node; node = node.parentNode) {
            path.push(node);
        }
        for (var i = path.length - 1; i >= 1 && !event.__stopPropagation; i--) {
            fireListeners(path[i], event, true);
        }
        if (!event.__stopPropagation) {
            fireListeners(this, event, null);
        }
        if (event.bubbles !== false && !event.__stopPropagation) {
            for (var j = 1; j < path.length && !event.__stopPropagation; j++) {
                fireListeners(path[j], event, false);
            }
        }
        return true;
    };

    // capture is true (capture phase), false (bubble phase), or null (target
    // phase: all listeners in registration order). stopImmediatePropagation
    // skips the remaining listeners on the current node.
    function fireListeners(node, event, capture) {
        if (!node.__listeners) {
            return;
        }
        var list = node.__listeners[event.type];
        if (!list) {
            return;
        }
        // Copy so listeners removed during dispatch do not run
        list.slice().forEach(function(entry) {
            if (event.__stopImmediate) {
                return;
            }
            if (capture === null || entry.capture === capture) {
                entry.listener.call(node, event);
            }
        });
    }

    function normalizeCapture(capture) {
        if (typeof capture === 'object' && capture !== null) {
            return Boolean(capture.capture);
        }
        return Boolean(capture);
    }

    // Event classes and common event types.
    function Event(type, options) {
        options = options || {};
        this.type = String(type);
        this.target = null;
        this.bubbles = Boolean(options.bubbles);
        this.cancelable = Boolean(options.cancelable);
        this.defaultPrevented = false;
    }

    // Event control methods. stopPropagation halts the event's remaining path
    // (other nodes and phases); stopImmediatePropagation also skips the
    // current node's remaining listeners; preventDefault marks the event
    // canceled when it is cancelable.
    Event.prototype.stopPropagation = function() {
        this.__stopPropagation = true;
    };

    Event.prototype.stopImmediatePropagation = function() {
        this.__stopPropagation = true;
        this.__stopImmediate = true;
    };

    Event.prototype.preventDefault = function() {
        if (this.cancelable) {
            this.defaultPrevented = true;
        }
    };

    function UIEvent(type, options) {
        Event.call(this, type, options);
        options = options || {};
        this.detail = options.detail === undefined ? 0 : options.detail;
        this.view = options.view || null;
    }
    UIEvent.prototype = Object.create(Event.prototype);
    UIEvent.prototype.constructor = UIEvent;

    function MouseEvent(type, options) {
        UIEvent.call(this, type, options);
        options = options || {};
        this.clientX = options.clientX === undefined ? 0 : options.clientX;
        this.clientY = options.clientY === undefined ? 0 : options.clientY;
        this.button = options.button === undefined ? 0 : options.button;
    }
    MouseEvent.prototype = Object.create(UIEvent.prototype);
    MouseEvent.prototype.constructor = MouseEvent;

    function CustomEvent(type, options) {
        Event.call(this, type, options);
        options = options || {};
        this.detail = options.detail === undefined ? null : options.detail;
    }
    CustomEvent.prototype = Object.create(Event.prototype);
    CustomEvent.prototype.constructor = CustomEvent;

    function KeyboardEvent(type, options) {
        UIEvent.call(this, type, options);
        options = options || {};
        this.key = options.key === undefined ? '' : String(options.key);
        this.code = options.code === undefined ? '' : String(options.code);
        this.keyCode = options.keyCode === undefined ? 0 : options.keyCode;
        this.repeat = Boolean(options.repeat);
        this.ctrlKey = Boolean(options.ctrlKey);
        this.shiftKey = Boolean(options.shiftKey);
        this.altKey = Boolean(options.altKey);
        this.metaKey = Boolean(options.metaKey);
    }
    KeyboardEvent.prototype = Object.create(UIEvent.prototype);
    KeyboardEvent.prototype.constructor = KeyboardEvent;

    KeyboardEvent.prototype.getModifierState = function(key) {
        switch (String(key)) {
            case 'Control':
            case 'Ctrl':
                return this.ctrlKey;
            case 'Shift':
                return this.shiftKey;
            case 'Alt':
                return this.altKey;
            case 'Meta':
                return this.metaKey;
            default:
                return false;
        }
    };

    Element.prototype.setAttribute = function(name, value) {
        this.attributes[String(name)] = String(value);
    };

    Element.prototype.getAttribute = function(name) {
        name = String(name);
        if (!Object.prototype.hasOwnProperty.call(this.attributes, name)) {
            return null;
        }
        return this.attributes[name];
    };

    Element.prototype.removeAttribute = function(name) {
        delete this.attributes[String(name)];
    };

    Element.prototype.hasAttribute = function(name) {
        return Object.prototype.hasOwnProperty.call(this.attributes, String(name));
    };

    // Namespace-scoped attributes, e.g. xlink:href on SVG elements.
    // setAttributeNS stores the attribute under its qualified name so html()
    // serialization and querySelector see it, and records the namespace next
    // to the value; getAttributeNS/removeAttributeNS match attributes by
    // localName plus namespace. Attributes set without a namespace (plain
    // setAttribute) match null-namespace lookups.
    Element.prototype.setAttributeNS = function(namespace, qualifiedName, value) {
        qualifiedName = String(qualifiedName);
        this.attributes[qualifiedName] = String(value);
        if (!this.__attrNamespaces) {
            this.__attrNamespaces = {};
        }
        this.__attrNamespaces[qualifiedName] = normalizeNamespace(namespace);
    };

    Element.prototype.getAttributeNS = function(namespace, localName) {
        localName = String(localName);
        var want = normalizeNamespace(namespace);
        for (var name in this.attributes) {
            if (!Object.prototype.hasOwnProperty.call(this.attributes, name)) {
                continue;
            }
            if (localNameOf(name) === localName && namespaceOf(this, name) === want) {
                return this.attributes[name];
            }
        }
        return null;
    };

    Element.prototype.removeAttributeNS = function(namespace, localName) {
        localName = String(localName);
        var want = normalizeNamespace(namespace);
        for (var name in this.attributes) {
            if (!Object.prototype.hasOwnProperty.call(this.attributes, name)) {
                continue;
            }
            if (localNameOf(name) === localName && namespaceOf(this, name) === want) {
                delete this.attributes[name];
                if (this.__attrNamespaces) {
                    delete this.__attrNamespaces[name];
                }
            }
        }
    };

    function normalizeNamespace(namespace) {
        return namespace === null || namespace === undefined ? null : String(namespace);
    }

    function localNameOf(qualifiedName) {
        var idx = qualifiedName.indexOf(':');
        return idx >= 0 ? qualifiedName.slice(idx + 1) : qualifiedName;
    }

    function namespaceOf(element, name) {
        var namespaces = element.__attrNamespaces;
        return namespaces && Object.prototype.hasOwnProperty.call(namespaces, name)
            ? namespaces[name]
            : null;
    }

    // Element.style is a live view over the style attribute. Each access
    // returns a fresh declaration object that parses the current attribute, so
    // setAttribute/removeAttribute stay the source of truth and every mutation
    // serializes back to the attribute.
    Object.defineProperty(Element.prototype, 'style', {
        get: function() {
            return createStyleDeclaration(this);
        }
    });

    function camelToDash(name) {
        name = String(name);
        if (name.indexOf('-') >= 0) {
            return name;
        }
        return name.replace(/[A-Z]/g, function(ch) {
            return '-' + ch.toLowerCase();
        });
    }

    function createStyleDeclaration(element) {
        var decls = {};
        var order = [];
        var priorities = {};

        function parse() {
            decls = {};
            order = [];
            priorities = {};
            var text = element.attributes.style;
            if (text) {
                String(text).split(';').forEach(function(part) {
                    var idx = part.indexOf(':');
                    if (idx < 0) {
                        return;
                    }
                    var name = part.slice(0, idx).trim();
                    var value = part.slice(idx + 1).trim();
                    if (name && value) {
                        decls[name] = value;
                        order.push(name);
                    }
                });
            }
        }

        function serialize() {
            if (!order.length) {
                delete element.attributes.style;
                return '';
            }
            var text = order.map(function(name) {
                var value = decls[name];
                if (priorities[name]) {
                    value += ' !' + priorities[name];
                }
                return name + ': ' + value + ';';
            }).join(' ');
            element.attributes.style = text;
            return text;
        }

        function removeDeclaration(name) {
            if (!Object.prototype.hasOwnProperty.call(decls, name)) {
                return;
            }
            delete decls[name];
            delete priorities[name];
            order.splice(order.indexOf(name), 1);
            serialize();
        }

        function setProperty(name, value, priority) {
            name = String(name);
            if (value === '' || value === null || value === undefined) {
                removeDeclaration(name);
                return;
            }
            if (!Object.prototype.hasOwnProperty.call(decls, name)) {
                order.push(name);
            }
            decls[name] = String(value);
            if (priority === '' || priority === undefined || priority === null) {
                delete priorities[name];
            } else {
                priorities[name] = String(priority);
            }
            serialize();
        }

        function getPropertyValue(name) {
            name = String(name);
            return Object.prototype.hasOwnProperty.call(decls, name) ? decls[name] : '';
        }

        function removeProperty(name) {
            name = String(name);
            if (!Object.prototype.hasOwnProperty.call(decls, name)) {
                return '';
            }
            var value = decls[name];
            removeDeclaration(name);
            return value;
        }

        parse();

        var api = Object.create(null);
        api.setProperty = setProperty;
        api.getPropertyValue = getPropertyValue;
        api.removeProperty = removeProperty;

        return new Proxy({}, {
            get: function(target, key) {
                if (key === 'length') {
                    return order.length;
                }
                if (key === 'cssText') {
                    return serialize();
                }
                if (key in api) {
                    return api[key];
                }
                var name = camelToDash(key);
                return Object.prototype.hasOwnProperty.call(decls, name) ? decls[name] : '';
            },
            set: function(target, key, value) {
                if (key === 'cssText') {
                    element.attributes.style = String(value);
                    parse();
                    serialize();
                    return true;
                }
                if (key in api) {
                    target[key] = value;
                    return true;
                }
                setProperty(camelToDash(key), value);
                return true;
            },
            has: function(target, key) {
                if (key === 'length' || key === 'cssText' || key in api) {
                    return true;
                }
                return Object.prototype.hasOwnProperty.call(decls, camelToDash(key));
            }
        });
    }

    // Element.dataset is a live view over the element's data-* attributes.
    // Each access returns a fresh Proxy that maps camelCase property names to
    // dashed attribute names (fooBar -> data-foo-bar), so component code reads
    // and writes data attributes directly against the attribute store, which
    // stays the source of truth: setAttribute and removeAttribute changes are
    // visible to the next access, and every mutation serializes back, showing
    // up in html().
    Object.defineProperty(Element.prototype, 'dataset', {
        get: function() {
            var element = this;
            return new Proxy({}, {
                get: function(target, key) {
                    if (typeof key !== 'string') {
                        return undefined;
                    }
                    var name = 'data-' + camelToDash(key);
                    return Object.prototype.hasOwnProperty.call(element.attributes, name)
                        ? element.attributes[name]
                        : undefined;
                },
                set: function(target, key, value) {
                    if (typeof key === 'string') {
                        element.attributes['data-' + camelToDash(key)] = String(value);
                    }
                    return true;
                },
                deleteProperty: function(target, key) {
                    if (typeof key === 'string') {
                        delete element.attributes['data-' + camelToDash(key)];
                    }
                    return true;
                },
                has: function(target, key) {
                    return typeof key === 'string' &&
                        Object.prototype.hasOwnProperty.call(
                            element.attributes, 'data-' + camelToDash(key));
                }
            });
        }
    });

    Element.prototype.toHTML = function() {
        var attributes = Object.keys(this.attributes).sort().map(function(name) {
            return ' ' + name + '="' + escapeAttribute(this.attributes[name]) + '"';
        }, this).join('');
        var children = this.childNodes.map(function(child) {
            return child.toHTML();
        }).join('');
        return '<' + this.tagName.toLowerCase() + attributes + '>' + children +
            '</' + this.tagName.toLowerCase() + '>';
    };

    Object.defineProperty(Element.prototype, 'id', {
        get: function() { return this.getAttribute('id') || ''; },
        set: function(value) { this.setAttribute('id', value); }
    });

    Object.defineProperty(Element.prototype, 'className', {
        get: function() { return this.getAttribute('class') || ''; },
        set: function(value) { this.setAttribute('class', value); }
    });

    // Element.classList is a live DOMTokenList view over the class attribute:
    // each access re-parses the attribute, so className and setAttribute
    // changes are visible and mutations serialize back, showing up in html().
    // add/remove/toggle take one or more tokens; empty or whitespace-containing
    // tokens are ignored so they never corrupt the serialized class attribute.
    // toggle(token, force) returns whether the token is present afterwards,
    // per the DOM.
    function ClassList(element) {
        this.element = element;
    }
    ClassList.prototype._tokens = function() {
        var value = this.element.getAttribute('class');
        if (!value) {
            return [];
        }
        return value.split(/\s+/).filter(function(token) {
            return token !== '';
        });
    };
    ClassList.prototype._save = function(tokens) {
        this.element.setAttribute('class', tokens.join(' '));
    };
    ClassList.prototype.add = function() {
        var tokens = this._tokens();
        for (var i = 0; i < arguments.length; i++) {
            var token = arguments[i];
            if (token === '' || /\s/.test(token) || tokens.indexOf(token) >= 0) {
                continue;
            }
            tokens.push(token);
        }
        this._save(tokens);
    };
    ClassList.prototype.remove = function() {
        var tokens = this._tokens();
        for (var i = 0; i < arguments.length; i++) {
            var token = arguments[i];
            var index;
            while ((index = tokens.indexOf(token)) >= 0) {
                tokens.splice(index, 1);
            }
        }
        this._save(tokens);
    };
    ClassList.prototype.toggle = function(token, force) {
        var tokens = this._tokens();
        var present = tokens.indexOf(token) >= 0;
        var add = force === undefined ? !present : !!force;
        if (add && !present) {
            tokens.push(token);
        } else if (!add && present) {
            tokens.splice(tokens.indexOf(token), 1);
        }
        this._save(tokens);
        return add;
    };
    ClassList.prototype.contains = function(token) {
        return this._tokens().indexOf(token) >= 0;
    };
    ClassList.prototype.item = function(index) {
        var tokens = this._tokens();
        return index >= 0 && index < tokens.length ? tokens[index] : null;
    };
    Object.defineProperty(ClassList.prototype, 'length', {
        get: function() {
            return this._tokens().length;
        }
    });

    Object.defineProperty(Element.prototype, 'classList', {
        get: function() {
            return new ClassList(this);
        }
    });

    Object.defineProperty(Element.prototype, 'textContent', {
        get: function() {
            return this.childNodes.filter(function(child) {
                return child.nodeType !== 8;
            }).map(function(child) {
                return child.textContent;
            }).join('');
        },
        set: function(value) {
            this.childNodes = [];
            this.appendChild(new TextNode(value));
        }
    });

    // Child and sibling navigation, computed from childNodes.
    function defineSiblingGetters(proto) {
        Object.defineProperty(proto, 'nextSibling', {
            get: function() {
                if (!this.parentNode) {
                    return null;
                }
                var siblings = this.parentNode.childNodes;
                var index = siblings.indexOf(this);
                return index >= 0 && index + 1 < siblings.length ? siblings[index + 1] : null;
            }
        });
        Object.defineProperty(proto, 'previousSibling', {
            get: function() {
                if (!this.parentNode) {
                    return null;
                }
                var siblings = this.parentNode.childNodes;
                var index = siblings.indexOf(this);
                return index > 0 ? siblings[index - 1] : null;
            }
        });
    }

    defineSiblingGetters(TextNode.prototype);
    defineSiblingGetters(Comment.prototype);
    defineSiblingGetters(Element.prototype);

    Object.defineProperty(Element.prototype, 'firstChild', {
        get: function() {
            return this.childNodes.length ? this.childNodes[0] : null;
        }
    });

    Object.defineProperty(Element.prototype, 'lastChild', {
        get: function() {
            return this.childNodes.length ? this.childNodes[this.childNodes.length - 1] : null;
        }
    });

    // Vue-specific DOM APIs, shared by text nodes and elements.
    function defineNodeApis(proto) {
        proto.cloneNode = function(deep) {
            if (this.nodeType === 3) {
                var text = new TextNode(this.nodeValue);
                text.ownerDocument = this.ownerDocument;
                return text;
            }
            if (this.nodeType === 8) {
                var comment = new Comment(this.nodeValue);
                comment.ownerDocument = this.ownerDocument;
                return comment;
            }
            var copy = new Element(this.tagName);
            copy.ownerDocument = this.ownerDocument;
            Object.keys(this.attributes).forEach(function(name) {
                copy.setAttribute(name, this.attributes[name]);
            }, this);
            if (deep) {
                this.childNodes.forEach(function(child) {
                    copy.appendChild(child.cloneNode(true));
                });
            }
            return copy;
        };
        proto.isEqualNode = function(other) {
            if (!other || other.nodeType !== this.nodeType) {
                return false;
            }
            if (this.nodeType === 3 || this.nodeType === 8) {
                return this.nodeValue === other.nodeValue;
            }
            if (other.nodeName !== this.nodeName) {
                return false;
            }
            var names = Object.keys(this.attributes);
            if (names.length !== Object.keys(other.attributes).length) {
                return false;
            }
            for (var i = 0; i < names.length; i++) {
                if (other.getAttribute(names[i]) !== this.attributes[names[i]]) {
                    return false;
                }
            }
            if (this.childNodes.length !== other.childNodes.length) {
                return false;
            }
            for (var j = 0; j < this.childNodes.length; j++) {
                if (!this.childNodes[j].isEqualNode(other.childNodes[j])) {
                    return false;
                }
            }
            return true;
        };
        proto.isSameNode = function(other) {
            return this === other;
        };
        proto.contains = function(other) {
            var node = other;
            while (node) {
                if (node === this) {
                    return true;
                }
                node = node.parentNode;
            }
            return false;
        };
    }

    defineNodeApis(TextNode.prototype);
    defineNodeApis(Comment.prototype);
    defineNodeApis(Element.prototype);

    // Element innerHTML getter/setter.
    Object.defineProperty(Element.prototype, 'innerHTML', {
        get: function() {
            return this.childNodes.map(function(child) {
                return child.toHTML();
            }).join('');
        },
        set: function(html) {
            var nodes = parseFragment(String(html), this.ownerDocument);
            this.childNodes.forEach(function(node) {
                node.parentNode = null;
            });
            this.childNodes = nodes;
            nodes.forEach(function(node) {
                node.parentNode = this;
            }, this);
        }
    });

    // Form control value and checked state.
    // value reads the value attribute on inputs, the text on textareas, and
    // the selected option on selects; setting select.value selects the matching
    // option. checked is a boolean on checkbox/radio inputs.
    Object.defineProperty(Element.prototype, 'value', {
        get: function() {
            if (this.tagName === 'TEXTAREA') {
                return this.textContent;
            }
            if (this.tagName === 'SELECT') {
                var option = selectedOption(this);
                return option ? option.value : '';
            }
            if (this.tagName === 'OPTION') {
                return this.hasAttribute('value') ? this.getAttribute('value') : this.textContent;
            }
            return this.hasAttribute('value') ? this.getAttribute('value') : '';
        },
        set: function(value) {
            if (this.tagName === 'TEXTAREA') {
                this.textContent = String(value);
            } else if (this.tagName === 'SELECT') {
                setSelectValue(this, String(value));
            } else {
                this.setAttribute('value', String(value));
            }
        }
    });

    Object.defineProperty(Element.prototype, 'checked', {
        get: function() {
            return this.hasOwnProperty('__checked') ? this.__checked : this.hasAttribute('checked');
        },
        set: function(value) {
            this.__checked = Boolean(value);
        }
    });

    Object.defineProperty(Element.prototype, 'selected', {
        get: function() {
            return this.hasOwnProperty('__selected') ? this.__selected : this.hasAttribute('selected');
        },
        set: function(value) {
            this.__selected = Boolean(value);
        }
    });

    function selectedOption(select) {
        var options = descendantOptions(select);
        for (var i = 0; i < options.length; i++) {
            if (options[i].selected) {
                return options[i];
            }
        }
        return null;
    }

    function descendantOptions(element) {
        var options = [];
        element.childNodes.forEach(function(child) {
            if (child.nodeType === 1) {
                if (child.tagName === 'OPTION') {
                    options.push(child);
                } else {
                    options = options.concat(descendantOptions(child));
                }
            }
        });
        return options;
    }

    function setSelectValue(select, value) {
        descendantOptions(select).forEach(function(option) {
            option.selected = option.value === value;
        });
    }

    function parseFragment(html, ownerDocument) {
        var pos = 0;

        function parseNodes(stopTag) {
            var level = [];

            function pushText(text) {
                var node = new TextNode(decodeEntities(text));
                if (ownerDocument) {
                    node.ownerDocument = ownerDocument;
                }
                level.push(node);
            }

            while (pos < html.length) {
                var lt = html.indexOf('<', pos);
                if (lt < 0) {
                    pushText(html.slice(pos));
                    pos = html.length;
                    break;
                }
                if (lt > pos) {
                    pushText(html.slice(pos, lt));
                }
                var gt = findTagEnd(html, lt);
                if (gt < 0) {
                    throw new Error('malformed HTML: unterminated tag');
                }
                var inner = html.slice(lt + 1, gt);
                pos = gt + 1;
                if (inner.charAt(0) === '/') {
                    var closeName = inner.slice(1).trim().toLowerCase();
                    if (VOID_ELEMENTS[closeName]) {
                        continue;
                    }
                    if (!stopTag || closeName !== stopTag) {
                        throw new Error('malformed HTML: unexpected </' + closeName + '>');
                    }
                    return level;
                }
                var selfClosing = /\/\s*$/.test(inner);
                var el = parseOpenTag(inner, selfClosing, ownerDocument);
                if (!selfClosing && !VOID_ELEMENTS[el.tagName.toLowerCase()]) {
                    parseNodes(el.tagName.toLowerCase()).forEach(function(child) {
                        el.appendChild(child);
                    });
                }
                level.push(el);
            }
            if (stopTag) {
                throw new Error('malformed HTML: missing </' + stopTag + '>');
            }
            return level;
        }

        return parseNodes(null);
    }

    function parseOpenTag(inner, selfClosing, ownerDocument) {
        var match = /^([a-zA-Z][a-zA-Z0-9-]*)([\s\S]*)$/.exec(inner);
        if (!match) {
            throw new Error('malformed HTML: bad tag <' + inner + '>');
        }
        var el = new Element(match[1]);
        if (ownerDocument) {
            el.ownerDocument = ownerDocument;
        }
        var rest = selfClosing ? match[2].replace(/\/\s*$/, '') : match[2];
        var attrRe = /^\s*([a-zA-Z_:][a-zA-Z0-9_.:-]*)(?:\s*=\s*("[^"]*"|'[^']*'))?/;
        while (rest) {
            if (/^\s*$/.test(rest)) {
                break;
            }
            var attrMatch = attrRe.exec(rest);
            if (!attrMatch) {
                throw new Error('malformed HTML: bad attribute in <' + inner + '>');
            }
            var value = '';
            if (attrMatch[2]) {
                value = decodeEntities(attrMatch[2].slice(1, -1));
            }
            el.setAttribute(attrMatch[1], value);
            rest = rest.slice(attrMatch[0].length);
        }
        return el;
    }

    function findTagEnd(html, start) {
        var quote = null;
        for (var i = start + 1; i < html.length; i++) {
            var ch = html.charAt(i);
            if (quote) {
                if (ch === quote) {
                    quote = null;
                }
            } else if (ch === '"' || ch === "'") {
                quote = ch;
            } else if (ch === '>') {
                return i;
            }
        }
        return -1;
    }

    function decodeEntities(text) {
        return text.replace(/&(#39|amp|lt|gt|quot|apos);/g, function(match, name) {
            return ENTITIES[name];
        });
    }

    var ENTITIES = {'#39': "'", amp: '&', lt: '<', gt: '>', quot: '"', apos: "'"};
    var VOID_ELEMENTS = {area: 1, br: 1, col: 1, embed: 1, hr: 1, img: 1, input: 1,
        link: 1, meta: 1, param: 1, source: 1, track: 1, wbr: 1};


    // DocumentFragment, a lightweight container whose children can be moved
    // into the document; backs <template>.content.
    function DocumentFragment() {
        this.nodeType = 11;
        this.nodeName = '#document-fragment';
        this.parentNode = null;
        this.ownerDocument = null;
        this.childNodes = [];
    }

    // Reuse Element's mutation methods: they already move a child out of its
    // previous parent, which is the fragment's append/insert semantics.
    DocumentFragment.prototype.appendChild = Element.prototype.appendChild;
    DocumentFragment.prototype.removeChild = Element.prototype.removeChild;
    DocumentFragment.prototype.insertBefore = Element.prototype.insertBefore;
    DocumentFragment.prototype.replaceChild = Element.prototype.replaceChild;

    function Document() {
        this.nodeType = 9;
        this.nodeName = '#document';
        this.parentNode = null;
        this.documentElement = new Element('html');
        this.body = new Element('body');
        this.documentElement.ownerDocument = this;
        this.body.ownerDocument = this;
        this.documentElement.appendChild(this.body);
    }

    Document.prototype.createElement = function(tagName) {
        var element = new Element(tagName);
        element.ownerDocument = this;
        if (element.content) {
            element.content.ownerDocument = this;
        }
        return element;
    };

    // Namespace-aware element creation. Vue 3 calls createElementNS for SVG
    // elements; the SVG namespace yields SVGElement instances so namespace
    // and instanceof checks stay consistent, other namespaces yield plain
    // elements like in the DOM.
    Document.prototype.createElementNS = function(namespace, tagName) {
        var element = String(namespace) === 'http://www.w3.org/2000/svg'
            ? new SVGElement(tagName)
            : new Element(tagName);
        element.namespaceURI = String(namespace);
        element.ownerDocument = this;
        return element;
    };

    Document.prototype.createTextNode = function(text) {
        var node = new TextNode(text);
        node.ownerDocument = this;
        return node;
    };

    Document.prototype.createComment = function(text) {
        var node = new Comment(text);
        node.ownerDocument = this;
        return node;
    };

    Document.prototype.createDocumentFragment = function() {
        var fragment = new DocumentFragment();
        fragment.ownerDocument = this;
        return fragment;
    };

    // React's event system attaches a "selectionchange" listener to the
    // document (the root container's ownerDocument). The listener machinery is
    // element-agnostic (it only touches __listeners and parentNode), so the
    // Document reuses Element's EventTarget methods; a document event's path
    // is just the document itself.
    Document.prototype.addEventListener = Element.prototype.addEventListener;
    Document.prototype.removeEventListener = Element.prototype.removeEventListener;
    Document.prototype.dispatchEvent = Element.prototype.dispatchEvent;

    // getElementById supports React's mount path
    // (ReactDOM.createRoot(document.getElementById('root'))); the selector
    // engine already parses #id, so this is a thin wrapper.
    Document.prototype.getElementById = function(id) {
        return this.querySelector('#' + String(id));
    };

    // CSS selector engine. querySelector/querySelectorAll locate elements by
    // tag name, #id, .class, [attr], [attr=value], the descendant combinator
    // (space) and the child combinator (>). Element queries search only the
    // element's descendants; document queries search the whole tree.
    // querySelectorAll returns a plain array in document order and querySelector
    // returns the first match or null.
    Document.prototype.querySelector = function(selector) {
        return querySelectorAllInternal(this, selector)[0] || null;
    };

    Document.prototype.querySelectorAll = function(selector) {
        return querySelectorAllInternal(this, selector);
    };

    Element.prototype.querySelector = function(selector) {
        return querySelectorAllInternal(this, selector)[0] || null;
    };

    Element.prototype.querySelectorAll = function(selector) {
        return querySelectorAllInternal(this, selector);
    };

    function querySelectorAllInternal(scope, selector) {
        selector = String(selector).trim();
        if (!selector) {
            return [];
        }
        var parts = parseSelector(selector);
        var elements = scope.nodeType === 9
            ? [scope.documentElement].concat(descendants(scope.documentElement))
            : descendants(scope);
        return elements.filter(function(element) {
            return matchesChain(element, parts, parts.length - 1);
        });
    }

    // Splits a selector into compounds and the combinator joining each to the
    // next: {combinator: 'child'|'descendant'|null, conditions}.
    function parseSelector(selector) {
        var parts = [];
        var current = {combinator: null, conditions: []};
        var pos = 0;
        while (pos < selector.length) {
            var ch = selector.charAt(pos);
            if (ch === '>') {
                parts.push(current);
                current = {combinator: 'child', conditions: []};
                pos++;
            } else if (/\s/.test(ch)) {
                pos++;
                while (pos < selector.length && /\s/.test(selector.charAt(pos))) {
                    pos++;
                }
                // Whitespace separates compounds unless it borders a child
                // combinator or trails the selector.
                if (pos < selector.length && selector.charAt(pos) !== '>' && current.conditions.length) {
                    parts.push(current);
                    current = {combinator: 'descendant', conditions: []};
                }
            } else {
                var simple = parseSimple(selector, pos);
                current.conditions.push(simple.condition);
                pos = simple.pos;
            }
        }
        parts.push(current);
        return parts;
    }

    // One simple selector token: a tag name, #id, .class, or [attr(=value)].
    function parseSimple(selector, pos) {
        var ch = selector.charAt(pos);
        if (ch === '#') {
            var idMatch = /^[a-zA-Z0-9_-]+/.exec(selector.slice(pos + 1));
            if (!idMatch) {
                throw new Error('invalid selector: bad #id');
            }
            return {condition: {type: 'id', value: idMatch[0]}, pos: pos + 1 + idMatch[0].length};
        }
        if (ch === '.') {
            var classMatch = /^[a-zA-Z0-9_-]+/.exec(selector.slice(pos + 1));
            if (!classMatch) {
                throw new Error('invalid selector: bad .class');
            }
            return {condition: {type: 'class', value: classMatch[0]}, pos: pos + 1 + classMatch[0].length};
        }
        if (ch === '[') {
            var end = selector.indexOf(']', pos);
            if (end < 0) {
                throw new Error('invalid selector: unterminated attribute');
            }
            var inner = selector.slice(pos + 1, end);
            var eq = inner.indexOf('=');
            var name = eq < 0 ? inner.trim() : inner.slice(0, eq).trim();
            var value;
            if (eq >= 0) {
                value = inner.slice(eq + 1).trim();
                if (value.length >= 2 &&
                        ((value.charAt(0) === '"' && value.charAt(value.length - 1) === '"') ||
                         (value.charAt(0) === "'" && value.charAt(value.length - 1) === "'"))) {
                    value = value.slice(1, -1);
                }
            }
            return {condition: {type: 'attr', name: name, value: value}, pos: end + 1};
        }
        var tagMatch = /^[a-zA-Z][a-zA-Z0-9-]*/.exec(selector.slice(pos));
        if (!tagMatch) {
            throw new Error('invalid selector: unexpected character "' + ch + '"');
        }
        return {condition: {type: 'tag', value: tagMatch[0]}, pos: pos + tagMatch[0].length};
    }

    // True when element matches every condition of one compound selector.
    function matchesCompound(element, conditions) {
        for (var i = 0; i < conditions.length; i++) {
            var condition = conditions[i];
            if (condition.type === 'tag') {
                if (element.tagName !== condition.value.toUpperCase()) {
                    return false;
                }
            } else if (condition.type === 'id') {
                if (element.getAttribute('id') !== condition.value) {
                    return false;
                }
            } else if (condition.type === 'class') {
                var classes = element.getAttribute('class');
                if (classes === null || (' ' + classes + ' ').indexOf(' ' + condition.value + ' ') < 0) {
                    return false;
                }
            } else if (condition.type === 'attr') {
                if (!element.hasAttribute(condition.name) ||
                        (condition.value !== undefined &&
                         element.getAttribute(condition.name) !== condition.value)) {
                    return false;
                }
            }
        }
        return true;
    }

    // True when element matches the compound at parts[index], linked through
    // parts[index].combinator to a matching ancestor chain.
    function matchesChain(element, parts, index) {
        if (!matchesCompound(element, parts[index].conditions)) {
            return false;
        }
        if (index === 0) {
            return true;
        }
        if (parts[index].combinator === 'child') {
            return element.parentNode !== null && matchesChain(element.parentNode, parts, index - 1);
        }
        for (var ancestor = element.parentNode; ancestor; ancestor = ancestor.parentNode) {
            if (matchesChain(ancestor, parts, index - 1)) {
                return true;
            }
        }
        return false;
    }

    // Element.matches tests whether the element itself matches a selector,
    // reusing the same parseSelector/matchesChain engine as querySelectorAll:
    // the element is the subject of the last compound, so complex selectors
    // like 'div > p' check the parent chain exactly the way a scoped query
    // would. Empty or whitespace-only selectors return false, matching
    // querySelectorAll's empty-selector behavior.
    Element.prototype.matches = function(selector) {
        selector = String(selector).trim();
        if (!selector) {
            return false;
        }
        var parts = parseSelector(selector);
        return matchesChain(this, parts, parts.length - 1);
    };

    // Element.closest returns the nearest element ancestor (including the
    // element itself) that matches a selector, or null. It reuses matches, so
    // empty selectors yield null and invalid selectors throw exactly like
    // matches. The walk stops at the first non-element ancestor (for example,
    // the DocumentFragment behind <template>.content), which has no matches
    // method.
    Element.prototype.closest = function(selector) {
        for (var element = this; element && element.nodeType === 1; element = element.parentNode) {
            if (element.matches(selector)) {
                return element;
            }
        }
        return null;
    };

    // Element descendants of root in document order.
    function descendants(root) {
        var elements = [];
        var nodes = root.childNodes || [];
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i].nodeType === 1) {
                elements.push(nodes[i]);
                elements = elements.concat(descendants(nodes[i]));
            }
        }
        return elements;
    }

    function escapeText(text) {
        return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;');
    }

    function escapeAttribute(value) {
        return escapeText(value).replace(/"/g, '&quot;');
    }

    // SVGElement global so Vue 3's namespace and instanceof checks run.
    // SVGElement inherits from Element; createElementNS creates SVG instances,
    // while createElement elements are not instanceof SVGElement.
    function SVGElement(tagName) {
        Element.call(this, tagName);
    }
    SVGElement.prototype = Object.create(Element.prototype);
    SVGElement.prototype.constructor = SVGElement;

    // React's commit phase checks the focused element with
    // `b instanceof window.HTMLIFrameElement`; without a constructor the check
    // throws "invalid 'instanceof' right operand". The empty constructor keeps
    // the check false, as no virtual DOM element is an iframe.
    global.HTMLIFrameElement = function() {};

    var document = new Document();
    global.document = document;
    global.window = global;
    global.Node = {ELEMENT_NODE: 1, TEXT_NODE: 3, COMMENT_NODE: 8, DOCUMENT_NODE: 9,
        DOCUMENT_FRAGMENT_NODE: 11};
    global.Element = Element;
    global.SVGElement = SVGElement;
    global.Comment = Comment;
    global.Event = Event;
    global.UIEvent = UIEvent;
    global.MouseEvent = MouseEvent;
    global.CustomEvent = CustomEvent;
    global.KeyboardEvent = KeyboardEvent;

    // Document lifecycle helpers (reset, snapshot, restore).
    var __snapshots = {};
    var __snapshotCounter = 0;

    function __cloneNode(node) {
        if (node.nodeType === 3) {
            return new TextNode(node.nodeValue);
        }
        if (node.nodeType === 8) {
            return new Comment(node.nodeValue);
        }
        var copy = new Element(node.tagName);
        Object.keys(node.attributes).forEach(function(name) {
            copy.setAttribute(name, node.attributes[name]);
        });
        node.childNodes.forEach(function(child) {
            copy.appendChild(__cloneNode(child));
        });
        return copy;
    }

    function __cloneDocument() {
        var copy = new Document();
        var html = new Element('html');
        document.documentElement.childNodes.forEach(function(child) {
            if (child === document.body) {
                copy.body = __cloneNode(child);
                html.appendChild(copy.body);
            } else {
                html.appendChild(__cloneNode(child));
            }
        });
        copy.documentElement = html;
        return copy;
    }

    function __replaceDocument(doc) {
        document = doc;
        global.document = doc;
    }

    global.resetDocument = function() {
        __replaceDocument(new Document());
    };

    // React's scheduler needs a way to run a callback later; with no
    // setImmediate/MessageChannel in dukpy it falls back to setTimeout. dukpy
    // drains the promise microtask queue at every evaljs boundary, so queueing
    // on a microtask runs the callback before the next evaljs body executes --
    // render() and event-driven re-renders commit by the time the test reads
    // html(). Real delays are not simulated.
    //
    // The callback must NOT run synchronously: react-dom assigns
    // root.callbackNode only after scheduleCallback returns, and
    // performConcurrentWorkOnRoot clears it when the task it was handed
    // matches. A synchronous timer would run the work before the assignment,
    // leaving a stale completed task in callbackNode so ensureRootIsScheduled
    // reuses it and drops every later update.
    global.setTimeout = function(fn) {
        if (typeof fn === 'function') {
            queueMicrotask(fn);
        }
        return 0;
    };
    global.clearTimeout = function() {};

    global.snapshotDocument = function() {
        var id = ++__snapshotCounter;
        __snapshots[id] = __cloneDocument();
        return id;
    };

    global.restoreDocument = function(id) {
        __replaceDocument(__snapshots[id]);
    };
})(globalThis);
