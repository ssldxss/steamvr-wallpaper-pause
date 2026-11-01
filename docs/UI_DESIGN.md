# Desktop settings design

Use the existing Python/Tkinter stack. No web runtime or screenshot assets.
The ui-ux-pro-max design-system search informed progressive disclosure, focus
visibility, loading feedback, and minimal layout; marketing-style oversized
type and decorative animation do not fit this desktop utility.

- Window: approximately 940 x 720 logical pixels, resizable; content can scroll
  vertically in a smaller window. Keep the save/cancel footer visible.
- Navigation: Automation, Connection guide, Advanced. Three destinations only.
- Palette: ink sidebar `#15262D`, canvas `#F3F6F6`, white surfaces, ink text
  `#182D36`, secondary text `#51666E`, teal action `#087F72`, borders `#DCE5E7`.
- Fonts: system Segoe UI / Microsoft YaHei UI; 10-11 pt body, 19-22 pt headings.
- Spacing: 8 px base; 16 px card padding; 24 px section gaps; 32 px page gutters.
- Automation: wallpaper mode, optional UU automation, trigger/region, Windows
  startup. Optional UU options disable clearly when the master switch is off.
- Connection: one status summary, read-only connection check, three concise
  manual setup steps. Show the next recovery action for unavailable/busy UU.
- Advanced: polling interval and executable paths. Game IDs and HTTP ports are
  configuration details, not ordinary UI fields.
- Feedback: text accompanies status colors; all network/CLI work runs in a
  worker and updates widgets through a main-thread queue. Errors stay inline.
- Interaction: native buttons/checkbuttons/comboboxes, visible focus, Tab order,
  Escape to cancel, and explicit Save. No decorative motion or emoji icons.
