@feature:F-VUE-RENDER
Feature: Vue 3 component rendering and reactivity

  A Python user can mount a Vue 3 component in the virtual DOM, inspect its
  rendered HTML, and observe re-renders after state changes or interactions.

  Rules:
    - A pinned Vue 3 runtime ships with the package and loads into the interpreter offline.
    - A test author may instead load their own Vue 3 browser build, so a component is tested against the framework version its application uses.
    - Mounted components render into the virtual DOM and are visible via html().
    - Reactive state changes and handled events update the rendered DOM after microtasks drain.

  @id:F-VUE-RENDER-S001
  Scenario: Mount a Vue component and read its rendered HTML
    Given an interpreter with a Vue 3 runtime loaded
    When the user mounts a counter component into the document body
    Then the interpreter html() shows the component's initial rendered markup

  @id:F-VUE-RENDER-S002
  Scenario: Reactive state change updates the rendered DOM
    Given a mounted Vue component showing a reactive value
    When the user evaluates JavaScript that changes that reactive value and drains microtasks
    Then the interpreter html() shows the updated value

  @id:F-VUE-RENDER-S003
  Scenario: Dispatched interaction updates the rendered DOM
    Given a mounted Vue component with a click handler
    When the user dispatches a click event on the component's button
    Then the interpreter html() shows the handler's effect after microtasks drain

  @id:F-VUE-RENDER-S004
  Scenario: Load a user-provided Vue build instead of the pinned one
    Given an interpreter without the pinned Vue runtime loaded
    When the user loads Vue from a path to their own browser bundle
    Then `typeof Vue` is "object"
    And mounting a counter component into the document body shows its rendered markup in html()
