# As Is

The user confirms that clicking causes the settings page to jump. The global
FocusIn handler scrolls for any descendant, including oversized containers, and
can move content during a mouse press. Separately, toggling UU automatically
navigates to the connection page. A deterministic reproduction of a container
FocusIn moved the canvas to 0.612 even though no keyboard traversal occurred.

# To Be

Mouse clicks keep controls in place. Tab/Shift-Tab reveal the actual focused
control only after focus traversal finishes. Navigation stays explicit.

# Requirements

1. Remove global focus-triggered scrolling. Only keyboard Tab traversal may
   schedule an automatic reveal, after the normal event has completed.
2. Reveal only the current, mapped interactive control in the active page;
   ignore ancestor frames, other pages, the sidebar, and the footer.
3. Do not scroll for controls already visible. Cancel pending reveal callbacks
   on pointer press and window close.
4. The UU switch expands/collapses settings in place. Only explicit navigation
   buttons change pages.
5. Respect the user's restriction to one preview program. Computer Use was
   physically stopped by Escape, so make no further desktop automation calls
   during this turn and report the remaining native verification limit.

# Acceptance Criteria

- No FocusIn binding can scroll the settings canvas.
- A pointer press never requests a scroll and cancels stale keyboard reveals.
- Offscreen controls are revealed after keyboard traversal; visible controls,
  frames and controls outside the active canvas do not move the page.
- Switching UU on or off does not call page navigation.
- Existing settings, UU and wallpaper tests remain green.

# Testing Plan

- First reproduce the original ancestor-focus scroll with mock geometry.
- Add event-routing and geometry regression tests without native UI input.
- Test deferred keyboard traversal, pointer cancellation and explicit UU setup.
- Run the complete suite, Python 3.10 syntax and entry-point smoke checks.
- Native mouse/keyboard verification remains pending because desktop automation
  was stopped; do not launch or control another application to bypass that stop.

# Implementation Plan

1. Add failing regression tests for in-place toggling and keyboard-only reveal.
2. Extract navigation bindings, defer reveal with after_idle, ignore containers
   and out-of-page focus, and cancel pending callbacks on pointer/close.
3. Remove forced navigation from the UU switch; run targeted then full tests.

# References and Tool Availability

- Tk focus semantics: https://web.tcl.tk/man/tcl9.1/TkCmd/focus.html
- Tk binding order: https://web.tcl.tk/man/tcl9.1/TkCmd/bindtags.html
- Idle scheduling: https://tkdocs.com/tutorial/eventloop.html
- TDD and ui-ux-pro-max guidance apply. Serena/Lad tools are unavailable.

# Verification Results

- Original behavior reproduced: a container focus event alone requested canvas
  position 0.612. The original UU toggle also navigated away without an explicit
  navigation action.
- The new routing and geometry tests passed after removing FocusIn scrolling,
  deferring keyboard-only reveal, filtering actual interactive focus, and
  canceling pending callbacks on pointer input and close.
- All 41 regression tests pass; all 18 Python files parse with Python 3.10
  grammar. Entry-point `--help` and `git diff --check` pass.
- No further Computer Use input or new preview launch was performed after the
  user's physical Escape stop. Real pointer verification of the fixed version
  remains pending; an already-running preview retains the old loaded code until
  it is closed and reopened.
