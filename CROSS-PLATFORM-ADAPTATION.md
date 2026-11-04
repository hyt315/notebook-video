# macOS + Windows cross-platform adaptation

The maintained contract now lives in [references/cross-platform-compatibility.md](references/cross-platform-compatibility.md): the parity rules, per-system requirements, macOS / Windows notes, launcher aliases and the verification commands all sit there.

Two things this page used to claim are no longer true and are worth naming, because they were read as current for several releases:

- it described the template as "themes flat + cel" — the template now ships five skins (flat / cel component themes plus the journal / papercut / archive hand-made skins);
- it said the build environment was Linux and Windows was only statically audited — CI runs both an Ubuntu job and a Windows job (Python 3.12 + Node 22 + FFmpeg), and the project is developed on Windows.

For the current state, read the contract above rather than this page.
