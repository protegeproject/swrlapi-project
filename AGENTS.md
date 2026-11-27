# SWRLAPI Shared Development Rules

These rules apply throughout `~/workspace/swrlapi`, including every sibling
repository. Start multi-repository work from that workspace root. The canonical,
version-controlled copy is **`swrlapi-project/AGENTS.md`**. Workspace `AGENTS.md`,
`CLAUDE.md`, and `model.md` are links to it; update this file rather than maintaining
separate model-specific copies. `ops/` at the workspace root links to the project's
ops directory, so the documentation links below work from either entry point.

Read [the runbook](ops/runbook.md) for commands, dependency versions, runtime
behavior, and validation evidence. Read [the roadmap](ops/roadmap.md) for open work.
Explicit user instructions and agreed scope take precedence over these defaults.

## Communication and Scope

- Keep outstanding discoveries and remaining work prominent as a numbered list in
  progress updates and the final response. Each item says what was found, why it
  matters, and the remaining action. Keep the list forward-looking; remove resolved
  items instead of retaining a completion checklist.
- Carry authorized work through implementation and verification. Routine reversible
  build, dependency-resolution, and test steps are part of the requested work; do
  not ask again for steps the user already authorized. Continue independent work
  while a genuinely necessary clarification is pending.
- Preserve the agreed scope. The current scope includes the core compatibility port,
  an incremental internal OWLAPI streams refactor preserving the public SWRLAPI API,
  and SWRLTab plugin experiments on Protégé `protege6/release-6.0.0-alpha-1`.
  The standalone SWRLTab port is also authorized. It does not authorize a Drools
  major-version upgrade.
  Their order and remaining work are in the roadmap. A dependency upgrade is not
  permission to redesign public APIs or product behavior.
- Report observable outcomes, tested boundaries, and remaining limitations. Do not
  call a focused test run a full build, a compile-only run a verified build, or a
  collection of passing cases complete standards conformance.

## Use the Supported Build Path

- Use the sibling Maven reactor and the runbook commands. The parent manages shared
  dependency versions and must be built before consumers. Do not independently
  upgrade a child dependency or make consumers resolve stale local/remote artifacts
  when the current sibling source should be used.
- Follow the documented JDK and dependency baseline. Check the environment when
  results differ between shells. This workspace is not controlled by `cedarcli`;
  do not source CEDAR profiles, launch its services, or import its infrastructure
  pins into SWRLAPI.
- A local development build consumes current working-tree sources, including
  uncommitted edits, plus the necessary local producers. It does not require a
  commit, push, stash, registry publication, or clean working tree first. Preserve
  those edits. Separate release reproducibility requirements from local SNAPSHOT
  development.
- Never silently substitute an old jar, a registry package, or a previous successful
  result when a current producer failed. Report the concrete failure. If relevant
  source changes during a build, verify the final inputs before declaring completion.
- Run commands headlessly and use supported entry points. Do not invent Terminal-tab
  automation or bypass a supported build path with internal scripts.
- Do not pipe a live Maven build into `head`, `grep -m`, or another early-closing
  consumer: SIGPIPE can terminate it while obscuring the failure. Redirect the full
  log to a file, preserve the exit status, then inspect it.

## Tests Must Prove Behavior

- The default core gate includes unit **and integration** tests and must require no
  live external service, production data access, or credentials. Use local fakes or
  fixtures. Any test listener binds loopback on an OS-assigned port, not a shared
  fixed port. Keep optional external-service checks separate and explicit.
- Tests must not pass vacuously. Assert nonempty discovery, expected result counts,
  and relevant negative cases. Do not silently skip regressions, weaken assertions,
  delete failing cases, or change expected values merely to match the implementation.
  Explain any intentional exclusions and check test reports for errors and skips.
- Add a regression that exposes the defect and validates the intended contract.
  Use independent semantic expectations, not an implementation copied into a test.
  Exercise public APIs and real converters/serialization as well as isolated units.
- A green unit suite proves logic, not the packaged or running consumer. Validate
  current library artifacts through the public rule/query/reasoner paths. For
  authorized plugin work, rebuild/package, load the actual plugin in the supported
  Protégé version, verify the loaded artifact, and smoke the affected user journeys.
  Publishing and deployment remain separate from a local library build.
- For inference changes, test required conclusions, forbidden conclusions, missing
  premises, rule selection, and interactions with equality, imports, and ontology
  changes where relevant. Isolate rules so alternate inference paths cannot hide
  defects. Document the supported profile; unknown or unsupported cases are not
  automatically success or inconsistency.
- Preserve agreement between representations and consumers: OWLAPI objects, Drools
  facts, built-in arguments, serialized values, and public results must honor the
  same declared contract. For round trips, test both directions, null/empty cases,
  lexical form, datatype, language, identity, and precision where relevant. Resolve
  disagreements against the specification and intended API, not by changing fixtures
  or stored data to accommodate the wrong implementation.
- Run the configured format/static-analysis gates and relevant tests. Preserve
  existing source formatting and line endings. SpotBugs is not a replacement for
  nullness checking. Do not claim a formatter or CI gate exists until it is configured.
- Reuse existing valid evidence when the tested inputs are unchanged; rerun checks
  when changes, failures, or unresolved concerns warrant it. Keep measurements out
  of competing build/benchmark workloads and record the conditions that matter.

## Preserve Public Contracts and Product Design

- Read the existing architecture, API contracts, and surrounding implementation
  before extending them. Keep model/semantic responsibilities separate from I/O,
  deployment, and UI concerns. Coordinate intentional public API or behavior changes
  with the affected consumers, version policy, documentation, and tests.
- Preserve existing visual design, displayed information, and interaction behavior
  by default. Bug fixes, styling cleanup, token adoption, refactoring, and commit/push
  requests do not authorize a redesign, hidden information, changed navigation, or
  changed selection behavior. Technical convenience and passing tests do not supply
  that authorization.
- Before an additional substantial UI change, describe the concrete before/after
  behavior and obtain agreement unless that change is already requested or approved.
  Continue independent authorized work while awaiting the decision. Do not ask again
  for a previously approved change.
- Reliability fixes should use the existing interface wherever possible. Recovery,
  retry, and diagnostic controls appear only when their triggering condition exists;
  they must not become permanent normal-page controls merely because failure is
  possible. Retaining recovery data does not itself justify a visible recovery panel.
- New buttons, banners, dialogs, and navigation require an agreed user-visible change.
  Inspect existing interaction patterns first. Check fresh, unchanged, ordinary-edit,
  and exceptional states; test that exceptional controls are absent in normal use.
- Keep functional verification and design review separate. Inspect the rendered
  interface against the agreed design. Do not rewrite tests or visual baselines to
  legitimize an unapproved redesign. Make intentional design changes visible in the
  progress and final reports.
- Keep documentation screenshots reproducible through the applicable automated UI
  workflow, with stable viewport, theme, and state. Never commit authentication
  storage, credentials, or personal browser state.

## Repository and Change Hygiene

- These are separate Git repositories, and other sessions may be editing them.
  Inspect each relevant working tree before changing or staging it. Preserve
  unrelated work. Do not reset, clean, discard, or stash it as a routine prerequisite.
- Commit and push only when asked. Stage specific reviewed paths; never blanket
  `git add -A` across an unread working tree. Inspect each repository's actual branch
  and release policy instead of importing CEDAR's `develop` or documentation `main`
  conventions by analogy. Do not force-push or rewrite shared history as a fix.
- Comments describe lasting code-level facts. Do not mention sessions, batches,
  "this PR", PR numbers, or conversational history in code comments. Put change
  history in the appropriate review/commit record.
- Keep repository roots for README/license files, established guides, shared agent
  entry points, standard build/tool configuration, manifests, and supported launch
  points. Put sources, assets, scripts, tools, and examples in their existing
  directories. Update callers when moving them; do not leave root compatibility
  copies merely to avoid updating references.
- Treat publication/release artifacts as immutable evidence tied to source. A failed
  or partial build is not current. Fixing captured release sources requires a new
  candidate/version as appropriate, not silently overwriting published artifacts.
  Follow the repository's release procedure when release work is authorized.

## Runbooks and Roadmaps

- Operational guidance belongs in the runbook; remaining work belongs in the roadmap.
  Put findings and measurements in the appropriate existing document instead of
  creating disconnected status, audit, or completion files.
- A roadmap is forward-looking only. Remove finished items and finished subparts;
  do not append an achievements section or retain a checked-off history. Commits
  record completed changes, and the runbook records current operating state.
- Number roadmap items contiguously in document order, with no gaps. When removing
  an item, renumber the rest and repair references. Numbers are conversational
  conveniences, not durable identifiers. Never put roadmap item/phase numbers in
  commit messages; describe the concrete change and affected surface.
- Keep instructions, examples, links, commands, and release/validation evidence
  synchronized with behavior. Review documentation from the perspective of someone
  who has not read the chat. Preview user-facing documentation when its rendering
  matters; verify local links and instruction-file aliases.

## CEDAR Provenance and Adaptation

Imported and adapted on **2026-11-26** from the local CEDAR development rules:

- [Shared CEDAR guidance](/Users/martin/CEDAR/cedar-development/AGENTS.md):
  the canonical source also reached through CEDAR's root `AGENTS.md` and `CLAUDE.md`.
- [Contributor workflow](/Users/martin/CEDAR/cedar-development/CONTRIBUTING.md):
  sibling builds, real runtime verification, non-vacuous tests, dependency ownership,
  safe staging, and paired ops documentation.
- [Library conventions](/Users/martin/CEDAR/cedar-artifact-library/CLAUDE.md):
  durable code comments, API discipline, formatting, and no silently skipped tests.
- [Documentation conventions](/Users/martin/CEDAR/cedar-mkdocs/AGENTS.md):
  previewing documentation and reproducible screenshots without committing auth state.

The reusable development rules above apply here. CEDAR-specific CLI commands,
service addresses, infrastructure locks, deployment credentials, framework details,
branch names, artifact schemas, and tooling such as its Spotless/MkDocs setup are
not SWRLAPI requirements. Their underlying principles are expressed above in
SWRLAPI terms. CEDAR remains a provenance reference, not a runtime dependency or a
live symlink target for this workspace's instructions. When a new general lesson is
learned there, reconcile this canonical file deliberately and keep all aliases
pointing to it.
