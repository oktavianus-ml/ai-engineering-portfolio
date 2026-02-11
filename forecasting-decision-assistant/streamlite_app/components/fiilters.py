import streamlit as st

def render_filters():
    product_name = st.text_input(
        "Nama Produk",
        value="CNI Ginseng Coffee"
    )

    horizon = st.slider(
        "Horizon Prediksi (hari)",
        min_value=7,
        max_value=90,
        value=14
    )

    return product_name, horizon
