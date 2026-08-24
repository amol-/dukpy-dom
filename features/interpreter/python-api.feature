@feature:F-API-INTERPRETER
Feature: Interpreter lifecycle and test isolation

  Test authors install the package, start a fresh interpreter per test, and
  capture and restore DOM state between steps.

  Rules:
    - A fresh interpreter starts with an empty virtual DOM.
    - reset() returns the interpreter to a fresh DOM.
    - snapshot() and restore() capture and restore DOM state.

  @id:F-API-INTERPRETER-S001
  Scenario: The package imports after installation
    Given dukpy-dom is installed
    When Python runs `from dukpy_dom import VirtualDomInterpreter`
    Then the import succeeds and VirtualDomInterpreter is callable

  @id:F-API-INTERPRETER-S002
  Scenario: reset restores a fresh DOM
    Given an interpreter whose body contains a div
    When Python calls reset()
    Then html() contains an empty body

  @id:F-API-INTERPRETER-S003
  Scenario: snapshot and restore capture DOM state
    Given an interpreter whose body contains a div
    When Python takes a snapshot and then appends a span
    Then html() contains the span
    When Python restores the snapshot
    Then html() contains the div and not the span
