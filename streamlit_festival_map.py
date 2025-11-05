import streamlit as st
import pandas as pd
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# ---------- Configurações ----------
CSV_FILE = "dados_festival.csv" 
CACHE_FILE = "coords_cache.csv"
IMAGES_FOLDER = "images" 
CITY_CENTER = (-5.7945, -35.2110)  #Natal, RN (aprox.)
DEFAULT_ZOOM = 12

st.set_page_config(page_title="Mapa dos Festivais - Natal", layout="wide")
st.title("Mapa dos Festivais — Sweet Coffee Week ☕🍰 & Sigablend 🍔")

# ---------- Funções utilitárias ----------

def haversine(lon1, lat1, lon2, lat2):
    # cálculo da distância em km entre dois pontos (lon/lat em graus)
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km


def load_data(csv_path):
    df = pd.read_csv(csv_path)
    return df


def load_cache(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["nome","rua","bairro","lat","lon"])


def save_cache(df_cache, path):
    df_cache.to_csv(path, index=False)


@st.cache_data(show_spinner=False)
def geocode_addresses(df):
    # Carrega cache
    cache = load_cache(CACHE_FILE)
    # Inicializa geocodificador
    geolocator = Nominatim(user_agent="festival_map_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

    results = []

    for idx, row in df.iterrows():
        cached = cache[(cache['nome'] == row['nome']) & (cache['rua'] == row['rua'])]
        if not cached.empty:
            lat = float(cached.iloc[0]['lat'])
            lon = float(cached.iloc[0]['lon'])
        else:
            query = f"{row['rua']}, {row['bairro']}, Natal, RN, Brazil"
            try:
                loc = geocode(query)
                if loc:
                    lat = loc.latitude
                    lon = loc.longitude
                    cache = pd.concat([cache, pd.DataFrame([{
                        'nome': row['nome'], 'rua': row['rua'], 'bairro': row['bairro'], 'lat': lat, 'lon': lon
                    }])], ignore_index=True)
                else:
                    lat = None
                    lon = None
            except Exception as e:
                lat = None
                lon = None

        results.append({'nome': row['nome'], 'rua': row['rua'], 'bairro': row['bairro'], 'festival': row.get('festival',''),
                        'horario': row.get('horario',''), 'quero_ir': row.get('quero_ir', ''), 'imagem': row.get('imagem',''),
                        'tema': row.get('tema',''), 'tempo': row.get('tempo',''), 'lat': lat, 'lon': lon})

    save_cache(cache, CACHE_FILE)
    return pd.DataFrame(results)


def build_map(df_points, center=CITY_CENTER, zoom=DEFAULT_ZOOM, ref_point=None, highlight_idx=None):
    m = folium.Map(location=center, zoom_start=zoom)

    # adiciona cada ponto
    for idx, r in df_points.iterrows():
        if pd.isna(r['lat']) or pd.isna(r['lon']):
            continue

        # escolha do emoji conforme festival
        fest = str(r.get('festival','')).lower()
        if 'sweet' in fest or 'coffee' in fest:
            emoji = '🍰'
        else:
            emoji = '🍔'

        # cor do marcador conforme quero_ir
        color_map = {'1': 'red', '2': 'orange', '3': 'green', 1: 'red', 2: 'orange', 3: 'green'}
        color = color_map.get(r.get('quero_ir'), 'blue')

        # popup HTML com imagem (assumindo pasta images no projeto)
        img_tag = ''
        if pd.notna(r.get('imagem','')) and str(r.get('imagem')).strip() != '':
            img_path = os.path.join(IMAGES_FOLDER, str(r['imagem']))
            if os.path.exists(img_path):
                img_tag = f"<img src='{img_path}' width='170'/>"
            else:
                img_tag = f"<div><small>Imagem: {r.get('imagem')}</small></div>"

        popup_html = f"""
        <div style='width:220px'>
          <h4 style='margin:0'>{r.get('nome')}</h4>
          <p style='margin:0'><b>Festival:</b> {r.get('festival')}<br>
          <b>Tempo:</b> {r.get('tempo')}<br>
          <b>Horário:</b> {r.get('horario')}<br>
          <b>Tema:</b> {r.get('tema')}</p>
          {img_tag}
        </div>
        """

        # marcador com emoji via DivIcon
        icon = folium.DivIcon(html=f"<div style='font-size:26px; filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.4))'>{emoji}</div>")

        folium.Marker(location=(r['lat'], r['lon']), popup=folium.Popup(popup_html, max_width=260), icon=icon).add_to(m)

        # adicionar um círculo pequeno colorido indicando a prioridade (quero_ir)
        folium.CircleMarker(location=(r['lat'], r['lon']), radius=6, color=color, fill=True, fill_opacity=0.9).add_to(m)

    # se houver ponto de referência escolhido, adiciona marcador e destaca o mais próximo
    if ref_point:
        folium.Marker(location=ref_point, popup='Ponto de referência', icon=folium.Icon(color='blue', icon='star')).add_to(m)
        if highlight_idx is not None and highlight_idx in df_points.index:
            r = df_points.loc[highlight_idx]
            folium.PolyLine(locations=[ref_point, (r['lat'], r['lon'])], color='blue', weight=2.5, opacity=0.7).add_to(m)
            # marcador destacado
            folium.CircleMarker(location=(r['lat'], r['lon']), radius=12, color='blue', fill=True, fill_opacity=0.5).add_to(m)

    return m


# ---------- Carregando dados e geocodificação ----------
if not os.path.exists(CSV_FILE):
    st.error(f"Arquivo CSV não encontrado: {CSV_FILE}. Coloque seu arquivo na raiz do projeto e atualize o nome se necessário.")
    st.stop()

raw_df = load_data(CSV_FILE)
with st.spinner('Geocodificando endereços (pode demorar alguns segundos)...'):
    df = geocode_addresses(raw_df)

# filtra apenas pontos com coordenadas válidas para o mapa
df_points = df.dropna(subset=['lat','lon']).reset_index(drop=True)

# ---------- Barra lateral (filtros e controles) ----------
st.sidebar.header('Filtros e controles')
festival_opts = ['Todos'] + sorted(raw_df['festival'].dropna().unique().tolist())
sel_festival = st.sidebar.selectbox('Festival', festival_opts)

# tipo de refeição: usamos a coluna `tempo` (ela pode ter valores separados por vírgula)
all_tipos = set()
for t in raw_df['tempo'].dropna().astype(str):
    for part in [p.strip() for p in t.split(',')]:
        if part:
            all_tipos.add(part)
all_tipos = sorted(list(all_tipos))
sel_tipos = st.sidebar.multiselect('Tipo de refeição (tempo)', ['Todos'] + all_tipos, default=['Todos'])

sel_quero = st.sidebar.multiselect('Quero ir (prioridade)', ['1','2','3'], default=['1','2','3'])

sel_bairro = st.sidebar.text_input('Filtrar por bairro (parte do nome)')

# referência escolhida pelo usuário (texto)
st.sidebar.markdown('---')
ref_text = st.sidebar.text_input('Escolha um ponto de referência (ex: UFRN, Ponta Negra, Midway)')

# botão para aplicar filtros
if st.sidebar.button('Aplicar filtros'):
    pass

# ---------- Aplicando filtros ----------
filtered = df_points.copy()
if sel_festival != 'Todos':
    filtered = filtered[filtered['festival'] == sel_festival]

if not ('Todos' in sel_tipos):
    # seleciona linhas cujo campo tempo contenha ao menos um dos tipos escolhidos
    mask = filtered['tempo'].fillna('').apply(lambda s: any(t.lower() in s.lower() for t in sel_tipos))
    filtered = filtered[mask]

if sel_quero:
    filtered = filtered[filtered['quero_ir'].astype(str).isin(sel_quero)]

if sel_bairro.strip() != '':
    filtered = filtered[filtered['bairro'].fillna('').str.contains(sel_bairro, case=False)]

# recalcula index para referência
filtered = filtered.reset_index(drop=True)

# ---------- Ponto de referência (geocodificar o texto digitado pelo usuário) ----------
ref_point = None
nearest_idx = None
if ref_text and ref_text.strip() != '':
    geolocator = Nominatim(user_agent="festival_map_app")
    try:
        loc = geolocator.geocode(f"{ref_text}, Natal, RN, Brazil")
        if loc:
            ref_point = (loc.latitude, loc.longitude)
            # calcula qual ponto está mais perto
            min_dist = None
            for idx, r in filtered.iterrows():
                d = haversine(ref_point[1], ref_point[0], r['lon'], r['lat'])
                if min_dist is None or d < min_dist:
                    min_dist = d
                    nearest_idx = idx
    except Exception:
        ref_point = None

# ---------- Construir mapa e exibir ----------
col1, col2 = st.columns([3,1])
with col1:
    st.subheader('Mapa — Natal')
    m = build_map(filtered, center=CITY_CENTER, zoom=DEFAULT_ZOOM, ref_point=ref_point, highlight_idx=nearest_idx)
    st_data = st_folium(m, width=900, height=700)

with col2:
    st.subheader('Lista e detalhes')
    st.markdown(f"**Total exibidos:** {len(filtered)}")
    if nearest_idx is not None:
        st.markdown('**Mais próximo do ponto escolhido:**')
        r = filtered.loc[nearest_idx]
        st.markdown(f"- **{r['nome']}** — {r['festival']} — {r['tempo']} — {r['horario']}")
        if pd.notna(r['imagem']) and str(r['imagem']).strip() != '':
            img_path = os.path.join(IMAGES_FOLDER, str(r['imagem']))
            if os.path.exists(img_path):
                st.image(img_path, width=240)
    st.markdown('---')
    # lista curta dos restaurantes filtrados
    for idx, r in filtered.iterrows():
        st.markdown(f"**{r['nome']}** — {r['festival']} — {r['tempo']} — Quero ir: {r['quero_ir']}")
        if pd.notna(r['imagem']) and str(r['imagem']).strip() != '':
            img_path = os.path.join(IMAGES_FOLDER, str(r['imagem']))
            if os.path.exists(img_path):
                st.image(img_path, width=200)
        st.markdown('---')

    