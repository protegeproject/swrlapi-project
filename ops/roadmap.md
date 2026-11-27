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

3. **Legacy temporal API migration.** Decide whether to replace the remaining Axis
   and `java.util.Date` internals using the [temporal boundary assessment](runbook.md#temporal-behavior-and-legacy-api-boundaries).
   Agree contracts for arbitrary fractional precision, duration range, partial
   ordering and implicit timezones before changing wrapper equality or comparison
   behavior. Preserve public signatures, including Axis-typed helpers, or coordinate
   a separately versioned API change. Completion: an agreed migration scope, adapter
   and serialization tests, and compatibility evidence for existing consumers.

4. **Repeatable validation and release readiness.** Publish the shared CI workflows,
   verify remote runs and configure required branch checks. Agree the supported
   build/runtime JDK matrix and extend coverage beyond the documented JDK 17 gate
   where needed; use the strict nullness and static-analysis gates in release builds.
   Promote the reconciled dependency fixes from `protege-6` to the appropriate
   default/release branches and verify GitHub refreshes the parent dependency alerts.
   Keep the unmodified Protégé host baseline in release validation and document
   host-specific compatibility limits. Propose host changes only for demonstrated
   blockers and with explicit authorization; maintenance belongs to its maintainers.
   Record the sibling and host revisions, dependency versions, and release notes;
   render the Protégé 6 update template only for an uploaded, verified release
   artifact. Completion: release builds on the
   agreed branches and an explicit compatibility statement for the released host.

5. **Notifications to Protégé developers.** Collect host issues and compatibility
   requests worth communicating, with reproduction steps, affected versions,
   observed impact, and the smallest proposed correction. Current unsent notification:
   on macOS with JDK 17, unmodified `6.0.0-alpha-1` logs an `IllegalAccessException`
   when `Workspace` reflectively constructs `com.apple.laf.AquaLookAndFeel` to name
   an appearance-menu entry; that entry is omitted, while the tested SWRLTab rule,
   query, editing, and lifecycle workflows pass. Prepare a focused report with the
   host revision and log excerpt from the runbook; consider Swing's registered
   look-and-feel metadata for name lookup without proposing dependency upgrades.
   Also report that unmodified `6.0.0-alpha-1` retains the
   `plugin.registry-5.0.url` preference key and the `update-info/5.0.0` registry
   default: a fresh Protégé 6 installation consequently searches the legacy catalog.
   Coordinate a separate Protégé 6 registry/default with its maintainers before
   registering the new SWRLTab release; never redirect the Protégé 5 feed to it.
   Record additional communication candidates here as they arise. Send notifications
   or open upstream issues only when explicitly authorized. Completion: agreed
   notifications delivered and their issue links or responses recorded in the runbook.
