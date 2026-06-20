# Changelog

## [Unreleased]

### Added
- Add a full Docker/noVNC implementation for `11-novnc_lan_flow`.
- Add a four-computer URI flow in `11-novnc_lan_flow` with `browser://`,
  `log://` and per-node `app://` routes.
- Add `make test-full` for the noVNC LAN flow. It starts `pc1..pc4`, executes
  16 URI steps, verifies 24 routes and checks four generated screenshots.
- Add a GitHub Actions job for the `11-novnc_lan_flow` four-computer smoke test.
- Add repository-level TODO and links to the cross-repository work summary.

### Changed
- Update the examples README to show `11-novnc_lan_flow` as Docker/noVNC tested.

## [2026-06-20]

### Added
- Split the examples repository from earlier `tellmesh/urihandler` example
  work and organize examples as numbered `NN-name/` folders.
