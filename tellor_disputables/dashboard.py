import streamlit as st
from tellor_disputables.utils import check_password


def dashboard():
    if check_password():
        st.write("🔎 Disputable Values Monitor 🧮")
