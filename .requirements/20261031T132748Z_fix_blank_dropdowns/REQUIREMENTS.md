# As Is

Readonly comboboxes can look empty after opening/dismissing them. The app
overrides the clam theme's readonly field background to white but inherits its
readonly+focus white foreground. The installed app's trigger field was observed
blank. UU regions also include a non-specific "Use UU preferences" item with
empty IDs, which the user explicitly wants removed.

# To Be

All dropdown values stay readable and retain a concrete valid selection when
focus changes or a popup is dismissed. Region choices contain only actual UU
regions; loading/unavailable status is outside the dropdown.

# Requirements

1. Override readonly foreground colors for focused and unfocused states; isolate
   entry selection from clipboard ownership and clear only selection highlights.
2. Keep the last valid choice when an interaction leaves an invalid/empty value.
   Apply this consistently to action, trigger, region, and language dropdowns.
3. Remove region placeholders with empty IDs. Load actual regions asynchronously
   when UU options are enabled, preserve an available saved region, and otherwise
   select the first actual region returned by UU (currently intelligent matching).
4. Hide an empty region dropdown while showing loading/recovery text. Require an
   actual region before saving enabled automation; unrelated settings may still
   be saved while UU is disabled, retaining existing region configuration.
5. Rebuild and update the locally installed app, preserving saved config/startup
   and keeping a backup. Control only this application's UI during verification.

# Acceptance Criteria

- Real Tk style lookup for readonly+focus resolves to readable ink, not white.
- Dropdown cancel/focus loss keeps the last valid value without resetting an
  explicitly selected new value. No-region entries are not offered as choices.
- Loading results preserve a selected/saved region by zone/server IDs, and stale
  or placeholder choices are replaced with a concrete available choice.
- Saving enabled UU without a real region displays a region-specific error and
  does not partially mutate config. Disabled UU preserves existing IDs.
- Automated tests, frozen startup smoke, local binary hash/config checks pass.

# Testing Plan

- Add a hidden-Tk style lookup regression to reproduce white-on-white text.
- Add selection retention and region loading/saving regression tests.
- Exercise only the installed app for native visual checks, unless Computer Use
  is stopped; never operate UU's own authorization or network controls.
- Run the full suite and syntax/diff checks, rebuild, back up, replace, and check
  the installed process/version and unchanged config.

# Implementation Plan

1. Add failing style, choice retention, and concrete-region tests.
2. Fix combobox colors and focus/selection handling; run targeted tests.
3. Implement concrete region loading, validation and localized recovery states;
   run settings/config/UU tests.
4. Build version 1.2.1 and replace the local app after waiting for file unlock.

# References

- Python ttk combobox/entry APIs:
  https://docs.python.org/3/library/tkinter.ttk.html
- Official Tcl/Tk combobox bindings:
  https://github.com/tcltk/tk/blob/main/library/ttk/combobox.tcl
- Local Tk 8.6 clamTheme.tcl confirms inherited readonly+focus foreground uses
  the theme's selected-text color. Native lookups are tested directly.
- TDD and ui-ux-pro-max guidance apply; Serena/Lad tools are unavailable.

# Verification Results

- The native Tk regression reproduced the cause: readonly+focus foreground was
  `#ffffff` on the overridden white field. It now resolves to `#182D36` with
  and without focus. An actual hidden Tk combobox retains its StringVar/get()
  value across selection clearing and focus-state changes.
- All 50 tests pass, including concrete region selection, placeholder removal,
  saved selection retention and disabled-UU configuration preservation.
- Python 3.10 syntax and diff checks pass. The PyInstaller 1.2.1 executable
  passes `--settings --help` with exit code 0.
- Updated the local installation to 1.2.1 and opened settings. The installed
  executable matches the build; saved configuration remains byte-for-byte
  unchanged. Previous 1.2.0 files/config/registry metadata are backed up under
  `%LOCALAPPDATA%/SteamVRWallpaperPause/backups/20261031T132748Z-1.2.0`.
- Computer Use then reported a physical Escape stop. No further desktop tools
  were called; final manual pointer verification remains incomplete.
