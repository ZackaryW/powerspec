# Scenario to executable feature

This example shows an OpenSpec-owned behavioral scenario and its executable coverage. The reference comments are illustrative; reuse an existing binding format when available.

## Behavioral source in OpenSpec

In `openspec/specs/survey-history/spec.md`:

```markdown
### Requirement: History access follows study policy
The client SHALL hide history and avoid history reads when the selected study disables history.

#### Scenario: Disabled history blocks direct entry
- **WHEN** a participant opens a history link for a study that disables history
- **THEN** history is unavailable and no history read is started
```

This scenario remains authoritative in OpenSpec after executable coverage is added. The feature does not take over ownership or replace the scenario with a link.

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

Use the project's existing reference convention to identify the owning OpenSpec scenario, not merely a similarly named feature area.

The runner supplies concrete study data, navigation, controlled dependencies, and assertions. For a UI client, exercise the route and observe both the rendered outcome and absence of outgoing history reads. A test of a boolean policy helper alone does not prove the route applies that policy.

Searching component source for `historyEnabled`, matching the scenario title, or snapshotting the feature text would still pass if the route ignored the policy. Those checks do not establish this scenario. Open the disabled route through the production interaction and observe the unavailable state and outgoing requests; an enabled-study example can distinguish genuine suppression from a harness that never starts reads.

If the accepted UI contract specifies an unavailable-state message, asserting that rendered text is legitimate. If only unavailability is contractual, avoid freezing incidental copy. Likewise, parse a structured response to check its state rather than searching its raw JSON for a word. A test that publishes this feature or guidance text can prove publication, but cannot prove the scenario ran or an agent followed the guidance.

Several fixture cases can exercise this behavior. Cases that change the product contract need an accepted decision recorded in OpenSpec; convenience of testing does not authorize new behavior.

## Existing examples with unclear intent

Read the available requirement, feature, actual assertions, and user decisions together. A link alone does not explain intended behavior, and a passing test does not settle an undocumented product decision.

Clarify material differences with the owner and record the accepted behavioral scenario in OpenSpec. If the only existing source is a feature or a reference-only specification placeholder, establish the missing OpenSpec scenario and trace the executable example to it. Preserve useful tests; passing them does not substitute for establishing their authoritative scenario.
