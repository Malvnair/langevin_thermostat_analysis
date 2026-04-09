"""Create a zoomed energy/temperature plot for the Langevin gamma runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from analyze_langevin_energies import (
    DEFAULT_RUNS,
    filter_production_region,
    parse_namd_log,
)

import matplotlib.pyplot as plt


PLOTS = [
    ("TEMP", "Temperature (K)", (280, 310)),
    ("TOTAL", "Total Energy (kcal/mol)", (-50800, -49600)),
    ("KINETIC", "Kinetic Energy (kcal/mol)", (11700, 12400)),
    ("POTENTIAL", "Potential Energy (kcal/mol)", (-62750, -61700)),
]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot zoomed NAMD Langevin thermostat energy traces."
    )
    parser.add_argument(
        "--output-pdf",
        default="energies_vs_gamma_zoomed.pdf",
        help="Output PDF filename.",
    )
    parser.add_argument(
        "--output-png",
        default="energies_vs_gamma_zoomed.png",
        help="Output PNG filename.",
    )
    parser.add_argument(
        "--timestep-fs",
        type=float,
        default=2.0,
        help="Simulation timestep in fs.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    timestep_ps = args.timestep_fs * 1e-3

    results = {}
    skipped = []
    for gamma, filename in DEFAULT_RUNS:
        path = Path(filename)
        if not path.exists():
            skipped.append((gamma, f"missing file: {filename}"))
            continue

        try:
            results[gamma] = filter_production_region(parse_namd_log(path))
        except ValueError as exc:
            skipped.append((gamma, str(exc)))

    if not results:
        raise ValueError("No valid NAMD ENERGY logs were found.")

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    for ax, (prop, ylabel, ylim) in zip(axes.flat, PLOTS):
        for gamma, _ in DEFAULT_RUNS:
            if gamma not in results:
                continue

            dataset = results[gamma]
            time_ps = dataset["STEP"] * timestep_ps
            ax.plot(time_ps, dataset[prop], label=f"gamma={gamma:g}", alpha=0.85)

        ax.set_xlabel("Time (ps)")
        ax.set_ylabel(ylabel)
        ax.set_ylim(*ylim)
        ax.legend(fontsize=8)

        if prop == "TEMP":
            ax.axhline(300, color="black", linestyle="--", linewidth=0.8, alpha=0.5)

    fig.suptitle("Zoomed Thermodynamic Traces vs. Langevin Damping", fontsize=14)
    plt.tight_layout()
    plt.savefig(args.output_pdf, dpi=150)
    plt.savefig(args.output_png, dpi=150)


    print(f"Saved figure to {args.output_pdf}")
    print(f"Saved figure to {args.output_png}")


if __name__ == "__main__":
    main()
