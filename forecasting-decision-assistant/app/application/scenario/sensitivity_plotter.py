import matplotlib
matplotlib.use("Agg")  # ⬅️ WAJIB (non-GUI backend)
import matplotlib.pyplot as plt
from pathlib import Path


class SensitivityPlotter:
    """
    Membuat grafik sensitivity analysis
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot(self, product_code: str, sensitivity_results: list) -> Path | None:
        if not sensitivity_results:
            return None

        deltas = [r["delta"] * 100 for r in sensitivity_results]
        actions = [r["action"] for r in sensitivity_results]

        # mapping action → numeric (biar bisa diplot)
        action_map = {
            "DELAY": 0,
            "HOLD": 1,
            "REORDER": 2,
            "REORDER_NOW": 3,
        }
        y = [action_map.get(a, 0) for a in actions]

        plt.figure(figsize=(6, 4))
        plt.plot(deltas, y, marker="o")
        plt.xlabel("Demand Change (%)")
        plt.ylabel("Decision Level")
        plt.title("Sensitivity Analysis – Decision Threshold")
        plt.grid(True)

        path = self.output_dir / f"{product_code}_sensitivity.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.close()

        return path
