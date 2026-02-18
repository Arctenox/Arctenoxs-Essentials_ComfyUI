"""
Arctenox Essentials - Seed Topology Mapper
===========================================

Generates deterministically related seeds from one input seed using
mathematical spacing methods for structured exploration.

Author: Arctenox
Version: 1.0.0
License: GPL-3.0
"""

import math

class SeedTopologyMapper:
    """
    Generates multiple deterministically related seeds from one input seed
    using mathematical spacing methods for structured exploration.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_seed": ("INT", {
                    "default": 0, 
                    "min": -0x7fffffffffffffff, 
                    "max": 0xffffffffffffffff,
                    "tooltip": "Base seed for topology generation"
                }),
                "topology_type": ([
                    "golden_angle",
                    "harmonic",
                    "fibonacci",
                    "chaos_neighbors",
                    "prime_spiral",
                    "phi_spacing"
                ], {
                    "default": "golden_angle",
                    "tooltip": "Mathematical spacing method"
                }),
                "num_seeds": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 16,
                    "tooltip": "Number of related seeds to generate"
                }),
                "spread": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Spacing spread multiplier"
                })
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("seed_1", "seed_2", "seed_3", "seed_4", "seed_5", "seed_6", "seed_7", "seed_8", 
                    "seed_9", "seed_10", "seed_11", "seed_12", "seed_13", "seed_14", "seed_15", "seed_16")
    FUNCTION = "generate_topology"
    CATEGORY = "Arctenox Essentials/Sampling"
    
    DESCRIPTION = """
    Generates deterministically related seeds for structured exploration.
    
    Topology Types:
    • Golden Angle: Seeds spaced by golden angle (~137.5°)
    • Harmonic: Musical harmony ratios (1:2:3:4...)
    • Fibonacci: Seeds follow Fibonacci sequence spacing
    • Chaos Neighbors: Deterministic chaos with repeatable patterns
    • Prime Spiral: Seeds along prime number spiral
    • Phi Spacing: Golden ratio (φ) based spacing
    
    Use Cases:
    • Explore variations systematically
    • Create seed families with related characteristics
    • Generate reproducible seed sets for batch processing
    """

    def _normalize_seed(self, seed):
        """Normalize seed to 32-bit range"""
        return int(seed) & 0xFFFFFFFF
    
    def _golden_angle_topology(self, base_seed, index, spread):
        """Golden angle spacing (137.5077...°)"""
        GOLDEN_ANGLE = 2.39996322972865332  # radians
        offset = int((GOLDEN_ANGLE * index * spread * 1000000) % 0xFFFFFFFF)
        return self._normalize_seed(base_seed + offset)
    
    def _harmonic_topology(self, base_seed, index, spread):
        """Harmonic series spacing"""
        harmonic_offset = int((base_seed * (index + 1) * spread) % 0xFFFFFFFF)
        return self._normalize_seed(harmonic_offset)
    
    def _fibonacci_topology(self, base_seed, index, spread):
        """Fibonacci sequence spacing"""
        fib = self._fibonacci(index + 1)
        offset = int((fib * spread * 10000) % 0xFFFFFFFF)
        return self._normalize_seed(base_seed + offset)
    
    def _fibonacci(self, n):
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def _chaos_neighbors(self, base_seed, index, spread):
        """Chaotic but deterministic neighbors"""
        # Logistic map with controlled chaos
        x = (base_seed % 10000) / 10000.0  # Normalize to [0, 1]
        r = 3.9  # Chaos parameter
        
        for _ in range(index + 1):
            x = r * x * (1 - x)
        
        offset = int(x * 0xFFFFFFFF * spread)
        return self._normalize_seed(base_seed + offset)
    
    def _prime_spiral(self, base_seed, index, spread):
        """Prime number spiral spacing"""
        prime = self._nth_prime(index + 1)
        offset = int((prime * spread * 1000) % 0xFFFFFFFF)
        return self._normalize_seed(base_seed + offset)
    
    def _nth_prime(self, n):
        """Get nth prime number (approximate for efficiency)"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
        if n <= len(primes):
            return primes[n - 1]
        return primes[-1] + (n - len(primes)) * 6  # Approximation
    
    def _phi_spacing(self, base_seed, index, spread):
        """Golden ratio (φ) spacing"""
        PHI = 1.618033988749895
        offset = int((base_seed * math.pow(PHI, index + 1) * spread) % 0xFFFFFFFF)
        return self._normalize_seed(offset)

    def generate_topology(self, base_seed, topology_type, num_seeds, spread):
        """Generate topology of related seeds"""
        
        topology_funcs = {
            "golden_angle": self._golden_angle_topology,
            "harmonic": self._harmonic_topology,
            "fibonacci": self._fibonacci_topology,
            "chaos_neighbors": self._chaos_neighbors,
            "prime_spiral": self._prime_spiral,
            "phi_spacing": self._phi_spacing
        }
        
        func = topology_funcs[topology_type]
        seeds = []
        
        for i in range(16):
            if i < num_seeds:
                seed = func(base_seed, i, spread)
            else:
                seed = base_seed  # Fill remaining with base seed
            seeds.append(seed)
        
        return tuple(seeds)


# Node registration
NODE_CLASS_MAPPINGS = {
    "SeedTopologyMapper": SeedTopologyMapper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedTopologyMapper": "Seed Topology Mapper (Arctenox's Essentials)",
}

__all__ = ["SeedTopologyMapper"]