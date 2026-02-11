class IntentClassifier:
    def classify(self, text: str) -> str:
        text = text.lower().strip()

        # 1️⃣ greeting (HARUS PALING ATAS)
        if any(k in text for k in [
            "halo", "hai", "hi", "hello",
            "selamat pagi", "selamat siang", "selamat malam"
        ]):
            return "greeting"

        # 2️⃣ forecast
        if any(k in text for k in [
            "prediksi", "forecast", "ramalan"
        ]):
            return "forecast"

        # 3️⃣ chart
        if any(k in text for k in [
            "grafik", "chart", "trend"
        ]):
            return "chart"

        # 4️⃣ fallback
        return "general"
