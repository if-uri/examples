# Changelog

## Unreleased

### Added
- Add `53-ecosystem-coverage-audit`, a host-runnable example that validates the
  if-uri repository coverage map and future repository drift.
- Add `ci/ecosystem-coverage.yml` covering the paginated if-uri GitHub
  repository inventory.
- Add `docs/ECOSYSTEM_COVERAGE.md` and `docs/EXAMPLES_BACKLOG.md`.
- Add scheduled `.github/workflows/ecosystem-audit.yml`.

### Changed
- Document ecosystem coverage from the main README.
- Extend CI classification with the ecosystem audit example.

## [0.1.10] - 2026-06-21

### Fixed
- Fix smart-return-type issues (ticket-12577722)
- Fix unused-imports issues (ticket-2cc858de)
- Fix magic-numbers issues (ticket-c9f0ec42)
- Fix ai-boilerplate issues (ticket-aa8828f6)
- Fix smart-return-type issues (ticket-412572ed)
- Fix ai-boilerplate issues (ticket-31a1a5a8)
- Fix smart-return-type issues (ticket-6ad056d2)
- Fix ai-boilerplate issues (ticket-a516db2e)
- Fix smart-return-type issues (ticket-f862aaa8)
- Fix string-concat issues (ticket-6f630234)
- Fix ai-boilerplate issues (ticket-bd3d3129)
- Fix unused-imports issues (ticket-ba257aa7)
- Fix smart-return-type issues (ticket-d15fd027)
- Fix string-concat issues (ticket-eef9424a)
- Fix unused-imports issues (ticket-77b241eb)
- Fix ai-boilerplate issues (ticket-232b8172)
- Fix smart-return-type issues (ticket-5f2225e9)
- Fix string-concat issues (ticket-4060fd1f)
- Fix unused-imports issues (ticket-14955783)
- Fix magic-numbers issues (ticket-252f2142)
- Fix ai-boilerplate issues (ticket-aedbc220)
- Fix unused-imports issues (ticket-c6a46940)
- Fix ai-boilerplate issues (ticket-eef7bdbe)
- Fix string-concat issues (ticket-e073907f)
- Fix unused-imports issues (ticket-efa89220)
- Fix ai-boilerplate issues (ticket-870f9d56)
- Fix smart-return-type issues (ticket-6e7aada7)
- Fix unused-imports issues (ticket-eae4fd4a)
- Fix magic-numbers issues (ticket-fce5a0dc)
- Fix smart-return-type issues (ticket-ca3cba27)
- Fix unused-imports issues (ticket-a4d22f01)
- Fix magic-numbers issues (ticket-173583e8)
- Fix ai-boilerplate issues (ticket-a0c4401c)
- Fix smart-return-type issues (ticket-dea6acda)
- Fix unused-imports issues (ticket-eda9da44)
- Fix ai-boilerplate issues (ticket-eaea79f4)
- Fix unused-imports issues (ticket-3bfb43f3)
- Fix magic-numbers issues (ticket-b8147500)
- Fix smart-return-type issues (ticket-56800a81)
- Fix string-concat issues (ticket-1a95c561)
- Fix unused-imports issues (ticket-1facb8f1)
- Fix ai-boilerplate issues (ticket-08f4ce4d)
- Fix unused-imports issues (ticket-3b64a833)
- Fix magic-numbers issues (ticket-adb55f3b)
- Fix smart-return-type issues (ticket-65cd8f57)
- Fix ai-boilerplate issues (ticket-439390e5)
- Fix smart-return-type issues (ticket-97159429)
- Fix string-concat issues (ticket-373f1ce4)
- Fix unused-imports issues (ticket-9c154a5b)
- Fix ai-boilerplate issues (ticket-e935093b)
- Fix string-concat issues (ticket-c209a89f)
- Fix unused-imports issues (ticket-7dad6524)
- Fix ai-boilerplate issues (ticket-22833b04)
- Fix duplicate-imports issues (ticket-556785af)
- Fix smart-return-type issues (ticket-f7388bda)
- Fix string-concat issues (ticket-a51895b5)
- Fix unused-imports issues (ticket-26203695)
- Fix magic-numbers issues (ticket-18906f51)
- Fix ai-boilerplate issues (ticket-10e3676f)
- Fix unused-imports issues (ticket-ea0edfae)
- Fix duplicate-imports issues (ticket-9d7693ae)
- Fix smart-return-type issues (ticket-9bf544a0)
- Fix string-concat issues (ticket-4a5e1231)
- Fix unused-imports issues (ticket-953ad44d)
- Fix magic-numbers issues (ticket-dc901e63)
- Fix ai-boilerplate issues (ticket-4deb0121)
- Fix duplicate-imports issues (ticket-cd17e415)
- Fix string-concat issues (ticket-b0acbf6d)
- Fix unused-imports issues (ticket-d5a250fb)
- Fix magic-numbers issues (ticket-4f3ed1c9)
- Fix ai-boilerplate issues (ticket-c21f9aab)
- Fix smart-return-type issues (ticket-d86411ea)
- Fix unused-imports issues (ticket-6338aa8e)
- Fix magic-numbers issues (ticket-d6bbf970)
- Fix ai-boilerplate issues (ticket-90a1b8f8)
- Fix string-concat issues (ticket-d58cf155)
- Fix unused-imports issues (ticket-ed542809)
- Fix magic-numbers issues (ticket-c4f4ac0e)
- Fix ai-boilerplate issues (ticket-5e3c1158)
- Fix string-concat issues (ticket-e36b654c)
- Fix unused-imports issues (ticket-5fc8ce81)
- Fix magic-numbers issues (ticket-63eb6aa2)
- Fix ai-boilerplate issues (ticket-9e08c28b)
- Fix duplicate-imports issues (ticket-ad6d9cb8)
- Fix smart-return-type issues (ticket-d28bfb3d)
- Fix unused-imports issues (ticket-cf347b27)
- Fix magic-numbers issues (ticket-19640389)
- Fix ai-boilerplate issues (ticket-66e29a76)
- Fix unused-imports issues (ticket-ae477b32)
- Fix ai-boilerplate issues (ticket-6e21934c)
- Fix smart-return-type issues (ticket-9634c854)
- Fix unused-imports issues (ticket-f42e0b89)
- Fix magic-numbers issues (ticket-a5b79087)
- Fix ai-boilerplate issues (ticket-7f610fe7)
- Fix smart-return-type issues (ticket-e2eb0f42)
- Fix ai-boilerplate issues (ticket-7a0d52b7)
- Fix smart-return-type issues (ticket-4b0aa45a)
- Fix string-concat issues (ticket-cde61c60)
- Fix ai-boilerplate issues (ticket-77fa76e8)
- Fix smart-return-type issues (ticket-2293b086)

## [Unreleased]

### Added
- Record the IFURI-016 full connector matrix as the next examples milestone.
- Add a full Docker/noVNC implementation for `11-novnc_lan_flow`.
- Add a four-computer URI flow in `11-novnc_lan_flow` with `browser://`,
  `log://` and per-node `app://` routes.
- Add `make test-full` for the noVNC LAN flow. It starts `pc1..pc4`, executes
  16 URI steps, verifies 24 routes and checks four generated screenshots.
- Add a GitHub Actions job for the `11-novnc_lan_flow` four-computer smoke test.
- Add repository-level TODO and links to the cross-repository work summary.

### Changed
- Update the examples README to show `11-novnc_lan_flow` as Docker/noVNC tested.
- Point active runtime install and Docker environment defaults at
  `github.com/if-uri/urirun`.

## [2026-06-20]

### Added
- Split the examples repository from earlier `tellmesh/urihandler` example
  work and organize examples as numbered `NN-name/` folders.
