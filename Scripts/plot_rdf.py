"""Plot radial distribution functions for each Langevin gamma run."""

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


RUNS = [
    (0.1, "rdf_gamma01.dat", "blue"),
    (1.0, "rdf_gamma1.dat", "orange"),
    (5.0, "rdf_gamma5.dat", "green"),
    (50.0, "rdf_gamma50.dat", "red"),
    (200.0, "rdf_gamma200.dat", "purple"),
]


def main() -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    plotted = 0

    for gamma, filename, color in RUNS:
        path = Path(filename)
        if not path.exists():
            print(f"  Skipping gamma={gamma:g}: {filename} not found")
            continue

        data = np.loadtxt(path)
        if data.ndim != 2 or data.shape[1] < 2:
            print(f"  Skipping gamma={gamma:g}: {filename} has unexpected format")
            continue

        radii = data[:, 0]
        g_of_r = data[:, 1]

        ax.plot(
            radii,
            g_of_r,
            label=f"gamma = {gamma:g} ps^-1",
            color=color,
            alpha=0.85,
            linewidth=1.4,
        )
        plotted += 1

    if plotted == 0:
        raise SystemExit("No RDF .dat files were found to plot.")

    ax.axhline(
        1.0,
        color="black",
        linestyle="--",
        linewidth=0.8,
        alpha=0.5,
        label="g(r) = 1",
    )
    ax.set_xlabel("r (A)", fontsize=13)
    ax.set_ylabel("g(r)", fontsize=13)
    ax.set_title(
        "Water O-O Radial Distribution Function\n"
        "vs. Langevin Damping Coefficient",
        fontsize=13,
    )
    ax.legend(fontsize=10)
    ax.set_xlim(0, 12)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig("rdf_comparison.pdf", dpi=150)
    plt.savefig("rdf_comparison.png", dpi=150)
    print("Saved rdf_comparison.pdf and rdf_comparison.png")


if __name__ == "__main__":
    main()
