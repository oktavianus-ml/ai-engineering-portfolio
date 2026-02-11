import re
import pandas as pd


class ProductResolver:
    def __init__(self, sales_repository, inventory_repository=None):
        self.sales_repo = sales_repository
        self.inventory_repo = inventory_repository

    # =========================
    # PUBLIC
    # =========================
    def resolve(self, text: str):
        df = self.sales_repo.get_all_sales()

        # 1️⃣ product_id (angka eksplisit)
        result = self._resolve_by_product_id(text, df)
        if result:
            return result

        # 2️⃣ product_code (FD01, SV392, dll)
        result = self._resolve_by_product_code(text, df)
        if result:
            return result

        # 3️⃣ product_name (keyword-based)
        result = self._resolve_by_product_name(text, df)
        if result:
            return result

        # 4️⃣ FALLBACK: STOCK ONLY (opsional tapi penting)
        if self.inventory_repo:
            stock_hit = self._resolve_from_stock(text)
            if stock_hit:
                return stock_hit

        return {"status": "not_found"}
    
    # =========================
    # AMBIGUOUS SELECTION
    # =========================
    def resolve_from_candidates(self, candidates, user_input: str):
        user_input = user_input.strip().upper()

        # pilih dengan nomor
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(candidates):
                return {
                    "status": "resolved",
                    **candidates[idx],
                }

        # pilih dengan product_code
        for p in candidates:
            if p["product_code"].upper() == user_input:
                return {
                    "status": "resolved",
                    **p,
                }

        return {"status": "invalid_selection"}

    # =========================
    # RESOLUTION STRATEGIES
    # =========================
    def _resolve_by_product_id(self, text: str, df: pd.DataFrame):
        match = re.search(r"\b\d{3,6}\b", text)
        if not match:
            return None

        product_id = int(match.group())
        hit = df[df["product_id"] == product_id]

        if hit.empty:
            return None

        return self._resolved(hit.iloc[0])

    def _resolve_by_product_code(self, text: str, df: pd.DataFrame):
        match = re.search(r"\b[A-Z]{2,5}\d{1,5}\b", text.upper())
        if not match:
            return None

        product_code = match.group()
        hit = df[df["product_code"].str.upper() == product_code]

        if hit.empty:
            return None

        return self._resolved(hit.iloc[0])

    def _resolve_by_product_name(self, text: str, df: pd.DataFrame):
        query = self._clean_product_text(text)
        if not query:
            return None

        keywords = query.split()

        hits = (
            df[df["product_name"]
               .str.lower()
               .apply(lambda name: all(k in name for k in keywords))
            ][["product_id", "product_code", "product_name"]]
            .drop_duplicates()
            .head(15)
            .reset_index(drop=True)
        )

        if len(hits) == 1:
            return self._resolved(hits.iloc[0])

        if len(hits) > 1:
            return {
                "status": "ambiguous",
                "candidates": hits.to_dict(orient="records"),
            }

        return None

    # =========================
    # STOCK FALLBACK
    # =========================
    def _resolve_from_stock(self, text: str):
        """
        Dipakai kalau produk belum pernah ada sales
        """
        query = self._clean_product_text(text)
        if not query:
            return None

        hit = self.inventory_repo.find_product(query)
        if not hit:
            return None

        return {
            "status": "resolved",
            "product_id": None,
            "product_code": hit["product_code"],
            "product_name": hit["product_name"],
            "source": "stock_only",
        }

    # =========================
    # UTIL
    # =========================
    def _clean_product_text(self, text: str) -> str:
        text = text.lower()

        text = re.sub(r"\d+", " ", text)

        text = re.sub(
            r"\b("
            r"forecast|forecasting|prediksi|prediction|"
            r"hari|day|days|minggu|mingguan|week|weekly|"
            r"bulan|bulanan|month|monthly|"
            r"tahun|tahunan|year|yearly|"
            r"ke|depan"
            r")\b",
            " ",
            text
        )

        return re.sub(r"\s+", " ", text).strip()

    def _resolved(self, row):
        return {
            "status": "resolved",
            "product_id": int(row["product_id"]),
            "product_code": row["product_code"],
            "product_name": row["product_name"],
        }