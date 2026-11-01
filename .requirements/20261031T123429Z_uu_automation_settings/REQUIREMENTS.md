# As Is

The Windows tray utility controls Wallpaper Engine from SteamVR process changes.
The existing settings dialog contains all fields in one form. There is no UU
integration. The user's reference images show UU's authorization entry point;
they are reference material only and must not be embedded or copied as UI.

# To Be

A compact desktop settings interface groups automation, UU connection guidance,
and advanced options. Optional UU automation starts the client when necessary
and accelerates VRChat on the selected process trigger without blocking wallpaper
monitoring or changing user-managed acceleration.

# Requirements

1. Default UU automation to disabled. Support VRChat, SteamVR, or either as a
   trigger; optional client launch; saved region selection; and optional stop on
   session exit. Preserve existing wallpaper and Windows startup settings.
2. Discover UU's official CLI in installed skill locations or extract only the
   CLI from the package shipped with UU into the app's local cache. Support an
   explicit executable path in advanced settings. Do not bundle user paths.
3. Use bounded, hidden CLI subprocesses with JSON validation, actionable errors,
   readiness checks, and post-start verification. Run automation independently
   from the wallpaper monitor and cancel stale start requests after exit.
4. Keep already-running acceleration and its selected node. Track only commands
   issued by this application; stop only the owned game when explicitly enabled.
   Never issue an unscoped stop command.
5. Provide text-only setup guidance: open/install UU, Settings > AI Settings >
   enable authorization manually, close UU's settings, and check connection.
   Never toggle UU permissions programmatically.
6. Use ui-ux-pro-max guidance for an original desktop design: native controls,
   readable labels, keyboard focus, inline status/loading/error feedback, and
   progressive disclosure. Hide IDs, CLI paths, and polling details from the
   automation page. Keep Chinese and English available.

# Acceptance Criteria

- Legacy configurations load with UU disabled; new settings survive save/load.
- CLI errors, timeouts, malformed output, and documented/actual region formats
  are handled without freezing the UI or monitor.
- Simulated process transitions start once, verify boosting, keep existing
  sessions, cancel stale starts, and stop only owned acceleration when selected.
- Initial connection checks are read-only. Guide buttons never alter UU's
  authorization. Connection checks have loading and recovery states.
- Basic settings, guidance, advanced fields, saving/canceling, both languages,
  and a smaller window are visually verified in the actual Tkinter UI.
- Existing regression tests remain green; native app startup smoke checks pass.

# Testing Plan

- Add failing tests for CLI protocol validation, region parsing, safe discovery,
  configuration persistence, automation ownership, readiness, and cancellation.
- Implement in small steps and run focused tests before the full suite.
- Test integration with fake CLI responses; use the real installed client only
  for doctor/status/region reads, preserving the user's running game/network.
- Exercise the actual settings UI with Computer Use and capture local previews.
- Check Python 3.10 syntax, final diff, and the packaging module list.

# Implementation Plan

1. Create the design notes and protocol/state regression tests.
2. Implement UU client discovery and CLI protocol adapter; run client tests.
3. Implement state reconciliation and background worker; run lifecycle tests.
4. Add configuration and process detection; integrate the worker into Monitor.
5. Replace the settings form with automation, connection, and advanced pages,
   using asynchronous operations and localized labels.
6. Update packaging/docs, perform full regression and visual QA, and record limits.

# References and Tools

- UI skill: `D:/vscode/.agents/skills/ui-ux-pro-max/SKILL.md`; ran its required
  design-system search and UX search. Adapted recommendations to Python/Tkinter.
- UU skill: official `netease-uu-booster.7z` shipped in the installed UU version;
  extracted for inspection to a temporary directory. CLI doctor/status/regions
  were verified against the local installation; actual regions use snake_case.
- No Serena or Lad tools are available. Review and tests run locally.

# Verification Results

- All 34 regression tests pass, including CLI validation, configuration
  persistence, trigger selection, session ownership, manual node changes,
  cancellation during readiness checks, and asynchronous settings results.
- All 18 source/test/preview Python files parse with the Python 3.10 grammar.
  The real entry point passes `--help`; `git diff --check` passes.
- Read-only native client checks return ready and six selectable regions.
  Discovery was also verified with skill locations excluded: extraction from
  the package shipped with installed UU produced a usable cached CLI.
- Actual Chinese automation and connection pages were inspected, including the
  live loading-to-connected transition. An enabled English preview at 780x560
  was inspected; it retained the save footer and vertical scrolling.
- Brand wrapping, responsive helper text, keyboard focus scrolling, and draft
  status labels were refined after inspection. The user then physically stopped
  Computer Use with Escape, so no further desktop automation was performed.
  The final visual pass of those refinements remains incomplete.
- The original screenshots are not copied into source or used as assets.
- Packaging metadata includes the UU module and version 1.2.0.
- On 2026-10-31, built the current source with PyInstaller 6.21.0 and Python
  3.14.4 after all 41 regression tests passed. The frozen executable passed
  `--help` with exit code 0 and no stderr.
- Updated the existing local installation to 1.2.0 in place and started it in
  the tray. The installed executable hash matches the build, the original
  configuration is byte-for-byte unchanged, and Windows startup still points
  to the installed executable. Exactly one application instance is running
  (the expected one-file parent and child processes).
- Old installation, configuration, and uninstall registry metadata were backed
  up under `%LOCALAPPDATA%/SteamVRWallpaperPause/backups/20261031T131947Z`.
  An initial file-lock failure rolled back safely; replacement succeeded after
  waiting for process exit and exclusive file access.
- No installer package was built because Inno Setup is not installed. The local
  executable and registered application version were updated directly.
