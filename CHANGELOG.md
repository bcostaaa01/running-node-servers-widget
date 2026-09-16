# Changelog

## v0.3.0 - 2026-09-16

- Added a per-row kill button (small "✕" next to the PID) that stops
  just that one Node process, instead of having to kill every `node.exe`
  at once. Turns red on hover; the list refreshes right after.

## v0.2.0 - 2026-09-16

- Replaced the native right-click menu with a proper UI: click the tray
  icon (either button) to open a small always-on-top dashboard card next
  to the cursor, like the OneDrive/battery/volume flyouts.
- The card follows Windows' light/dark app theme and fills with a soft
  green-to-sand gradient; it resizes to fit however many servers are
  running and caps the list at 8 rows with a "+N more" overflow line.
- Click a row to open that server's port in your browser; Refresh and
  Quit live as links in the card's footer.

## v0.1.0 - 2026-09-16

- Initial release: tray icon that lists every running Node.js process with
  an open listening port, labeled with its working-directory name.
- Right-click the tray icon to see the live list; click an entry to open
  that port in your browser.
- Tooltip shows a quick summary of active ports; rescans every 5 seconds.
