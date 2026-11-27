# OWLAPI 5 migration guide

This guide applies to the coordinated **`protege-6` branches, version
2.1.5-SNAPSHOT**. Published releases and the default branches may have different
OWLAPI/Protégé requirements. Follow the [build guide](../README.md) to check out and
validate the sibling sources together.

## Baseline and build scopes

| Component | Development baseline |
| --- | --- |
| Core OWLAPI | 5.5.1 |
| Drools | 7.74.1.Final |
| Build validation | JDK 17, Maven 3.9; Java 11 bytecode |
| Protégé plugin host | Unmodified 6.0.0-alpha-1, branch `protege6/release-6.0.0-alpha-1` |
| Core dependency versions | Managed in `swrlapi-parent`; see the [resolved baseline](../ops/runbook.md#dependency-security-baseline) |

The core and standalone builds require no Protégé installation. The plugin uses
host-provided OWLAPI and logging packages, while embedding the SWRLAPI engine and
its selected runtime dependencies. The core dependency baseline is not a request
to replace Guava, Jackson or OWLAPI inside Protégé.

Use explicit profiles: `core,static-analysis` for library verification,
`core,standalone,static-analysis` for the standalone application, and the
[host reactor](../ops/runbook.md#prot%C3%A9g%C3%A9-6-plugin-experiment) for a complete
host/plugin build. `full` is the default aggregator profile and includes both UIs.

## Compatibility for library callers

The internal OWLAPI streams refactor preserves public SWRLAPI signatures,
collection-returning APIs and custom-argument contracts. Recompile consumers that
previously used OWLAPI 4; public SWRLAPI API preservation does not make the OWLAPI
major versions binary compatible. Use the matching sibling snapshot artifacts,
not a mixture of default-branch jars and migration-branch sources.

OWLAPI 5 normalizes a language-free `rdf:PlainLiteral` to `xsd:string`. In SQWRL
results use `isString()` / `getString()` for those values. Language-tagged values
retain their tags. Datatype reasoning compares values where appropriate without
rewriting stored lexical forms or redefining literal structural equality.

The `getOWLReasoner()` accessor returns a cached, non-buffering reasoner with its
own materialized ontology/imports snapshot. It incorporates ontology changes,
including removals, and does not export inferred axioms. Dispose it after use;
serialize ontology edits and reasoner calls. Calling the rule engine's `infer()`
is the separate path that exports inferred axioms into the source ontology.

The accessor uses the default OWL 2 RL rule set independently of interactive rule
selection and SQWRL queries. Consult the [runtime contract](../ops/runbook.md#runtime-behavior-and-boundaries)
and [datatype support matrix](../ops/runbook.md#datatype-support-matrix):
unknown/custom datatypes and unsupported constraints are not proof of consistency.
Custom datatype definitions and facet restrictions are not evaluated; known
empty-class detection is not general satisfiability. Unsupported entailment axiom
types throw `UnsupportedEntailmentTypeException`.

## Built-in libraries and the plugin

For an external Protégé contributor, use
`swrltab-plugin.SWRLBuiltInLibraryFactoryPlugin` and a public no-argument factory.
Library prefixes and namespaces come from the registered library, not an ontology
prefix declaration. Register before importing saved rules/queries. Follow the
[complete registration guide](https://github.com/protegeproject/swrltab-plugin/blob/protege-6/docs/built-in-registration.md)
for the tested contributor, lifecycle, imports and collision handling.

A Protégé contributor must share the API exported by SWRLTab; embedding another
SWRLAPI jar can make identically named classes incompatible. The standalone
application does not discover Protégé extensions. Plain Java applications can use
the engine factory's pre-import configuration hook described in that guide.

## Validation and release status

Unit tests prove local behavior; the core `verify` gate also runs public rule,
query and reasoner integration tests. Plugin verification additionally checks the
assembled OSGi bundle and actual Protégé workflows. The runbook separates
[validation evidence](../ops/runbook.md#last-validation) by scope and artifact.
SpotBugs is configured; nullness type checking and additional CI coverage remain
[roadmap work](../ops/roadmap.md).

This snapshot has not been published as a Protégé 6 release. Installing to your
local Maven repository, copying a development plugin into a test host, and
publishing a release are separate operations. Use the [release procedure](../release/README.md)
for release artifacts and plugin update metadata.

[BSD 2-Clause license](../license.txt).
