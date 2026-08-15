# Building, Signing, and Notarizing Dad Ware

This document covers building the standalone `yourdad` executable, and
signing/notarizing it for distribution outside the Mac App Store.

## Prerequisites

- macOS (Intel or Apple Silicon)
- Python 3.9+ with the project's `venv` set up
- PyInstaller, installed via `requirements-dev.txt`:
  ```bash
  ./venv/bin/pip install -r requirements-dev.txt
  ```
- For signing/notarizing only (not needed for a local dev build):
  - A paid Apple Developer Program membership
  - A **Developer ID Application** certificate installed in your keychain
  - Either an App Store Connect API key, or an Apple ID with an
    app-specific password (see [Signing and notarizing](#signing-and-notarizing) below)

## Building locally

```bash
./build_executable.sh
```

This cleans old build artifacts and runs
`pyinstaller yourdad.spec`, producing `dist/yourdad` (~8.5 MB, single
file, no Python installation required to run it). Equivalent manual
invocation:

```bash
./venv/bin/python -m PyInstaller yourdad.spec --noconfirm
```

Sanity-check the result:

```bash
./dist/yourdad --version
./dist/yourdad --terminal --no-color --volume ~/Documents --no-mac-libraries
```

## Environment variables read by `yourdad.spec`

The spec file takes its architecture and signing configuration from the
environment rather than hardcoding them, so the same spec works for an
unsigned local dev build and a signed CI build:

| Variable | Default | Purpose |
|---|---|---|
| `DADWARE_TARGET_ARCH` | *(unset → native arch)* | Passed to PyInstaller's `target_arch`. Set to `universal2` to build a fat binary — see [the universal2 constraint](#the-universal2-constraint) below. |
| `DADWARE_CODESIGN_IDENTITY` | *(unset → unsigned)* | Passed to PyInstaller's `codesign_identity`. The same `"Developer ID Application: Name (TEAMID)"` string used by `sign_and_notarize.sh`. Lets PyInstaller sign ad-hoc during the build itself. |
| `DADWARE_ENTITLEMENTS` | *(unset → none)* | Passed to PyInstaller's `entitlements_file`. Normally `entitlements.plist` in the repo root. |

None of these need to be set for a normal local build — that's the whole
point of defaulting to `None`/native.

### The universal2 constraint

PyInstaller **cannot cross-compile**. A `universal2` (Intel + Apple
Silicon fat) output requires the Python interpreter doing the *building*
to itself be a universal2 build (e.g. the official python.org installer,
or a `venv` created from one). A single-arch Python — which is what most
Homebrew installs and most CI runners default to — can only ever produce
a single-arch binary.

Concretely: if you set `DADWARE_TARGET_ARCH=universal2` while building
with a single-arch Python, PyInstaller does not silently downgrade to a
single-arch binary — it fails outright, partway through bundling, with
an error like:

```
PyInstaller.utils.osx.IncompatibleBinaryArchError: .../_struct.cpython-314-darwin.so is not a fat binary!
```

This was verified directly on this machine (Intel/x86_64-only Python):
setting the variable reproduces exactly that failure. That's why the
spec's default is `None` (build for whatever arch the current Python
is) — universal2 is opt-in, and only useful once the build is actually
running on a universal2 Python.

## Signing and notarizing

Run this **after** `./build_executable.sh` has produced `dist/yourdad`:

```bash
export DADWARE_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"

# Preferred: App Store Connect API key
export APPLE_API_KEY_ID="..."
export APPLE_API_ISSUER="..."
export APPLE_API_KEY_PATH="/path/to/AuthKey_XXXX.p8"

# OR: Apple ID + app-specific password
# export APPLE_ID="you@example.com"
# export APPLE_TEAM_ID="ABCDE12345"
# export APPLE_APP_PASSWORD="app-specific-password"

./sign_and_notarize.sh
```

The script:
1. Codesigns `dist/yourdad` with the hardened runtime, a secure
   timestamp, and `entitlements.plist`.
2. Verifies the signature (`codesign --verify`, `codesign -dv --entitlements -`).
3. Zips the binary with `ditto` (a raw executable can't be submitted to
   `notarytool` directly), submits it with
   `xcrun notarytool submit --wait`, and checks the result.
4. Explains why stapling is skipped for a bare binary (see below) and
   prints a `spctl` command to spot-check the result.

### What secrets are needed

- **Signing**: a Developer ID Application certificate + private key in
  your keychain (`security find-identity -v -p codesigning` to list what's
  available). `DADWARE_CODESIGN_IDENTITY` just names which one to use —
  it doesn't itself contain a secret.
- **Notarization**, one of:
  - An **App Store Connect API key** (`.p8` file) plus its Key ID and
    Issuer ID, generated at App Store Connect → Users and Access → Keys.
    Preferred: it doesn't expire the way app-specific passwords can, and
    doesn't touch your Apple ID password at all.
  - An **app-specific password** for your Apple ID, generated at
    [appleid.apple.com](https://appleid.apple.com) → Sign-In and
    Security → App-Specific Passwords. Never use your actual Apple ID
    password here.

None of these are present in this repo, and `sign_and_notarize.sh` reads
all of them from the environment — never hardcode them into any script,
CI config, or commit.

### Why the binary isn't stapled

`xcrun stapler staple` only works on `.app` bundles, `.dmg` images, and
`.pkg` installers — it has no support for stapling a ticket onto a bare
Mach-O executable, and running it against `dist/yourdad` would simply
fail. `sign_and_notarize.sh` does not attempt it.

This doesn't mean the binary is unverifiable offline in principle — it
means Gatekeeper falls back to its other mechanism: after notarization
succeeds, Apple's notary service holds the ticket on its servers, keyed
to the binary's code signature. When a user runs the binary, Gatekeeper
looks the ticket up online (rather than reading it from a stapled
attachment) and allows the binary through. The practical difference is
that first-run verification needs network access; everything else about
the user experience is the same as a stapled app.

If fully offline verification ever becomes a requirement, the fix is to
package `yourdad` inside a `.dmg` (or `.pkg`) and staple that instead —
that's a bigger scope change than this script covers and hasn't been
done here.

### Verifying the result

```bash
spctl -a -vvv -t install dist/yourdad
```

Note that `spctl`'s `install` policy check is primarily designed for
`.app` bundles and installer packages. Run against a bare, notarized CLI
binary, it can print something like `rejected` or `no usable signature`
even when signing and notarization both genuinely succeeded — this is a
known quirk of `spctl` with loose executables, not proof the binary is
broken. The trustworthy checks are the ones `sign_and_notarize.sh`
already performs: `codesign --verify` passing, and the notarytool
submission status reading `Accepted`.

## Gatekeeper behavior for end users

- **Unsigned binary** (a plain `./build_executable.sh` output, no
  signing step run): downloaded via a browser, macOS quarantines it.
  Gatekeeper will refuse to run it via double-click, and even
  `chmod +x && ./yourdad` from Terminal may be blocked outright on
  current macOS depending on how it was transferred. The standard
  workaround, and the one to give end users:
  ```bash
  xattr -d com.apple.quarantine /path/to/yourdad
  ```
  This strips the quarantine attribute macOS attached to the download,
  after which the binary runs normally. (Right-click → Open, then
  confirming the dialog, is the other standard workaround and doesn't
  require Terminal.)

- **Signed and notarized binary**: still gets the quarantine attribute
  on download, but Gatekeeper's online check against Apple's notary
  ticket succeeds automatically, so the user just sees a brief "Apple
  checked this app" first-run confirmation instead of a block — no
  `xattr` workaround needed.

## Honesty note on what's verified here

This project currently has no Developer ID certificate and no Apple
credentials available in this environment, so the signing and
notarization steps in `sign_and_notarize.sh` have **not** been exercised
end-to-end against Apple's services. What has been verified:

- `bash -n sign_and_notarize.sh` passes (valid syntax).
- Running the script with missing/incomplete env vars fails fast with
  the intended, specific error messages (tested for: missing identity,
  missing `dist/yourdad`, incomplete API-key trio, no notarization
  credentials at all).
- The `codesign`, `ditto`, and `xcrun notarytool` invocations match
  Apple's documented usage for onefile/CLI binaries.
- `entitlements.plist` is valid XML (`plutil -lint`).
- `yourdad.spec` was rebuilt after every change and the resulting
  `dist/yourdad` was smoke-tested (`--version` and a real `--terminal`
  scan) after each one, including a deliberate test of
  `DADWARE_TARGET_ARCH=universal2` on this machine's single-arch
  (x86_64) Python to confirm it fails the way this document describes.

**Not verified**, and requiring a real Developer ID certificate + Apple
credentials to check: that `codesign` actually produces a signature
Gatekeeper accepts, that `notarytool submit` succeeds against Apple's
live service, and that the finished binary passes Gatekeeper on a clean
machine.
