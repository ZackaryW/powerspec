## MODIFIED Requirements

### Requirement: Profiles reference resources and supply defaults

Profiles SHALL reference contexts and traits through separate optional lists of qualified resource-reference strings. Skills SHALL use qualified resource references for packaged or registered catalog resources and `<source-alias>/<path-pattern>` strings for direct paths in a declared Git source. Profiles SHALL provide defaults without copying resource definitions or runtime answers. Explicit project values SHALL override selected-profile defaults, which SHALL override global-profile defaults. Conflicting same-precedence defaults, unknown source aliases, or ambiguous resource identities SHALL be diagnosed rather than silently selected by traversal order. Repeated skill installations SHALL be deduplicated by resolved identity, target agent, scope, and project root where applicable. Distinct installation scopes SHALL NOT be collapsed. Excluding a profile SHALL not uninstall shared user-level skills as a side effect.

#### Scenario: Local override
- **WHEN** the global and selected profiles supply defaults and the project overrides a key
- **THEN** the effective input layers expose the project value without modifying either profile or any installed skill

#### Scenario: Shared skill remains installed
- **WHEN** a project stops selecting a profile used elsewhere
- **THEN** composition changes for that project without removing another project's shared user-level skill

#### Scenario: Declared source shorthand
- **WHEN** a profile declares source alias `tools` and lists `tools/skills/*`
- **THEN** composition treats it as a direct selection from that declared source rather than a packaged or local catalog reference
