"""
crucible.signal — generic UART event infrastructure and plot utilities.

Quick imports:
    from crucible.signal.events   import UartEvent, SessionEndEvent
    from crucible.signal.analysis import UartParser, EventDefinition
    from crucible.signal.plot     import plot_sensor_trace, plot_metric_bar, plot_metric_timeline

Domain-specific event types, parsers, and plot wrappers are generated
per-project in src/ by `/toolchain scaffold`.
"""
