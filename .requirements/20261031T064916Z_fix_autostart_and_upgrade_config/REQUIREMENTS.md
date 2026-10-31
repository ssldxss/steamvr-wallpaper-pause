# As Is

- Source-mode auto-start wraps an already quoted interpreter/script command in
  another pair of quotes, so Windows does not receive separate executable and
  script arguments.
- Every installer run overwrites the user's existing `config.json`.
- A skipped stop/pause returns success and the monitor records pause ownership.
  This task reconfirms that behavior without changing it.

# To Be

Source and packaged startup commands parse correctly on Windows. Reinstalling or
upgrading preserves the existing configuration. Fresh installations still use
the installer-selected language and auto-start setting.

# Requirements

1. Serialize executable, script (source mode only), and `--minimized` as separate
   Windows command-line arguments, including paths with spaces and Unicode.
2. Initialize installer configuration only when `config.json` does not exist.
   Preserve existing files byte-for-byte; the application already supplies
   defaults for missing configuration keys.
3. Reconfirm skipped-control ownership with isolated stop/pause scenarios, without
   changing the running user's wallpaper or registry.

# Acceptance Criteria

1. Commands captured at the registry write parse with Windows
   `CommandLineToArgvW` to the expected arguments in source and packaged modes.
2. The installer exits configuration initialization before any write when a file
   exists. The fresh-install initialization stays intact. Legacy configurations
   still load user values and defaults for missing keys without rewriting files.
3. Record whether a skipped action sets ownership and causes `play` after a
   simulated SteamVR session; distinguish this from testing real engine startup.

# Testing Plan

- Use `unittest` and mocked registry writes to test Windows command parsing for
  source and packaged paths, with and without spaces and Unicode.
- Load a legacy configuration in a temporary directory and verify preserved
  values, missing-key defaults, and unchanged bytes.
- Reproduce skipped actions with mocked process detection and subprocess calls.
- Review installer control flow against the official Inno Setup documentation.
  Compile or execute the installer only if an Inno Setup compiler is available.
- Check Python syntax, the final diff, and whitespace errors.

# Implementation Plan

1. Add startup command regression tests and run them against the existing code to
   confirm source-mode failure. Add the legacy configuration compatibility test.
2. Build the complete startup command from an argument list using
   `subprocess.list2cmdline`; rerun startup tests.
3. Add an early `FileExists(ConfigPath)` return to installer initialization;
   verify placement before file creation/writing and rerun the full test suite.
4. Inspect the final changes and report the reconfirmed behavior and test limits.

# References and Tool Availability

- Windows subprocess quoting:
  https://docs.python.org/3/library/subprocess.html#converting-an-argument-sequence-to-a-string-on-windows
- Inno Setup `FileExists`:
  https://jrsoftware.org/ishelp/topic_isxfunc_fileexists.htm
- Inno Setup `SaveStringToFile` (`Append=False` overwrites):
  https://jrsoftware.org/ishelp/topic_isxfunc_savestringtofile.htm
- Serena and Lad tools are not available in this session.
- No Inno Setup compiler was found on PATH or in the standard installation paths.

# Verification Results

- Before the startup change, both source-mode command parsing tests failed;
  packaged-mode and legacy configuration tests passed.
- After the change, all five tests pass with `python -B -m unittest discover -v`.
- The generated source startup command successfully launches the actual entry
  point with an appended `--help`, exiting with code 0 without registry writes.
- All 12 source/test Python files parse with the Python 3.10 grammar, and
  `git diff --check` passes.
- Both skipped stop and skipped pause reproduce false ownership and an extra
  `play` command after simulated SteamVR exit, even with auto-restart disabled.
  Real wallpaper startup was not exercised, and this behavior remains unchanged.
- The installer guard was reviewed before directory creation and file writing.
  Native installer compilation/execution was not performed because the compiler
  is unavailable.
