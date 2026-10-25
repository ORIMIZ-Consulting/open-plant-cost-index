# Release notes template

Copy the block below into CHANGELOG.md as a new section, fill it in and delete what does not apply. The release workflow publishes the section for the tagged version as the GitHub release notes.

Version numbers follow MAJOR.MINOR.PATCH:

- **First number (MAJOR), for example 2.0.0:** a change that can alter results or break calling tools. Examples: new weights, a new method, a changed location value, a changed interface.
- **Second number (MINOR), for example 1.1.0:** new features or new data that leave existing results unchanged. Examples: new locations, a new output format.
- **Third number (PATCH), for example 1.0.1:** fixes and text changes only.

---

```markdown
## X.Y.Z (DD Month YYYY)

One or two sentences on what this release is.

DOI (Digital Object Identifier) for this version: added after Zenodo mints it.

### Added
- 

### Changed
- 

### Fixed
- 

### Values
- Escalation values: unchanged / changed (say which and why).
- Location values: unchanged / changed (say which and why). New locations: list codes.
- Location module version: X.Y.Z.
- Data release used for the checks: data-YYYY-MM.

### Checks
- Tests: all pass.
- Back-test worst error on normal years: X.X% (fail limit 8%).

### For a first-number (MAJOR) change only
- Update dependent tools: open-fel1-lng-cost
- Say what changed in the results and how much, with an example.

CEPCI is a trademark of Chemical Engineering magazine. OPCI is not affiliated with or endorsed by Chemical Engineering.
```
