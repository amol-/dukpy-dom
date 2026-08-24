@feature:F-DOM-SELECTORS
Feature: Locating elements with CSS selectors

  Test authors and JavaScript code locate elements in the virtual DOM using
  CSS selectors on the document and on individual elements.

  Rules:
    - document.querySelector(selector) returns the first matching element in document order, or null when nothing matches.
    - document.querySelectorAll(selector) returns every matching element in document order, or an empty list when nothing matches.
    - element.querySelector and element.querySelectorAll search only that element's descendants.
    - Selectors support tag names, #id, .class, [attr], [attr=value], the descendant combinator (space), and the child combinator (>).

  @id:F-DOM-SELECTORS-S001
  Scenario: Query by tag name returns all matching elements
    Given a document body containing two div elements and one span
    When JavaScript calls document.querySelectorAll("div")
    Then the result contains the two div elements and not the span

  @id:F-DOM-SELECTORS-S002
  Scenario: Query by id returns the matching element
    Given a div with id "target" in the document body
    When JavaScript calls document.querySelector("#target")
    Then the returned element is the div with id "target"

  @id:F-DOM-SELECTORS-S003
  Scenario: Query by class returns the first matching element
    Given a document body containing a p and a span that both have class "note"
    When JavaScript calls document.querySelector(".note")
    Then the returned element is the p with class "note"

  @id:F-DOM-SELECTORS-S004
  Scenario: Attribute selectors match presence and value
    Given a document body containing a button with a data-kind attribute and an input without it
    When JavaScript calls document.querySelector("[data-kind]")
    Then the returned element is the button
    And document.querySelector("[data-kind=button]") also returns the button

  @id:F-DOM-SELECTORS-S005
  Scenario: Descendant combinator matches nested elements
    Given a div with id "card" containing a span, and a span outside the div
    When JavaScript calls document.querySelectorAll("#card span")
    Then the result contains only the span inside the div

  @id:F-DOM-SELECTORS-S006
  Scenario: Child combinator matches only direct children
    Given a div with id "list" containing a direct span and a nested span inside another div
    When JavaScript calls document.querySelectorAll("#list > span")
    Then the result contains the direct span and not the nested span

  @id:F-DOM-SELECTORS-S007
  Scenario: Element query is scoped to descendants
    Given a div with id "outer" containing a div with id "inner" and a span inside the inner div
    When JavaScript calls the outer div's querySelectorAll("span")
    Then the result contains the span inside the inner div

  @id:F-DOM-SELECTORS-S008
  Scenario: A non-matching query returns an empty result
    Given a document body containing a div
    When JavaScript calls document.querySelector(".missing")
    Then the result is null
    And document.querySelectorAll(".missing") returns an empty list
