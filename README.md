Shared contributor and agent rules: [AGENTS.md](AGENTS.md). Operational guidance: [runbook](ops/runbook.md). Open work: [roadmap](ops/roadmap.md).

## SWRLAPI Build Project

This project contains a Maven POM that builds a core set of SWRLAPI-related components.
Currently it builds the [SWRLAPI](https://github.com/protegeproject/swrlapi.git), 
the [SWRLAPI Drools Engine](https://github.com/protegeproject/swrlapi-drools-engine.git), 
the [SWRLAPI Example](https://github.com/protegeproject/swrlapi-example.git) project, 
the [SWRLAPI Integration Tests](https://github.com/protegeproject/swrlapi-integration-tests.git) project, 
the standalone [SWRLTab](https://github.com/protegeproject/swrltab.git) application, 
and the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git).

#### Core library build (OWLAPI 5)

The `core` profile builds the local parent POM, SWRLAPI, the Drools engine,
the example application, and the integration tests in one reactor. It excludes
both SWRLTab modules; their OWLAPI 5 / Protégé integration is deferred.

With those repositories checked out as sibling directories, run from
`swrlapi-project`:

    mvn -Pcore clean verify

Use Java 11 or later. Tests run headlessly and write logs under each module's
`target/logs` directory. `verify` runs both the unit tests and the Failsafe
integration tests; `test` alone does not run the integration suite. The local
parent POM and aligned snapshot versions ensure the tests use the libraries
built in this reactor, without requiring a separate `mvn install` first.

This is a compatibility-first port to OWLAPI 5.5.1. Existing collection-based
calls are retained where supported; a broad streams refactor is deferred.
Downstream applications must recompile against OWLAPI 5. OWLAPI 5 normalizes
language-free `rdf:PlainLiteral` values to `xsd:string`; read such query results
with `isString()` / `getString()` rather than `isRDFPlainLiteral()` /
`getRDFPlainLiteral()`. Language-tagged literals retain their language tags.
Guava is aligned with OWLAPI 5.5.1 at 33.0.0-jre.

The clean OWLAPI 4.5.27 baseline passed 166 unit tests and 607 integration
tests. Current validation totals, outcomes, and exact commands are maintained in
[the runbook](ops/runbook.md#last-validation). Core verification includes custom
argument contracts, isolated OWL 2 RL rules, public reasoner and query integration,
and temporal/duration regressions. Run the full gate with:

    mvn -Pcore,static-analysis clean verify

The `static-analysis` profile runs SpotBugs 4.10.4.1 at maximum effort and high
confidence, failing `verify` on findings or analyzer errors. Reports are written to
each module's `target/spotbugsXml.xml`. The old Checker Framework 1.9.13/JDK 8
annotation processor remains disabled; SpotBugs does not replace its nullness
type checking. Broader SpotBugs confidence levels are not part of this gate.

Custom-argument contract tests cover equality, hashing, comparison laws, numeric
and temporal ordering, mixed native/custom OWL objects, entity and expression
signatures, current bindings, cycle-safe signature traversal, and signatures
collected by enclosing native OWLAPI atoms. Mutable arguments must not be changed
while used as hashed or sorted collection keys.

`getOWLReasoner()` returns a cached, non-buffering Drools reasoner. It materializes
an isolated copy of the root ontology's imports closure on demand, including SWRL
rules, and does not export inferred axioms into the source ontology. Changes,
including removals and imported-ontology changes, invalidate the snapshot. The
reasoner owns its inference session; dispose it when finished. A disposed accessor
instance is replaced on the next call. Direct construction also supports buffering
mode and `flush()`. Reasoner calls and ontology edits should be serialized;
`interrupt()` can be called from another thread.

The reasoner uses the default RL rule set independently of interactive rule
selection and SQWRL query execution. It implements hierarchy, equivalence,
disjointness, types, instances, property-value and identity queries, consistency,
known empty-class detection, and materialized entailment checks. Unsupported
entailment axiom types throw `UnsupportedEntailmentTypeException` and are reported
by `isEntailmentCheckingSupported`. This is a view over the existing rule engine,
with the inference limitations below; it is not a complete OWL 2 DL reasoner.

The class-expression rules now decompose intersections, require all operands when
constructing intersections, and infer unions from either operand. Additional tests
caught and fixed the missing object `hasValue` reverse rule, missing disjoint-data-
property contradiction rule, omitted disjoint-class/negative-assertion imports,
and reasoner index and consistency-reporting defects. `OWL2RLRuleTest` isolates
rules so alternative schema inference paths cannot mask a broken rule.

Temporal parsing validates complete XML Schema date/date-time values, respects
explicit offsets, and retains millisecond precision through the existing
`java.util.Date` APIs. Date-time serialization includes the offset and milliseconds;
ordering uses instants rather than a 12-hour clock. Values without a timezone
retain the historical interpretation in the JVM's default timezone.

Duration arithmetic normalizes year/month values to signed months and day/time
values to signed seconds. Scaling and division accept finite numeric factors,
with XPath month rounding; zero divisors are rejected. Date/time differences use
elapsed time, and duration parsing/results preserve fractional seconds instead of
Axis's hundredth-second rounding. Duration equality and hashing normalize values;
comparison provides a total order by normalized months and then seconds. This
ordering does not equate months with a fixed number of elapsed days. The old Java helpers taking two durations for multiplication or
returning a duration from division are deprecated and reject those dimensionally
invalid calls; use the singular helper names taking a `BigDecimal` factor.

Property chains and keys are compiled into ordinary Drools agenda rules, respecting
rule selection. Chains support ordered paths, inverse operands/heads, and inferred
edges. Keys require every property to have a shared value between named members of
the key class; numeric data keys compare values across integer/decimal subtypes,
while preserving language tags and disjoint datatype value spaces. Literal export
preserves lexical forms and datatypes, including ill-typed values, so consistency
checks can report a contradiction instead of failing during conversion.

Datatype checks validate built-in lexical forms and numeric bounds, and propagate
range/universal-restriction membership through data intersections. Disabling range,
universal-restriction, or datatype rules disables their corresponding reasoning.
Custom datatypes are left undecided. These tests establish the covered cases,
not full RL conformance.

Operating instructions and the ordered backlog now live in
[ops/runbook.md](ops/runbook.md) and [ops/roadmap.md](ops/roadmap.md).

The default `full` profile retains the historical module list below. It is not
part of the core migration validation.

#### Building

To run the build process in this project, you must have the following items installed:

+ [Java 11](https://www.oracle.com/java/technologies/downloads/archive/) or later
+ A tool for checking out a [Git](https://git-scm.com/) repository
+ Apache's [Maven](https://maven.apache.org/index.html)
+ A Protégé (5.6.4 or higher) distribution. Download [here](https://protege.stanford.edu/products.php#desktop-protege).

Create a suitable local directory and then clone the core SWRLAPI-related projects as follows:

    git clone https://github.com/protegeproject/swrlapi-parent.git
    git clone https://github.com/protegeproject/swrlapi-project.git
    git clone https://github.com/protegeproject/swrlapi.git
    git clone https://github.com/protegeproject/swrlapi-drools-engine.git
    git clone https://github.com/protegeproject/swrlapi-example.git
    git clone https://github.com/protegeproject/swrlapi-integration-tests.git
    git clone https://github.com/protegeproject/swrltab.git
    git clone https://github.com/protegeproject/swrltab-plugin.git

Change into the SWRLAPI parent directory:

    cd swrlapi-parent

And then build the parent project with Maven:

    mvn clean install

Then change into the project directory:

    cd ../swrlapi-project

And then build everything with Maven:

    mvn clean install

The SWRLAPI integration tests can take quite a while to run. You can skip them as follows:

    mvn -DskipTests=true clean install

Documentation for the SWRLAPI library can be found [here](https://github.com/protegeproject/swrlapi/wiki).
See the documentation for the [Protégé SWRLTab Plugin](https://github.com/protegeproject/swrltab-plugin.git) for details on installing the generated SWRLTab plugin in your local Protégé installation.

#### License

The software is licensed under the [BSD 2-clause License](https://github.com/protegeproject/swrltab-project/blob/master/license.txt).

#### Questions

If you have questions about this project, please go to the main
Protégé website and subscribe to the [Protégé Developer Support
mailing list](http://protege.stanford.edu/support.php#mailingListSupport).
After subscribing, send messages to protege-dev at lists.stanford.edu.
