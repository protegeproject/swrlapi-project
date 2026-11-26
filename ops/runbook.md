# Core migration runbook

The shared [development rules](../AGENTS.md) apply to every sibling repository.
This runbook covers the compatibility-first OWLAPI 5 port and its Drools engine.
The ordered backlog lives in [roadmap.md](roadmap.md). SWRLTab / Protégé work and
the streams refactor are deferred.

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
swrltab-plugin/            # deferred
```

The parent POM pins OWLAPI **5.5.1**, Drools **7.74.1.Final**, and Guava **33.0.0-jre**.
The project version is **2.1.4-SNAPSHOT**. Compilation targets Java 11; validation
in this workspace uses JDK 17. Latest Drools verified on 2026-11-26 is **10.2.0**;
see the [official Apache KIE releases](https://github.com/apache/incubator-kie/releases).
No Drools major-version upgrade is part of the current port.

The port is being published on `protege-6` branches. A remote check on 2026-11-26
found that upstream `development` has since moved through release 2.1.4 to
2.1.5-SNAPSHOT, with updated publishing configuration. The verified port still uses
its 2.1.4-SNAPSHOT baseline; reconcile those upstream changes and version choices
before merging or releasing it. See the release-readiness roadmap item.

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
| Public API/query integration tests | 666 | 0 | 0 | 0 |
| Total | 933 | 0 | 0 | 0 |

SpotBugs reported **zero high-confidence findings** in all analyzed production
modules. Coverage includes 54 isolated RL rule cases, 20 chain/key/datatype
integration tests, 11 duration integration tests, and 21 reasoner lifecycle/API
tests. The final run includes the inverse-key/accessor regression and the test
ensuring key class-expression properties are not mistaken for key operands.

The local full build log is `/tmp/swrlapi-final-full.log`; durable test/report
locations are listed above. Documentation checks confirmed that all shared-rule
aliases resolve to the canonical file, local guidance links resolve, roadmap
numbering is contiguous, and changed repositories pass the whitespace check.
SWRLTab/plugin builds and full RL/DL conformance are outside this verification.

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
