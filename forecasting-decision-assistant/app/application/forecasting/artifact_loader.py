from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]

class ArtifactLoader:
    def load(self, horizon: str, product_code: str):
        """
        horizon: 'weekly' | 'monthly' | 'yearly'
        """
        base = ROOT

        meta_path = base / "logs" / horizon / f"{product_code}_meta.json"
        plot_path = base / "plots" / horizon / f"{product_code}_forecast.png"

        meta = json.loads(meta_path.read_text()) if meta_path.exists() else None
        plot = plot_path if plot_path.exists() else None

        return meta, plot