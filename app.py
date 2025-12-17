import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Imobiliária", layout="wide")

# --- SISTEMA DE LOGIN SIMPLES ---
def check_password():
    """Retorna True se o usuário acertar a senha."""
    
    # Se a senha ainda não foi digitada ou está errada
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Acesso Restrito - Imobiliária")
        password = st.text_input("Digite a senha de acesso", type="password")
        
        # A senha correta está configurada nos 'Segredos' do Streamlit
        if st.button("Entrar"):
            if password == st.secrets["general"]["system_password"]:
                st.session_state["password_correct"] = True
                st.rerun()  # Recarrega a página para entrar
            else:
                st.error("Senha incorreta.")
        return False
    return True

if not check_password():
    st.stop()  # Para a execução aqui se não estiver logado

# --- CONEXÃO COM GOOGLE SHEETS ---
# Usa o cache para não conectar toda vez que alguém clica num botão
@st.cache_resource
def get_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Pega as credenciais dos 'Segredos' do Streamlit
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# --- FUNÇÕES DE DADOS ---
def load_data(client):
    try:
        # Substitua pelo NOME EXATO da sua planilha no Google
        sheet = client.open("Banco_Imoveis_Imobiliaria").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar planilha. Verifique se o nome está correto e se o robô tem acesso. Erro: {e}")
        return pd.DataFrame()

def save_data(client, dados):
    sheet = client.open("Banco_Imoveis_Imobiliaria").sheet1
    sheet.append_row(dados)
    st.success("Imóvel cadastrado com sucesso!")

# --- INTERFACE PRINCIPAL ---
client = get_connection()

st.title("🏢 Gestão de Imóveis")

# Abas para separar Cadastro de Busca
tab1, tab2 = st.tabs(["🔍 Buscar Imóveis", "📝 Novo Cadastro"])

# --- ABA 1: BUSCA E FILTROS ---
with tab1:
    st.header("Biblioteca de Anúncios")
    
    # Botão para atualizar dados manualmente
    if st.button("🔄 Atualizar Tabela"):
        st.cache_data.clear()
        
    df = load_data(client)
    
    if not df.empty:
        # Filtros na barra lateral ou topo
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_bairro = st.text_input("Filtrar por Bairro")
        with col2:
            filtro_quartos = st.text_input("Filtrar por Quartos (ex: 2Q)")
        with col3:
            filtro_valor_max = st.number_input("Valor Máximo", min_value=0.0, value=0.0, step=1000.0)

        # Lógica de Filtragem
        df_filtrado = df.copy()
        
        # Converte a coluna Valor para número para poder filtrar (remove R$ e pontos)
        # Assumindo que no sheets está salvo limpo, mas garantindo:
        df_filtrado['Valor'] = pd.to_numeric(df_filtrado['Valor'], errors='coerce').fillna(0)

        if filtro_bairro:
            df_filtrado = df_filtrado[df_filtrado['Bairro'].astype(str).str.contains(filtro_bairro, case=False)]
        
        if filtro_quartos:
            df_filtrado = df_filtrado[df_filtrado['Quartos'].astype(str).str.contains(filtro_quartos, case=False)]
            
        if filtro_valor_max > 0:
            df_filtrado = df_filtrado[df_filtrado['Valor'] <= filtro_valor_max]

        # Mostra a tabela
        st.dataframe(
            df_filtrado, 
            column_config={
                "Link Drive": st.column_config.LinkColumn("Link Drive"), # Transforma em link clicável
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            hide_index=True,
            use_container_width=True
        )
        st.info("💡 Dica: Para editar um valor, abra a planilha Google Sheets diretamente. As alterações aparecerão aqui após atualizar.")
    else:
        st.warning("Nenhum dado encontrado ou erro na conexão.")

# --- ABA 2: CADASTRO ---
with tab2:
    st.header("Cadastrar Novo Imóvel")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        codigo = col_a.text_input("Código do Anúncio")
        valor = col_b.number_input("Valor (R$)", min_value=0.0, step=100.0)
        
        construtora = col_a.text_input("Nome da Construtora")
        entrega = col_b.text_input("Previsão de Entrega")
        
        bairro = st.text_input("Bairro")
        endereco = st.text_input("Endereço Completo")
        link_drive = st.text_input("Link do Drive (Pasta do Imóvel)")
        
        st.write("Tipologias (Quartos):")
        c1, c2, c3, c4, c5 = st.columns(5)
        flat = c1.checkbox("Flat")
        q1 = c2.checkbox("1 Quarto")
        q2 = c3.checkbox("2 Quartos")
        q3 = c4.checkbox("3 Quartos")
        q4 = c5.checkbox("4+ Quartos")
        
        submitted = st.form_submit_button("Salvar Imóvel")
        
        if submitted:
            if not codigo or not bairro:
                st.error("Código e Bairro são obrigatórios!")
            else:
                # Processar quartos
                lista_quartos = []
                if flat: lista_quartos.append("Flat")
                if q1: lista_quartos.append("1Q")
                if q2: lista_quartos.append("2Q")
                if q3: lista_quartos.append("3Q")
                if q4: lista_quartos.append("4Q+")
                quartos_str = ", ".join(lista_quartos)
                
                # Dados para salvar
                nova_linha = [codigo, valor, quartos_str, bairro, endereco, entrega, construtora, link_drive]
                save_data(client, nova_linha)
