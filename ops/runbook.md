# SWRLAPI migration runbook

The shared [development rules](../AGENTS.md) apply to every sibling repository.
This runbook covers the compatibility-first OWLAPI 5 port and its Drools engine.
The ordered backlog lives in [roadmap.md](roadmap.md). The Protégé 6 plugin and
standalone application pass the local migration gates described below. The
internal OWLAPI streams migration preserves the public SWRLAPI API. These are
development builds; public release and host upstream integration are separate.

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
mvn -o -B -f swrlapi-project/pom.xml -Pfull,static-analysis clean verify
```

Use the appropriate JDK 17 path on other machines. `-o` uses the local Maven cache;
for a fresh checkout or missing dependencies, omit `-o` and resolve dependencies
through the configured repositories. Avoid running concurrent Maven builds against
these same module output directories.

The `core` profile builds the parent, library, Drools engine, example, and integration
tests. The default `full` profile adds the Protégé plugin and standalone application.
Use `-Pcore,standalone,static-analysis` for the standalone gate without host APIs,
or `-Pcore,protege-plugin,static-analysis` for the plugin gate without standalone.
When host sources change, use the combined host reactor below so consumers use
current producer artifacts. `verify` is required: `test` alone does not run and
check the Failsafe integration suite.

SpotBugs runs at maximum effort and high confidence, failing the build for findings
or analyzer errors. The old Checker Framework 1.9.13 / JDK 8 annotation processor is
disabled. SpotBugs does not replace nullness type checking.

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

For timezone regressions, repeat relevant temporal tests with `-Duser.timezone=UTC`
and `-Duser.timezone=America/Los_Angeles` in separate Maven invocations. Keep the
same assertions: explicit offsets must represent the same instant in both runs.

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

Datatype checks cover built-in lexical forms, numeric bounds, ranges, universal
restrictions, and intersections. Unknown/custom datatypes are left undecided.
XML canonical equivalence and value semantics throughout older data-property rules
remain roadmap work. This is not a complete OWL 2 DL reasoner or a claim of complete
RL conformance. Unsupported entailment axiom types throw
`UnsupportedEntailmentTypeException`; known empty classes do not establish arbitrary
class-expression satisfiability.

Duration arithmetic uses signed months or seconds, finite numeric scaling factors,
XPath month rounding, and explicit zero-divisor errors. Fractional seconds are
preserved in library parsing and results. Java helpers taking two duration operands
for multiplication or returning a duration from division are deprecated and reject
those calls; use singular helper names with a `BigDecimal` factor. Duration ordering
uses normalized months and then seconds for a total collection order; it does not
convert months to a fixed number of elapsed days. Timezone-free date/time values
retain the historical JVM-default-timezone interpretation.

## Last validation

Verified **2026-11-26**, JDK 17 and Maven 3.9.14: **BUILD SUCCESS** for the combined
host and `-Pfull,static-analysis clean verify` reactor. Fresh sibling clones were
overlaid with the current source changes and built without copied `target`
directories or installed copies of the modified host. The host's reactor outputs
were consumed directly by the plugin. This validates clean-source packaging;
the source changes were uncommitted, so this is not a tagged release build.

| Suite | Tests | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Library unit/contract tests | 209 | 0 | 0 | 0 |
| Drools engine unit/rule tests | 76 | 0 | 0 | 0 |
| Plugin unit/contract tests | 23 | 0 | 0 | 0 |
| Standalone packaged-application integration test | 1 | 0 | 0 | 0 |
| Public API/query integration tests | 681 | 0 | 0 | 0 |
| SWRLAPI total | 990 | 0 | 0 | 0 |
| Protégé host tests | 558 | 0 | 0 | 3 |

The host's three existing skips are native file-chooser cases in
`MacUIUtil_TestCase`, excluded when headless; 555 host tests passed. The host suite
also accesses public ontology/prefix services, unlike the offline SWRLAPI core
gate. SpotBugs reports zero findings, analyzer errors, or missing classes across
all five analyzed SWRLAPI production modules. No formatter gate is configured;
nullness type checking remains separate roadmap work.

The query-view regression first failed with expected `7`, actual `5`, then passed
after replacing the result object in the existing result panel. It also checks
column-count changes, empty results, result-tab recreation, and exactly one Run
button. Plugin lifecycle regressions use a positive listener control before
release and prove that released models no longer receive ontology changes.
The graphical fixture separately checks dialog reuse, rule editing, query edits,
ontology switching, initialization failure recovery, and tab close/reopen.

Local evidence:

- Combined clean-source build: `/tmp/swrlapi-fresh-host-reactor.log`.
- Source/build workspace: `/var/folders/c1/gtt0h33d00z7yg3w_fkfyhl40000gr/T/swrlapi-fresh-sources-q119wq4v`.
- Query-view failure/pass: `/tmp/swrlapi-query-view-before.log` and
  `/tmp/swrlapi-query-view-after.log`.
- Final packaged OSGi check: `/tmp/swrlapi-final-osgi.log`.
- Final graphical matrix: `/tmp/swrlapi-final-graphical.log` and
  `/var/folders/c1/gtt0h33d00z7yg3w_fkfyhl40000gr/T/swrlapi-graphical-i6pz7e8b`.
- Standalone window startup: `/tmp/swrlapi-standalone-graphical.log`.

The exact fresh-built plugin used by both final OSGi and graphical checks has
SHA-256 `d015a0b3253ec7c58fd4060e1aa0de63f504cfbe7d9484534fbdb37466600b9b`.
Its embedded core and engine jars match the same build's producers byte-for-byte.
A final comparison confirmed 2,416 current source/build input files match the fresh
workspace. Public signatures and JVM descriptors of the three modified library
classes match their pre-migration counterparts (`javap -public -s`).
These paths are temporary local evidence; retain the module reports for CI or
release review. Passing cases do not establish complete OWL RL/DL conformance.

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
affect the plain core classpath, not those nested jars. The modified local host now
builds its own OWLAPI runtime bundle from the plain distribution, embedding managed
Jackson 2.21.9 / annotations 2.21. The assembled host verifier checks those actual
nested bytes and Guava 33.8.0-jre. This does not constitute an advisory audit of
every dependency in the Protégé distribution.
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

The host checkout is `/Users/martin/workspace/protege/protege`, review branch
`swrlapi-protege6-migration`, based on `protege6/release-6.0.0-alpha-1` at
`7c6d34f921cd33affa7aa075e1e28b10236d3648`. The migration changes are kept on this
review branch for upstream integration; the baseline is the alpha release branch,
not the moving `protege-6` branch. Build current host sources and
all SWRLAPI siblings in one reactor from the SWRLAPI workspace:

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/ops/experiments/host-reactor.xml \
  -Dprotege.source=../../../../protege/protege \
  -Pfull,static-analysis clean verify
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

The host parent now manages Guava 33.8.0-jre and the Jackson 2.21.9 BOM. Its new
`protege-owlapi` module wraps the ordinary OWLAPI 5.5.1 distribution in an OSGi
bundle (`org.semanticweb.owl.owlapi`, version `5.5.1.protege6alpha1`) with managed
nested dependencies. Published OWLAPI jars are untouched. Assembly descriptors
include this wrapper and Guava's `failureaccess`; unused HTTP OSGi adapters are
excluded to avoid their additional service requirements. Inlined dependencies'
`module-info.class` files are excluded from host/plugin bundles so a dependency's
JPMS descriptor cannot misidentify the assembled host on the test classpath.

`Workspace` obtains appearance-menu labels from Swing's registered look-and-feel
metadata instead of reflectively constructing Apple's unexported Aqua class.
Two host tests verify name lookup without loading implementation classes. The
JDK 17 platform-independent graphical launch passes without the former Aqua
access error.

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

SWRLTab owns the extension point
`swrltab-plugin.SWRLBuiltInLibraryFactoryPlugin`. A contributor's `plugin.xml`
contains an identified extension with a factory class:

```xml
<extension id="myLibrary" point="swrltab-plugin.SWRLBuiltInLibraryFactoryPlugin">
  <name value="My built-in library"/>
  <class value="example.MyLibraryFactory"/>
</extension>
```

The class must be a public no-argument subclass of `SWRLBuiltInLibraryFactory`:

```java
public class MyLibraryFactory extends SWRLBuiltInLibraryFactory {
  @Override protected SWRLBuiltInLibrary createSWRLBuiltInLibrary() {
    return new MyLibrary();
  }
}
```

The wrapper initializes the factory before exposing its library. Access before
initialization or after disposal fails explicitly; repeated initialization and
disposal are safe. Each engine receives fresh contributed instances, registered
before the first ontology import so saved rules and queries are recognized.
Both SWRLTab and SQWRLTab use this path. Tab disposal and ontology changes release
the old factories and unregister the old model's ontology listener; failed
registration disposes already-created factories. Prefix and namespace collisions
are rejected, and every declared built-in method is validated before registration.
The Protégé resolver obtains registered built-in names from the library manager,
which uses each library's declared `getPrefix()` and `getNamespace()`. Thus
`contributed:answer` is displayed even without an ontology prefix declaration,
after prefix refresh, or when an ontology alias or cached autogenerated prefix
exists. Known built-in names resolve back to the same IRI; unknown predicates and
ordinary OWL entities retain the existing ontology/host rendering behavior.

Contributors import `org.swrltab.core`, `org.swrlapi.builtins`,
`org.swrlapi.builtins.arguments`, and `org.swrlapi.exceptions` with compatible
package versions (for example `[2.1,3)`), plus any additional APIs they use.
They must not embed a second SWRLAPI copy. The SWRLTab bundle re-exports its embedded
core API and the types exposed by that API so contributors share class identity
with the engine; the Drools implementation packages remain private.
The public SWRLAPI interfaces and existing signatures are unchanged; registration
is an additive manager method and engine-factory configuration hook.

Build the separate test contributor after running the plugin tests:

```sh
python3 swrlapi-project/ops/experiments/build-contributor-fixture.py \
  swrltab-plugin /tmp/swrlapi-contributor-fixture.jar
```

This jar contains only two fixture classes and their extension descriptor, using
exactly the same library implementation tested by the plugin unit suite. Pass its
path as the fourth argument to `PluginSmoke` to test actual Equinox discovery,
shared API identity, the contributed query result `42`, an empty negative result,
and independent inference of `ContributedAdult(alice)`. Without that argument the
harness checks the declared extension point, an empty contribution registry, and
ordinary rule/query execution. The registry bootstrap starts the host's SAX parser
service and Equinox registry; the complete graphical host remains a separate gate.

### Packaged and graphical validation

Run the assembled-host inventory and packaged semantic checks after building:

```sh
protege_dist=/Users/martin/workspace/protege/protege/protege-desktop/target/protege-6.0.0-alpha-1-platform-independent/Protege-6.0.0-alpha-1
python3 swrlapi-project/ops/experiments/verify-host-bundles.py "$protege_dist"
java -cp "$HOME/.m2/repository/org/apache/felix/org.apache.felix.main/7.0.5/org.apache.felix.main-7.0.5.jar" \
  swrlapi-project/ops/experiments/PluginSmoke.java \
  "$protege_dist" swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar \
  /tmp/swrlapi-plugin-smoke.ttl /tmp/swrlapi-contributor-fixture.jar
```

The final ordinary contributor check passes: the plugin becomes ACTIVE, both tab
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
The fixture runs on Swing's event thread inside the actual Protégé process. It
selects tables and presses existing buttons, edits through the real modal editor,
and reads the displayed result model. It is not a native mouse-routing or
screenshot test; native screenshot attachment failed to identify the Java window.

The final graphical matrix passes:

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
readme. Validate it against the built plugin with the actual host parser:

```sh
java -cp "$protege_dist/bundles/*" \
  swrlapi-project/ops/experiments/PluginUpdateSmoke.java \
  swrltab-plugin/update-info/protege-6/update.properties.template \
  swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar
python3 -m unittest discover -s swrlapi-project/release -p 'test_*.py'
```

The parser check and all six release-tool tests pass. The parser check renders a
temporary candidate based on the bundle version, verifies identity/version/tagged URLs, and makes no download or
publication request. Two release-script tests validate inherited project versions,
release/next-snapshot SCM tags, absent optional siblings, and wrong-branch rejection
without writes. Four bundle-verifier tests check inherited versions, mandatory
standalone zip inclusion, and archive checksum validation; only the external GPG
call is mocked in those tests. Real release verification still invokes GPG for
every payload. See [release guidance](../release/README.md) for the separate
publishing procedure. The modified host must be integrated and identified by a
release before advertising the plugin's compatibility with a public distribution.

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
