#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
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


ENERGY_KEYS = [
    "STEP",
    "BOND",
    "ANGLE",
    "DIHED",
    "IMPRP",
    "ELECT",
    "VDW",
    "BOUNDARY",
    "MISC",
    "KINETIC",
    "TOTAL",
    "TEMP",
    "POTENTIAL",
    "TOTAL3",
    "TEMPAVG",
]

DEFAULT_RUNS = [
    (0.1, "run_gamma01.log"),
    (1.0, "run_gamma1.log"),
    (5.0, "run_gamma5.log"),
    (50.0, "run_gamma50.log"),
    (200.0, "run_gamma200.log"),
]


def parse_namd_log(filename: Path) -> dict[str, np.ndarray]:
    """Parse NAMD ENERGY lines into numpy arrays."""
    data = {key: [] for key in ENERGY_KEYS}

    with filename.open() as handle:
        for line in handle:
            if not line.startswith("ENERGY:"):
                continue

            fields = line.split()[1:]
            if len(fields) < len(ENERGY_KEYS):
                continue

            for key, value in zip(ENERGY_KEYS, fields):
                data[key].append(float(value))

    if not data["STEP"]:
        raise ValueError(f"No ENERGY lines found in {filename}")

    return {key: np.asarray(values) for key, values in data.items()}


def summarize_equilibrated_region(
    data: dict[str, np.ndarray], skip_fraction: float
) -> dict[str, float]:
    skip = int(len(data["TEMP"]) * skip_fraction)
    trimmed = {key: values[skip:] for key, values in data.items()}

    return {
        "skip_points": skip,
        "temp_mean": trimmed["TEMP"].mean(),
        "temp_std": trimmed["TEMP"].std(),
        "ke_mean": trimmed["KINETIC"].mean(),
        "ke_std": trimmed["KINETIC"].std(),
        "pe_mean": trimmed["POTENTIAL"].mean(),
        "pe_std": trimmed["POTENTIAL"].std(),
        "etot_mean": trimmed["TOTAL"].mean(),
        "etot_std": trimmed["TOTAL"].std(),
    }


def filter_production_region(data: dict[str, np.ndarray]) -> dict[str, np.ndarray]:

    mask = data["TEMP"] > 0
    return {key: values[mask] for key, values in data.items()}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot and summarize NAMD Langevin thermostat runs."
    )
    parser.add_argument(
        "--output",
        default="energies_vs_gamma.pdf",
        help="Output figure filename.",
    )
    parser.add_argument(
        "--summary-csv",
        default="energies_summary.csv",
        help="Output CSV filename for summary statistics.",
    )
    parser.add_argument(
        "--skip-fraction",
        type=float,
        default=0.2,
        help="Fraction of frames to discard as equilibration.",
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

    results: dict[float, dict[str, np.ndarray]] = {}
    summaries: list[dict[str, float]] = []
    skipped: list[tuple[float, str]] = []

    for gamma, filename in DEFAULT_RUNS:
        path = Path(filename)
        if not path.exists():
            skipped.append((gamma, f"missing file: {filename}"))
            continue

        try:
            parsed = parse_namd_log(path)
        except ValueError as exc:
            skipped.append((gamma, str(exc)))
            continue

        production = filter_production_region(parsed)
        if not len(production["TEMP"]):
            skipped.append((gamma, f"no production dynamics found in {filename}"))
            continue

        results[gamma] = production

        summary = summarize_equilibrated_region(results[gamma], args.skip_fraction)
        summary["gamma"] = gamma
        summaries.append(summary)

    if not results:
        raise ValueError("No valid NAMD ENERGY logs were found.")

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    props = ["TEMP", "TOTAL", "KINETIC", "POTENTIAL"]
    ylabels = [
        "Temperature (K)",
        "Total Energy (kcal/mol)",
        "Kinetic Energy (kcal/mol)",
        "Potential Energy (kcal/mol)",
    ]

    timestep_ps = args.timestep_fs * 1e-3

    for ax, prop, ylabel in zip(axes.flat, props, ylabels):
        for gamma, _ in DEFAULT_RUNS:
            if gamma not in results:
                continue
            dataset = results[gamma]
            time_ps = dataset["STEP"] * timestep_ps
            ax.plot(time_ps, dataset[prop], label=f"gamma={gamma:g}", alpha=0.8)

        ax.set_xlabel("Time (ps)")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)

    fieldnames = [
        "gamma",
        "skip_points",
        "temp_mean",
        "temp_std",
        "ke_mean",
        "ke_std",
        "pe_mean",
        "pe_std",
        "etot_mean",
        "etot_std",
    ]

    with Path(args.summary_csv).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print(
        f"{'gamma':>8} {'<T>':>10} {'sigma_T':>10} {'<KE>':>12} "
        f"{'sigma_KE':>10} {'<PE>':>12} {'sigma_PE':>10} {'<Etot>':>12} {'sigma_E':>10}"
    )
    for summary in summaries:
        print(
            f"{summary['gamma']:>8.1f} "
            f"{summary['temp_mean']:>10.2f} {summary['temp_std']:>10.2f} "
            f"{summary['ke_mean']:>12.2f} {summary['ke_std']:>10.2f} "
            f"{summary['pe_mean']:>12.2f} {summary['pe_std']:>10.2f} "
            f"{summary['etot_mean']:>12.2f} {summary['etot_std']:>10.2f}"
        )



if __name__ == "__main__":
    main()
