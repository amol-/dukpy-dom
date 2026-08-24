@feature:F-TESTING-WAITING
Feature: Waiting for asynchronous updates

  Test authors wait for the virtual DOM to reach an expected state after an
  asynchronous update, without writing manual sleeps.

  Rules:
    - Waiting polls the DOM until the condition holds or a timeout expires.
    - A successful wait returns as soon as the condition holds.
    - A timed-out wait raises a clear failure.

  @id:F-TESTING-WAITING-S001
  Scenario: Wait for an element to appear
    Given a mounted Vue component that adds an element with id "late" after an asynchronous delay
    When Python waits for "#late" to appear
    Then the wait succeeds and "#late" is present in the DOM

  @id:F-TESTING-WAITING-S002
  Scenario: Wait for text to reach an expected value
    Given a mounted Vue component whose text updates asynchronously
    When Python waits for the text of an element to equal "done"
    Then the wait succeeds

  @id:F-TESTING-WAITING-S003
  Scenario: Waiting times out when the state never arrives
    Given a document body that never contains an element with id "missing"
    When Python waits for "#missing" to appear with a short timeout
    Then the wait fails with a message naming "#missing" and the timeout
