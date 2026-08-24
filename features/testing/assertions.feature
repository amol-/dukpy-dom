@feature:F-TESTING-ASSERTIONS
Feature: Reading and asserting virtual DOM state

  Test authors read element state from Python and assert on it to verify a
  component's rendered output.

  Rules:
    - Inspection helpers return the current DOM state as plain Python values.
    - Assertion helpers raise a clear failure naming expected and actual when
      the expectation is not met.

  @id:F-TESTING-ASSERTIONS-S001
  Scenario: Read an element's text
    Given a div with id "greeting" containing the text "hello" in the document body
    When Python reads the text of "#greeting"
    Then the returned text is "hello"

  @id:F-TESTING-ASSERTIONS-S002
  Scenario: Assert an element attribute
    Given a div with id "widget" and a data-kind attribute equal to "button" in the document body
    When Python asserts the attribute "data-kind" of "#widget" equals "button"
    Then the assertion passes

  @id:F-TESTING-ASSERTIONS-S003
  Scenario: Assert an element has a class
    Given a div with id "card" and class "active" in the document body
    When Python asserts "#card" has class "active"
    Then the assertion passes

  @id:F-TESTING-ASSERTIONS-S004
  Scenario: Assert the rendered HTML
    Given a mounted Vue component
    When Python asserts html() contains the component's expected markup
    Then the assertion passes

  @id:F-TESTING-ASSERTIONS-S005
  Scenario: A failed assertion reports expected and actual values
    Given a div with id "status" containing the text "actual" in the document body
    When Python asserts the text of "#status" equals "expected"
    Then the assertion fails with a message naming "expected" and "actual"
