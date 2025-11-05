import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# CONFIGURAÇÕES DO GITHUB
REPO_USER = "Sgnsilv" 
REPO_NAME = "festival_map"  
BRANCH = "main"             

# FUNÇÃO PARA GERAR LINK DE IMAGEM NO GITHUB RAW
def make_img_tag_url(img_filename, width=170):
    if pd.isna(img_filename) or not str(img_filename).strip():
        return ""
    # Se não tiver extensão, adiciona .jpg por padrão
    if not any(img_filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
        img_filename += ".jpg"
    url = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/{BRANCH}/images/{img_filename}"
    return f"<img src='{url}' width='{width}' style='margin-top:5px; border-radius:8px;'/>"

# LEITURA DOS DADOS
df = pd.read_csv("dados_festival.csv")

# GEOCODIFICAÇÃO AUTOMÁTICA (caso ainda não tenha lat/lon)
geolocator = Nominatim(user_agent="festival_map")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

if "latitude" not in df.columns or "longitude" not in df.columns:
    st.info("Convertendo endereços em coordenadas... Isso pode levar alguns minutos na primeira vez.")
    df["endereco_completo"] = df["rua"] + ", " + df["bairro"] + ", Natal, RN, Brasil"
    df["local"] = df["endereco_completo"].apply(geocode)
    df["latitude"] = df["local"].apply(lambda loc: loc.latitude if loc else None)
    df["longitude"] = df["local"].apply(lambda loc: loc.longitude if loc else None)
    df.to_csv("dados_festival_geo.csv", index=False)
else:
    st.success("Coordenadas já existentes na planilha!")

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Mapa dos Festivais de Natal", layout="wide")
st.title("🍰🍔 Mapa dos Festivais Gastronômicos de Natal")
st.caption("Sweet Coffee Week & Sigablend Festival - 6 a 16 de novembro")

# FILTROS LATERAIS
st.sidebar.header("Filtros")
festivais = st.sidebar.multiselect("Festival", options=df["festival"].unique(), default=df["festival"].unique())
tempos = st.sidebar.multiselect("Tipo de refeição", options=df["tempo"].unique(), default=df["tempo"].unique())
quero_ir = st.sidebar.multiselect("Nível de interesse", options=[1, 2, 3], default=[1, 2, 3])

# FILTRAR DADOS
filtro = (df["festival"].isin(festivais)) & (df["tempo"].isin(tempos)) & (df["quero_ir"].isin(quero_ir))
df_filtrado = df[filtro]

# MAPA CENTRALIZADO EM NATAL
mapa = folium.Map(location=[-5.7945, -35.211], zoom_start=12)

# CORES BASEADAS NO NÍVEL DE INTERESSE
cores = {1: "red", 2: "orange", 3: "green"}

# ADICIONAR PONTOS AO MAPA
for _, r in df_filtrado.iterrows():
    if pd.isna(r["latitude"]) or pd.isna(r["longitude"]):
        continue

    # Ícone de acordo com o festival
    if "sweet" in r["festival"].lower():
        icon = "cupcake"  # ícone doce
    else:
        icon = "hamburger"  # ícone hambúrguer

    # HTML do popup
    img_tag = make_img_tag_url(str(r["imagem"]))
    popup_html = f"""
    <b>{r['nome']}</b><br>
    <b>Festival:</b> {r['festival']}<br>
    <b>Tempo:</b> {r['tempo']}<br>
    <b>Horário:</b> {r['horario']}<br>
    <b>Tema:</b> {r['tema']}<br>
    {img_tag}
    """

    folium.Marker(
        location=[r["latitude"], r["longitude"]],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=cores.get(r["quero_ir"], "blue"), icon="cutlery", prefix="fa"),
    ).add_to(mapa)

# CAMPO PARA ESCOLHER LOCAL DE REFERÊNCIA
st.sidebar.markdown("### 📍 Escolher ponto de referência")
referencia = st.sidebar.text_input("Digite um endereço ou ponto conhecido em Natal:")

if referencia:
    local_ref = geocode(referencia + ", Natal, RN, Brasil")
    if local_ref:
        st.sidebar.success(f"Local encontrado: {local_ref.address}")
        folium.Marker(
            [local_ref.latitude, local_ref.longitude],
            icon=folium.Icon(color="blue", icon="star"),
            popup="📍 Ponto de referência",
        ).add_to(mapa)

        # Calcular o mais próximo
        df_filtrado["distancia"] = ((df_filtrado["latitude"] - local_ref.latitude)**2 + 
                                    (df_filtrado["longitude"] - local_ref.longitude)**2)**0.5
        mais_proximo = df_filtrado.loc[df_filtrado["distancia"].idxmin()]
        st.sidebar.markdown(f"**Mais próximo:** {mais_proximo['nome']} ({mais_proximo['festival']})")
    else:
        st.sidebar.error("Endereço não encontrado.")

# MOSTRAR MAPA
st_folium(mapa, width=1000, height=600)
