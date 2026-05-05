# Example: Crucible Comfort — Wearable Thermal Comfort Monitor

**Repository:** [github.com/rturcottetardif/crucible-comfort](https://github.com/rturcottetardif/crucible-comfort)

**Device:** Seeed XIAO nRF52840 Sense — nRF52840 + on-board sensors + BLE 5.0  
**Domain:** Thermal comfort — human thermal state monitoring and classification  
**Status:** Reference implementation — all stages documented with real results

---

## Why this is the reference implementation

`crucible-comfort` is the cleanest end-to-end example of Crucible on a real device. Use it to understand what a complete, governed hardware project looks like before starting your own.

Key things it demonstrates:

**1. What a complete Amendment set looks like.**  
Device-specific Amendments derived from thermal comfort domain primitives — not generic placeholders. Each Amendment has a physical justification and a failure mode it was written to prevent.

**2. What the signal-only simulation path looks like.**  
`src/signals.py` and `src/algorithm.py` fully implemented. The physics model runs without firmware or Renode. Simulation and hardware results converge at Stage 1 gate.

**3. What governed toolchain registration looks like.**  
`docs/toolchain_config.md` is fully filled in: active board, FQBN, pin map, firmware UART format, and any blocked tools with block rationale.

**4. What case law looks like after real decisions.**  
`docs/governance/case_law.md` contains binding precedents from actual Hearings — not hypothetical examples.

---

## How to use this as a starting point

1. Read the `CONSTITUTION.md` and `docs/governance/amendments.md` in that repo to understand how domain primitives were derived for thermal comfort.
2. Compare the `src/signals.py` implementation to the physics in `docs/device_context.md` — this is what Article I compliance looks like in code.
3. Fork `crucible-lite` (this repo), run `/spec collect` for your own device domain, and use `crucible-comfort` as the template for what you're building toward.

---

## Domain primitives (thermal comfort)

See the full derivation in the repo. The core primitives follow from the physics of human thermoregulation — skin temperature, core temperature differential, sweat rate, and ambient conditions are first-order measurable quantities that all algorithm thresholds must trace back to.
