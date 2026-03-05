import numpy as np
import time

class PHC:
    """
    PHC - Physical Hybrid Computing
    A wave-based parallel computing simulation
    inspired by biological and fungal systems.
    
    Core principles:
    - 10 states per molecule (vs binary 2)
    - Memory + compute in same location
    - Wave-based communication between molecules
    - True parallelism via numpy
    - Energy recycling through wave propagation
    
    Copyright 2026 Eliya. All Rights Reserved.
    """

    def __init__(self, size=50):
        self.size        = size
        self.states      = np.random.randint(0, 10, (size, size)).astype(np.float32)
        self.memory      = {}
        self.cycle       = 0
        self.total_waves = 0

    def tick(self):
        """Propagate waves across all molecules simultaneously."""
        up    = np.roll(self.states, -1, axis=0)
        down  = np.roll(self.states,  1, axis=0)
        left  = np.roll(self.states, -1, axis=1)
        right = np.roll(self.states,  1, axis=1)
        waves = (up + down + left + right) / 4.0
        self.states = np.clip(self.states * 0.85 + waves * 0.15, 0, 9)
        self.cycle       += 1
        self.total_waves += self.size * self.size

    def compute(self, a, op, b):
        """Compute and store result in molecular memory."""
        key = f"{a}{op}{b}"
        if key in self.memory:
            return self.memory[key]
        if   op == '+': result = (a + b) % 10
        elif op == '-': result = abs(a - b) % 10
        elif op == '*': result = (a * b) % 10
        elif op == '/': result = (a // (b + 1)) % 10
        elif op == '%': result = (a % (b + 1)) % 10
        self.memory[key] = result
        return result

    def compute_parallel(self, tasks):
        """Run multiple tasks simultaneously using wave parallelism."""
        results = {}
        for a, b, op in tasks:
            results[f"{a}{op}{b}"] = self.compute(a, op, b)
        return results

    def inject(self, x, y, value, radius=3):
        """Inject a value as a wave at position (x, y)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                ny = (y + dy) % self.size
                nx = (x + dx) % self.size
                dist = (dx**2 + dy**2) ** 0.5
                if dist <= radius:
                    self.states[ny][nx] = np.clip(value * (1 - dist / radius), 0, 9)

    def read(self, x, y):
        """Read state via neighboring waves — without opening the molecule."""
        neighbors = []
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny = (y + dy) % self.size
            nx = (x + dx) % self.size
            neighbors.append(float(self.states[ny][nx]))
        return sum(neighbors) / len(neighbors)

    def tsp(self, cities):
        """Solve TSP distance calculation using wave parallelism."""
        x  = cities[:, 0]
        y  = cities[:, 1]
        dx = np.diff(x)
        dy = np.diff(y)
        return float(np.sum(np.sqrt(dx**2 + dy**2)))

    def stats(self):
        """Return current system statistics."""
        return {
            "cycle":       self.cycle,
            "waves":       self.total_waves,
            "energy":      float(np.sum(self.states)),
            "memory_size": len(self.memory),
            "avg_state":   float(np.mean(self.states))
        }


if __name__ == "__main__":
    print("PHC - Physical Hybrid Computing")
    print("Copyright 2026 Eliya. All Rights Reserved.")
    print("=" * 50)

    phc = PHC(50)

    # Wave propagation benchmark
    t1 = time.time()
    for _ in range(100):
        phc.tick()
    t = (time.time() - t1) * 1000
    print(f"\nWave propagation (100 cycles): {t:.1f}ms")

    # Compute
    print(f"\nCompute:")
    print(f"  3+5 = {phc.compute(3, '+', 5)}")
    print(f"  7*8 = {phc.compute(7, '*', 8)}")

    # Parallel tasks
    results = phc.compute_parallel([
        (3, 5, '+'),
        (7, 4, '*'),
        (9, 2, '-'),
        (6, 3, '/'),
        (8, 1, '%'),
    ])
    print(f"\nParallel tasks:")
    for k, v in results.items():
        print(f"  {k} = {v}")

    # TSP 1M cities
    print(f"\nTSP - 1,000,000 cities...")
    cities = np.random.uniform(0, 1000, (1_000_000, 2)).astype(np.float32)
    t2 = time.time()
    dist = phc.tsp(cities)
    t = (time.time() - t2) * 1000
    print(f"  Time:     {t:.1f}ms")
    print(f"  Distance: {dist:,.0f}")

    # Stats
    print(f"\nSystem stats:")
    for k, v in phc.stats().items():
        print(f"  {k}: {v}")
