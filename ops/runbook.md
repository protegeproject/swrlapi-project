# SWRLAPI migration runbook

The shared [development rules](../AGENTS.md) apply to every sibling repository.
This runbook covers the compatibility-first OWLAPI 5 port and its Drools engine.
The ordered backlog lives in [roadmap.md](roadmap.md). The validation records below
separate the bounded core conformance audit and datatype changes from full-build and graphical
workflows on unmodified Protégé 6 alpha-1. No host source or dependency upgrade was
required for those workflows. The internal OWLAPI streams migration preserves the
public SWRLAPI API. These are development builds; public release is separate.

## Checkout layout and versions

Keep the repositories beside one another under the workspace root:

```text
swrlapi-parent/
swrlapi/
swrlapi-drools-engine/
swrlapi-example/
swrlapi-integration-tests/
swrlapi-project/           # aggregator and this ops directory
swrltab/                  # standalone application
swrltab-plugin/            # Protégé 6 alpha experiment
```

The parent POM pins OWLAPI **5.5.1**, Drools **7.74.1.Final**, and Guava **33.8.0-jre**.
The project version is **2.1.5-SNAPSHOT**. Compilation targets Java 11; validation
in this workspace uses JDK 17. Latest Drools verified on 2026-11-26 is **10.2.0**;
see the [official Apache KIE releases](https://github.com/apache/incubator-kie/releases).
No Drools major-version upgrade is part of the current port.

The `protege-6` branches incorporate upstream `development` through the coordinated
2.1.4 release and 2.1.5-SNAPSHOT baseline. The parent retains OWLAPI 5.5.1 and SLF4J
2.0.16 for the core; upstream's OWLAPI 4 / SLF4J 1.7 choices apply to its older host.
The core/full profiles remain separate. Central Portal publishing configuration and
upstream release scripts are retained; no deployment, release tag, or publication
was performed. Release preparation is described in [release/README.md](../release/README.md).

Each directory is a separate Git repository. Inspect status in each relevant
repository; the enclosing workspace is not a single repository. Preserve unrelated
uncommitted changes. Do not reset or clean repositories as part of routine builds.

## Full verification

Run from the enclosing workspace directory:

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/pom.xml -Pfull,nullness,static-analysis clean verify
```

Use the appropriate JDK 17 path on other machines. `-o` uses the local Maven cache;
for a fresh checkout or missing dependencies, omit `-o` and resolve dependencies
through the configured repositories. Avoid running concurrent Maven builds against
these same module output directories.

The `core` profile builds the parent, library, Drools engine, example, and integration
tests. The default `full` profile adds the Protégé plugin and standalone application.
Use `-Pcore,standalone,nullness,static-analysis` for the standalone gate without host APIs,
or `-Pcore,protege-plugin,nullness,static-analysis` for the plugin gate without standalone.
When host sources change, use the combined host reactor below so consumers use
current producer artifacts. `verify` is required: `test` alone does not run and
check the Failsafe integration suite.

SpotBugs runs at maximum effort and high confidence, failing the build for findings
or analyzer errors. The `nullness` profile separately enforces Checker Framework
contracts on production sources; both belong in the verification gate. No formatter
gate is configured.

## Nullness checking

The `nullness` profile uses Checker Framework **4.4.0** and Maven Compiler Plugin
**3.14.1** on JDK 17+. Java bytecode still targets Java 11. Normal dependencies use
matching `checker-qual:4.4.0` annotations. The processor is isolated on the annotation
processor path, with compiler exports confined to forked javac, following the
[Checker Framework Maven instructions](https://checkerframework.org/manual/#maven).
The obsolete checker compiler and annotated JDK 8 jars are no longer application
dependencies. The profile checks all production sources in whichever reactor modules
are selected, including the core UI, plugin and standalone application in `full`.
It does not check test sources or Protégé and does not run the separate Optional
Checker. Dependency implementations remain outside this source check.

Run from the sibling workspace (omit `-o` if dependencies need downloading):

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/pom.xml -Pcore,nullness,static-analysis clean verify \
  > /tmp/swrlapi-nullness-core.log 2>&1
python3 swrlapi-project/ops/experiments/check-nullness-profile.py
```

Check Maven's exit status; nullness contract errors fail the strict build. The probe requires
a guarded nullable access to compile and an unsafe access to fail with exactly one
nullable-dereference site. It also checks the permitted null arguments in the JDK
stubs. It builds temporary fixtures without installing artifacts. The stub path
assumes this sibling layout; external experiments must pass `-Dchecker.stubs=` with
an absolute path to `swrlapi-parent/src/main/checker/jdk.astub`.

The three narrow dependency models cover documented nullable arguments in
`DatatypeFactory.newDuration`, `TransformService.init(TransformParameterSpec)`, and
`JTabbedPane.addTab`. They do not make SWRLAPI return values nullable. Reviewed
suppressions are limited to six private `ThreadLocal` fields whose non-null suppliers
initialize every thread, constructor initialization boundaries, and the manager's
existing live `Map.keySet` return. The constructor boundaries are in the built-in
library manager, query, tokenizer, bridge, dialog manager, Drools engine and class
expression handler, and the plugin's renderer and engine factory. Comments explain
the initialized state or deferred callback at each site. There are no class-wide
nullness suppressions or source exclusions. These trusted boundaries remain part
of code review; the gate is not a proof of arbitrary third-party behavior.

For a non-failing diagnostic inventory, add `nullness-audit` **alongside** `nullness`:

```sh
mvn -o -B -f swrlapi-project/pom.xml -Pcore,nullness,nullness-audit clean compile \
  > /tmp/swrlapi-nullness-audit.log 2>&1
python3 swrlapi-project/ops/experiments/summarize-nullness.py \
  /tmp/swrlapi-nullness-audit.log --csv /tmp/swrlapi-nullness-findings.csv
```

Audit mode uses `-Awarns`; its success does not imply zero findings. The summarizer
requires fresh nonempty compilation in all three core production modules and a
successful complete log, deduplicates repeated diagnostic sites, and runs the
strict probe before accepting a zero-finding inventory.

The shared GitHub Actions workflow in `swrlapi-project` runs the strict core and
SpotBugs gate on JDK 17 in UTC and America/Los_Angeles, checks the enforcement probe,
and retains logs, reports and sibling revisions for 14 days. Thin workflows in each core repository
call it, overlaying the triggering source revision onto sibling `protege-6` checkouts.
The workflows run on pushes and pull requests targeting `protege-6`, and support
manual dispatch. They use read-only repository permissions and Temurin 17 on
`ubuntu-latest`. The Maven step allows 35 minutes within a 40-minute job limit;
the initial successful hosted builds took 16–22 minutes. Maven output is streamed
to the job and saved in full with `pipefail` preserving its exit status.

Both timezone checks are required on `protege-6` in the project, parent, library,
Drools engine, example and integration-test repositories. Their names are
`verify (UTC)` / `verify (America/Los_Angeles)` in the project and
`verify / verify (UTC)` / `verify / verify (America/Los_Angeles)` in callers.
The project additionally requires `verify-update-channels`; the plugin repository
requires `verify-update-channels / verify-update-channels`. Checks are associated
with GitHub Actions and require an up-to-date branch. Administrator bypass remains
available; no review requirement or push restriction was added. These hosted gates
do not replace the local standalone packaging and actual Protégé loading/UI checks.

## Focused regression checks

```sh
mvn -o -B -f swrlapi-project/pom.xml -Pcore \
  -Dtest=DurationArithmeticTest,SWRLBuiltInArgumentContractTest,LiteralValuesTest,OWL2RLRuleTest \
  -Dsurefire.failIfNoSpecifiedTests=false \
  -Dit.test=DurationArithmeticIT,OWL2RLRemainingRulesIT,DroolsOWLReasonerIT verify
```

The Surefire option permits modules with no matching unit tests. Keep the Failsafe
selection explicit and confirm that the named integration classes actually ran.
A focused run supplements the full gate; it does not establish full compatibility.

For datatype regressions, use the same reactor with
`-Dtest=LiteralValuesTest,DatatypeRuleTest,DatatypeMembershipTest,OperandTraversalTest,OWL2RLRuleTest`
and `-Dit.test=DatatypeConformanceIT,OWL2RLRemainingRulesIT,DroolsOWLReasonerIT`.

For the bounded OWL 2 RL audit, use
`-Dtest=OWL2RLRuleTest,OWL2RLSchemaRuleTest,OWL2RLRuleCoverageTest,DefaultDroolsOWLAxiomHandlerTest,NaryAxiomTraversalTest`
and `-Dit.test=OWL2RLConformanceIT`, retaining the Surefire option above.
These selections contain 114 unit/rule cases and 20 integration tests; the full
core gate also checks their interactions with the existing datatype and query suites.

For timezone regressions, repeat relevant temporal tests with `-Duser.timezone=UTC`
and `-Duser.timezone=America/Los_Angeles` in separate Maven invocations. Keep the
same assertions: explicit offsets must represent the same instant in both runs.
The temporal boundary gate uses
`-Dtest=TemporalBoundaryTest,DurationArithmeticTest,XSDTimeUtilTest` and
`-Dit.test=DurationScalingMatrixIT,CalendarArithmeticMatrixIT,TemporalReasoningMatrixIT,TemporalSubtractionMatrixIT,DurationArithmeticIT`,
with the same sibling reactor and Surefire option above. The matrix cases assert
their expected counts; errors must reach the arithmetic path rather than fail
early in the rule parser. Do not mutate the JVM's global timezone inside tests.

## Evidence and failure triage

Inspect module reports:

- `swrlapi/target/surefire-reports/`: library unit and contract tests.
- `swrlapi-drools-engine/target/surefire-reports/`: isolated rule and converter tests.
- `swrlapi-integration-tests/target/failsafe-reports/`: public API and query tests.
- `swrltab-plugin/target/surefire-reports/`: rendering, registration, and lifecycle tests.
- `swrltab/target/failsafe-reports/`: assembled standalone application test.
- Each production module's `target/spotbugsXml.xml`: static-analysis findings.

Check `BUILD SUCCESS`, test counts, failures, errors, and skips. A failed Failsafe
run can finish executing all tests before failing `verify`. For DRL compilation
errors, inspect the generated rule text and the first compiler diagnostic. For
semantic failures, reduce the ontology to a regression and determine whether the
axiom was imported, converted, matched by a rule, and exposed by the reasoner.
Use isolated rule tests where alternate inference paths could hide a defect.

Before review, run `git -c core.whitespace=cr-at-eol diff --check` in each changed
repository. Existing sources use mixed LF and CRLF; preserve the file's format.

## OWLAPI stream accessors

Internal OWLAPI traversal in the library, Drools converters/reasoner, and plugin
renderer uses the OWLAPI 5 stream accessors for axioms, signatures, annotations,
rule bodies/heads/arguments, class/data-range operands, and reasoner node entities.
The public SWRLAPI interfaces, method signatures, return types, collection
mutability, and eager error behavior remain unchanged. No parallel traversal is
introduced.

Keep eager `asSet` / `asList` snapshots where callers mutate state, perform multiple
passes, or rely on collection evaluation before processing. Import-aware axiom
streams can repeat equal axioms from different ontologies; ordered sets or
`distinct()` retain the old deduplication. N-ary converters reuse one ordered
operand snapshot and keep independent mutable copies for directed pair expansion.
Existing `HashSet(Collection)` construction is retained where replacing it with a
collector could change capacity and iteration order used to allocate internal IDs.

OWLAPI's no-argument `getSignature()` delegates to `unsortedSignature()`, so its
replacements use that stream to preserve encounter order. Custom built-in argument
signature methods traverse bindings eagerly with identity-based cycle detection;
their public stream methods still capture detached collection snapshots before
returning. Changing a binding after obtaining a stream does not alter that stream,
and traversal errors remain immediate.

The source audit retains these intentional collection boundaries:

- Public SWRLAPI collection methods and custom signature stream adapters preserve
  existing dispatch, mutability, snapshots, and exception behavior.
- `getPropertyChain()` is an ordered OWLAPI list without a direct stream accessor;
  chain position is semantically significant.
- `asPairwiseAxioms()` performs semantic axiom expansion and has no direct stream
  replacement; its collection is streamed where needed.
- SWRLAPI multi-value argument lists and Drools path arguments are SWRLAPI-owned
  collections, not OWLAPI accessors.

Regression coverage includes duplicate/transitive/unrelated imports, live versus
independent collections, binding changes after stream creation, cycles, eager
failures, signature encounter order, annotated rule import, every directed pair
for eight kinds of n-ary axiom, nested class operands, and data-range operand
round trips. The signature-order regression failed with `signature()` and passes
with `unsortedSignature()`; its negative log is `/tmp/swrlapi-stream-order-before.log`.
The data-range tests verify representation preservation, not additional datatype
inference support.

The before/after `javap -public -s` comparison is identical across all 454 library,
154 Drools engine, and 10 plugin classes: public signatures and JVM descriptors
are unchanged. The plugin embeds the current library and engine jars byte-for-byte.
Subsequent full-build and graphical migration checks also cover these stream-based artifacts;
see the current evidence below.

## Runtime behavior and boundaries

`getOWLReasoner()` caches a non-buffering reasoner over an isolated snapshot of the
root ontology and imports. It includes SWRL rules and does not export inferred
axioms into the source ontology. Ontology changes invalidate that snapshot; direct
construction also supports buffering and `flush()`. Dispose reasoners when finished.
Serialize reasoner calls and ontology edits; interruption may come from another
thread. The accessor uses the default RL rule set independently of interactive
rule selection and SQWRL queries.

Property chains and keys compile to ordinary agenda rules. Chains retain path order
and support inverse operands/heads. Keys require a shared value for every property
and named class members/object values. Numeric data keys use value comparisons;
OWL literal structural identity and language tags remain intact. The interactive
engine honors rule selection. For OWLAPI 5.5.1 keys, use the actual property
operands: `getObjectPropertyExpressions()` returns the signature, losing inverses
and including properties from the key class expression. The current converter
filters `getPropertyExpressions()` instead; regression tests cover both cases.

Datatype reasoning uses the support matrix below. This is not a complete OWL 2 DL
reasoner or a claim of complete RL conformance. Unsupported entailment axiom types throw
`UnsupportedEntailmentTypeException`; known empty classes do not establish arbitrary
class-expression satisfiability.

### OWL 2 RL rule and API support matrix

This is a bounded audit of the **typed OWLAPI implementation**, using the
[OWL 2 RL rule tables](https://www.w3.org/TR/owl2-profiles/#Reasoning_in_OWL_2_RL_and_RDF_Graphs_using_Rules)
as the reference. It is not a general RDF triple engine or a certification of
[complete OWL 2 conformance](https://www.w3.org/TR/owl2-conformance/).
The public rule enum has 78 names. Of these, 67 have static DRL definitions and
isolated behavioral cases; 11 refer to generated rules, grouped/conversion paths,
or vocabulary/value handling. A name being enabled does not establish complete
implementation of the corresponding RDF rule.

Coverage is guarded by
[OWL2RLRuleCoverageTest](https://github.com/protegeproject/swrlapi-drools-engine/blob/protege-6/src/test/java/org/swrlapi/drools/owl2rl/OWL2RLRuleCoverageTest.java).
The principal evidence is:

- [OWL2RLRuleTest](https://github.com/protegeproject/swrlapi-drools-engine/blob/protege-6/src/test/java/org/swrlapi/drools/owl2rl/OWL2RLRuleTest.java): isolated assertion/equality rules, missing-premise and negative controls, and a required fixpoint.
- [OWL2RLSchemaRuleTest](https://github.com/protegeproject/swrlapi-drools-engine/blob/protege-6/src/test/java/org/swrlapi/drools/owl2rl/OWL2RLSchemaRuleTest.java): all 20 Table 9 rule names, 29 object/data cases, exact conclusion sets and removal of every premise.
- [OWL2RLConformanceIT](https://github.com/protegeproject/swrlapi-integration-tests/blob/protege-6/src/test/java/org/swrlapi/OWL2RLConformanceIT.java): public entailment, schema direction, alias propagation, imports/retractions, rule selection/export and SQWRL results.
- [OWL2RLRemainingRulesIT](https://github.com/protegeproject/swrlapi-integration-tests/blob/protege-6/src/test/java/org/swrlapi/OWL2RLRemainingRulesIT.java), [DroolsOWLReasonerIT](https://github.com/protegeproject/swrlapi-integration-tests/blob/protege-6/src/test/java/org/swrlapi/DroolsOWLReasonerIT.java), [NaryAxiomTraversalTest](https://github.com/protegeproject/swrlapi-drools-engine/blob/protege-6/src/test/java/org/swrlapi/drools/converters/oo/NaryAxiomTraversalTest.java), and the datatype tests linked below cover the generated/conversion and lifecycle paths.

The following rows describe tested behavior and its limits. They are not claims
that every possible ontology or interaction in a rule family has been tested.
`CLS_SFV1/2` are the existing public enum spellings of the specification's `cls-svf1/2`.

| Rules | Audited behavior / boundary | Evidence |
| --- | --- | --- |
| `EQ_REF`, `EQ_SYM`, `EQ_TRANS` | Individual reflexivity, symmetry and transitive closure; no generalized RDF equality over arbitrary subjects/predicates/literals. | Isolated rules; existing `OWL2RLIT` SQWRL cases |
| `EQ_REP_S`, `EQ_REP_O` | Equality propagates class membership, property assertions and different-individual facts; alias removal retracts derived facts in the reasoner snapshot. | Isolated rules; conformance alias and imported chain/key cases |
| `EQ_REP_P` | Grouped with property-equivalence rules; individual `sameAs` does not equate punned properties. This is a typed-OWL boundary, not full RDF predicate replacement. | Conformance punning control; property-equivalence rules |
| `EQ_DIFF1`, `EQ_DIFF2`, `EQ_DIFF3` | Same/different conflicts; n-ary different-individual axioms expand to pairs. | Isolated conflict; converter pair matrix; key/AllDifferent conflict and recovery |
| `PRP_AP` | Referenced annotation-property declarations can be imported; annotation entailments and all built-in RDF axiomatic triples are not materialized. | Converter inspection; no claim of annotation reasoning |
| `PRP_DOM`, `PRP_RNG` | Object/data domains, object ranges and data membership obligations in the supported datatype subset. | Isolated rules; reasoner domain/range tests; datatype integration tests |
| `PRP_FP`, `PRP_IFP` | Object equality from functionality/inverse functionality; data functionality conflicts only for proved distinct values. | Isolated rules; datatype functional-property tests |
| `PRP_IRP`, `PRP_SYMP`, `PRP_ASYP`, `PRP_TRP` | Irreflexive/asymmetric conflicts, symmetric edges and transitive closure with matching endpoints/properties. | Isolated rules and missing-premise controls |
| `PRP_SPO1`, `PRP_SPO2` | Object/data subproperties; generated ordered chains, inverse operands/heads, connected edges and repeated inference. | Isolated subproperty rules; remaining-rules and imported chain/key integration tests |
| `PRP_EQP1`, `PRP_EQP2`, `PRP_INV1`, `PRP_INV2` | Both directions of typed property equivalence and object inversion. | Isolated rules; public property/value and inverse assertion queries |
| `PRP_PDW`, `PRP_ADP`, `PRP_NPA1`, `PRP_NPA2` | Binary/n-ary property disjointness and negative assertion conflicts; data values use semantic comparison. | Isolated rules; n-ary pair conversion; conformance and datatype integration tests |
| `PRP_KEY` | Generated keys require every operand, shared values and named class members/object values; inverse operands and mixed data/object keys are tested. | Remaining-rules tests; imported chain/equality/key composition; key conflict/retraction |
| `CLS_THING`, `CLS_NOTHING1`, `CLS_NOTHING2` | Built-in class declarations and contradiction on a Nothing instance. | Isolated rules; reasoner built-in node tests |
| `CLS_INT1`, `CLS_INT2`, `CLS_UNI`, `CLS_COM` | Nonempty object intersection composition/decomposition, union membership from operands and complement conflicts. No disjunctive choice or general complement reasoning. | Isolated rules; public intersection/union queries and forbidden conclusions |
| `CLS_SFV1`, `CLS_SFV2`, `CLS_AVF` | Existential membership from known edges/fillers, Thing filler, and universal propagation; data fillers use the datatype membership subset. No existential witness generation. | Isolated rules; datatype membership and public tests |
| `CLS_HV1`, `CLS_HV2`, `CLS_OO` | Has-value in both directions and membership of object-enumeration members. Data has-value compares values. | Isolated rules; datatype has-value/export tests |
| `CLS_MAXC1`, `CLS_MAXC2`, `CLS_MAXQC1`, `CLS_MAXQC2`, `CLS_MAXQC3`, `CLS_MAXQC4` | Object/data maximum zero/one, qualified fillers and Thing/top-datatype cases. Higher cardinalities have no evaluator. | Isolated object/data rules; qualified-filler conversion and public datatype tests |
| `CAX_SCO`, `CAX_EQC1`, `CAX_EQC2` | Membership through subclass/equivalent-class closure. | Isolated rules; public types, instances and entailments |
| `CAX_DW`, `CAX_ADC` | Disjoint-class conflicts; n-ary operands become pairs. | Isolated conflicts; converter pair matrix; reasoner empty-class tests |
| `DT_TYPE1`, `DT_TYPE2`, `DT_EQ`, `DT_DIFF`, `DT_NOT_TYPE` | Named datatype identity, supported value membership/equality/inequality and lexical/membership conflicts. Value operations are helpers, not literal `sameAs` RDF triples; no complete datatype axiomatic graph is emitted. | Datatype support matrix, `DatatypeMembershipTest`, `DatatypeRuleTest`, `LiteralValuesTest`, `DatatypeConformanceIT` |
| `SCM_CLS`, `SCM_SCO`, `SCM_EQC1`, `SCM_EQC2` | Class bounds, subclass transitivity and conversion between equivalence and mutual subclass relations. | Exact schema cases; public hierarchy and entailment cases |
| `SCM_OP`, `SCM_DP`, `SCM_SPO`, `SCM_EQP1`, `SCM_EQP2` | Typed property reflexivity, transitivity and equivalence/subproperty conversion. | Exact schema cases; public property hierarchy/entailments |
| `SCM_DOM1`, `SCM_DOM2`, `SCM_RNG1`, `SCM_RNG2` | Domain inheritance, object-range superclass propagation and object/data range inheritance down subproperties. `SCM_RNG1` has no general datatype-subsumption schema rule. | Exact schema cases; public domains/ranges |
| `SCM_HV`, `SCM_SVF1`, `SCM_SVF2` | Has-value/property covariance and existential covariance; `SCM_SVF1` filler subsumption is implemented for object classes, not a general data-range lattice. | Exact object/data schema cases; datatype value-equal has-value case |
| `SCM_AVF1`, `SCM_AVF2` | Object universal filler covariance and object/data property contravariance: if `p` is below `q`, `all q.C` is below `all p.C`. | Exact schema cases; public hierarchy, consistency, selection/export and SQWRL controls |
| `SCM_INT`, `SCM_UNI` | Intersection-to-operand and operand-to-union subclass relations. | Exact schema cases; anonymous query preparation |

#### Public reasoner queries

`isEntailmentCheckingSupported` advertises the 15 axiom types below.
`advertisedEntailmentTypesHavePositiveAndNegativePublicCases` exercises a derived
or decomposed positive and a negative query for every advertised type, plus empty
and mixed-true/false sets. This is a capability map, not a completeness guarantee
for arbitrary expressions of those types.

| Query surface | Supported behavior / limits |
| --- | --- |
| Subclass, class assertion | Uses materialized schema/membership; new query expressions are prepared without asserting them. Subclass reflexivity and Thing/Nothing bounds are handled explicitly. |
| Object/data property assertions | Uses materialized assertions; inverse object assertion spelling is normalized and data assertion checks use value equality. |
| Same/different individuals; equivalent/disjoint classes; equivalent object/data properties | Checks required pairs in multi-operand queries and extracts pairs from stored multi-operand axioms. It does not infer inequality from different names. |
| Sub-object/data-property; object-property domain/range; data-property domain | Queries materialized schema consequences. |
| Other axiom types | `isEntailmentCheckingSupported` returns false and `isEntailed` throws `UnsupportedEntailmentTypeException`. Axiom types can participate as input rules without being supported as entailment queries; keys, chains, data ranges and property characteristics are examples. |
| Hierarchies, types, instances and property values | Named-entity results from the snapshot, with tested direct/transitive flags and equivalence groups. This is not complete classification of arbitrary anonymous expressions; inherited disjointness and general empty-class closure are not complete. |
| `isSatisfiable`, bottom/unsatisfiable class nodes | Detects Nothing, classes below/equivalent to Nothing, and classes below disjoint parents. A true result is not proof of general class-expression satisfiability. No witness-based satisfiability procedure is implemented. |
| `isConsistent` | False when supported rules find a contradiction; true means no supported contradiction was found. Unsupported constraints are not thereby validated. |
| Ontology lifecycle | Imports and imported edits are included; additions/removals and import removal invalidate the non-buffering snapshot. Buffered changes take effect on `flush()`. The reasoner does not export inferred axioms; the rule engine's `infer()` does. |

#### Unsupported constructs and converter audit

Datatype definitions, facet constraints, data unions/complements/enumerations and
cardinalities above one remain outside the evaluated subset described below.
The ID-based data-range handler retains original OWLAPI objects for round trips,
but its `DOO` fact does not carry enumeration literals and its `DRR` fact does not
carry facets. Those are representation/evaluation limits, not evidence that a
constraint has been checked.

The separate legacy `DroolsOWLDataRange2DRConverter` throws
`TargetSWRLRuleEngineNotImplementedFeatureException` for all its conversions and
has no construction site in the engine's current source path. The active path is
`DroolsOWLDataRangeHandler`. Property-expression built-in argument conversion
also retains explicit stubs in `DroolsSWRLBuiltInArgument2BAConverter`; those are
SWRL bridge extensions, not missing Table 9 rules.

The axiom converter ignores datatype definitions, reflexive-property axioms,
disjoint unions and annotation axioms. Class-expression representations exist for
self restrictions and minimum/exact cardinalities, but the rule set does not
supply their general semantics. General RDF metamodeling, arbitrary anonymous
individual results and full satisfiability are outside this audit. Some of these
constructs are outside the OWL 2 RL grammar; distinguish profile requirements
from optional extensions before selecting further work in the [roadmap](roadmap.md).

### Datatype support matrix

The declared reasoning subset follows the
[OWL 2 RL datatype and restriction grammar](https://www.w3.org/TR/owl2-profiles/#OWL_2_RL)
and [OWL datatype value spaces](https://www.w3.org/TR/owl2-syntax/#Datatype_Maps).
Value equality, proven inequality, and undecided comparisons are separate outcomes;
failure to prove equality never establishes inequality. `L.equals`/`hashCode`,
OWLAPI literal objects, and returned property-value sets retain structural identity.
`hasValue` can infer another lexical representation; it does not replace the original.

| Datatype / construct | Implemented behavior and limits | Regression evidence |
| --- | --- | --- |
| `xsd:decimal`, `integer`, `long`, `int`, `short`, `byte`, signed integer restrictions and four unsigned types | Exact numeric comparison across this family, integer bounds, lexical rejection and value-based subtype membership; decimal exponents are rejected. | `LiteralValuesTest`, `DatatypeRuleTest`, `DatatypeConformanceIT`, existing range tests |
| `xsd:float`, `xsd:double` | Separate value spaces from each other and decimal; finite values, infinities and NaN; positive and negative zero are distinct OWL values. | Floating-point identity unit tests and functional-property integration cases |
| `xsd:boolean` | `true`/`1` and `false`/`0` denote the same respective values. | Literal comparison and functional-property cases |
| `xsd:string`, `normalizedString`, `token`, `language`, `Name`, `NCName`, `NMTOKEN` | XML whitespace facets, name/language lexical checks, shared string values and subtype membership; string content remains case sensitive. | Literal tests, token/string functional comparison |
| `rdf:langString`, `rdf:PlainLiteral` | Case-insensitive, syntactically well-formed BCP 47 tags; distinct languages stay distinct; empty-language PlainLiteral maps to a string. Language registry validity and tag aliases are not resolved. | Language unit cases, language-tag functional/key cases |
| `xsd:dateTime`, `dateTimeStamp` | JDK XML Gregorian parsing/validation, timezone-normalized equality and required timezone for timestamps; an indeterminate comparison involving an absent timezone is not inequality. Explicit DST offsets, absent timezones, fractional precision and large years are covered by the temporal matrix. | Date/time units, functional properties, `TemporalReasoningMatrixIT`, existing invalid-date tests |
| `xsd:hexBinary`, `base64Binary` | Lexical validation and byte equality within each datatype, including base64 padding checks; the two value spaces remain disjoint. | Literal tests and functional-property integration cases |
| `xsd:anyURI` | Whitespace collapse and string identity within the URI value space; no network lookup or URI equivalence normalization. | Literal value-space tests |
| `rdf:XMLLiteral` | Well-balanced XML fragments are compared using exclusive XML canonicalization with comments and an empty inclusive prefix list; attribute order, empty-element spelling and CDATA normalize, while comments, content whitespace, namespace identity and prefix spelling remain significant. External entities/DTDs and XML declarations inside a fragment are rejected. | XML units, negative assertions, functional properties, keys, and serialization/entailment tests |
| Functional/disjoint data properties, negative assertions, data `hasValue` and its schema rule, data keys | Use value equality or proven inequality as appropriate; distinct lexical forms alone cannot cause a functional conflict. | Isolated rule cases and public reasoner tests |
| Data ranges, `allValuesFrom`, `someValuesFrom`, intersections | Check required membership or infer proved membership in supported named types and nested intersections; inferred memberships can feed existential and cardinality rules. | Membership unit matrix, range/universal tests, existential and qualified-intersection integration cases |
| Data maximum cardinality zero/one | Unqualified restrictions count all values; qualified restrictions retain their filler and count only proved members; maximum one rejects proved distinct values. | Isolated rules, converter round trips, public reasoner tests |
| Unknown/custom datatypes and datatype definitions | Definitions are not expanded; identical literal terms can match, but different unknown terms do not establish inequality or membership in known types. Required membership supplied by an asserted range remains an assumption, not lexical validation. | Unknown-value and custom-definition boundary tests |
| Facet restrictions, data unions/complements/enumerations, cardinalities above one | Outside this supported RL reasoning subset; representations can round-trip, but their datatype constraints are not evaluated. `owl:real`/`owl:rational` likewise have no value evaluator. Basic `xsd:date`/`time` parsing is an extension, not a claim of full temporal conformance. | Unsupported-range integration cases and existing converter tests |

XML canonicalization uses standard JDK XML DSig APIs, with no added Maven dependency.
See the [RDF XML literal representation guidance](https://www.w3.org/TR/2004/REC-rdf-concepts-20040210/#section-XMLLiteral)
for canonical comparison of noncanonical internal representations.
These checks apply to OWL reasoning; they do not change SWRL built-in arithmetic or
comparison contracts. `isConsistent() == true` means no supported rule detected a
contradiction; it does not certify constraints the matrix marks unsupported.
Rule selection applies to the interactive engine; the public reasoner accessor
continues to use its independent default rule set.

### Temporal behavior and legacy API boundaries

SWRL duration scaling uses signed months or seconds and XPath month rounding.
Multiplication by positive/negative zero yields zero; division by either zero,
NaN factors and multiplication by infinity raise `SWRLBuiltInException` with an
arithmetic diagnostic. Division by either infinity yields zero, including for a
zero duration. The rule parser accepts XSD `INF` and `-INF` floating-point literals;
floating overflow/underflow is handled as infinity/zero before scaling. Finite
decimal arithmetic retains the existing precision policy. Unrepresentable duration
results raise errors rather than wrapping integer fields. These boundary expectations
follow the [XPath duration operations](https://www.w3.org/TR/xpath-functions/).

The ten SWRL date/date-time/time addition and subtraction built-ins use JDK XML
calendar arithmetic. They preserve the input's explicit offset or absent timezone,
clip year/month shifts to the destination month's last day, wrap time-only values
at midnight, and retain fractional seconds in the result literal. An explicit
`-08:00` is a fixed offset, not a named timezone with daylight-saving rules. Thus
results are independent of the host's DST transitions. Year-month and day-time
operations reject operands containing components from the other duration subtype.
Whole-day shifts use direct calendar calculations because the JDK XML calendar's
day addition walks through months; only the remaining fraction of a day is passed
to that addition. Huge time-only shifts are reduced modulo a day, while date/date-time
results outside the supported range raise errors. The matrix includes ten-thousand-year
shifts and huge time-only durations, with a per-case timeout guarding against hangs.

Legacy Java conversions and wrappers retain their existing contracts: converting a
timezone-free date/date-time to `Date` uses the JVM's default timezone; `Date` helpers
and wrapper equality/order have millisecond precision. Day-time shifts truncate
submillisecond fractions and check overflow; year-month shifts retain local calendar
behavior and month-end clipping. Calendar-to-`Date` conversions reject years outside
the representable millisecond range. Date and date-time wrappers can be safely read
from threads other than their constructing thread.
`swrlb:subtractDateTimesYieldingDayTimeDuration` is registered and returns elapsed
time using these millisecond-based conversions. Its DST matrix distinguishes the
two occurrences of a repeated local hour by their explicit offsets, tests the spring
clock change, and covers equal instants and negative differences.

The OWL reasoner has a separate value-space contract: absent timezone comparisons
can be undecided, never assumed unequal, and XML calendar comparisons retain
fractional precision and large years beyond `Date`. The temporal reasoning matrix
checks entailment, functional-property conflicts, negative assertions and recovery
after removals using that contract in both JVM timezones.

Axis replacement assessment: JDK XML calendars already cover the built-in calendar
arithmetic path, but replacing Axis throughout is not a drop-in change. Public helpers
expose Axis duration/time classes; duration fields have integer component limits and
seconds ultimately use `double`. Date/date-time wrapper equality remains millisecond
based, and duration ordering deliberately compares normalized months and then seconds
as a total collection order. It does not equate months with a fixed number of days
or implement XML Schema's partial duration ordering. Retain those contracts until a
separate migration agrees precision, ordering, implicit timezone and adapter behavior.
The deprecated two-duration multiply/divide Java helpers still reject calls; use
the singular helpers with a `BigDecimal` factor. Remaining migration decisions are
in the [roadmap](roadmap.md).

## Last validation

### Nullness baseline inventory

Verified **2026-11-27**, JDK 17 / Maven 3.9.14, using the audit command above:
**429 production source files compiled**, with **188 contract findings in 54 files**.
This is a diagnostic inventory, not 188 confirmed runtime defects and not a passing
nullness gate. The unsafe/guarded profile probe passed both expectations.

| Module | Production sources | Contract findings | Annotation placement | Primitive annotations |
| --- | ---: | ---: | ---: | ---: |
| SWRLAPI | 277 | 160 | 1,781 | 8 |
| Drools engine | 151 | 28 | 1,433 | 0 |
| Example | 1 | 0 | 0 | 0 |
| Total | 429 | 188 | 3,214 | 8 |

The raw log contains 6,624 checker diagnostics; removing repeated identical sites
leaves 3,410. Contract categories are: nullable dereference 83; incompatible
argument 35; override parameter 25; method receiver 11; return 9; assignment 9;
generic type argument 7; generic inference 5; field initialization 2; nullable
unboxing 1; nullable iteration 1. Placement notices are reported separately and
were not suppressed to make the inventory look cleaner.

The subsequent strict-checking cleanup resolved these findings and the annotation
placement notices. Repeated map lookups now use checked local values or explicit
invariant guards; nullable overrides, visitor returns, lazy fields and UI lifecycle
state have accurate annotations. Concrete defects fixed include missing engine
version metadata, built-in invocation context left behind after exceptions,
nullable reflection returns, per-thread temporal initialization, and SQWRL column
lookup through an original name after a display alias is assigned.

Baseline logs: `/tmp/swrlapi-nullness-audit.log` and
`/tmp/swrlapi-nullness-findings.csv`. The original audit had no production behavior
fixes; the strict gate and consumer validation below cover the subsequent fixes.

### Strict nullness and consumer validation

Verified **2026-11-27**, JDK 17 / Maven 3.9.14. The full
`-Pfull,nullness,static-analysis clean verify` gate passed with **1,397 tests**, no
failures, errors or skips. A final clean rebuild after import/line-wrapping cleanup
and two additional boundary tests used the same profiles with
`-Duser.timezone=UTC -Dit.test=EngineVersionNullnessIT,PackagedApplicationIT`:
all unit suites and those two integration tests passed (**448 cases**). This second
run is focused integration validation, not a second full integration suite.
Together the reports contain **1,399 distinct passing cases**:

| Suite | Full gate | Final focused gate |
| --- | ---: | ---: |
| Library unit/contract tests | 241 | 242 |
| Drools engine unit/rule tests | 180 | 181 |
| Plugin unit/contract tests | 23 | 23 |
| Standalone packaged application | 1 | 1 |
| Public API/query integration tests | 952 | 1 |
| Total | 1,397 | 448 |

All **438 production source files** (277 library, 151 engine, seven plugin, two
standalone, one example) compile under strict checking without Checker diagnostics.
SpotBugs reports zero findings, analyzer errors or missing classes across all five
production modules. The guarded/unsafe checker probe passes, including the three
JDK dependency models; the clean-log summarizer reports zero core findings after
requiring fresh compilation and the active profile. The original baseline remains
reproducible from its saved log. No formatter gate is configured.

The thirteen new cases cover built-in failure/reset cleanup, null reflection
results, unreadable library directories, XML/JDBC temporal helpers used on another
thread, original/display column names, absent engine manifest metadata, public
query execution/version access, and nullable equals/visitor behavior across custom
argument kinds. Existing suites cover the map-lookup, reasoner lifecycle, ontology
change, collection, and plugin disposal paths. The normal dependency baseline now
uses `checker-qual:4.4.0`; packaged applications contain no checker compiler or old
annotated JDK jar.

Public/protected signatures and descriptors are unchanged across **319 library and
156 engine classes**. This comparison excludes annotation metadata: nullable
Object/visitor contracts and annotation placement were deliberately corrected.
All **551 source/resource/POM hashes** captured for the final build match after
validation. Logs and reports: `/tmp/swrlapi-nullness-full.log`,
`/tmp/swrlapi-nullness-full-reports`, `/tmp/swrlapi-nullness-final.log`,
`/tmp/swrlapi-nullness-clean-summary.log`, and
`/tmp/swrlapi-nullness-strict-probe.log`.

The packaged plugin SHA-256 is
`7492fdd04dab3b40dcfaf2062e7690cc54514e1fcce008e0a87ed4431b57a5d4`.
Its embedded library/engine jars match the final producers byte-for-byte, and its
only Checker jar is `checker-qual-4.4.0.jar`. The inventory and packaged OSGi checks
pass on the unchanged Protégé alpha-1 distribution: both tabs load, rule/variable
rendering is correct, arithmetic returns `5`, the contributed query returns `42`
with its negative control, and rules independently infer `Adult(alice)` and
`ContributedAdult(alice)`. Evidence: `/tmp/swrlapi-nullness-host-inventory.log` and
`/tmp/swrlapi-nullness-plugin-smoke.log`.

The graphical smoke test also passes with the same artifact: contributed/arithmetic
queries (`42`, `5`, then edited `7` and `9`), rule editing/import/run/export,
`Adult(alice)` inference, ontology switching, listener/factory cleanup, deliberate
initialization failure and recovery, and tab close/reopen. The initial sandboxed
launcher aborted before running the fixture; rerunning with desktop access passed.
Evidence: `/tmp/swrlapi-nullness-graphical-desktop.log` and
`/var/folders/c1/gtt0h33d00z7yg3w_fkfyhl40000gr/T/swrlapi-graphical-z0p0cjgm`.
The host checkout is still clean at `7c6d34f921cd33affa7aa075e1e28b10236d3648`.
Its pre-existing Aqua appearance-menu `IllegalAccessException` remains nonblocking
and queued for notification; errors explicitly marked as intentional fixture
initialization failures are the recovery test's negative control.

The first hosted core matrices passed on **2026-11-27** in all six repositories:
[project](https://github.com/protegeproject/swrlapi-project/actions/runs/46000400411),
[parent](https://github.com/protegeproject/swrlapi-parent/actions/runs/46000442759),
[library](https://github.com/protegeproject/swrlapi/actions/runs/46000449328),
[engine](https://github.com/protegeproject/swrlapi-drools-engine/actions/runs/46000455749),
[example](https://github.com/protegeproject/swrlapi-example/actions/runs/46000462812), and
[integration tests](https://github.com/protegeproject/swrlapi-integration-tests/actions/runs/46000465080).
Downloaded reports confirm **1,375 tests per timezone job** (242 library, 181
engine, 952 integration), zero failures/errors/skips, and three clean SpotBugs
reports per job. Both timezone properties were verified. Strict Checker compilation
and its enforcement probe passed. These runs used Temurin 17.0.21 on Ubuntu 26.04.1;
artifacts include the exact sibling revisions. Required checks were configured only
after these successful runs were verified. Later documentation, logging and timeout
changes do not alter the tested production sources.

### Temporal boundary validation

The final sibling reactor passed with
`mvn -o -B -f swrlapi-project/pom.xml -Pcore,static-analysis -Duser.timezone=America/Los_Angeles clean verify`:
**BUILD SUCCESS**, **1,362 tests passed** (231 library unit tests, 180 engine
unit/rule tests and 951 integration tests), with zero failures, errors or skips.
SpotBugs reported zero findings, analyzer errors or missing classes in all three
core production modules. Log: `/tmp/swrlapi-temporal-core.log`. The source/POM
hashes captured before this gate match the final working-tree inputs.

Verified **2026-11-27**, JDK 17 / Maven 3.9.14: the same **255 new parameterized
cases** passed in both `UTC` and `America/Los_Angeles`, with zero failures, errors
or skips. The matrices comprise 22 helper/wrapper boundaries, 156 duration-scaling
cases, 62 calendar-arithmetic cases, 10 OWL value-semantics cases and five registered
date-time subtraction cases. XML reports confirm both JVM timezone properties and
matching case names. UTC evidence: `/tmp/swrlapi-temporal-utc.log`,
`/tmp/swrlapi-temporal-registration-utc.log` and `/tmp/swrlapi-temporal-utc-reports/`.

The first regression run exposed ten helper/wrapper failures, 48 scaling
failures/errors and 38 calendar failures (`/tmp/swrlapi-temporal-before.log`);
that diagnostic deliberately continued after failures. Five further tests failed
because date-time subtraction was absent from the built-in registration list
(`/tmp/swrlapi-temporal-registration-before.log`) and pass after correcting it.
The huge-shift diagnostic was stopped; inspection of the installed JDK source
confirmed month-by-month day addition. The final calendar matrix guards the direct
whole-day calculation with large valid shifts, overflow errors and per-case timeouts.

Before/after `javap -protected -s` output is identical across **319 library classes**
and **156 engine classes**; the comparisons are
`/tmp/swrlapi-temporal-api.diff` and `/tmp/swrlapi-drools-engine-temporal-api.diff`.
No dependency or public signature changes were needed. Protégé remains clean at
`7c6d34f921cd33affa7aa075e1e28b10236d3648`; the plugin was not rebuilt or retested,
so its earlier packaged/GUI evidence predates these library changes.

### Bounded OWL 2 RL conformance audit

Verified **2026-11-26**, JDK 17 / Maven 3.9.14, with
`mvn -o -B -f swrlapi-project/pom.xml -Pcore,static-analysis clean verify`:
**BUILD SUCCESS**, **1,107 tests passed** (209 library unit tests, 180 engine
unit/rule tests and 718 integration tests), with zero failures, errors or skips.
SpotBugs reported zero findings, analyzer errors and missing classes in the three
core production modules. Full log: `/tmp/swrlapi-rl-audit-core.log`.

The regressions expose and verify seven defect families: reversed object/data
universal-restriction subproperty inference; missing inequality propagation across
individual aliases; existential rather than conjunctive axiom-set checking; n-ary
entailment/pair extraction; missing preparation of new anonymous query expressions;
inverse object-assertion entailment; and loss of the second equivalent object
property during axiom export. Fresh-entity policy and annotation-insensitive
entailment are also checked. The support matrix above records the tested subset
and known limits rather than claiming complete standards conformance.

Failing regressions were captured before their fixes in
`/tmp/swrlapi-rl-audit-before.log`, `/tmp/swrlapi-rl-equality-before.log`,
`/tmp/swrlapi-rl-audit-extended.log` and `/tmp/swrlapi-rl-export-before.log`.
The first two diagnostic runs deliberately continued after test failures and are
not passing gates. The final full gate includes all 20 new public integration
tests, 29 isolated schema cases, the expanded 75-case assertion/equality suite,
the rule coverage guard and real converter/extractor round trips.

Before/after `javap -protected -s` output is identical for all **319 compiled
SWRLAPI classes** and **156 engine classes**. Evidence:
`/tmp/swrlapi-rl-api.diff` and `/tmp/swrlapi-drools-engine-rl-api.diff` are empty.
Production and test sources were unchanged after the passing gate. Documentation
links and instruction-file aliases were checked, and the rendered support matrix
was inspected for readability.

Protégé remains clean on `protege6/release-6.0.0-alpha-1` at
`7c6d34f921cd33affa7aa075e1e28b10236d3648`. This was a **core-only** gate;
the plugin was not rebuilt or retested. The plugin artifact and GUI evidence
below predate these engine changes.

### Documentation and contributor validation

Verified **2026-11-26** with the documented focused sibling plugin package command:
**360 unit tests passed** (209 library, 128 engine and 23 plugin), with zero
failures, errors or skips. Log: `/tmp/swrlapi-doc-plugin-build.log`. This package
run is not a new full integration/static-analysis gate; the unchanged core sources
retain the core evidence below. The README query source printed exactly `4`, and
the packaged example printed `x: 4` (`/tmp/swrlapi-doc-snippet.log` and
`/tmp/swrlapi-doc-example.log`).

The packaged contributor passed ACTIVE-bundle, shared-API, positive/negative query,
rendering and inference checks (`/tmp/swrlapi-doc-plugin-smoke.log`). The actual
Protégé GUI passed contributed result `42`, arithmetic `5`/`7`/`9`, rule editing
and inference, ontology switches, initialization-failure recovery, tab reopen and
cleanup (`/tmp/swrlapi-doc-graphical.log`). Evidence directory:
`/var/folders/c1/gtt0h33d00z7yg3w_fkfyhl40000gr/T/swrlapi-graphical-mzwl_h7o`.
The harness used a temporary distribution copy and isolated home; the original
host remains clean at `7c6d34f921cd33affa7aa075e1e28b10236d3648`.

Validated plugin SHA-256:
`b4d965b03a0a6e41f3b5db484a0f22a3ec7ce6529be6236d74e9acec393518a4`.
Its embedded library and engine jars matched the producers built for that validation
byte-for-byte; its HTML readme matched the source. The contributor jar includes the exact
BSD text from `swrltab-plugin/license.txt`. Existing license terms and Stanford
attribution are unchanged; copyright ranges now include 2026, and wiki checkouts
include the same project license. README/local and cross-repository links, heading
anchors and shell syntax were checked, and the quick start and lifecycle table
were previewed as rendered Markdown.

The [migration guide](../docs/owlapi5-migration.md), sibling READMEs and
[registration guide](https://github.com/protegeproject/swrltab-plugin/blob/protege-6/docs/built-in-registration.md)
are versioned with the `protege-6` source branches. The SWRLAPI and SWRLTab plugin
wikis link to these guides and distinguish the development snapshot from released
Protégé 5 builds. Keep version-specific instructions in those guides and preserve
the wiki's general language/API reference pages.

### Core datatype validation

Verified **2026-11-26**, JDK 17 / Maven 3.9.14, with
`mvn -o -B -f swrlapi-project/pom.xml -Pcore,static-analysis clean verify`:
**1,033 tests passed** (209 library unit tests, 126 engine unit/rule tests and
698 integration tests), with zero failures, errors or skips. SpotBugs reported
zero findings, analyzer errors and missing classes in all three core production
modules. Full log: `/tmp/swrlapi-datatype-core.log`.

The new regressions reproduced seven isolated-rule failures and nine public-reasoner
failures before implementation (`/tmp/swrlapi-datatype-before.log`; that diagnostic
run deliberately continued after failures). The passing cases cover value equality,
proved inequality, unknown values, XML canonicalization, restrictions, rule selection,
imports, equality propagation, retractions and serialization. Two additional legacy
qualified-cardinality cases were subsequently added to the isolated-rule suite;
all 43 final focused cases passed with no failures, errors or skips
(`/tmp/swrlapi-datatype-isolated-final.log`).
Production sources did not change after the full gate.

Before/after `javap -protected -s` output is identical for all **454 SWRLAPI classes**.
All existing Drools signatures and descriptors are retained; the engine adds the
internal qualified-cardinality fact and two value-operation helpers used by DRL.
API comparison evidence is in `/tmp/swrlapi-datatype-api.diff` and
`/tmp/swrlapi-drools-engine-datatype-api.diff`.

Protégé remains clean at `7c6d34f921cd33affa7aa075e1e28b10236d3648`.
This datatype validation used the core profile only; it neither rebuilt nor
retested the plugin/host. The earlier plugin artifact and GUI evidence below
therefore predate the datatype changes.

### Previous combined host and plugin validation

Verified **2026-11-26**, JDK 17 and Maven 3.9.14: **BUILD SUCCESS** for the combined
unmodified Protégé host and `-Pfull,static-analysis clean verify` reactor. The host
is exactly `7c6d34f921cd33affa7aa075e1e28b10236d3648`, with no source changes.
The checkout is on `protege6/release-6.0.0-alpha-1`; the unused local experiment
branch was removed after validation. The reactor consumes current
host and SWRLAPI sources directly, without installing or publishing host artifacts.

| Suite | Tests | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Library unit/contract tests | 209 | 0 | 0 | 0 |
| Drools engine unit/rule tests | 76 | 0 | 0 | 0 |
| Plugin unit/contract tests | 23 | 0 | 0 | 0 |
| Standalone packaged-application integration test | 1 | 0 | 0 | 0 |
| Public API/query integration tests | 681 | 0 | 0 | 0 |
| SWRLAPI total | 990 | 0 | 0 | 0 |
| Protégé host tests | 556 | 0 | 0 | 0 |

All host tests passed, including its three native file-chooser cases. The host
suite accesses public ontology/prefix services, unlike the offline SWRLAPI core
gate. SpotBugs reports zero findings, analyzer errors, or missing classes across
all five analyzed SWRLAPI production modules. No formatter gate was configured in this earlier validation; current strict
nullness enforcement is documented above.

The packaged OSGi and graphical checks use the exact plugin from this build:
SHA-256 `412b743076f97118f6c810b518a0b4015787583b5e857f3097088aa8ea2c92f1`.
Its embedded library and engine jars match the producers from that validation
byte-for-byte. The actual host Guava 18.0 and OWLAPI 5.5.1 bundle jars match their
original Maven artifacts byte-for-byte; the OWLAPI jar embeds Jackson 2.16.1.
No upgraded wrapper or dependency jar is substituted into the host distribution.
The inventory check rejects duplicate bundle identities and unexpected upgrades;
negative controls exercised both failures against copies of the real distribution.

The query-view regression originally failed with expected `7`, actual `5`, then
passed after replacing the result object in the existing result panel. It checks
column-count changes, empty results, result-tab recreation, and exactly one Run
button. Listener tests include positive controls before disposal. The actual
Protégé process additionally exercises rule/query editing, contributed query `42`,
ontology switching, failure recovery, tab close/reopen, and editor cleanup.
The test-only editor cleanup was compiled and the graphical matrix rerun after
the full gate; the packaged production plugin is unchanged.

Local evidence:

- Combined clean build: `/tmp/swrlapi-unmodified-protege-full.log`.
- Packaged OSGi check: `/tmp/swrlapi-unmodified-osgi.log`.
- Graphical matrix: `/tmp/swrlapi-unmodified-graphical-final.log`; application evidence
  is `/var/folders/c1/gtt0h33d00z7yg3w_fkfyhl40000gr/T/swrlapi-graphical-kky28yw6`.
- Test fixture compilation: `/tmp/swrlapi-unmodified-fixture-compile.log`.
- Earlier query-view failure/pass: `/tmp/swrlapi-query-view-before.log` and
  `/tmp/swrlapi-query-view-after.log`.

The original host's JDK 17 Aqua appearance-menu access error is still logged; it
does not prevent the tested plugin workflows. That host limitation has not been
patched or hidden. Two additional initialization errors are intentional negative
controls in the contributor fixture. Historical modified-host reports under
`/tmp/swrlapi-fresh-host-reactor.log` and their temporary source/distribution copies
are superseded by the unmodified-host evidence above. Passing cases do not
establish complete OWL RL/DL conformance or a security audit of the entire host.

## Dependency security baseline

The shared parent manages Guava **33.8.0-jre**, the Jackson **2.21.9 LTS BOM**,
and XStream **1.4.21**. Maven Enforcer rejects older versions of Guava,
Jackson core/databind, and XStream, including transitive selections. The original
versions (33.0.0-jre, 2.16.1, and 1.4.20) each failed an explicit downgrade check.

The four open GitHub Dependabot alerts on `swrlapi-parent` were all Guava alerts:
CVE-2018-10237, CVE-2020-8908, CVE-2023-2976, and
[GHSA-xxph-c9ww-hj94](https://github.com/google/guava/security/advisories/GHSA-xxph-c9ww-hj94).
The first three were already fixed by 33.0.0-jre; the fourth required the upgrade.
[Guava 33.8.0](https://github.com/google/guava/releases/tag/v33.8.0) also includes
hash-flooding protections. GitHub default-branch alerts remain open until the fixed
version reaches that branch and GitHub refreshes its dependency graph.

An OSV query of the resolved core graph on 2026-11-26 additionally flagged Jackson
core/databind and XStream. After the updates, **91 distinct resolved Maven
coordinates/versions** returned **zero OSV matches**. This is a dated advisory
lookup of declared core dependencies, not a complete binary or plugin security
assessment. Upstream OWLAPI 5.5.1's OSGi jar embeds Jackson 2.16.1; Maven overrides
affect the plain core classpath, not those nested jars. The unmodified Protégé alpha
host retains Guava 18.0, its Jackson 2.9.8 POM baseline, and OWLAPI's nested Jackson
2.16.1. These original versions are validated for plugin compatibility here;
functional success is not a security audit. The broader host-upgrade experiment
was withdrawn. Protégé dependency-alert triage belongs to its maintainers and is
outside this SWRLAPI backlog.
POI is not a dependency of this project and is outside this work.

Eight added integration tests cover:

- Four Guava collection deserialization cases, each in a bounded child JVM. All four
  fail with the old dependency and pass with the patched dependency; ordinary
  serialization round trips are checked as well.
- RDF/JSON and JSON-LD ontology round trips preserving language, escaping, typed
  values, ontology identity, and asserted axioms through OWLAPI/RDF4J.
- Drools module/session configuration round trips through its XStream converter.
- Jackson's number-length constraint with chunked input and a valid-input control.

Dependency inventory command, run after or together with packaging current sources:

```sh
mvn -o -B -f swrlapi-project/pom.xml -Pcore -DskipTests package \
  dependency:tree -DoutputFile=target/dependencies-after.txt
```

The full test gate must run separately without `-DskipTests`. Dependency trees live
under each module's `target`; logs for the red/green Guava check are
`/tmp/swrlapi-guava-before.log` and `/tmp/swrlapi-guava-after.log`. The final OSV
query/result is `/tmp/swrlapi-osv-after.json`. These temporary files are local
verification evidence, not release artifacts. Version rationale:
[Jackson 2.21 LTS](https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.21),
[XStream 1.4.21](https://x-stream.github.io/changes.html#1.4.21).

## Protégé 6 plugin experiment

The host checkout is `/Users/martin/workspace/protege/protege`, on
`protege6/release-6.0.0-alpha-1` at `7c6d34f921cd33affa7aa075e1e28b10236d3648`,
with no source changes. The unused local `protege-6-swrlapi` branch was deleted;
recreate it only for a demonstrated need and never push it without explicit
authorization.
Protégé is an external test dependency: prefer plugin-side fixes, retain its
original dependencies, and demonstrate any necessary host change before applying
it. Shared Guava/Jackson upgrades may affect unrelated host functionality and need
a separate decision. Build the unmodified host and
all SWRLAPI siblings in one reactor from the SWRLAPI workspace:

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/ops/experiments/host-reactor.xml \
  -Dprotege.source=../../../../protege/protege \
  -Pfull,nullness,static-analysis clean verify
```

`protege.source` is a relative module path from `ops/experiments`, not the shell's
working directory. For a fresh workspace with `protege` alongside `swrlapi-project`,
use `../../../protege`. Omit `-o` when the cache lacks dependencies. This reactor
avoids silently using stale installed host jars and does not install modified
alpha artifacts over released coordinates in the local Maven repository.

For a focused plugin package with unchanged, already-built host dependencies:

```sh
mvn -o -B -f swrlapi-project/pom.xml -Pcore,protege-plugin \
  -pl :swrltab-plugin -am package
```

This runs producer unit tests and packages the plugin; it does not replace the
full `verify` gate. The plugin is
`swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar`.

No host change is needed for the verified SWRLTab workflows. The original
platform-independent launcher logs an Aqua appearance-menu `IllegalAccessException`
on JDK 17 because `Workspace` reflectively constructs Apple's unexported look-and-
feel implementation. The host catches the exception and omits that menu entry.
The plugin's query, inference, editing, and lifecycle checks pass despite this
separate host UI limitation. This is an unsent notification queued under
**Notifications to Protégé developers** in [the roadmap](roadmap.md). Reproduce
with the original platform-independent launcher on macOS/JDK 17; the relevant
`Workspace.addLookAndFeelMenuItem` stack trace is in the final graphical run's
`user/.Protege/logs/protege.log` (evidence directory under **Last validation**).
No issue or message has been sent. Do not broaden the plugin port into host
dependency maintenance.

Clean the host when changing assembly dependency sets. An old OWLAPI jar left in
`target` previously hid a wrapper-resolution error by supplying a second bundle
with the same symbolic name. Both the packaged harness and host verifier now
reject duplicate bundle identities; tests explicitly start and identify the
actual OWLAPI and Guava bundles.

The plugin uses the host's SLF4J 1.7 API; ordinary core builds retain SLF4J 2.0.16.
Protégé exports packages at 6.0.0 even though the Maven artifact is an alpha, so
host imports use `[6.0.0,7.0.0)`. OWLAPI 5.5.1 has independently versioned package
exports (for example model 5.4.0, formats 6.0.0, util 7.0.1); using one range based
on the artifact version prevented resolution. bnd now derives those imports in
all three bundles. The plugin no longer declares the host's `ProtegeOWL` activator,
which would replace the host's static bundle context with the plugin context.

The plugin POM declares host APIs as `provided`, obtains Drools transitively from
`swrlapi-drools-engine`, and embeds an explicit runtime allowlist. It excludes the
old Checker compiler and annotated JDK 8 jars; annotation types remain available.
JUnit and the simple SLF4J binding are test-only. The unused CDI/JPA dependencies,
Maven integration payload, duplicate version properties, and redundant
install-time manifest execution have been removed. Drools' OSGi compiler adapter
remains a runtime dependency, with its unused Spring dependencies excluded.
Remaining optional imports cover unused Axis SOAP providers and Drools integrations;
Java desktop/XML APIs
remain required. The packaged smoke test rejects compiler/test/host jars in the
bundle and requires both embedded SWRLAPI jars.

SWRL objects in the axiom panels use a Manchester renderer with explicit built-in
prefixes and variable names: `swrlb:add(?sum, 2, 3) -> sqwrl:select(?sum)`.
Ordinary OWL objects still use the host renderer, and class/individual display
names inside rules retain the host's entity rendering. This operates on typed
objects, so literal text resembling rule syntax is not rewritten.
Eight plugin tests cover the arithmetic query, default and explicit variable
namespaces, custom built-in prefixes, literal text, ordinary OWL delegation,
anonymous class expressions, and the actual Asserted Axioms Swing table on the EDT.
Four of the initial six tests reproduced the old rendering failure before the fix.

The contributor regression suite adds eleven cases, plus two library-prefix
regressions, to the original eight rendering tests:
factory initialization/access/disposal, null or unconfigured factories, empty
contribution sets, positive and negative queries, saved-query import, contributed
rule inference, collision rejection, atomic validation, and cleanup on failure.
The original four factory cases failed before the fix (three assertion failures
and the null dereference), recorded in `/tmp/swrlapi-contributor-before.log`.
The latest combined `-Pfull,static-analysis clean verify` results,
including these plugin regressions, are recorded under **Last validation** above.
The plugin static-analysis gate now reports zero findings and zero analyzer errors;
the two factory null defects are fixed without suppressions.

### Third-party built-in contributions

The [contributor guide](https://github.com/protegeproject/swrltab-plugin/blob/protege-6/docs/built-in-registration.md)
is the implementation reference for the extension point, factory/library lifecycle,
prefix ownership, OSGi imports and collision/error behavior. The executable example
uses the plugin's tested `ExampleLibrary`, `ExampleLibraryFactory` and descriptor;
its packager includes the project's BSD license and no duplicate API classes.

Build the separate test contributor after running the plugin tests:

```sh
python3 swrlapi-project/ops/experiments/build-contributor-fixture.py \
  swrltab-plugin /tmp/swrlapi-contributor-fixture.jar
```

This jar contains two fixture classes, their extension descriptor, manifest and
BSD license, using
exactly the same library implementation tested by the plugin unit suite. Pass its
path as the fourth argument to `PluginSmoke` to test actual Equinox discovery,
shared API identity, the contributed query result `42`, an empty negative result,
and independent inference of `ContributedAdult(alice)`. Without that argument the
harness checks the declared extension point, an empty contribution registry, and
ordinary rule/query execution. The registry bootstrap starts the host's SAX parser
service and Equinox registry; the complete graphical host remains a separate gate.

### Packaged and graphical validation

Run the assembled-host inventory and packaged semantic checks after building.
The inventory script verifies the original alpha-1 baseline, including nested jar
versions; it is a compatibility check, not a statement about dependency security:

```sh
protege_dist=/Users/martin/workspace/protege/protege/protege-desktop/target/protege-6.0.0-alpha-1-platform-independent/Protege-6.0.0-alpha-1
python3 swrlapi-project/ops/experiments/verify-host-bundles.py "$protege_dist"
java -cp "$HOME/.m2/repository/org/apache/felix/org.apache.felix.main/7.0.5/org.apache.felix.main-7.0.5.jar" \
  swrlapi-project/ops/experiments/PluginSmoke.java \
  "$protege_dist" swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar \
  /tmp/swrlapi-plugin-smoke.ttl /tmp/swrlapi-contributor-fixture.jar
```

The unmodified-host contributor check passes: the plugin becomes ACTIVE, both tab
classes load, rule/variable rendering is correct, arithmetic returns exactly `5`,
the contributed query returns exactly `42` with an empty negative control, and
rules independently infer `Adult(alice)` and `ContributedAdult(alice)`. The harness
writes the ontology before inference so the graphical test starts from premises.
Its Felix storage is isolated from the user's plugin cache. This functional OSGi
check is distinct from the graphical host gate.

Build and run the optional graphical test fixture in a desktop session:

```sh
python3 swrlapi-project/ops/experiments/build-contributor-fixture.py \
  swrltab-plugin /tmp/swrlapi-graphical-fixture.jar --graphical
python3 swrlapi-project/ops/experiments/run-graphical-smoke.py \
  "$protege_dist" swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar \
  /tmp/swrlapi-graphical-fixture.jar /tmp/swrlapi-plugin-smoke.ttl \
  --java-home "$JAVA_HOME"
```

The runner copies the distribution and inputs to a temporary directory, launches
its supported `run.sh` with a test home and the opt-in `swrlapi.guiSmoke` property,
prints artifact hashes, and checks a bounded result file. It closes its process
on completion; `--keep-open` retains a successful test application for inspection.
On an ordinary run, the fixture removes and disposes its editor while the OSGi
registry is still active, asserting that all contributed factories are released.
This avoids window-activation callbacks after the launcher stops the registry.
The fixture runs on Swing's event thread inside the actual Protégé process. It
selects tables and presses existing buttons, edits through the real modal editor,
and reads the displayed result model. It is not a native mouse-routing or
screenshot test; native screenshot attachment failed to identify the Java window.

The unmodified-host graphical matrix passes:

- Contributed query displays one result, `42`; arithmetic displays `5`, then `7`
  and `9` after two edits through the same editor dialog.
- SWRL rule editing followed by import, Run Drools, and export adds `Adult(alice)`
  after checking that it was initially absent.
- Ontology switches clear views, dispose old editors, unregister old listeners,
  and release contributed factories; a positive listener control prevents a
  vacuous cleanup assertion.
- Deliberately failing contributor initialization releases resources and leaves
  no stale model; the next ontology switch recovers. Its two expected error log
  entries are fixture failures, not an ordinary-launch defect.
- Closing both tabs prevents listener/factory recreation; reopening creates exactly
  two live factories and the contributed query displays `42` again.
- Closing the editor releases the final contributed factories before OSGi shutdown;
  the final run has no window-event error after framework disposal.

Manual verification uses the same generated ontology: enable **Window → Tabs →
SWRLTab** and **SQWRLTab**; run **OWL+SWRL→Drools**, **Run Drools**, and
**Drools→OWL**, then inspect `Adult(alice)`. Run `osgiSmoke` and `contributedAnswer`
in SQWRLTab and inspect exact values `5` and `42`. Repeat after editing a query and
switching ontologies. Test copies use a separate home, but macOS Java preferences
may still share system-backed settings; restore any temporary appearance/tab
choices. No official distribution or published plugin was replaced.

### Standalone application

The standalone module now uses the same parent/core/engine snapshot and ordinary
OWLAPI dependency jars. Its application zip retains the main jar and `lib/`
dependencies separately, preserving service resources. See the
[standalone README](../../swrltab/README.md) for launch commands.

The headless packaged-application integration test launches a child JVM using
only the assembled jar's manifest classpath and test probe. It verifies rule
inference, a query returning `5`, file save/close/reopen, query edit and another
save/reopen returning `7`. It rejects obsolete Checker/JDK 8 and OWLAPI OSGi jars
in the standalone distribution. The optional desktop startup check invokes both
actual application entry points, requires two visible populated windows, and
closes them:

```sh
java -cp swrltab/target/swrltab-2.1.5-SNAPSHOT-application/swrltab-2.1.5-SNAPSHOT/swrltab-2.1.5-SNAPSHOT.jar \
  swrlapi-project/ops/experiments/StandaloneSmoke.java
```

### Release metadata

The existing Protégé 5 update feed remains on its released 2.1.4 version. The
Protégé 6 `update.properties.template` is deliberately unpublished; it uses a
release-version placeholder and immutable release-tag links for both jar and
readme, and is labelled `SWRLTab (Protege 6 only)`. The Protégé 5 readme is also
pinned to `release-2.1.4` on this branch so a later default-branch promotion cannot
show Protégé 6 instructions to legacy users. Validate both channels and the actual
packaged host imports, then use the host's update parser:

```sh
python3 swrlapi-project/release/check-plugin-update-channels.py swrltab-plugin \
  --bundle swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar
java -cp "$protege_dist/bundles/*" \
  swrlapi-project/ops/experiments/PluginUpdateSmoke.java \
  swrltab-plugin/update-info/protege-6/update.properties.template \
  swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar
python3 -m unittest discover -s swrlapi-project/release -p 'test_*.py'
```

The parser check and all fifteen release-tool tests pass. Nine update-channel
regressions cover the real metadata plus unsafe version/download/readme changes,
missing host labels, SNAPSHOT publication, relaxed/optional imports, and weakened
packaged manifests. The current plugin's real manifest passes the same guard.
The dedicated `Plugin update channels` workflow runs the source guard and its
regressions for project/plugin pushes and pull requests on `protege-6`.
Its first [plugin run](https://github.com/protegeproject/swrltab-plugin/actions/runs/46002331974)
passed all nine channel tests and the real metadata/POM guard; its check is required
on the plugin branch. This workflow does not build the plugin: packaged-manifest
and host runtime checks remain separate gates. The protections cover `protege-6`
and release preparation, not arbitrary edits to the live `master` feed.

Verified live on 2026-11-27: the
[Protégé 5 registry](https://github.com/protegeproject/autoupdate/blob/master/update-info/5.0.0/plugins.repository)
references the plugin's `master/update-info/protege-5/update.properties`, which
still advertises only the released 2.1.4 jar. The
[Protégé 6 registry](https://github.com/protegeproject/autoupdate/blob/master/update-info/6.0.0/plugins.repository)
does not yet list SWRLTab. Neither registry nor the live `master` feed was changed.

The host update parser reads plugin identity, plugin version and URLs; it does not
check a minimum Protégé version. Separate registries/feeds protect discovery, while
the plugin's mandatory `[6.0.0,7.0.0)` imports protect loading. Manual copying or
pointing a client at the wrong registry can still offer/install an incompatible jar,
which must then fail OSGi resolution; the metadata is not a download-time host check.
The unmodified alpha-1 source at `7c6d34f` still uses `plugin.registry-5.0.url` and the
5.0.0 registry as its default. This host issue is queued for maintainer coordination
in the roadmap; the host remains unchanged.

The parser check renders a temporary candidate based on the bundle version,
verifies identity/version/tagged URLs, and makes no download or publication request. Two release-script tests validate inherited project versions,
release/next-snapshot SCM tags, absent optional siblings, and wrong-branch rejection
without writes. Four bundle-verifier tests check inherited versions, mandatory
standalone zip inclusion, and archive checksum validation; only the external GPG
call is mocked in those tests. Real release verification still invokes GPG for
every payload. See [release guidance](../release/README.md) for the separate
publishing procedure. Validate the final plugin against an identified, unmodified
host release before advertising compatibility with a public distribution.

## Protégé Plugin Development References

Reviewed 2026-11-26; these references complement the local experiment above.
They do not replace testing the assembled plugin and host.

- [Protégé 6 migration requirements](https://github.com/protegeproject/protege/issues/1367):
  the documentation issue remains open. Its checklist covers OWLAPI 5.5.1,
  Java Optional, visitor interfaces, Maven dependencies, OSGi import ranges,
  collection/stream API boundaries, and testing in an assembled distribution.
- [SPARQL Query plugin](https://github.com/protegeproject/sparql-query-plugin):
  its current README describes version 4 targeting Protégé 6, OWLAPI 5.5.1,
  Java 11, and RDF Library 4. It gives Maven build commands and an interactive
  verification procedure using both bundle JARs in an assembled Protégé 6.
  The live GitHub API confirmed these settings at revision
  [`a357a48`](https://github.com/protegeproject/sparql-query-plugin/blob/a357a48d5559799b429c1327f3b8c22173084e13/pom.xml),
  with `protege.version` set to `6.0.0-alpha-1`; cached pages can show the old POM.
  [Migration issue](https://github.com/protegeproject/protege/issues/1358)
  is closed. This is a concrete migration reference, not a local validation result.
- [Generic plugin examples](https://github.com/protegeproject/protege-plugin-examples):
  small tabs, views, menus, plugin descriptors, and Maven OSGi packaging. The
  examined POM still targets `protege-editor-owl` 5.0.0 and Java 8; adapt its
  dependencies and bundle imports rather than treating it as a Protégé 6 template.
- [Protégé 6 plugin registry](https://github.com/protegeproject/autoupdate):
  `update-info/6.0.0/plugins.repository` lists compatible released plugins.
  The repository documents a validator that checks downloaded bundle identities
  and versions; this does not replace interactive workflow verification.

## Shared Agent Entry Points

The version-controlled rules are in `swrlapi-project/AGENTS.md`. Workspace
`AGENTS.md`, `CLAUDE.md`, and `model.md` link to that file; the project repository's
`CLAUDE.md` and `model.md` link to its `AGENTS.md`. Workspace `ops` links to
`swrlapi-project/ops`. These aliases share one source of truth and preserve relative
links. CEDAR is the documented provenance, not the symlink target.

After a fresh sibling checkout, create missing workspace links from the workspace
root (inspect existing paths first; do not overwrite other instructions):

```sh
ln -s swrlapi-project/AGENTS.md AGENTS.md
ln -s swrlapi-project/AGENTS.md CLAUDE.md
ln -s swrlapi-project/AGENTS.md model.md
ln -s swrlapi-project/ops ops
```

The workspace aliases sit outside the individual Git repositories and must be
recreated on a new machine. The canonical rules and project-local aliases travel
with `swrlapi-project`. Start multi-repository sessions at the enclosing workspace
so tools discover the shared rules before working in a child repository.
