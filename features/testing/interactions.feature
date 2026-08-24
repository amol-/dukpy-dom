@feature:F-TESTING-INTERACTIONS
Feature: Browserless user interactions

  Test authors simulate clicks, typing, and form interactions against the
  virtual DOM and observe the resulting state — the core Cypress-like journey.

  Rules:
    - Interaction helpers dispatch events that mounted components handle.
    - Changes are visible in html() and value assertions afterward.
    - Checking a checkbox or radio sets its checked state and dispatches a change event.
    - A generic trigger helper dispatches a named event on a matching element.
    - Typing dispatches keyboard events before the input event.

  @id:F-TESTING-INTERACTIONS-S001
  Scenario: The click helper updates a Vue component
    Given a mounted Vue component with a button that increments a counter on click
    When Python calls the click helper on the button
    Then html() shows the incremented counter

  @id:F-TESTING-INTERACTIONS-S002
  Scenario: Typing into an input updates its value
    Given an input element in the document body
    When Python types "hello" into the input
    Then the input's value is "hello" and an input event was dispatched

  @id:F-TESTING-INTERACTIONS-S003
  Scenario: Selecting an option updates a select element
    Given a select element with options "a" and "b" in the document body
    When Python selects "b"
    Then the select's value is "b" and a change event was dispatched

  @id:F-TESTING-INTERACTIONS-S004
  Scenario: Checking a checkbox sets its checked state and fires change
    Given a checkbox input with id "agree" in the document body
    When Python checks "#agree"
    Then the checkbox's checked state is true and a change event was dispatched

  @id:F-TESTING-INTERACTIONS-S005
  Scenario: Unchecking a checkbox clears its checked state
    Given a checked checkbox with id "agree" in the document body
    When Python unchecks "#agree"
    Then the checkbox's checked state is false and a change event was dispatched

  @id:F-TESTING-INTERACTIONS-S006
  Scenario: The trigger helper dispatches a named event
    Given a form with id "login" in the document body
    When Python triggers a submit event on "#login"
    Then the form observed one submit event

  @id:F-TESTING-INTERACTIONS-S007
  Scenario: Typing fires keyboard events before the input event
    Given an input element with id "field" in the document body
    When Python types "a" into the input
    Then the input received keydown, keypress, and keyup events with key "a"
    And the input's value is "a"
