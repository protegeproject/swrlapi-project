# Roadmap

Ordered backlog for the OWLAPI 5 migration. Remove completed items and keep evidence
and operating instructions in [runbook.md](runbook.md).

1. **Reasoning extensions beyond the audited subset.** Choose further capabilities
   from the [rule/API support matrix](runbook.md#owl-2-rl-rule-and-api-support-matrix):
   custom datatype definitions and facet evaluation, broader entailment and inherited
   disjointness, complete empty-class/satisfiability reasoning, or anonymous-individual
   and RDF metamodeling support. Distinguish required OWL 2 RL cases from optional
   out-of-profile extensions before selecting work. Address the remaining data-range
   and property-expression built-in converter stubs only with an agreed contract.
   Completion for each selected extension: positive, negative and interaction tests,
   an updated support matrix, and preserved public SWRLAPI API compatibility.

2. **Drools upgrade assessment.** Evaluate a separate migration from the currently
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

3. **Temporal edge cases and legacy APIs.** Extend coverage for non-finite duration
   scaling factors, extreme ranges, timezone-free values, and daylight-saving
   transitions. Assess replacement of Axis date/time/duration internals and their
   legacy precision/equality behavior. Completion: explicit contracts and tests
   before changing public representations or comparison behavior.

4. **Repeatable validation and release readiness.** Add CI coverage for the supported
   JDKs, timezone variants, and the core/static-analysis profiles; retain test reports.
   Promote the reconciled dependency fixes from `protege-6` to the appropriate
   default/release branches and verify GitHub refreshes the parent dependency alerts.
   Keep the unmodified Protégé host baseline in release validation and document
   host-specific compatibility limits. Propose host changes only for demonstrated
   blockers and with explicit authorization; maintenance belongs to its maintainers.
   Record the sibling and host revisions, dependency versions, and release notes;
   render the Protégé 6 update template only for an uploaded, verified release
   artifact. Completion: release builds on the
   agreed branches and an explicit compatibility statement for the released host.

5. **Checker Framework nullness coverage.** Replace the disabled Checker Framework
   1.9.13 / JDK 8 setup with a supported checker on the supported build JDKs.
   Audit annotations and nullness contracts across public SWRLAPI APIs and their
   implementations, including OWLAPI/Drools boundaries, Optional values, collections,
   and custom built-in arguments. Add precise stubs for dependencies only where
   necessary; document narrowly scoped suppressions rather than weakening checking.
   Completion: a reproducible Maven/CI nullness gate, meaningful coverage of core
   production sources, and regression checks for null-contract defects. Keep this
   distinct from SpotBugs and preserve public API compatibility.

6. **Notifications to Protégé developers.** Collect host issues and compatibility
   requests worth communicating, with reproduction steps, affected versions,
   observed impact, and the smallest proposed correction. Current unsent notification:
   on macOS with JDK 17, unmodified `6.0.0-alpha-1` logs an `IllegalAccessException`
   when `Workspace` reflectively constructs `com.apple.laf.AquaLookAndFeel` to name
   an appearance-menu entry; that entry is omitted, while the tested SWRLTab rule,
   query, editing, and lifecycle workflows pass. Prepare a focused report with the
   host revision and log excerpt from the runbook; consider Swing's registered
   look-and-feel metadata for name lookup without proposing dependency upgrades.
   Record additional communication candidates here as they arise. Send notifications
   or open upstream issues only when explicitly authorized. Completion: agreed
   notifications delivered and their issue links or responses recorded in the runbook.
