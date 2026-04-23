from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path


PLOT_DIR = Path(__file__).parent.parent / "results" / "processed"


def _save(fig: plt.Figure, name: str, out_dir: Path | None = None) -> Path:
    d = out_dir or PLOT_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_depth_comparison(df: pd.DataFrame, out_dir: Path | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for workload, group in df.groupby("workload"):
        for backend, sub in group.groupby("backend"):
            label = f"{workload} / {backend}"
            ax.plot(sub["opt_level"], sub["depth"], marker="o", label=label)
    ax.set_xlabel("Optimization level")
    ax.set_ylabel("Circuit depth")
    ax.set_title("Circuit depth vs. optimization level")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    return _save(fig, "depth_comparison", out_dir)


def plot_two_qubit_gate_count(df: pd.DataFrame, out_dir: Path | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for workload, group in df.groupby("workload"):
        for backend, sub in group.groupby("backend"):
            label = f"{workload} / {backend}"
            ax.plot(sub["opt_level"], sub["two_qubit_gate_count"], marker="s", label=label)
    ax.set_xlabel("Optimization level")
    ax.set_ylabel("Two-qubit gate count")
    ax.set_title("Two-qubit gate count vs. optimization level")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    return _save(fig, "two_qubit_gates", out_dir)


def plot_quality_scores(df: pd.DataFrame, out_dir: Path | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for workload, group in df.groupby("workload"):
        for backend, sub in group.groupby("backend"):
            label = f"{workload} / {backend}"
            ax.plot(sub["opt_level"], sub["quality_score"], marker="^", label=label)
    ax.set_xlabel("Optimization level")
    ax.set_ylabel("Quality score")
    ax.set_title("Output quality vs. optimization level")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, alpha=0.3)
    return _save(fig, "quality_scores", out_dir)


def plot_runtime_comparison(df: pd.DataFrame, out_dir: Path | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot = df.pivot_table(index=["workload", "backend"], columns="opt_level", values="runtime_s", aggfunc="mean")
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("Workload / Backend")
    ax.set_ylabel("Runtime (s)")
    ax.set_title("Runtime by workload, backend, and optimization level")
    ax.legend(title="Opt level", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=30, ha="right")
    return _save(fig, "runtime_comparison", out_dir)


def plot_output_distribution(counts: dict[str, int], title: str = "", out_dir: Path | None = None, name: str = "distribution") -> Path:
    total = sum(counts.values())
    labels = list(counts.keys())
    probs = [v / total for v in counts.values()]
    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 0.4), 4))
    ax.bar(labels, probs)
    ax.set_xlabel("Bitstring")
    ax.set_ylabel("Probability")
    ax.set_title(title or "Output distribution")
    plt.xticks(rotation=90, fontsize=7)
    ax.grid(True, alpha=0.3, axis="y")
    return _save(fig, name, out_dir)


def generate_all_plots(df: pd.DataFrame, out_dir: Path | None = None) -> list[Path]:
    return [
        plot_depth_comparison(df, out_dir),
        plot_two_qubit_gate_count(df, out_dir),
        plot_quality_scores(df, out_dir),
        plot_runtime_comparison(df, out_dir),
    ]
