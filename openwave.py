# OpenWave Protocol — Wave-based communication layer for PHC
# Part of the PHC repository by Eliya, 2026
# Connects to phc.py and extends it with named wave channels,
# multi-grid routing, and signal monitoring.

import numpy as np
from phc import PHC


class OpenWave:
    """
    OpenWave sits on top of the PHC engine and provides:
    - Named channels (send data between grids via wave signals)
    - Signal monitoring (watch wave activity in real time)
    - Multi-grid routing (connect multiple PHC instances)
    - Wave encoding/decoding (convert data to wave patterns)
    """

    def __init__(self, grid_size: int = 50):
        self.grid_size = grid_size
        self.grids: dict[str, PHC] = {}          # named PHC grids
        self.channels: dict[str, list] = {}       # named signal channels
        self.signal_log: list[dict] = []          # history of signals sent

    # --- Grid management ---

    def create_grid(self, name: str) -> PHC:
        """Create and register a named PHC grid."""
        grid = PHC(size=self.grid_size)
        self.grids[name] = grid
        self.channels[name] = []
        return grid

    def get_grid(self, name: str) -> PHC:
        """Get a grid by name, create if missing."""
        if name not in self.grids:
            self.create_grid(name)
        return self.grids[name]

    def list_grids(self) -> list[str]:
        return list(self.grids.keys())

    # --- Wave encoding ---

    def encode(self, value: float, min_val: float = 0, max_val: float = 9) -> float:
        """Encode a value into a 0-9 wave state."""
        normalized = (value - min_val) / (max_val - min_val + 1e-9)
        return float(np.clip(normalized * 9, 0, 9))

    def decode(self, wave_state: float, min_val: float = 0, max_val: float = 9) -> float:
        """Decode a wave state back to original value range."""
        return float((wave_state / 9.0) * (max_val - min_val) + min_val)

    # --- Signal transmission ---

    def send(self, from_grid: str, to_grid: str, value: float, cycles: int = 10):
        """
        Send a wave signal from one grid to another.
        Encodes value, injects into source grid, propagates, reads result.
        """
        src = self.get_grid(from_grid)
        dst = self.get_grid(to_grid)

        # Encode and inject into center of source grid
        encoded = self.encode(value)
        cx, cy = self.grid_size // 2, self.grid_size // 2
        src.states[cx, cy] = encoded

        # Propagate waves
        for _ in range(cycles):
            src.tick()

        # Read average wave energy from source edge → inject into destination
        edge_signal = float(np.mean([
            src.states[0, :].mean(),
            src.states[-1, :].mean(),
            src.states[:, 0].mean(),
            src.states[:, -1].mean(),
        ]))

        # Inject into destination grid
        dst.states[cx, cy] = np.clip(dst.states[cx, cy] + edge_signal, 0, 9)

        # Log the transmission
        entry = {
            "from": from_grid,
            "to": to_grid,
            "value": value,
            "encoded": encoded,
            "edge_signal": edge_signal,
            "cycles": cycles
        }
        self.signal_log.append(entry)
        if to_grid in self.channels:
            self.channels[to_grid].append(entry)

        return edge_signal

    def broadcast(self, value: float, from_grid: str, cycles: int = 10):
        """Send a signal from one grid to ALL other grids."""
        results = {}
        for name in self.grids:
            if name != from_grid:
                results[name] = self.send(from_grid, name, value, cycles)
        return results

    # --- Monitoring ---

    def energy(self, grid_name: str) -> dict:
        """Get wave energy stats for a grid."""
        grid = self.get_grid(grid_name)
        return {
            "mean": float(np.mean(grid.states)),
            "max":  float(np.max(grid.states)),
            "min":  float(np.min(grid.states)),
            "std":  float(np.std(grid.states)),
            "total": float(np.sum(grid.states)),
        }

    def snapshot(self) -> dict:
        """Get energy snapshot of all grids."""
        return {name: self.energy(name) for name in self.grids}

    def channel_history(self, grid_name: str) -> list:
        """Get all signals received by a grid."""
        return self.channels.get(grid_name, [])

    def clear_log(self):
        """Clear signal history."""
        self.signal_log = []
        for name in self.channels:
            self.channels[name] = []

    # --- Tick all ---

    def tick_all(self, cycles: int = 1):
        """Advance all grids by N wave cycles simultaneously."""
        for _ in range(cycles):
            for grid in self.grids.values():
                grid.tick()

    def tick_grid(self, name: str, cycles: int = 1):
        """Advance a single grid by N wave cycles."""
        grid = self.get_grid(name)
        for _ in range(cycles):
            grid.tick()
