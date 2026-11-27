# SWRLAPI migration runbook

The shared [development rules](../AGENTS.md) apply to every sibling repository.
This runbook covers the compatibility-first OWLAPI 5 port and its Drools engine.
The ordered backlog lives in [roadmap.md](roadmap.md). The Protégé 6 plugin is
under experimental validation; standalone SWRLTab and the streams refactor remain
deferred.

## Checkout layout and versions

Keep the repositories beside one another under the workspace root:

```text
swrlapi-parent/
swrlapi/
swrlapi-drools-engine/
swrlapi-example/
swrlapi-integration-tests/
swrlapi-project/           # aggregator and this ops directory
swrltab/                  # deferred
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
was performed. The release reactor still requires separate plugin validation.

Each directory is a separate Git repository. Inspect status in each relevant
repository; the enclosing workspace is not a single repository. Preserve unrelated
uncommitted changes. Do not reset or clean repositories as part of routine builds.

## Full verification

Run from the enclosing workspace directory:

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/pom.xml -Pcore,static-analysis clean verify
```

Use the appropriate JDK 17 path on other machines. `-o` uses the local Maven cache;
for a fresh checkout or missing dependencies, omit `-o` and resolve dependencies
through the configured repositories. Avoid running concurrent Maven builds against
these same module output directories.

The `core` profile builds the parent, library, Drools engine, example, and integration
tests. The default `full` profile includes the deferred plugin modules; it is not the
core migration gate. `verify` is required: `test` alone does not run and check the
Failsafe integration suite.

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
- Each production module's `target/spotbugsXml.xml`: static-analysis findings.

Check `BUILD SUCCESS`, test counts, failures, errors, and skips. A failed Failsafe
run can finish executing all tests before failing `verify`. For DRL compilation
errors, inspect the generated rule text and the first compiler diagnostic. For
semantic failures, reduce the ontology to a regression and determine whether the
axiom was imported, converted, matched by a rule, and exposed by the reasoner.
Use isolated rule tests where alternate inference paths could hide a defect.

Before review, run `git -c core.whitespace=cr-at-eol diff --check` in each changed
repository. Existing sources use mixed LF and CRLF; preserve the file's format.

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

Verified **2026-11-26**, JDK 17, with the full offline core/static-analysis command
above: **BUILD SUCCESS**.

| Suite | Tests | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Library unit/contract tests | 201 | 0 | 0 | 0 |
| Drools engine unit/rule tests | 66 | 0 | 0 | 0 |
| Public API/query integration tests | 677 | 0 | 0 | 0 |
| Total | 944 | 0 | 0 | 0 |

SpotBugs reported **zero high-confidence findings** in all analyzed production
modules. Coverage includes 54 isolated RL rule cases, 20 chain/key/datatype
integration tests, 11 duration integration tests, and 21 reasoner lifecycle/API
tests. Three rule-editing regressions cover adding a rule after querying, replacing
and deleting compiled rules, and edits processed by the UI model listener. Two
failed before the cache fix. The engine compares source axioms (including imports)
as well as change flags before reusing compiled rules, because UI model processing
can clear the bridge flag before a run.

The local full build log is `/tmp/swrlapi-plugin-final-core.log`; durable test/report
locations are listed above. Documentation checks confirmed that all shared-rule
aliases resolve to the canonical file, local guidance links resolve, roadmap
numbering is contiguous, and changed repositories pass the whitespace check.
The full core gate excludes SWRLTab/plugin builds and does not establish full RL/DL conformance.

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
assessment. OWLAPI's OSGi jar embeds Jackson 2.16.1; Maven overrides affect the plain
core classpath, not those nested jars. The plugin roadmap tracks that distinction.
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

The host checkout is `/Users/martin/workspace/protege/protege`, branch
`protege6/release-6.0.0-alpha-1`, revision
`7c6d34f921cd33affa7aa075e1e28b10236d3648`. This is the release branch, not the
moving `protege-6` branch. Its unmodified source passed `mvn -B clean install`
with JDK 17, including host tests (`/tmp/protege6-alpha-build.log`).
Build/install this host before building the plugin so its alpha artifacts are local.

Build the plugin with the current sibling producers, from the SWRLAPI workspace:

```sh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
mvn -o -B -f swrlapi-project/pom.xml -Pcore,protege-plugin \
  -pl :swrltab-plugin -am package
```

This runs producer unit tests and packages the plugin. Run the full core `verify`
gate separately for integration tests and static analysis. The combined profiles
exclude the deferred standalone application. The resulting artifact is
`swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar`.

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
The combined `-Pcore,protege-plugin,static-analysis verify` gate passed 965 tests
(201 library, 66 engine, 21 plugin, 677 integration), with zero failures, errors,
or skips. Log: `/tmp/swrlapi-prefix-full.log` (2026-11-26).
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

Run the packaged artifact in a fresh Felix framework using
[PluginSmoke.java](experiments/PluginSmoke.java):

```sh
java -cp "$HOME/.m2/repository/org/apache/felix/org.apache.felix.main/7.0.5/org.apache.felix.main-7.0.5.jar" \
  swrlapi-project/ops/experiments/PluginSmoke.java \
  /Users/martin/workspace/protege/protege/protege-desktop/target/protege-6.0.0-alpha-1-platform-independent/Protege-6.0.0-alpha-1 \
  swrltab-plugin/target/swrltab-plugin-2.1.5-SNAPSHOT.jar \
  /tmp/swrlapi-plugin-smoke.ttl
```

Verified 2026-11-26: **PASS**. The actual bundle becomes ACTIVE, both tab classes
load against the host's packages, axiom rendering preserves built-in prefixes and
variable names, SQWRL arithmetic returns exactly `5`, and a rule
infers exactly `Adult(alice)` after an initial empty-result control. The source
fixture also asserts `Person(alice)` as a positive control. The optional third
argument writes an ontology before inference for graphical testing. Felix storage
is isolated in a temporary directory printed by the harness; it does not use the
user's Protégé plugin cache. This is an OSGi functional test, not a graphical test.
Log for the earlier cleaned POM and renderer: `/tmp/swrlapi-clean-pom-osgi.log`.
The contribution and library-prefix version passes in
`/tmp/swrlapi-prefix-osgi.log`, including exact rendering of the contributed query,
real registry discovery and both contributed positive/negative execution cases.
The final empty-contributor packaged check also passes in
`/tmp/swrlapi-prefix-empty-osgi.log`.

The contribution fixes were also loaded in two separate full macOS applications
under `/Users/martin/workspace/protege/runtime-contributor-test/` on 2026-11-26:
`SWRL Empty Test.app` (no contributor) and `SWRL Contributor Test.app` (the separate
fixture bundle). Both tabs initialized without extension-point or factory errors.
Their logs are `/tmp/swrlapi-empty-test-user/.Protege/logs/protege.log` and
`/tmp/swrlapi-contributor-test-user/.Protege/logs/protege.log`; both identify
Protégé 6.0.0 alpha-1, OWLAPI 5.5.1 and SWRLTab 2.1.5.SNAPSHOT, with no warning or
error entries. The contributor log identifies the discovered fixture extension.

Before the final prefix adjustment, graphical import and Run Drools produced
`:alice Type :ContributedAdult` and `:alice Type :Adult` in Inferred Axioms.
After the adjustment, the contributor application was restarted with the rebuilt
jar; loading `/tmp/swrlapi-contributor-smoke.ttl` visibly showed
`contributed:answer(?value) -> sqwrl:select(?value)` in both tabs.
The final built and installed jars match SHA-256
`ef7db81fafd18ee29531fc6c5e50dd59b192b240fabdff7f541e5df1d332c2b4`.
The empty-contributor GUI check used the preceding contribution build; the final
build's empty-contributor behavior is covered by unit and packaged tests.
Native menu focus/input routing prevented a reliable graphical query Run during
the final check despite reconnecting and restoring the window; do not treat the
packaged query result `42` as a verified graphical result. That remaining UI check
is recorded in the roadmap. Standard tabs and window size were restored.

Local graphical copies are under `/Users/martin/workspace/protege/runtime-alpha-1`
and `runtime-alpha-1-mac/Protégé.app`. The latter contains the tested plugin in
`Contents/plugins`; its `Contents/conf/jvm.conf` selects JDK 17 and a test
`user.home` at `/tmp/swrlapi-protege-mac-user`. JVM properties were verified with
`jcmd`. Java's macOS preferences can still share existing system-backed settings,
so do not assume `java.util.prefs.userRoot` fully isolates the native preferences.
The temporary look-and-feel choice was restored and standard tabs re-enabled.

Graphical procedure: open `/tmp/swrlapi-plugin-smoke.ttl`, enable **Window → Tabs →
SWRLTab** and **SQWRLTab**, then select each panel. Both panels were observed
rendering the rule/query table and recognizing Drools. Martin subsequently reported
on 2026-11-26 that the graphical Run/import/export and query workflows work. This
closes the previously outstanding manual smoke verification; it is user-reported
evidence, separate from the automated OSGi test. Repeatable smoke procedure:

- In SWRLTab, use **OWL+SWRL→Drools**, **Run Drools**, then **Drools→OWL**; inspect
  `Adult(alice)` in the ontology, not just a success message.
- In SQWRLTab, select `osgiSmoke` and **Run**; expect one row containing `5`.
  Run `before` after rule execution and expect `alice`.

The final cleaned-POM/renderer jar was independently retested through the full
macOS application on 2026-11-26, using the separate copy
`/Users/martin/workspace/protege/runtime-rendering-test/SWRL Rendering Test.app`
and `/tmp/swrlapi-rendering-smoke.ttl`. The built jar and installed jar both have
SHA-256 `27eb88c14dd72dd5857990a3ce78b11f8f825252a2dc29de0f2ebf34b3d26e72`.
The application's own log identifies Protégé 6.0.0 alpha-1, OWLAPI 5.5.1,
JDK 17, and SWRLTab 2.1.5.SNAPSHOT; it is at
`/tmp/swrlapi-rendering-test-user/.Protege/logs/protege.log`.

Observed through computer control: both panels loaded; import transferred nine
axioms; Run Drools succeeded and the Inferred Axioms table contained
`:alice Type :Adult`; export reported successful transfer to the OWL model.
The Asserted Axioms table visibly showed
`swrlb:add(?sum, 2, 3) -> sqwrl:select(?sum)`.
Running `osgiSmoke` in SQWRLTab returned one row, and its result table displayed
column `sum` with value `5`. Native menus enabled the tabs; some Swing controls
required screenshot-based clicks, and query selection used keyboard navigation
from the New button after cancelling the editor. The test copy remains open with
the result visible; the user's previous application was not replaced or closed.
This is actual graphical-host evidence in addition to the isolated OSGi harness.

Broader graphical regressions for editing/deleting rules, switching ontologies,
and listener lifecycle remain on the roadmap; these additional cases were not
established by the smoke test.

The platform-independent macOS launcher
logs an Aqua look-and-feel reflective-access error on JDK 17. Host code in
`Workspace.addLookAndFeelMenuItem` tries to construct `com.apple.laf.AquaLookAndFeel`
reflectively to obtain its display name, but `java.desktop` does not export that
package to the caller. The host catches the exception and omits that appearance
menu entry; this observed error is outside rule/query execution. The packaged
macOS application's log did not contain it. A host UI/launcher correction and
retest remain necessary for the affected launch path.

The macOS host log is `/tmp/swrlapi-protege-mac-user/.Protege/logs/protege.log`.
That earlier run confirms plugin 2.1.5.SNAPSHOT and OWLAPI 5.5.1 and contains the
then-unresolved extension-point warning; the contribution fix and its new test logs
are described above. The
alpha host still ships Guava 18 and OWLAPI's nested Jackson 2.16.1. Functional
success does not establish a patched OSGi distribution. No host sources or
published OWLAPI artifacts were rewritten, and no plugin release was published.

## Protégé Plugin Development References

Reviewed 2026-11-26; these references complement the local experiment below.
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
