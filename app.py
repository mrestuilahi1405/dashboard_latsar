import streamlit as st
import pandas as pd
import json
import os
import datetime
from streamlit_echarts import st_echarts, JsCode, Map

# ==============================================================================
# 1. KONFIGURASI HALAMAN & ENGINES TEMA PREMIUM (CARD-BASED UI)
# ==============================================================================
st.set_page_config(page_title="Dashboard Eksekutif BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"
COLORS = ['#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6', '#14B8A6']

# CSS Tingkat Lanjut untuk mewujudkan Card-Based Layout dan Desain Border Presisi
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
[data-testid="stHeader"] {background-color: transparent !important;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 96% !important;}
[data-testid="stMetricValue"] {font-weight: 900 !important; font-size: 2.2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1.1rem !important; font-weight: 600;}

/* Komponen Card Kontainer ala Dashboard Foto Referensi */
.chart-card {
    background-color: color-mix(in srgb, var(--text-color) 3%, transparent);
    border: 1px solid color-mix(in srgb, var(--text-color) 10%, transparent);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
.card-title {
    font-size: 1.1rem;
    font-weight: 800;
    margin-bottom: 15px;
    border-bottom: 2px solid color-mix(in srgb, var(--text-color) 8%, transparent);
    padding-bottom: 8px;
}
.insight-box {
    background-color: color-mix(in srgb, var(--text-color) 6%, transparent);
    border-left: 5px solid #3B82F6;
    padding: 15px; 
    border-radius: 4px; 
    margin-bottom: 20px;
}
.insight-title {font-weight: 800; margin-bottom: 5px; font-size: 1rem;}
.insight-text {font-size: 0.95rem; line-height: 1.5;}
</style>
""", unsafe_allow_html=True)

FMT_ID = JsCode("""
function(params) {
    if (Array.isArray(params)) {
        let res = '<b>' + params[0].name + '</b>';
        for (let i = 0; i < params.length; i++) {
            let val = Number(params[i].value).toLocaleString('id-ID');
            res += '<br/>' + params[i].marker + params[i].seriesName + ': <b>' + val + '</b>';
        }
        return res;
    } else {
        let val = Number(params.value).toLocaleString('id-ID');
        let sName = params.seriesName ? params.seriesName : '';
        return '<b>' + params.name + '</b><br/>' + params.marker + sName + ': <b>' + val + '</b>';
    }
}
""")

# ==============================================================================
# 2. INGESTI DATA & GEOSPASIAL
# ==============================================================================
def clean_numeric(val):
    if pd.isna(val): return 0.0
    v = str(val).strip().replace(' ', '')
    if v.lower() in ['nan', 'none', 'null', '-']: return 0.0
    if ',' in v and '.' in v: v = v.replace(',', '')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        for col in df.columns:
            if col not in ['kecamatan', 'sektor', 'komoditas', 'bulan']: df[col] = df[col].apply(clean_numeric)
        return df
    except: return pd.DataFrame()

@st.cache_data
def load_geojson():
    if os.path.exists("tanah_laut.geojson"):
        with open("tanah_laut.geojson", "r", encoding="utf-8") as f: return json.load(f)
    return None

def download_csv(df, filename):
    st.download_button("📥 Unduh CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=filename, mime='text/csv', use_container_width=True)

with st.spinner("Sinkronisasi Database BPS..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")
    geo_data = load_geojson()

# ==============================================================================
# 3. SIDEBAR & THEME ENGINE (MENGADOPSI NAVIGASI GRANULAR FOTO REFERENSI)
# ==============================================================================
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="150" style="background-color:rgba(255,255,255,0.8); padding:10px; border-radius:8px;"></div>', unsafe_allow_html=True)
    
    st.markdown("### 🎨 Pengaturan")
    tema_gelap = st.toggle("🌙 Mode Gelap (Dark Mode)", value=False)
    e_theme = "dark" if tema_gelap else "light"
    
    st.markdown("---")
    st.markdown("### 🧭 Menu Utama")
    # Memecah menu menjadi item granular persis seperti struktur aplikasi di foto
    menu = st.sidebar.radio(
        "Navigasi", 
        ["Ringkasan Eksekutif", "Pertumbuhan Ekonomi", "Struktur PDRB", "Analisis Portofolio", "Demografi Wilayah", "Sektor Pertanian"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    min_year = int(df_demo['tahun'].min()) if not df_demo.empty else 2010
    curr_year = datetime.datetime.now().year
    f_tahun = st.slider("Rentang Evaluasi", min_year, curr_year, (min_year, curr_year), label_visibility="collapsed")

# Injeksi CSS Tema Dinamis
if tema_gelap:
    st.markdown("""<style>
    .stApp { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMarkdownContainer"], .card-title { color: #FAFAFA !important; }
    [data-testid="stMetricValue"] { color: #60A5FA !important; }
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
    .stApp { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
    h1, h2, h3, h4, h5, h6, p, label, div[data-testid="stMarkdownContainer"], .card-title { color: #31333F !important; }
    [data-testid="stMetricValue"] { color: #1E3A8A !important; }
    </style>""", unsafe_allow_html=True)

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty: return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

# ==============================================================================
# 4. ROUTING HALAMAN CORE DASHBOARD
# ==============================================================================

# --- HALAMAN 1: RINGKASAN EKSEKUTIF ---
if menu == "Ringkasan Eksekutif":
    st.title("📊 Ringkasan Indikator Makro Utama")
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf]):
        c_dem = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun').iloc[-1]
        c_kes = df_kes.sort_values('tahun').iloc[-1]
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        pe_growth = ((df_pe.iloc[-1]['nilai_adhk'] - df_pe.iloc[-2]['nilai_adhk']) / df_pe.iloc[-2]['nilai_adhk']) * 100
        
        # Penataan KPI Block ala Enterprise
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kemiskinan (P0)", f"{c_kes['p0']:g}%", border=True)
        m2.metric("IPM", f"{c_kes['ipm']:.2f}", border=True)
        m3.metric("Pertumbuhan Ekonomi", f"{pe_growth:.2f}%", border=True)
        m4.metric("Pengangguran (TPT)", f"{c_dem['tpt']:g}%", border=True)
        
        st.markdown(f"""<div class='insight-box'><div class='insight-title'>💡 Sintesis Eksekutif</div><div class='insight-text'>Kabupaten Tanah Laut mencatatkan pertumbuhan ekonomi sebesar <b>{pe_growth:.2f}%</b> dengan tingkat kemiskinan makro terkendali pada level <b>{c_kes['p0']}%</b>. Indeks Pembangunan Manusia kokoh di level <b>{c_kes['ipm']}</b>.</div></div>""", unsafe_allow_html=True)

# --- HALAMAN 2: PERTUMBUHAN EKONOMI (BENCHMARKING MASIF SEPERTI DI FOTO) ---
elif menu == "Pertumbuhan Ekonomi":
    st.title("📈 Analisis Pertumbuhan Ekonomi & Benchmarking")
    df_f = apply_filter(df_pdrb)
    if not df_f.empty:
        df_pe = df_f.groupby('tahun', as_index=False).agg({'nilai_adhk':'sum', 'pe_kalsel':'mean'})
        df_pe['pe_tala'] = df_pe['nilai_adhk'].pct_change() * 100
        df_pe = df_pe.dropna()
        
        # Menerapkan struktur asimetris: Grafik Utama berdampingan dengan Tabel Share Data Teknis
        c_graph, c_table = st.columns([2.2, 1])
        
        with c_graph:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Tren Pertumbuhan YoY: Tanah Laut vs Provinsi</div>""", unsafe_allow_html=True)
            bench_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "axis"},
                "legend": {"top": "top"},
                "xAxis": {"type": "category", "data": df_pe['tahun'].astype(int).astype(str).tolist()},
                "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
                "series": [
                    {"name": "Kab. Tanah Laut", "type": "bar", "data": df_pe['pe_tala'].round(2).tolist(), "itemStyle": {"color": COLORS[0]}},
                    {"name": "Prov. Kalimantan Selatan", "type": "line", "data": df_pe['pe_kalsel'].tolist(), "itemStyle": {"color": COLORS[1]}, "lineStyle": {"width": 3}, "symbolSize": 8}
                ]
            }
            st_echarts(options=bench_opts, height="400px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_table:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Matriks Pembanding Regional</div>""", unsafe_allow_html=True)
            df_disp = df_pe[['tahun', 'pe_tala', 'pe_kalsel']].copy().rename(columns={'tahun':'Tahun', 'pe_tala':'Tala (%)', 'pe_kalsel':'Kalsel (%)'})
            st.dataframe(df_disp.sort_values('Tahun', ascending=False), use_container_width=True, hide_index=True)
            download_csv(df_pe, "benchmarking_pe.csv")
            st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN 3: STRUKTUR PDRB SEXTORAL (CROSS FILTERING & TREEMAP) ---
elif menu == "Struktur PDRB":
    st.title("💰 Struktur Produk Domestik Regional Bruto (PDRB)")
    df_f = apply_filter(df_pdrb)
    if not df_f.empty:
        t_max = df_f['tahun'].max()
        df_latest = df_f[df_f['tahun'] == t_max].sort_values('nilai_adhb', ascending=False)
        
        c_bar, c_tree = st.columns([1.2, 1])
        with c_bar:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Pangsa Lapangan Usaha ({int(t_max)})</div>""", unsafe_allow_html=True)
            bar_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                "grid": {"left": "35%", "bottom": "10%"},
                "xAxis": {"type": "value", "show": False},
                "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}},
                "series": [{"type": "bar", "data": df_latest['nilai_adhb'].tolist()[::-1], "itemStyle": {"color": COLORS[0]}]}]
            }
            bar_click = st_echarts(options=bar_opts, height="380px", key="pdrb_bar_enterprise", on_select="rerun", selection_mode="points", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_tree:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Visualisasi Treemap Komposisi</div>""", unsafe_allow_html=True)
            tree_data = [{"name": s, "value": v} for s, v in zip(df_latest['sektor'], df_latest['nilai_adhb'])]
            tree_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"formatter": "{b}: {c}"},
                "series": [{"type": "treemap", "data": tree_data, "roam": False, "label": {"show": True, "formatter": "{b}"}, "color": COLORS}]
            }
            st_echarts(options=tree_opts, height="380px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)

        # Deep-Dive tren historis berdasarkan sektor yang diklik user
        sel_sektor = df_latest.iloc[0]['sektor']
        if bar_click and "selection" in bar_click and bar_click["selection"].get("point_indices"):
            sel_sektor = df_latest['sektor'].tolist()[::-1][bar_click["selection"]["point_indices"][0]]
            
        df_tren = df_f[df_f['sektor'] == str(sel_sektor)].sort_values('tahun')
        st.markdown(f"""<div class='chart-card'><div class='card-title'>Dinamika Historis Sektor: {sel_sektor}</div>""", unsafe_allow_html=True)
        line_opts = {
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "formatter": FMT_ID},
            "xAxis": {"type": "category", "data": df_tren['tahun'].astype(int).astype(str).tolist()},
            "yAxis": {"type": "value", "axisLabel": {"formatter": JsCode("function(v){return (v/1000000).toFixed(1) + ' T'}")}},
            "series": [{"type": "line", "smooth": True, "data": df_tren['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}}]
        }
        st_echarts(options=line_opts, height="300px", theme=e_theme)
        st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN 4: ANALISIS PORTFOLIO & EARLY WARNING MATRIX ---
elif menu == "Analisis Portofolio":
    st.title("📊 Portfolio Bisnis Sektoral & Peringatan Dini")
    df_f = apply_filter(df_pdrb)
    if not df_f.empty:
        c_quad, c_heat = st.columns([1.2, 1])
        
        with c_quad:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Kuadran Kinerja Sektoral (BCG Model)</div>""", unsafe_allow_html=True)
            t_akhir = df_f['tahun'].max()
            df_now = df_f[df_f['tahun'] == t_akhir].copy()
            df_prev = df_f[df_f['tahun'] == (t_akhir - 1)].copy()
            df_m = pd.merge(df_now, df_prev, on='sektor', suffixes=('_curr', '_prev'))
            
            tot_adhb = df_m['nilai_adhb_curr'].sum()
            true_growth = ((df_m['nilai_adhk_curr'].sum() - df_m['nilai_adhk_prev'].sum()) / df_m['nilai_adhk_prev'].sum()) * 100
            avg_p = 100.0 / len(df_m)
            
            df_m['pangsa'] = (df_m['nilai_adhb_curr'] / tot_adhb) * 100
            df_m['pertumbuhan'] = ((df_m['nilai_adhk_curr'] - df_m['nilai_adhk_prev']) / df_m['nilai_adhk_prev']) * 100
            
            scat_data = [{"name": r['sektor'], "value": [round(r['pangsa'], 2), round(r['pertumbuhan'], 2)]} for _, r in df_m.iterrows()]
            scatter_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "item", "formatter": JsCode("function(p){if(p.componentType==='markLine'){return p.name+': '+Number(p.value).toFixed(2)+'%';}return '<b>'+p.data.name+'</b><br/>Pangsa: '+p.data.value[0]+'%<br/>Growth: '+p.data.value[1]+'%';}")},
                "xAxis": {"type": "value", "name": "Pangsa PDRB (%)", "nameLocation": "middle", "nameGap": 25},
                "yAxis": {"type": "value", "name": "Pertumbuhan (%)", "nameLocation": "middle", "nameGap": 30},
                "series": [{
                    "type": "scatter", "symbolSize": 18, "itemStyle": {"color": COLORS[4], "opacity": 0.8}, "data": scat_data,
                    "label": {"show": True, "formatter": "{b}", "position": "right", "fontSize": 10},
                    "markLine": {"animation": False, "lineStyle": {"type": "dashed", "color": "#7F8C8D"}, "data": [{"xAxis": avg_p, "name": "Batas Pangsa"}, {"yAxis": true_growth, "name": "Laju Daerah"}]}
                }]
            }
            st_echarts(options=scatter_opts, height="400px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_heat:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>🚦 Heatmap Early Warning System</div>""", unsafe_allow_html=True)
            df_piv = df_f.pivot(index='tahun', columns='sektor', values='nilai_adhk').pct_change() * 100
            df_piv = df_piv.dropna().reset_index()
            sektors = [c for c in df_piv.columns if c != 'tahun']
            years = df_piv['tahun'].astype(int).astype(str).tolist()
            heat_data = [[y_idx, s_idx, round(row[s], 2)] for y_idx, row in df_piv.iterrows() for s_idx, s in enumerate(sektors)]
            
            heat_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"position": "top", "formatter": JsCode("function(p){return 'Pertumbuhan: <b>' + p.data[2] + '%</b>'}")},
                "grid": {"top": "5%", "bottom": "15%", "left": "35%"},
                "xAxis": {"type": "category", "data": years},
                "yAxis": {"type": "category", "data": sektors},
                "visualMap": {"min": -5, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%", "inRange": {"color": ["#EF4444", "#FEE2E2", "#3B82F6"]}},
                "series": [{"type": "heatmap", "data": heat_data, "label": {"show": True, "formatter": JsCode("function(p){return p.data[2] + '%'}")}, "itemStyle": {"borderColor": "#fff", "borderWidth": 1}}]
            }
            st_echarts(options=heat_opts, height="400px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN 5: DEMOGRAFI WILAYAH (PETA TEMATIK INTERAKTIF) ---
elif menu == "Demografi Wilayah":
    st.title(":material/group: Potret Kependudukan Spasial")
    df_f = apply_filter(df_demo)
    if not df_f.empty:
        t_akhir = df_f['tahun'].max()
        df_kec = df_f[(df_f['tahun'] == t_akhir) & (df_f['kecamatan'].str.lower() != 'tanah laut')]
        
        c_map, c_details = st.columns([2.5, 1])
        with c_map:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Distribusi Geospasial Penduduk ({int(t_akhir)})</div>""", unsafe_allow_html=True)
            if geo_data:
                map_data = [{"name": r['kecamatan'], "value": r['jumlah_penduduk']} for _, r in df_kec.iterrows()]
                map_opts = {
                    "backgroundColor": "transparent",
                    "tooltip": {"trigger": "item", "formatter": "{b}<br/>Penduduk: <b>{c} Jiwa</b>"},
                    "visualMap": {"min": df_kec['jumlah_penduduk'].min(), "max": df_kec['jumlah_penduduk'].max(), "left": "left", "calculable": True, "inRange": {"color": ["#D4E6F1", "#1E3A8A"]}},
                    "series": [{"type": "map", "map": "TALA_MAP", "roam": True, "data": map_data}]
                }
                st_echarts(options=map_opts, map=Map("TALA_MAP", geo_data), height="480px", theme=e_theme)
            else:
                st.warning("Silakan taruh file 'tanah_laut.geojson' sejajar dengan script ini.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_details:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Data Statistik Sektoral Wilayah</div>""", unsafe_allow_html=True)
            st.dataframe(df_kec[['kecamatan', 'jumlah_penduduk', 'kepadatan']].rename(columns={'kecamatan':'Kecamatan', 'jumlah_penduduk':'Penduduk', 'kepadatan':'Kepadatan/km²'}), use_container_width=True, hide_index=True)
            download_csv(df_kec, "demografi_kecamatan.csv")
            st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN 6: SEKTOR PERTANIAN ---
elif menu == "Sektor Pertanian":
    st.title("🌾 Sektor Pertanian & Ketahanan Pangan")
    df_f = apply_filter(df_pert)
    df_n = apply_filter(df_inf)
    if not df_f.empty and not df_n.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        df_n['periode'] = df_n['bulan'].astype(str) + " " + df_n['tahun'].astype(int).astype(str)
        
        c_padi, c_ntp = st.columns(2)
        with c_padi:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Dinamika Luas Panen vs Produksi Padi</div>""", unsafe_allow_html=True)
            padi_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Ha", "splitLine": {"show":False}}, {"type": "value", "name": "Ton"}],
                "series": [{"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}}, {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}}]
            }
            st_echarts(options=padi_opts, height="400px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_ntp:
            st.markdown(f"""<div class='chart-card'><div class='card-title'>Dinamika Tren Nilai Tukar Petani (NTP)</div>""", unsafe_allow_html=True)
            ntp_opts = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "axis"},
                "dataZoom": [{"type": "inside"}],
                "xAxis": {"type": "category", "data": df_n['periode'].tolist()},
                "yAxis": {"type": "value", "scale": True},
                "series": [{"name": "NTP", "type": "line", "data": df_n['ntp'].tolist(), "itemStyle": {"color": COLORS[1]}, "markLine": {"data": [{"yAxis": 100, "name": "Batas Sejahtera"}], "lineStyle": {"color": COLORS[3]}}}]
            }
            st_echarts(options=ntp_opts, height="400px", theme=e_theme)
            st.markdown("</div>", unsafe_allow_html=True)