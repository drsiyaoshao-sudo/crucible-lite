"""
crucible.sim — Renode simulation bridge + IronPython peripheral stubs.

Quick imports:
    from crucible.sim.renode import RenoneBridge, detect_renode, detect_firmware

Stubs (IronPython, loaded by Renode at runtime — not importable as Python):
    crucible/sim/stubs/sim_imu_stub.py   — float32 IMU sample peripheral
    crucible/sim/stubs/sim_uart_stub.py  — nRF52840 UARTE0 DMA capture peripheral
"""
