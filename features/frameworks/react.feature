@feature:F-FRAMEWORK-REACT
Feature: React component rendering and interaction

  Test authors can mount a React component in the virtual DOM and simulate
  user interactions against it, the same way they can with Vue.

  Rules:
    - Pinned React and ReactDOM builds ship with the package and load offline.
    - A test author may instead load their own React and ReactDOM builds, so a component is tested against the framework version its application uses.
    - ReactDOM.createRoot(container).render() renders a component into the virtual DOM.
    - Interaction helpers drive React event handlers, and the re-rendered output is visible in html().

  @id:F-FRAMEWORK-REACT-S001
  Scenario: Load React offline
    Given an interpreter with the React runtime loaded
    Then `typeof React` and `typeof ReactDOM` are objects
    And `typeof ReactDOM.createRoot` is a function

  @id:F-FRAMEWORK-REACT-S002
  Scenario: Mount a React component and read its rendered HTML
    Given an interpreter with the React runtime loaded and a body containing a div with id "root"
    When the user renders a counter component with ReactDOM.createRoot(document.getElementById("root"))
    Then html() shows the component's initial rendered markup

  @id:F-FRAMEWORK-REACT-S003
  Scenario: The click helper updates a React component
    Given a mounted React counter component with a button that increments on click
    When Python calls the click helper on the button
    Then html() shows the incremented counter

  @id:F-FRAMEWORK-REACT-S004
  Scenario: Load user-provided React and ReactDOM builds instead of the pinned ones
    Given an interpreter without the pinned React runtime loaded
    When the user loads React from paths to their own react and react-dom browser bundles
    Then `typeof React` and `typeof ReactDOM` are objects
    And rendering a counter component with ReactDOM.createRoot shows its rendered markup in html()
