@feature:F-DOM-ELEMENT-API
Feature: Common element APIs for real applications

  Application code and test assertions use standard element APIs beyond the
  core tree and attribute surface: class lists, data attributes, and
  selector-based matching on one element.

  Rules:
    - classList reads and writes the element's class attribute, and html() reflects the resulting class list.
    - matches(selector) returns true only when the element matches the CSS selector.
    - closest(selector) returns the nearest matching ancestor, or null when none matches.
    - dataset maps data-* attributes to camelCase properties and back into serialized HTML.

  @id:F-DOM-ELEMENT-API-S001
  Scenario: classList add and contains round-trip through serialized HTML
    Given a button in the document body
    When JavaScript calls `button.classList.add("active")`
    Then `button.classList.contains("active")` is true
    And html() contains `class="active"`

  @id:F-DOM-ELEMENT-API-S002
  Scenario: classList remove and toggle update the class list
    Given a div with class "a b" in the document body
    When JavaScript calls `div.classList.remove("a")` and `div.classList.toggle("c")`
    Then `div.classList.contains("b")` and `div.classList.contains("c")` are true
    And html() contains `class="b c"`

  @id:F-DOM-ELEMENT-API-S003
  Scenario: matches reports whether an element matches a selector
    Given a div with id "card" and class "note" in the document body
    When JavaScript evaluates `div.matches(".note")`
    Then the result is true
    And `div.matches("#missing")` is false

  @id:F-DOM-ELEMENT-API-S004
  Scenario: closest returns the nearest matching ancestor
    Given a div with id "outer" containing a span containing a button
    When JavaScript evaluates `button.closest("#outer")`
    Then the returned element is the div with id "outer"
    And `button.closest(".missing")` is null

  @id:F-DOM-ELEMENT-API-S005
  Scenario: dataset reads and writes data attributes
    Given a div with data-kind="button" in the document body
    When JavaScript reads `div.dataset.kind`
    Then the value is "button"
    And after JavaScript sets `div.dataset.kind = "link"`, html() contains `data-kind="link"`
