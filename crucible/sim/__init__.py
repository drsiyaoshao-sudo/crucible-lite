"""
crucible.sim — Renode simulation bridge + signal-only simulator + IronPython stubs.

Two simulation paths:

    Signal-only (fast — no Renode, no firmware):
        from crucible.sim.signal_sim import SignalSimulator, compare_paths
        sim = SignalSimulator(src.signals.generate, src.algorithm.run)
        result = sim.run("nominal", n_steps=100)

    Renode path (thorough — firmware runs in emulator):
        from crucible.sim.renode import RenoneBridge, detect_renode, detect_firmware
        bridge = RenoneBridge(elf_path)
        uart_text = bridge.run(samples)  # parse with src/analysis.py

Stubs (IronPython, loaded by Renode at runtime — not importable as Python):
    crucible/sim/stubs/sim_imu_stub.py   — float32 sensor sample peripheral
    crucible/sim/stubs/sim_uart_stub.py  — nRF52840 UARTE0 DMA capture peripheral
"""
