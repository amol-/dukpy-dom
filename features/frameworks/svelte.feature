@feature:F-FRAMEWORK-SVELTE
Feature: Svelte component rendering and interaction

  Test authors can mount a Svelte component compiled with their own Svelte
  version into the virtual DOM, read its rendered HTML, and simulate user
  interactions against it.

  Rules:
    - A compiled Svelte component mounts into the virtual DOM when its target is a virtual-DOM element.
    - Mounted components render into the virtual DOM and are visible via html().
    - Interaction helpers drive Svelte event handlers, and the re-rendered output is visible in html().

  @id:F-FRAMEWORK-SVELTE-S001
  Scenario: Mount a compiled Svelte component and read its rendered HTML
    Given an interpreter with a compiled Svelte counter component
    When the user mounts the component with the document body as its target
    Then html() shows the component's initial rendered markup

  @id:F-FRAMEWORK-SVELTE-S002
  Scenario: The click helper updates a Svelte component
    Given a mounted Svelte counter component with a button that increments on click
    When Python calls the click helper on the button
    Then html() shows the incremented counter
