# Coordinated SWRLAPI release

Release the five public artifacts together: parent, API, Drools engine, Protégé plugin, and standalone SWRLTab. The ordinary project reactor selects modules through the `full` or `core` profiles. The `core` profile excludes SWRLTab and the Protégé plugin; the optional built-in-library example is not checked out in this workspace. This release reactor excludes the auxiliary projects from publication.

The `protege-6` compatibility branch passes the full library, plugin, standalone,
and graphical gates on JDK 17 with the unmodified Protégé 6 alpha-1 host; see the
[runbook](../ops/runbook.md) for the exact artifacts and tested boundaries. Keep
that host baseline for release validation. Protégé is an external repository; a
SWRLAPI release does not authorize host dependency upgrades or publishing its code.
The unused local `protege-6-swrlapi` branch has been removed; recreate it only if a
host change becomes necessary, and do not push without explicit authorization.
Passing local validation does not publish or authorize a release.
The instructions below describe the existing coordinated `development`/`master`
release policy; choose the release branch policy explicitly before promoting the
compatibility branch.

For metadata-only tests, run `python3 -m unittest discover -s release -p 'test_*.py'`.
`set-version.py` supports inherited child versions and `--branch protege-6` for
an explicitly selected compatibility checkout; its default remains `development`.
`--workspace PATH` supports isolated preparation. It checks every present sibling's
branch before writing any POM, and skips absent auxiliary repositories. It neither
builds nor commits, tags, pushes, or publishes. The bundle verifier includes the
standalone `-application.zip`, requiring its signature and checksums as well as
the five POMs, binary jars, source jars, and javadoc jars.

Use sibling checkouts on the agreed release branch, JDK 17, Maven, GPG, and a Portal token in the `central` server in `~/.m2/settings.xml`. Ensure the Git checkouts are current and the target release/tag does not already exist. Inspect existing Portal deployments before retrying an interrupted upload.

From `swrlapi-project`:

```sh
# Build/test all projects first.
mvn -Pfull,static-analysis clean verify

# Align release dependencies and set the five release versions and SCM tags.
# Auxiliary project versions stay SNAPSHOT.
python3 release/set-version.py 2.1.5

# Build one signed bundle. This does NOT upload it.
mvn -f release/pom.xml -Pmaven-central-release \
  -DskipUpload=true -Dmaven.install.skip=true clean deploy
python3 release/verify-bundle.py ../swrlapi-parent/target/central-publishing/central-bundle.zip 2.1.5
```

Before upload, review and commit changes in each repository. Create `release-2.1.5` tags in the five main repositories, and push the commits/tags. Tags must identify the exact source used to build the bundle. Do not run the per-repository `release:prepare`/`release:perform` in addition to this coordinated workflow.

```sh
# Upload the existing verified bytes once, for validation.
python3 release/portal.py upload ../swrlapi-parent/target/central-publishing/central-bundle.zip \
  --name 'SWRLAPI 2.1.5' --receipt release/target/portal-2.1.5.json

# Use the deployment ID printed by upload and saved in the receipt.
python3 release/portal.py status DEPLOYMENT_ID
# Only after VALIDATED, publish the same deployment:
python3 release/portal.py publish DEPLOYMENT_ID
python3 release/portal.py status DEPLOYMENT_ID
```

Do not repeat upload after an uncertain response; first check the Portal to avoid duplicates. `portal.py` does not log token values. Maven-encrypted credentials should use the Maven publishing plugin instead of this helper.

After the Portal reports PUBLISHED, verify the five artifact POMs are available from Maven Central.

Update `master` in each of the five released repositories from the release tag, not from `development` (which may already contain the next snapshot version). Run the following in dependency order: `swrlapi-parent`, `swrlapi`, `swrlapi-drools-engine`, `swrltab-plugin`, and `swrltab`.

```sh
git checkout master
git pull --ff-only origin master
git merge -X theirs --no-ff --no-commit release-2.1.5
# Review the staged changes and any differences from the release tag.
git diff --cached
git diff release-2.1.5
mvn install
git commit -m "Release 2.1.5"
git push origin master
git checkout development
```

`-X theirs` favors the release tag for conflicting changes; it preserves non-conflicting master changes, so review the result. Do not move the release tags. The examples, integration tests, and project aggregator are not released and do not receive these release-tag merges.

For a Protégé 6 release, update `src/main/resources/readme.html` with the final
version and tested released-host compatibility. Render
`update-info/protege-6/update.properties.template` by replacing `@VERSION@` with
the release version and save it as `update-info/protege-6/update.properties` before
tagging. Keep the Protégé 5 feed on its compatible released version; never point it
at the Protégé 6 build. Validate the new metadata using the host parser as described
in the runbook. The template's jar and readme URLs identify the same immutable tag.

Upload the verified plugin JAR to the corresponding GitHub release, verify the
auto-update download URL resolves to those exact bytes, and only then register
its metadata URL in the Protégé 6 registry. Upload the standalone application zip
as a release attachment too; its main jar requires the accompanying `lib/`
directory. Neither metadata templates nor unuploaded SNAPSHOT artifacts are live
update feeds. A local parser check does not verify remote downloads or signatures.

Advance development if it has not already been advanced:

```sh
python3 release/set-version.py 2.1.6-SNAPSHOT
```

Commit and push the next-development versions in the affected repositories. Keep release tags unchanged. Publishable binaries remain in the module `target` directories and can also be attached to GitHub releases separately.

GPG agent caching may expire during a long test run. Prime it in your terminal immediately before the signed build. Never put a passphrase in these scripts or in command-line arguments.
