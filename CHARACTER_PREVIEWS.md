# Character preview integration

The app owns rendering. The agent must never capture the desktop, inspect other applications, or control a live show.

## Export contract

Export independent male and female Character Studio renders to `~/Library/Application Support/DMX Studio/DiagnosticPreviews/male.png` and `female.png`. Use an isolated scene with the same production character assembly and materials as Character Studio. Do not change the live stage, selected character, playback, or saved show. Write atomically, with user-only directory and file permissions. Each PNG must be at most 4 MiB and 4096 pixels per dimension. Export only with explicit diagnostic preview opt-in.

## Transfer contract (not implemented)

Use a separate authenticated, device-scoped private image channel, not the existing 8 KiB JSON diagnostic result. No public image URLs or desktop capture. Bind each preview to the request ID, installed build, character preset and capture timestamp; reject stale exports. Require expiry and deletion of transferred previews. Do not enable transfer until authorization and size-limit tests pass.

## Acceptance

Verify actual male and female renders, consistent framing and lighting, no playback interruption, correct build metadata, stale-file rejection and no access to unrelated files. Coordinate app changes with the unified release process. This document specifies the interface; it does not implement rendering or transfer.
