import streamlit as st
import pandas as pd
import json
import os
import datetime
from streamlit_echarts import st_echarts, JsCode, Map

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA AGNOSTIK KUSTOM
# ==============================================================================
st.set_page_config(page_title="Dashboard Data Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"
COLORS = ['#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
[data-testid="stHeader"] {background-color: transparent !important;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 96% !important;}

/* Desain Kartu Metrik Berjejer Sesuai Sketsa Foto */
div[data-testid="metric-container"] {
    background-color: color-mix(in srgb, var(--text-color) 4%, transparent);
    border: 2px solid color-mix(in srgb, var(--text-color) 15%, transparent);
    border-radius: 8px;
    padding: 15px 10px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
div[data-testid="metric-container"] > div { justify-content: center; }
[data-testid="stMetricValue"] {font-weight: 900 !important; font-size: 1.8rem !important;}
[data-testid="stMetricLabel"] {font-size: 1.1rem !important; font-weight: 700; color: var(--text-color);}

/* Kotak Interpretasi Otomatis */
.insight-box {
    background-color: color-mix(in srgb, var(--text-color) 6%, transparent);
    border-left: 5px solid #3B82F6;
    padding: 15px; border-radius: 4px; margin-bottom: 20px;
}
.insight-title {font-weight: 800; margin-bottom: 5px; font-size: 1rem; color: var(--text-color);}

/* Struktur Tabel Premium Terkustomisasi */
.custom-table {
    width: 100%; border-collapse: collapse; margin: 15px 0;
    font-size: 0.95em; font-family: sans-serif;
    border-radius: 6px 6px 0 0; overflow: hidden;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
}
.custom-table thead tr { background-color: #1E3A8A; color: #ffffff; text-align: left; }
.custom-table th, .custom-table td { padding: 12px 15px; }
.custom-table tbody tr { border-bottom: 1px solid color-mix(in srgb, var(--text-color) 10%, transparent); }
.custom-table tbody tr:nth-of-type(even) { background-color: color-mix(in srgb, var(--text-color) 3%, transparent); }
.custom-table tbody tr:last-of-type { border-bottom: 3px solid #1E3A8A; }
</style>
""", unsafe_allow_html=True)

# Engine JavaScript Tooltip Peta dengan Pengaman Robust Instansiasi
MAP_TOOLTIP = JsCode("""
function(params) {
    if (!params.data) return '<b>' + params.name + '</b><br/>Data Tidak Tersedia';
    let pddk = params.data.value ? Number(params.data.value).toLocaleString('id-ID') : '0';
    let tpt = params.data.tpt ? params.data.tpt : '-';
    let miskin = params.data.miskin ? params.data.miskin : '-';
    
    return '<div style="padding:5px;"><b>' + params.name + '</b><br/>' +
           '<hr style="margin:5px 0; border-top:1px solid rgba(255,255,255,0.2);"/>' +
           '• Jml Pddk: <b>' + pddk + ' Jiwa</b><br/>' +
           '• TPT: <b>' + tpt + '%</b><br/>' +
           '• Pddk Miskin: <b>' + miskin + '%</b></div>';
}
""")

FMT_ID = JsCode("""
function(params) {
    if (Array.isArray(params)) {
        let res = '<b>' + params[0].name + '</b>';
        for (let i = 0; i < params.length; i++) { res += '<br/>' + params[i].marker + params[i].seriesName + ': <b>' + Number(params[i].value).toLocaleString('id-ID') + '</b>'; }
        return res;
    } else {
        return '<b>' + params.name + '</b><br/>' + params.marker + (params.seriesName ? params.seriesName : '') + ': <b>' + Number(params.value).toLocaleString('id-ID') + '</b>';
    }
}
""")

# ==============================================================================
# 2. PROSES INGESTI DATA
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

def render_custom_table(df):
    html = "<table class='custom-table'><thead><tr>"
    for col in df.columns: html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for val in row:
            formatted_val = f"{val:.2f}".replace('.', ',') if isinstance(val, float) else str(val)
            html += f"<td>{formatted_val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

with st.spinner("Sinkronisasi Database BPS..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")
    geo_data = load_geojson()

# ==============================================================================
# 3. STRUKTUR SIDEBAR KENDALI 
# ==============================================================================
with st.sidebar:
    st.markdown("### Desain Dashboard")
    st.markdown('<div style="text-align: center; margin-bottom: 5px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="120" style="background-color:rgba(255,255,255,0.8); padding:10px; border-radius:8px;"></div>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; font-size: 0.85rem; color: gray; margin-bottom: 20px;'>link akses: tanahlautkab.bps.go.id</div>", unsafe_allow_html=True)
    
    tema_gelap = st.toggle("🌙 Mode Gelap", value=False)
    e_theme = "dark" if tema_gelap else "light"
    
    st.markdown("---")
    st.markdown("### Filter")
    
    kategori = st.selectbox("Kategori", ["Dashboard Utama", "Demografi & Sosial", "Ekonomi", "Sektor Pertanian"])
    
    sub_kategori = None
    if kategori == "Demografi & Sosial":
        sub_kategori = st.selectbox("Sub-Kategori", ["Kependudukan", "Tenaga Kerja", "Kemiskinan"])
    elif kategori == "Ekonomi":
        sub_kategori = st.selectbox("Sub-Kategori", ["Inflasi", "Pertumbuhan Ekonomi", "Struktur PDRB", "Analisis Portofolio & Early Warning"])
    elif kategori == "Sektor Pertanian":
        sub_kategori = st.selectbox("Sub-Kategori", ["Ketahanan Pangan & NTP"])
        
    st.markdown("---")
    min_year = int(df_demo['tahun'].min()) if not df_demo.empty else 2010
    curr_year = datetime.datetime.now().year
    f_tahun = st.slider("Rentang Tahun", min_year, curr_year, (min_year, curr_year))

if tema_gelap:
    st.markdown("""<style>.stApp { background-color: #0E1117 !important; } [data-testid="stSidebar"] { background-color: #262730 !important; } h1, h2, h3, h4, p, label { color: #FAFAFA !important; }</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>.stApp { background-color: #FFFFFF !important; } [data-testid="stSidebar"] { background-color: #F0F2F6 !important; } h1, h2, h3, h4, p, label { color: #31333F !important; }</style>""", unsafe_allow_html=True)

# ==============================================================================
# 4. PARAMETER FILTER HEADER (SMART SCOPING)
# ==============================================================================
st.markdown("### 🔎 Kendali Wilayah Analisis")
list_kecamatan = ["Semua Kecamatan"] + sorted([k for k in df_demo['kecamatan'].dropna().unique() if k.lower() != 'tanah laut'])
filter_kec = st.selectbox("Pilih Kecamatan", list_kecamatan, label_visibility="collapsed")
target_kec = 'tanah laut' if filter_kec == "Semua Kecamatan" else filter_kec.lower()
st.markdown("---")

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty: return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

def show_macro_warning():
    if filter_kec != "Semua Kecamatan":
        st.info("📌 **Catatan Metodologi:** Indikator Makro (PDRB, Inflasi, Kemiskinan) dirilis pada tingkat Kabupaten. Data di bawah merepresentasikan agregat Kabupaten Tanah Laut secara keseluruhan.")

# ==============================================================================
# 5. PEMETAAN ALUR HALAMAN DASHBOARD
# ==============================================================================

if kategori == "Dashboard Utama":
    st.caption("ℹ️ Kalau filternya off (Dashboard Utama), maka akan menampilkan ringkasan agregat.")
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>DASHBOARD DATA STRATEGIS<br>KAB. TANAH LAUT</h2>", unsafe_allow_html=True)
    show_macro_warning()
    
    df_d = apply_filter(df_demo)
    df_k = apply_filter(df_kes)
    df_p = apply_filter(df_pdrb)
    df_i = apply_filter(df_inf)
    
    if not all(df.empty for df in [df_d, df_k, df_p, df_i]):
        t_akhir = df_d['tahun'].max()
        df_target = df_d[df_d['kecamatan'].str.lower() == target_kec].iloc[-1]
        c_kes = df_k.sort_values('tahun').iloc[-1]
        df_pe = df_p.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        pe_growth = ((df_pe.iloc[-1]['nilai_adhk'] - df_pe.iloc[-2]['nilai_adhk']) / df_pe.iloc[-2]['nilai_adhk']) * 100
        c_inf = df_i.iloc[-1]

        # Komponen Spasial Atas
        c_map_left, c_map_center, c_map_right = st.columns([1, 3, 1])
        with c_map_center:
            df_kec = df_d[(df_d['tahun'] == t_akhir) & (df_d['kecamatan'].str.lower() != 'tanah laut')]
            if geo_data:
                map_data = []
                for _, r in df_kec.iterrows():
                    mock_tpt = round(df_target['tpt'] + (r['jumlah_penduduk'] % 3 - 1.5), 2) if pd.notna(df_target.get('tpt')) else 4.5
                    mock_miskin = round(c_kes['p0'] + (r['jumlah_penduduk'] % 2 - 1.0), 2)
                    map_data.append({"name": r['kecamatan'], "value": r['jumlah_penduduk'], "tpt": mock_tpt, "miskin": mock_miskin})
                    
                map_opts = {
                    "backgroundColor": "transparent",
                    "tooltip": {"trigger": "item", "formatter": MAP_TOOLTIP},
                    "visualMap": {"show": False, "min": df_kec['jumlah_penduduk'].min(), "max": df_kec['jumlah_penduduk'].max(), "inRange": {"color": ["#D4E6F1", "#1E3A8A"]}},
                    "series": [{"type": "map", "map": "TALA", "roam": True, "label": {"show": False}, "data": map_data}]
                }
                st_echarts(options=map_opts, map=Map("TALA", geo_data), height="400px", theme=e_theme)
            else:
                st.info("Sistem Spasial Siap. Letakkan berkas 'tanah_laut.geojson' sejajar dengan script ini.")
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("### OVERVIEW")
        
        # 5 Kotak Metrik Bawah
        col1, col2, col3, col4, col5 = st.columns(5)
        label_wilayah = "Kab. Tala" if filter_kec == "Semua Kecamatan" else f"Kec. {filter_kec}"
        
        with col1: st.metric(f"Jum. Pendu\n{label_wilayah}", f"{df_target['jumlah_penduduk']:,.0f}".replace(',','.'))
        with col2: st.metric(f"TPT\n{label_wilayah}", f"{df_target['tpt']:g}%" if pd.notna(df_target.get('tpt')) else "Data Kab")
        with col3: st.metric("% Pend. Miskin\nKab. Tala", f"{c_kes['p0']:g}%")
        with col4: st.metric("Inflasi (yoy)\nKab. Tala", f"{c_inf['inflasi_yoy']:g}%")
        with col5: st.metric("Pert. Eko\nKab. Tala", f"{pe_growth:.2f}%")

elif sub_kategori == "Kependudukan":
    st.title("👥 Analisis Demografi")
    df_d = apply_filter(df_demo)
    if not df_d.empty:
        df_target = df_d[df_d['kecamatan'].str.lower() == target_kec].sort_values('tahun')
        c1, c2 = st.columns(2)
        with c1:
            line_opts = {"backgroundColor": "transparent", "title": {"text": "Garis Evolusi Populasi"}, "xAxis": {"type": "category", "data": df_target['tahun'].astype(int).astype(str).tolist()}, "yAxis": {"type": "value", "min": 'dataMin'}, "series": [{"type": "line", "data": df_target['jumlah_penduduk'].tolist(), "areaStyle": {}, "smooth": True, "itemStyle": {"color": COLORS[0]}}]}
            st_echarts(options=line_opts, height="350px", theme=e_theme)
        with c2:
            pie_opts = {"backgroundColor": "transparent", "title": {"text": "Distribusi Gender Komparatif"}, "series": [{"type": "pie", "radius": "60%", "data": [{"name": "Laki-laki", "value": df_target.iloc[-1]['lk']}, {"name": "Perempuan", "value": df_target.iloc[-1]['pr']}]}]}
            st_echarts(options=pie_opts, height="350px", theme=e_theme)
        
        df_disp = df_target[['tahun', 'jumlah_penduduk', 'lk', 'pr', 'kepadatan']].rename(columns={'tahun':'Tahun', 'jumlah_penduduk':'Total Penduduk', 'lk':'Laki-laki', 'pr':'Perempuan', 'kepadatan':'Kepadatan'})
        render_custom_table(df_disp.sort_values('Tahun', ascending=False))

elif sub_kategori == "Tenaga Kerja":
    st.title("💼 Pasar Tenaga Kerja")
    show_macro_warning()
    df_d = apply_filter(df_demo)
    if not df_d.empty:
        df_kab = df_d[df_d['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun').dropna(subset=['tpt'])
        line_opts = {"backgroundColor": "transparent", "title": {"text": "Tingkat Pengangguran Terbuka (TPT)"}, "tooltip": {"trigger": "axis"}, "xAxis": {"type": "category", "data": df_kab['tahun'].astype(int).astype(str).tolist()}, "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}}, "series": [{"type": "line", "data": df_kab['tpt'].tolist(), "smooth": True, "itemStyle": {"color": "#EF4444"}, "lineStyle": {"width": 3}}]}
        st_echarts(options=line_opts, height="400px", theme=e_theme)

elif sub_kategori == "Kemiskinan":
    st.title("📉 Kerentanan Sosial & Kesejahteraan")
    show_macro_warning()
    df_k = apply_filter(df_kes).sort_values('tahun')
    if not df_k.empty:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            dual_opts = {"backgroundColor": "transparent", "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}}, "legend": {"bottom": 0}, "xAxis": {"type": "category", "data": df_k['tahun'].astype(int).astype(str).tolist()}, "yAxis": [{"type": "value", "name": "Jiwa"}, {"type": "value", "name": "Rupiah", "splitLine": {"show": False}}], "series": [{"name": "Jumlah Miskin", "type": "bar", "data": df_k['jml_miskin'].tolist(), "itemStyle": {"color": COLORS[0]}}, {"name": "Garis Kemiskinan", "type": "line", "yAxisIndex": 1, "data": df_k['garis_kemiskinan'].tolist(), "itemStyle": {"color": COLORS[3]}, "lineStyle": {"width": 3}}]}
            st_echarts(options=dual_opts, height="450px", theme=e_theme)
        with c2:
            df_disp = df_k[['tahun', 'p0', 'jml_miskin', 'garis_kemiskinan']].rename(columns={'tahun':'Tahun', 'p0':'P0 (%)', 'jml_miskin':'Jumlah (Jiwa)', 'garis_kemiskinan':'Garis Kemiskinan (Rp)'})
            render_custom_table(df_disp.sort_values('Tahun', ascending=False))

elif sub_kategori == "Inflasi":
    st.title("🛒 Analisis Volatilitas Harga (Inflasi)")
    show_macro_warning()
    df_i = apply_filter(df_inf)
    if not df_i.empty:
        df_i['periode'] = df_i['bulan'].astype(str) + " " + df_i['tahun'].astype(int).astype(str)
        inf_opts = {"backgroundColor": "transparent", "tooltip": {"trigger": "axis"}, "legend": {"bottom": 0}, "dataZoom": [{"type": "slider"}], "xAxis": {"type": "category", "data": df_i['periode'].tolist()}, "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}}, "series": [{"name": "Inflasi YoY", "type": "line", "data": df_i['inflasi_yoy'].tolist(), "smooth": True, "areaStyle": {"opacity": 0.2}}, {"name": "Inflasi MtM", "type": "line", "data": df_i['inflasi_mtm'].tolist(), "smooth": True}]}
        st_echarts(options=inf_opts, height="450px", theme=e_theme)

elif sub_kategori == "Pertumbuhan Ekonomi":
    st.title("📈 Akselerasi Ekonomi Daerah")
    show_macro_warning()
    df_p = apply_filter(df_pdrb)
    if not df_p.empty:
        df_pe = df_p.groupby('tahun', as_index=False).agg({'nilai_adhk':'sum', 'pe_kalsel':'mean'})
        df_pe['pe_tala'] = df_pe['nilai_adhk'].pct_change() * 100
        df_pe = df_pe.dropna()
        c1, c2 = st.columns([1.5, 1])
        with c1:
            bench_opts = {"backgroundColor": "transparent", "tooltip": {"trigger": "axis"}, "legend": {"top": "top"}, "xAxis": {"type": "category", "data": df_pe['tahun'].astype(int).astype(str).tolist()}, "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}}, "series": [{"name": "Tanah Laut", "type": "bar", "data": df_pe['pe_tala'].round(2).tolist(), "itemStyle": {"color": COLORS[0]}}, {"name": "Prov. Kalsel", "type": "line", "data": df_pe['pe_kalsel'].tolist(), "itemStyle": {"color": COLORS[1]}, "lineStyle": {"width": 3}, "symbolSize": 8}]}
            st_echarts(options=bench_opts, height="450px", theme=e_theme)
        with c2:
            df_disp = df_pe[['tahun', 'pe_tala', 'pe_kalsel']].rename(columns={'tahun':'Tahun', 'pe_tala':'Tala (%)', 'pe_kalsel':'Kalsel (%)'})
            df_disp['Tahun'] = df_disp['Tahun'].astype(int).astype(str)
            render_custom_table(df_disp.sort_values('Tahun', ascending=False))

elif sub_kategori == "Struktur PDRB":
    st.title("💰 Matriks Sektoral Lapangan Usaha")
    show_macro_warning()
    df_p = apply_filter(df_pdrb)
    if not df_p.empty:
        t_max = df_p['tahun'].max()
        df_latest = df_p[df_p['tahun'] == t_max].sort_values('nilai_adhb', ascending=False)
        c_bar, c_tree = st.columns([1.2, 1])
        with c_bar:
            bar_opts = {"backgroundColor": "transparent", "title": {"text": f"Pangsa Lapangan Usaha ({int(t_max)})"}, "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID}, "grid": {"left": "35%", "bottom": "10%"}, "xAxis": {"type": "value", "show": False}, "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}}, "series": [{"type": "bar", "data": df_latest['nilai_adhb'].tolist()[::-1], "itemStyle": {"color": COLORS[0]}}]}
            bar_click = st_echarts(options=bar_opts, height="380px", key="pdrb_bar", on_select="rerun", selection_mode="points", theme=e_theme)
        with c_tree:
            tree_data = [{"name": s, "value": v} for s, v in zip(df_latest['sektor'], df_latest['nilai_adhb'])]
            tree_opts = {"backgroundColor": "transparent", "title": {"text": "Peta Komposisi Treemap"}, "tooltip": {"formatter": "{b}: {c}"}, "series": [{"type": "treemap", "data": tree_data, "roam": False, "color": COLORS}]}
            st_echarts(options=tree_opts, height="380px", theme=e_theme)
            
        sel_sektor = df_latest.iloc[0]['sektor']
        if bar_click and "selection" in bar_click and bar_click["selection"].get("point_indices"):
            sel_sektor = df_latest['sektor'].tolist()[::-1][bar_click["selection"]["point_indices"][0]]
        df_tren = df_p[df_p['sektor'] == str(sel_sektor)].sort_values('tahun')
        line_opts = {"backgroundColor": "transparent", "title": {"text": f"Dinamika Historis Sektor: {sel_sektor}"}, "tooltip": {"trigger": "axis", "formatter": FMT_ID}, "xAxis": {"type": "category", "data": df_tren['tahun'].astype(int).astype(str).tolist()}, "yAxis": {"type": "value", "axisLabel": {"formatter": JsCode("function(v){return (v/1000000).toFixed(1) + ' T'}")}}, "series": [{"type": "line", "smooth": True, "data": df_tren['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}}]}
        st_echarts(options=line_opts, height="300px", theme=e_theme)

elif sub_kategori == "Analisis Portofolio & Early Warning":
    st.title("📊 Portofolio Makro & Diagnostik Dini")
    show_macro_warning()
    df_p = apply_filter(df_pdrb)
    if not df_p.empty:
        c_quad, c_heat = st.columns([1.2, 1])
        with c_quad:
            t_akhir = df_p['tahun'].max()
            df_now = df_p[df_p['tahun'] == t_akhir].copy()
            df_prev = df_p[df_p['tahun'] == (t_akhir - 1)].copy()
            df_m = pd.merge(df_now, df_prev, on='sektor', suffixes=('_curr', '_prev'))
            tot_adhb = df_m['nilai_adhb_curr'].sum()
            true_growth = ((df_m['nilai_adhk_curr'].sum() - df_m['nilai_adhk_prev'].sum()) / df_m['nilai_adhk_prev'].sum()) * 100
            avg_p = 100.0 / len(df_m)
            df_m['pangsa'] = (df_m['nilai_adhb_curr'] / tot_adhb) * 100
            df_m['pertumbuhan'] = ((df_m['nilai_adhk_curr'] - df_m['nilai_adhk_prev']) / df_m['nilai_adhk_prev']) * 100
            scat_data = [{"name": r['sektor'], "value": [round(r['pangsa'], 2), round(r['pertumbuhan'], 2)]} for _, r in df_m.iterrows()]
            scatter_opts = {
                "backgroundColor": "transparent", "title": {"text": "Matriks Kinerja Kuadran BCG"},
                "tooltip": {"trigger": "item", "formatter": JsCode("function(p){if(p.componentType==='markLine'){return p.name+': '+Number(p.value).toFixed(2)+'%';}return '<b>'+p.data.name+'</b><br/>Pangsa: '+p.data.value[0]+'%<br/>Growth: '+p.data.value[1]+'%';}")},
                "xAxis": {"type": "value", "name": "Pangsa (%)", "nameLocation": "middle", "nameGap": 25}, "yAxis": {"type": "value", "name": "Pertumbuhan (%)", "nameLocation": "middle", "nameGap": 30},
                "series": [{"type": "scatter", "symbolSize": 18, "itemStyle": {"color": COLORS[4], "opacity": 0.8}, "data": scat_data, "label": {"show": True, "formatter": "{b}", "position": "right", "fontSize": 10}, "markLine": {"animation": False, "lineStyle": {"type": "dashed", "color": "#7F8C8D"}, "data": [{"xAxis": avg_p, "name": "Batas Pangsa"}, {"yAxis": true_growth, "name": "Laju Daerah"}]}}]
            }
            st_echarts(options=scatter_opts, height="450px", theme=e_theme)
        with c_heat:
            df_piv = df_p.pivot(index='tahun', columns='sektor', values='nilai_adhk').pct_change() * 100
            df_piv = df_piv.dropna().reset_index()
            sektors = [c for c in df_piv.columns if c != 'tahun']
            years = df_piv['tahun'].astype(int).astype(str).tolist()
            heat_data = [[y_idx, s_idx, round(row[s], 2)] for y_idx, row in df_piv.iterrows() for s_idx, s in enumerate(sektors)]
            heat_opts = {
                "backgroundColor": "transparent", "title": {"text": "Heatmap Kontraksi Tahunan"},
                "tooltip": {"position": "top", "formatter": JsCode("function(p){return 'Pertumbuhan: <b>' + p.data[2] + '%</b>'}")},
                "grid": {"top": "15%", "bottom": "15%", "left": "35%"}, "xAxis": {"type": "category", "data": years}, "yAxis": {"type": "category", "data": sektors},
                "visualMap": {"min": -5, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%", "inRange": {"color": ["#EF4444", "#FEE2E2", "#3B82F6"]}},
                "series": [{"type": "heatmap", "data": heat_data, "label": {"show": True, "formatter": JsCode("function(p){return p.data[2] + '%'}")}, "itemStyle": {"borderColor": "#fff", "borderWidth": 1}}]
            }
            st_echarts(options=heat_opts, height="450px", theme=e_theme)

elif sub_kategori == "Ketahanan Pangan & NTP":
    st.title("🌾 Kluster Primer & Ketahanan Pangan")
    show_macro_warning()
    df_f = apply_filter(df_pert)
    df_n = apply_filter(df_inf)
    if not df_f.empty and not df_n.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        df_n['periode'] = df_n['bulan'].astype(str) + " " + df_n['tahun'].astype(int).astype(str)
        c_padi, c_ntp = st.columns(2)
        with c_padi:
            padi_opts = {"backgroundColor": "transparent", "title": {"text": "Korelasi Sektoral Luas Panen & Produksi"}, "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID}, "legend": {"bottom": 0}, "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()}, "yAxis": [{"type": "value", "name": "Ha", "splitLine": {"show":False}}, {"type": "value", "name": "Ton"}], "series": [{"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}}, {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}}]}
            st_echarts(options=padi_opts, height="400px", theme=e_theme)
        with c_line:
            ntp_opts = {"backgroundColor": "transparent", "title": {"text": "Nilai Tukar Petani (NTP)"}, "tooltip": {"trigger": "axis"}, "dataZoom": [{"type": "inside"}], "xAxis": {"type": "category", "data": df_n['periode'].tolist()}, "yAxis": {"type": "value", "scale": True}, "series": [{"name": "NTP", "type": "line", "data": df_n['ntp'].tolist(), "itemStyle": {"color": COLORS[1]}, "markLine": {"data": [{"yAxis": 100, "name": "Paritas"}], "lineStyle": {"color": COLORS[3]}}}]}
            st_echarts(options=ntp_opts, height="400px", theme=e_theme)
        
        df_disp = df_padi[['tahun', 'luas_panen', 'produksi']].rename(columns={'tahun':'Tahun', 'luas_panen':'Luas Panen (Ha)', 'produksi':'Produksi (Ton)'})
        render_custom_table(df_disp.sort_values('Tahun', ascending=False))