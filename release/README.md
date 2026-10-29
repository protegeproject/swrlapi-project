# Coordinated SWRLAPI release

Release the five public artifacts together: parent, API, Drools engine, Protégé plugin, and standalone SWRLTab. The ordinary project reactor builds all nine repositories, including examples and integration tests. This release reactor excludes the auxiliary projects from publication.

Use sibling checkouts on `development`, Java 11 or later, Maven, GPG, and a Portal token in the `central` server in `~/.m2/settings.xml`. Ensure the Git checkouts are current and the target release/tag does not already exist. Inspect existing Portal deployments before retrying an interrupted upload.

From `swrlapi-project`:

```sh
# Build/test all projects first.
mvn clean verify

# Align release dependencies and set the five release versions and SCM tags.
# Auxiliary project versions stay SNAPSHOT.
python3 release/set-version.py 2.1.4

# Build one signed bundle. This does NOT upload it.
mvn -f release/pom.xml -Pmaven-central-release \
  -DskipUpload=true -Dmaven.install.skip=true clean deploy
python3 release/verify-bundle.py ../swrlapi-parent/target/central-publishing/central-bundle.zip 2.1.4
```

Before upload, review and commit changes in each repository. Create `release-2.1.4` tags in the five main repositories, and push the commits/tags. Tags must identify the exact source used to build the bundle. Do not run the per-repository `release:prepare`/`release:perform` in addition to this coordinated workflow.

```sh
# Upload the existing verified bytes once, for validation.
python3 release/portal.py upload ../swrlapi-parent/target/central-publishing/central-bundle.zip \
  --name 'SWRLAPI 2.1.4' --receipt release/target/portal-2.1.4.json

# Use the deployment ID printed by upload and saved in the receipt.
python3 release/portal.py status DEPLOYMENT_ID
# Only after VALIDATED, publish the same deployment:
python3 release/portal.py publish DEPLOYMENT_ID
python3 release/portal.py status DEPLOYMENT_ID
```

Do not repeat upload after an uncertain response; first check the Portal to avoid duplicates. `portal.py` does not log token values. Maven-encrypted credentials should use the Maven publishing plugin instead of this helper.

After the Portal reports PUBLISHED, verify the five artifact POMs are available from Maven Central, then advance development:

```sh
python3 release/set-version.py 2.1.5-SNAPSHOT
```

Commit and push the next-development versions in the affected repositories. Keep release tags unchanged. Publishable binaries remain in the module `target` directories and can also be attached to GitHub releases separately.

GPG agent caching may expire during a long test run. Prime it in your terminal immediately before the signed build. Never put a passphrase in these scripts or in command-line arguments.
