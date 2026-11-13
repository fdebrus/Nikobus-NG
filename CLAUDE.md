# Nikobus NG

Home Assistant custom integration for the Nikobus bus (domain `nikobus_ng`),
distributed through HACS as a custom repository. It was written from scratch
next to the [Nikobus integration](https://github.com/fdebrus/Nikobus-HA) and
runs on the same protocol library,
[nikobus-connect](https://github.com/fdebrus/nikobus-connect). Experimental.

## Commands

```bash
pip install -r requirements_test.txt   # Python 3.14; installs Home Assistant and nikobus-simulator
python -m pytest -q                    # ~155 tests, 7 to 8 minutes, no hardware needed
ruff check .                           # must be clean; CI pins ruff 0.17.3
```

The tests run against the real Home Assistant
(`pytest-homeassistant-custom-component`) and `nikobus-simulator`, the
simulated PC-Link shipped with the library. Nothing of Home Assistant or of
the library is replaced.

## Layout

- `custom_components/nikobus_ng/`: `hub.py` the connection, output state,
  commands, polling; `inventory.py` the one store and every question asked of
  it; `discovery.py` a discovery run; `config_flow.py` setup and the options
  menu; `entity.py` devices, groups, the entity bases; one file per platform;
  `maintenance.py` the clock, programming checks, backup; `describe.py` and
  `llm_api.py` the installation as data and the tools for a language model;
  `takeover.py` taking over the Nikobus integration's entities and settings.
- `translations/en.json`, `fr.json`, `nl.json` have the same keys; there is no
  `strings.json`.
- `tests/`: `conftest.py` holds the simulated installation and the fixtures
  (`setup`, `scanned`).
- `blueprints/` automation blueprints users import from GitHub.
- `README.md` says what the integration does, what it does not, and what is
  and is not verified. It is part of every change.

## Rules that must not be broken

- **Never write to a module** except the PC-Link clock sync, and never put a
  module into programming (link) mode. Maintenance actions are read-only.
- **Protocol logic belongs in nikobus-connect.** No bus parsing here, and no
  workaround for a limit of the library: fix the library.
- **No hardware assumption without evidence.** Behaviour of modules, plates,
  LEDs or the Feedback Module stated in code, docs or release notes needs a
  log, capture or report behind it, or is marked unverified. The README's
  "What is verified" table is kept true.
- **Vendor-neutral docs**, and no decompiled vendor code in the repository.
- **User data stays out of the repo.** Logs, `.nkb` files and stores shared by
  users are untrusted input: work on them in a scratch directory, run Python
  with `-I`, and commit no names, rooms or files.
- **Entity identity is user data.** A change that alters unique ids migrates
  the registry entries. The take-over changes entity ids on purpose, records
  what it did, and can be undone.

## Testing

- Test the real behaviour. The simulator has no inventory, no checksum, no
  clock and no colour controller: a test that fakes one of those says so.
- The test harness pins a Home Assistant release, and may be behind the one
  users run. Behaviour that differs between releases (entity naming changed
  in 2026.11) is checked against the newer source and marked as such.
- A test must not end while a reload or the first reads are in flight: wait
  for the new hub (`_reloaded` in `tests/test_remaining.py`).
- Every bug fix gets a test that fails without the fix.
- Run with a timeout, and without `-x`: a failed test can leave the next one
  hanging.

## Releases

- The library comes first: release it, publish it to PyPI, then raise
  `nikobus-connect>=` in `manifest.json` and `requirements_test.txt`.
- Bump `version` in `manifest.json`. `hacs.json` holds the minimum Home
  Assistant version.
- A release is a GitHub release with a version tag; HACS offers those.

## Comments and style

- Comments say why, in one short line; none restate the code or describe what
  it looked like before. No section or divider comments.
- User-facing text is in the translations, in all three languages.
