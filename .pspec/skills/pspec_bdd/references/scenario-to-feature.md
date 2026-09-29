# Scenario to executable feature

This illustrative example shows ownership and traceability, not a new binding syntax or a migration of any existing repository.

## Behavioral source in OpenSpec

In `openspec/specs/survey-history/spec.md`:

```markdown
### Requirement: History access follows study policy
The client SHALL hide history and avoid history reads when the selected study disables history.

#### Scenario: Disabled history blocks direct entry
- **WHEN** a participant opens a history link for a study that disables history
- **THEN** history is unavailable and no history read is started
```

This scenario remains in the spec after executable coverage is added.

## Executable example

In the project's normal feature location:

```gherkin
# Source: openspec/specs/survey-history/spec.md
# Requirement: History access follows study policy
# Scenario: Disabled history blocks direct entry
Feature: Study-controlled history
  Scenario: A history link cannot bypass disabled study history
    Given the selected study disables history
    When the participant opens its history link
    Then history is unavailable
    And no history read is started
```

Use the repository's binding format instead of these illustrative comments when one exists. A binding must identify the source scenario, not merely a similarly named requirement.

The runner supplies concrete study data, navigation, controlled dependencies, and assertions. For a UI client, exercise the route and observe the rendered outcome and absence of outgoing history reads. A test of a boolean policy helper alone does not prove the route applies that policy.

Several fixture cases can exercise the same source scenario. Additional cases that change the product contract need their own accepted source wording; they are not automatically authorized by being convenient to test.

## Existing reference-only specifications

If the spec instead contains only `Scenario: Bound widget acceptance` followed by a feature path, it provides a link but leaves the behavioral example in the test layer. To adopt this model:

1. Read the requirement, linked feature, actual assertions, and available decisions.
2. Recover the intended scenario and resolve any differences with the owner.
3. Keep that behavioral scenario in OpenSpec and trace the existing executable example to it.

Do not rewrite or regenerate passing tests merely to rename their owner. Do not treat a passing test as approval for undocumented behavior. Existing repository ownership rules must be explicitly revised before such a migration.
