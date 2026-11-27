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
   after compatibility behavior is stable. Preserve the public SWRLAPI API:
   existing public method signatures and return types must remain unchanged;
   collect internal streams at collection-returning API boundaries. Preserve
   collection mutability and exception timing as well as ordering where observable,
   signature contents, imports handling, equality/hash contracts, and exception
   behavior. Completion: one reviewable group of API changes at a time, with the full
   core regression suite green and no unrelated semantic changes.

3. **SWRLTab / Protégé plugin migration.** Complete graphical Run/import/export,
   rule editing, ontology switching, and SQWRL result-table smoke tests on
   `protege6/release-6.0.0-alpha-1`; the current computer-control tool can enable and
   render both panels but cannot operate their Swing content controls.
   Upgrade the alpha host's Guava 18 and the Jackson 2.16.1 jars embedded in
   OWLAPI 5.5.1's OSGi bundle, rebuilding affected host imports and validating the
   assembled distribution. Maven dependency management does not update nested jars.
   Repair custom built-in-library discovery: the loader requests an undeclared
   `SWRLBuiltInLibraryFactoryPlugin` extension point in the host's namespace; define
   the owning namespace and test an actual contributed library. Check the macOS
   platform-independent launcher's JDK 17 Aqua look-and-feel access error.
   Port the standalone SWRLTab application separately, then validate clean-checkout
   packaging and release metadata for Protégé 6. Completion: reproducible plugin
   packaging and the full UI smoke matrix, in addition to the core and OSGi gates.

4. **Broader OWL 2 RL conformance.** Extend the isolated rule matrix and public API
   tests, including combinations of chains, keys, equality, imports, retractions,
   and datatype constraints. Audit unimplemented conversions and distinguish known
   empty-class detection from general satisfiability. Completion: a documented
   entailment/satisfiability support matrix and targeted regressions for each claim.

5. **Drools upgrade assessment.** Evaluate a separate migration from the currently
   pinned 7.74.1.Final to Apache KIE / Drools 10.2.0 (latest verified 2026-11-26).
   Check Java requirements, KIE and compiler APIs, DRL compatibility, dependency
   convergence, and plugin packaging. Completion: an isolated compatibility spike,
   the same semantic regression suite, and a measured upgrade decision. Do not fold
   this into the OWLAPI port or streams refactor.

6. **Temporal edge cases and legacy APIs.** Extend coverage for non-finite duration
   scaling factors, extreme ranges, timezone-free values, and daylight-saving
   transitions. Assess replacement of Axis date/time/duration internals and their
   legacy precision/equality behavior. Completion: explicit contracts and tests
   before changing public representations or comparison behavior.

7. **Repeatable validation and release readiness.** Add CI coverage for the supported
   JDKs, timezone variants, and the core/static-analysis profiles; retain test reports.
   Record the sibling repository
   revisions used for releases, dependency versions, and release notes. Completion:
   a clean-checkout build, reproducible dependency resolution, and an explicit plugin
   compatibility statement.

8. **Checker Framework nullness coverage.** Replace the disabled Checker Framework
   1.9.13 / JDK 8 setup with a supported checker on the supported build JDKs.
   Audit annotations and nullness contracts across public SWRLAPI APIs and their
   implementations, including OWLAPI/Drools boundaries, Optional values, collections,
   and custom built-in arguments. Add precise stubs for dependencies only where
   necessary; document narrowly scoped suppressions rather than weakening checking.
   Completion: a reproducible Maven/CI nullness gate, meaningful coverage of core
   production sources, and regression checks for null-contract defects. Keep this
   distinct from SpotBugs and preserve public API compatibility.
