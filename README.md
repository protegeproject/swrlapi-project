# SWRLAPI build project

Build the SWRLAPI library, Drools engine, examples, and tests from sibling source
checkouts. The `protege-6` branches use **2.1.5-SNAPSHOT**, **OWLAPI 5.5.1** and
**Drools 7.74.1.Final**. This development snapshot is not a published Protégé 5 update.

Use **JDK 17** and **Maven 3.9** for the documented validation path; the libraries
compile to Java 11 bytecode. Set `JAVA_HOME` to your JDK 17 installation. The core
build needs no Protégé installation, credentials, running services or production data.

## Get the source and run the core gate

Run these commands from a new workspace directory. All checkouts must be siblings
and use the same branch/version; `swrlapi-project` is an aggregator, not their parent directory.

```sh
for repo in swrlapi-parent swrlapi-project swrlapi swrlapi-drools-engine \
  swrlapi-example swrlapi-integration-tests; do
  git clone --branch protege-6 "https://github.com/protegeproject/$repo.git"
done
mvn -B -f swrlapi-project/pom.xml -Pcore,static-analysis clean verify
```

`verify` runs unit and integration tests and SpotBugs. `test` alone omits the
Failsafe integration suite. The reactor builds the local parent and producers
before consumers, including uncommitted source edits; a separate `install` is
unnecessary. Add `-o` only when all required dependencies are already cached.
Logs and reports are under each module's `target/` directory. SpotBugs is not
Checker Framework nullness checking; no formatter gate is configured.

The packaged example prints `x: 4` without needing an ontology file:

```sh
java -jar swrlapi-example/target/swrlapi-example-2.1.5-SNAPSHOT-jar-with-dependencies.jar
```

## Choose the build scope

| Profiles | Modules and prerequisites |
| --- | --- |
| `core,static-analysis` | Parent, library, engine, example and integration tests; JDK 17 and Maven 3.9. |
| `core,standalone,static-analysis` | Core plus the standalone Swing application; also clone `swrltab` on `protege-6`. |
| `core,protege-plugin,static-analysis` | Core plus the Protégé plugin; also clone `swrltab-plugin` and provide the matching host APIs. |
| `full,static-analysis` | All modules; clone both UI repositories and follow the host reactor instructions. |

`full` is the aggregator's default profile; select `core` explicitly for an
independent library build. The standalone app has no Protégé dependency. The plugin
targets **unmodified Protégé 6.0.0-alpha-1**, branch
`protege6/release-6.0.0-alpha-1`; its build/runtime procedure is in the
[plugin runbook](ops/runbook.md#prot%C3%A9g%C3%A9-6-plugin-experiment). Use the combined host
reactor when host sources are needed, so the plugin consumes those sources rather
than stale installed artifacts. Host dependency upgrades are not required by this workflow.

## Documentation

- [OWLAPI 5 migration guide](docs/owlapi5-migration.md): compatibility, dependency ownership and supported reasoning boundaries.
- [Third-party built-in registration](https://github.com/protegeproject/swrltab-plugin/blob/protege-6/docs/built-in-registration.md): a runnable OSGi contributor example and lifecycle contract.
- [Runbook](ops/runbook.md): exact commands, dependency baseline, runtime behavior and validation evidence.
- [Roadmap](ops/roadmap.md): remaining work; [shared development rules](AGENTS.md): contributor workflow.
- [SWRL and SQWRL reference wiki](https://github.com/protegeproject/swrlapi/wiki): language and API background; use the branch guides above for this snapshot.

To consume the snapshot in a separate Maven project, run the same core reactor
with `install` instead of `verify`. This installs local artifacts and also runs the
verification phases; it does not publish a release. Release publication has a
separate [procedure](release/README.md).


## License

[BSD 2-Clause](license.txt), copyright Stanford University.
