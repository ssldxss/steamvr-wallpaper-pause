# As Is

When Wallpaper Engine is not running, the controller skips stop/pause but returns
`True`. The monitor then records `_paused_by_us`, emits a success notification,
and sends `play` when SteamVR exits, even with auto-restart disabled. Tray status
also assumes that an active VR session means wallpaper control succeeded.

# To Be

Only an executed, successful stop/pause command records ownership. Skipped
commands cause neither a success nor an error notification and do not schedule
restoration. The explicit auto-restart option continues to work.

# Requirements

1. Distinguish executed success (`True`), failure (`False`), and skipped control
   (`None`) at the controller boundary for stop/pause.
2. Record ownership and notify success only for executed success. Notify errors
   only for actual failures. A skipped action must not lead to `play` on VR exit.
3. Report stopped/paused tray status only when control ownership was recorded.
4. Preserve successful stop/pause-and-resume behavior and the existing explicit
   auto-restart option. Keep `resume_wallpaper` returning a boolean.

# Acceptance Criteria

1. With no wallpaper process and auto-restart disabled, both action modes leave
   ownership false, issue no control commands, and show no control notifications.
2. With a running wallpaper process, stop/pause succeeds exactly once during the
   VR session and `play` runs once after VR exits.
3. A skipped action followed by the user opening Wallpaper Engine during VR does
   not claim ownership or display a false stopped/paused status.
4. Actual command failure still produces an error, without claiming ownership or
   displaying a false success status.
5. With no wallpaper process and auto-restart enabled, VR exit starts the engine
   once through the existing auto-restart path, without issuing a spurious `play`.

# Testing Plan

- Exercise the real controller functions through the monitor with mocked process
  detection, subprocess execution, tray notifications, and sleep.
- Run every scenario in both stop and pause modes, including multiple active-VR
  polls to verify commands are not repeated.
- Run the regression suite before implementation and confirm the new scenarios
  fail for the reported reasons, then rerun after each small implementation step.
- Run all existing tests, check Python 3.10 syntax and the final diff, and smoke
  test the entry point using `--help`.
- Do not alter the running user's wallpaper, configuration, or registry.

# Implementation Plan

1. Add regression tests for skipped actions, normal restoration, explicit
   auto-restart, late wallpaper startup, and command failure; run them red.
2. Return `None` for skipped stop/pause, document the result contract, and make the
   monitor handle success/failure/skip separately; run the relevant tests.
3. Gate tray paused/stopped reporting on ownership and run the complete suite.
4. Review the final changes and record verification results.

# References and Tool Availability

- Wallpaper Engine control semantics:
  https://help.wallpaperengine.io/en/functionality/cli.html
- Python 3.10 union types and truth values:
  https://docs.python.org/3.10/library/stdtypes.html#types-union
- Mock patching in the namespace where objects are used:
  https://docs.python.org/3/library/unittest.mock.html#patch-object
- Serena and Lad tools are unavailable in this session; review is performed
  locally with regression tests and diff inspection.

# Verification Results

- Before implementation, eight subcases failed across skipped ownership,
  explicit auto-restart, late wallpaper startup, and false success status. The
  normal stop/pause-and-resume scenarios passed.
- After separating skipped results from success/failure, skipped control, normal
  restoration, and explicit auto-restart tests passed in both modes.
- After gating tray status on ownership, all 10 tests pass with
  `python -B -m unittest discover -v`; the monitor tests cover 10 scenarios.
- All 13 Python source/test files parse with the Python 3.10 grammar. The entry
  point exits successfully with `--help`, and `git diff --check` passes.
- Tests use the real controller wrappers and monitor, replacing process and
  subprocess boundaries. They do not open or close the user's wallpaper engine.
- Existing auto-start quoting and installer configuration fixes remain intact.
