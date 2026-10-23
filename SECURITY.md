# Security policy

## Supported versions

Only the [latest release](https://github.com/H4Z4RD-H42/RED-Spectrogram/releases/latest) receives fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.
Report them privately through GitHub instead:
[Report a vulnerability](https://github.com/H4Z4RD-H42/RED-Spectrogram/security/advisories/new).

You can expect a first reply within a couple of weeks.

## Verifying downloads

Release files are built by GitHub Actions directly from this repository. You can verify that a
download is genuine with the [GitHub CLI](https://cli.github.com/):

```bash
gh attestation verify RED-Spectrogram-v3.0.0-windows-x64.zip --repo H4Z4RD-H42/RED-Spectrogram
```

or by comparing its SHA-256 hash with `SHA256SUMS.txt` from the same release.
