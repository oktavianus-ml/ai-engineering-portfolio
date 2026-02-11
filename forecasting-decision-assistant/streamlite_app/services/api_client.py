import requests

API_URL = "http://127.0.0.1:8000/chat"

def request_forecast(product_name: str, horizon: int):
    message = f"Prediksi penjualan {product_name} {horizon} hari ke depan"

    response = requests.post(
        API_URL,
        json={"message": message},
        timeout=60
    )

    return response.json()
