import streamlit as st
import requests
import os
from dotenv import load_dotenv

# 🔥 WAJIB
load_dotenv()

API_URL = os.getenv("FASTAPI_CHAT_URL")

st.title("📈 Sales Forecast Dashboard")

product_id = st.number_input("Product ID", value=6467)
horizon = st.slider("Forecast Horizon (days)", 7, 90, 30)

if st.button("Run Forecast"):
    with st.spinner("Running forecast..."):
        try:
            response = requests.post(
                API_URL,
                json={
                    "message": f"Prediksi penjualan product {product_id} {horizon} hari"
                },
                timeout=60
            )

            if response.status_code != 200:
                st.error(f"API Error {response.status_code}")
            else:
                st.write(response.json().get("response"))

        except Exception as e:
            st.error(str(e))
