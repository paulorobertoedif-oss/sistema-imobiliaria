import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Imobiliária", layout="wide")

# --- SISTEMA DE LOGIN SIMPLES ---
def check_password():
    """Retorna True se o usuário acertar a senha."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Acesso Restrito - Imobiliária")
        password = st.text_input("Digite a senha de acesso", type="password")
        
        if st.button("Entrar"):
            if password == st.secrets["general"]["system_password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

if not check_password():
    st.stop()

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://
