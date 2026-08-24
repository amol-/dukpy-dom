@feature:F-DOM-NAMESPACES
Feature: Namespace-scoped attributes

  SVG templates and frameworks set namespace-qualified attributes such as
  xlink:href, which ordinary setAttribute cannot represent.

  Rules:
    - setAttributeNS(namespace, name, value) stores a namespaced attribute.
    - getAttributeNS(namespace, localName) reads it back; removeAttributeNS deletes it.
    - Serialized HTML renders the qualified attribute name with its value.

  @id:F-DOM-NAMESPACES-S001
  Scenario: Set and read a namespaced attribute
    Given an SVG rect element created with createElementNS
    When JavaScript calls `rect.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", "#a")`
    Then reading `rect.getAttributeNS("http://www.w3.org/1999/xlink", "href")` returns "#a"
    And html() contains `xlink:href="#a"`

  @id:F-DOM-NAMESPACES-S002
  Scenario: Removing a namespaced attribute drops it from serialized HTML
    Given an SVG rect with an xlink:href attribute set via setAttributeNS
    When JavaScript calls `rect.removeAttributeNS("http://www.w3.org/1999/xlink", "href")`
    Then html() does not contain `xlink:href`
