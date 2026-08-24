@feature:F-DOM-STYLE
Feature: Inline styles

  JavaScript and frameworks set an element's inline styles through its style
  property, and Python reads them back in serialized HTML.

  Rules:
    - Each element exposes a style object whose properties read and write CSS declarations.
    - style.setProperty(name, value) and style.getPropertyValue(name) manipulate one declaration.
    - Serialized HTML includes a style attribute for declared styles.

  @id:F-DOM-STYLE-S001
  Scenario: Setting a style property round-trips through the DOM
    Given a div in the document body
    When JavaScript sets `el.style.color = "red"` and `el.style.fontSize = "16px"`
    Then reading `el.style.color` returns "red"
    And html() contains `style="color: red; font-size: 16px;"`

  @id:F-DOM-STYLE-S002
  Scenario: setProperty adds a declaration and getPropertyValue reads it
    Given a div in the document body
    When JavaScript calls `el.style.setProperty("--brand", "acme")`
    Then reading `el.style.getPropertyValue("--brand")` returns "acme"
    And html() contains `style="--brand: acme;"`
