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

2. **Broader OWL 2 RL conformance.** Extend the isolated rule matrix and public API
   tests, including combinations of chains, keys, equality, imports, retractions,
   and datatype constraints. Audit unimplemented conversions and distinguish known
   empty-class detection from general satisfiability. Completion: a documented
   entailment/satisfiability support matrix and targeted regressions for each claim.

3. **Drools upgrade assessment.** Evaluate a separate migration from the currently
   pinned 7.74.1.Final to Apache KIE / Drools 10.2.0 (latest verified 2026-11-26).
   **Java 17 minimum:** Drools 10 requires Java 17+, raising the library's current
   Java 11 baseline; assess downstream compatibility and update build, runtime,
   CI, and documentation requirements before adopting the upgrade
   ([migration guide](https://kie.apache.org/docs/10.1.x/drools/drools/migration-guide/index.html)).
   **OSGi support retired:** Drools stopped providing out-of-the-box OSGi support
   from version 8; validate the embedded Drools dependencies, service discovery,
   and class loading in the assembled Protégé 6 plugin, including rule execution,
   SQWRL queries, and third-party built-ins
   ([release notes](https://docs.drools.org/8.34.0.Final/drools-docs/docs-website/drools/release-notes/index.html)).
   Check KIE and compiler APIs, DRL compatibility, dependency
   convergence, and plugin packaging. Completion: an isolated compatibility spike,
   the same semantic regression suite, and a measured upgrade decision. Do not fold
   this into the OWLAPI port or streams refactor.

4. **Temporal edge cases and legacy APIs.** Extend coverage for non-finite duration
   scaling factors, extreme ranges, timezone-free values, and daylight-saving
   transitions. Assess replacement of Axis date/time/duration internals and their
   legacy precision/equality behavior. Completion: explicit contracts and tests
   before changing public representations or comparison behavior.

5. **Repeatable validation and release readiness.** Add CI coverage for the supported
   JDKs, timezone variants, and the core/static-analysis profiles; retain test reports.
   Promote the reconciled dependency fixes from `protege-6` to the appropriate
   default/release branches and verify GitHub refreshes the parent dependency alerts.
   Revalidate the final plugin against the unmodified supported Protégé host after
   withdrawal of the experimental host changes. Document host dependency and JDK 17
   appearance-menu limitations; host maintenance belongs to the Protégé maintainers.
   Record the sibling and host revisions,
   dependency versions, and release notes; render the Protégé 6 update template only
   for an uploaded, verified release artifact. Completion: release builds on the
   agreed branches and an explicit compatibility statement for the released host.

6. **Checker Framework nullness coverage.** Replace the disabled Checker Framework
   1.9.13 / JDK 8 setup with a supported checker on the supported build JDKs.
   Audit annotations and nullness contracts across public SWRLAPI APIs and their
   implementations, including OWLAPI/Drools boundaries, Optional values, collections,
   and custom built-in arguments. Add precise stubs for dependencies only where
   necessary; document narrowly scoped suppressions rather than weakening checking.
   Completion: a reproducible Maven/CI nullness gate, meaningful coverage of core
   production sources, and regression checks for null-contract defects. Keep this
   distinct from SpotBugs and preserve public API compatibility.

7. **README and GitHub documentation updates.** Update the sibling repository
   READMEs and GitHub documentation/wiki for the OWLAPI 5 and Protégé 6 baseline,
   supported build and test commands, and third-party built-in registration.
   Document the extension-point namespace, factory implementation and lifecycle,
   OSGi imports and shared API identity, collision/error behavior, and a working
   contributor example. Completion: consistent links and instructions across the
   repositories, with the registration example built and exercised in Protégé.
