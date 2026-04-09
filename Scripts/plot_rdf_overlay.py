
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

XDG_CACHE_HOME = Path(".cache")
XDG_CACHE_HOME.mkdir(exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(XDG_CACHE_HOME.resolve()))

MPLCONFIGDIR = Path(".matplotlib")
MPLCONFIGDIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR.resolve()))

import matplotlib.pyplot as plt


DEFAULT_RUNS = [
    (0.1, "rdf_gamma01.dat"),
    (1.0, "rdf_gamma1.dat"),
    (5.0, "rdf_gamma5.dat"),
    (50.0, "rdf_gamma50.dat"),
    (200.0, "rdf_gamma200.dat"),
]


def load_rdf(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path)
    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"Unexpected RDF format in {path}")
    return data[:, 0], data[:, 1]


def main() -> None:
    plt.figure(figsize=(7, 5))

    for gamma, filename in DEFAULT_RUNS:
        radii, values = load_rdf(Path(filename))
        plt.plot(radii, values, label=f"gamma={gamma:g}", linewidth=1.5)

    plt.xlabel("r (A)")
    plt.ylabel("g(r)")
    plt.title("Water Oxygen RDF for Ubiquitin Langevin Runs")
    plt.legend()
    plt.tight_layout()
    plt.savefig("rdf_overlay.pdf", dpi=150)


if __name__ == "__main__":
    main()
