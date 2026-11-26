# Roadmap

Ordered backlog for the OWLAPI 5 migration. Remove completed items and keep evidence
and operating instructions in [runbook.md](runbook.md).

1. **Datatype conformance.** Finish value-based equality across the older
   data-property rules (functional properties, negative assertions, disjointness,
   and restrictions), XML literal canonical value equivalence, and the supported
   datatype boundary. Document handling of custom definitions and facet restrictions,
   including constructs outside OWL 2 RL.
   Completion: positive, negative, cross-datatype, and rule-selection tests through
   both isolated rules and the public reasoner; publish a precise support matrix.

2. **Streams refactor.** Replace deprecated OWLAPI collection accessors incrementally
   after compatibility behavior is stable. Preserve ordering where observable,
   signature contents, imports handling, equality/hash contracts, and exception
   behavior. Completion: one reviewable group of API changes at a time, with the full
   core regression suite green and no unrelated semantic changes.

3. **SWRLTab / Protégé plugin migration.** Port the deferred UI and plugin modules to
   the chosen OWLAPI 5 / Protégé combination. Align dependencies and OSGi imports,
   then test loading, rule editing, inference, SQWRL queries, and ontology changes in
   Protégé. Completion: reproducible plugin packaging and a documented UI smoke test,
   in addition to the core suite.

4. **Maven dependency updates, including Apache POI.** Inventory direct and
   transitive dependencies and Maven plugins across the sibling projects, including
   POI and its XMLBeans/Commons dependencies. Check supported stable releases,
   security fixes, Java requirements, dependency convergence, and OSGi compatibility.
   Manage shared versions in `swrlapi-parent` and upgrade in reviewable groups,
   keeping the Drools major-version assessment separate. Completion: dependency-tree
   evidence, spreadsheet import/export and round-trip regressions where affected,
   and a passing full core/static-analysis build; verify plugin compatibility when
   that migration is in scope.

5. **Broader OWL 2 RL conformance.** Extend the isolated rule matrix and public API
   tests, including combinations of chains, keys, equality, imports, retractions,
   and datatype constraints. Audit unimplemented conversions and distinguish known
   empty-class detection from general satisfiability. Completion: a documented
   entailment/satisfiability support matrix and targeted regressions for each claim.

6. **Drools upgrade assessment.** Evaluate a separate migration from the currently
   pinned 7.74.1.Final to Apache KIE / Drools 10.2.0 (latest verified 2026-11-26).
   Check Java requirements, KIE and compiler APIs, DRL compatibility, dependency
   convergence, and plugin packaging. Completion: an isolated compatibility spike,
   the same semantic regression suite, and a measured upgrade decision. Do not fold
   this into the OWLAPI port or streams refactor.

7. **Temporal edge cases and legacy APIs.** Extend coverage for non-finite duration
   scaling factors, extreme ranges, timezone-free values, and daylight-saving
   transitions. Assess replacement of Axis date/time/duration internals and their
   legacy precision/equality behavior. Completion: explicit contracts and tests
   before changing public representations or comparison behavior.

8. **Repeatable validation and release readiness.** Reconcile the `protege-6`
   branches with upstream `development`, which now contains the coordinated 2.1.4
   release and 2.1.5-SNAPSHOT development baseline, before merging or releasing the
   port. Resolve version and publishing changes explicitly. Add CI coverage for the supported
   JDKs, timezone variants, and the core/static-analysis profiles; retain test reports.
   Reassess nullness analysis separately from SpotBugs. Record the sibling repository
   revisions used for releases, dependency versions, and release notes. Completion:
   a clean-checkout build, reproducible dependency resolution, and an explicit plugin
   compatibility statement.
