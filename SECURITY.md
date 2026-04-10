# Security Policy

## Scope

Crucible is a governance framework. Most security considerations apply to the *devices you build with it*, not to the framework itself. This document covers both.

---

## Framework security (this repository)

### No secrets in the repo

Crucible does not store credentials, API keys, device serial numbers, or patient data. If you fork this repo, ensure your `toolchain_config.md` does not contain proprietary device identifiers that should not be public.

### Agent commands are prompts, not executable code

The `.claude/commands/` files are Claude Code prompt templates. They do not contain executable scripts. They invoke shell commands through Claude Code's Bash tool, which runs in your local environment with your permissions. Review the commands you use before running them in a new environment.

---

## Device security (what you build)

### BLE security posture (current: open)

The GaitSense reference implementation uses open BLE advertising with no bonding, pairing, or encryption. Any device running a BLE scanner can connect and receive data.

**Current posture is acceptable for:**
- Dev kit bench testing
- Single-user field testing in a controlled environment
- Prototypes not handling sensitive personal data

**Current posture is NOT acceptable for:**
- Multi-user environments where data attribution matters
- Devices that handle personally identifiable health information
- Production devices subject to HIPAA, GDPR, or equivalent

**What you need to add before production:**
- BLE pairing (at minimum: Just Works pairing if the device has no display)
- BLE bonding (so only authorised host devices reconnect)
- Application-layer encryption if the data is sensitive and BLE transport encryption is not sufficient
- A mechanism to factory-reset bonding state (e.g., long button press)

### Firmware signing (not implemented)

The current UF2 flash workflow has no firmware authentication. Anyone with physical access to the device and a double-tap of the reset button can overwrite the firmware. For production devices:

- Implement bootloader-level signature verification before executing application firmware
- nRF52840 supports SoftDevice-based firmware validation via Nordic DFU with signed images
- The signing key must be generated, stored, and rotated outside this repository

### Field data handling

The GaitSense reference captures step count, stance/swing timing, SI, and cadence over BLE. This data is not directly personally identifiable, but in combination with other data (user ID, timestamp, location) it may constitute health data under applicable regulations.

Before deploying a Crucible-based device in a context where field data is stored or transmitted:
- Determine whether the data qualifies as health data under your jurisdiction
- Implement appropriate data minimisation (only collect what is needed)
- Define retention and deletion policies
- Document the data flow in `docs/field-test/data_handling.md`

---

## Reporting a vulnerability

If you find a security issue in the Crucible framework itself (not in a device built with it), file a GitHub Issue with the title `[SECURITY] <brief description>`. Do not include proof-of-concept exploit code in the issue. The maintainer will respond within 5 business days.

For vulnerabilities in devices built with Crucible: contact the team that built the device directly. This repository is not responsible for the security of derivative devices.
