@feature:F-DOM-CORE
Feature: Virtual DOM manipulation and inspection

  A Python user can build and mutate a DOM tree through JavaScript and read it
  back as HTML.

  Rules:
    - DOM state persists across JavaScript evaluations on one interpreter.
    - HTML output escapes text content and attribute values.

  @id:F-DOM-CORE-S001
  Scenario: Create and read back a DOM element
    Given a fresh VirtualDomInterpreter
    When the user evaluates JavaScript that creates a button, sets its id and label, and appends it to the document body
    Then the interpreter html() equals '<html><body><button id="answer">Ready</button></body></html>'

  @id:F-DOM-CORE-S002
  Scenario: DOM state persists across evaluations
    Given an interpreter whose body already contains an element from a previous evaluation
    When the user evaluates JavaScript that changes that element's text
    Then the interpreter html() reflects only the latest change

  @id:F-DOM-CORE-S003
  Scenario: Python drives DOM changes through JavaScript
    Given a fresh VirtualDomInterpreter
    When the user passes a label into evaljs and the script assigns it to a new element's text
    Then the interpreter html() exposes the element with the injected label

  @id:F-DOM-CORE-S004
  Scenario: Removing an element updates the serialized HTML
    Given a document body containing a div and a span
    When the user evaluates JavaScript that removes the div
    Then the interpreter html() contains the span and not the div

  @id:F-DOM-CORE-S005
  Scenario: Replacing an element updates the serialized HTML
    Given a document body containing a div
    When the user evaluates JavaScript that replaces the div with a p element
    Then the interpreter html() contains the p and not the div

  @id:F-DOM-CORE-S006
  Scenario: Attribute values round-trip through the DOM
    Given a fresh VirtualDomInterpreter
    When the user evaluates JavaScript that sets an attribute and reads it back
    Then the read value equals the set value
    And after the attribute is removed reading it again returns null

  @id:F-DOM-CORE-S007
  Scenario: Attribute values are escaped in serialized HTML
    Given a div in the document body
    When the user evaluates JavaScript that sets its data-note attribute to `a"b<c&`
    Then the interpreter html() contains `data-note="a&quot;b&lt;c&amp;"`
