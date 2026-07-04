import streamlit as st
import pandas as pd
import json
import os
import datetime
from streamlit_echarts import st_echarts, JsCode, Map

# ==============================================================================
# 1. KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(page_title="Dashboard Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"
COLORS = ['#1E3A8A', '#E67E22', '#059669', '#DC2626', '#8E44AD', '#16A085', '#F39C12']

st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 96% !important;}
[data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 800 !important; font-size: 2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1rem !important;}
.insight-box {background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 15px; border-radius: 6px; margin-bottom: 20px;}
.insight-title {font-weight: 800; color: #1E3A8A; margin-bottom: 5px; font-size: 1.1rem;}
.insight-text {font-size: 1rem; line-height: 1.5; color: #334155;}
</style>
""", unsafe_allow_html=True)

# Format JSON ECharts Helper
FMT_ID = JsCode("""
function(params) {
    if (!Array.isArray(params)) { return params.name + '<br/>' + params.seriesName + ': <b>' + Number(params.value).toLocaleString('id-ID') + '</b>'; }
    let res = '<b>' + params[0].name + '</b>';
    for (let i = 0; i < params.length; i++) { res += '<br/>' + params[i].marker + params[i].seriesName + ': <b>' + Number(params[i].value).toLocaleString('id-ID') + '</b>'; }
    return res;
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
        with open("tanah_laut.geojson", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def download_csv(df, filename):
    return st.download_button(label="📥 Unduh CSV Rekap", data=df.to_csv(index=False).encode('utf-8'), file_name=filename, mime='text/csv', use_container_width=True)

with st.spinner("Sinkronisasi Database BPS..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")
    geo_data = load_geojson()

# ==============================================================================
# 3. SIDEBAR NAVIGASI
# ==============================================================================
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="160"></div>', unsafe_allow_html=True)
    menu = st.radio("Menu Navigasi", ["Ringkasan Eksekutif", "Sosial & Demografi", "Perekonomian Daerah", "Sektor Pertanian"], label_visibility="collapsed")
    st.markdown("---")
    
    min_year = int(df_demo['tahun'].min()) if not df_demo.empty else 2010
    curr_year = datetime.datetime.now().year
    f_tahun = st.slider("Rentang Analisis", min_year, curr_year, (min_year, curr_year), label_visibility="collapsed")
    st.markdown("---")
    st.caption("BPS Kabupaten Tanah Laut")

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty:
        return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

# ==============================================================================
# 4. HALAMAN DASHBOARD INTERAKTIF
# ==============================================================================

# ---------------------------------------------------------
# HALAMAN 1: EKSEKUTIF (THE 7 KEY METRICS)
# ---------------------------------------------------------
if menu == "Ringkasan Eksekutif":
    st.title(":material/dashboard: Command Center Makro Daerah")
    
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf, df_pert]):
        df_kab = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
        c_dem, p_dem = df_kab.iloc[-1], df_kab.iloc[-2]
        c_kes, p_kes = df_kes.sort_values('tahun').iloc[-1], df_kes.sort_values('tahun').iloc[-2]
        
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        c_pe, p_pe = df_pe.iloc[-1], df_pe.iloc[-2]
        gwth = ((c_pe['nilai_adhk'] - p_pe['nilai_adhk']) / p_pe['nilai_adhk']) * 100
        
        c_inf, p_inf = df_inf.iloc[-1], df_inf.iloc[-2]
        c_pd, p_pd = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun').iloc[-1], df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun').iloc[-2]

        st.markdown("#### Kesejahteraan & SDM")
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Kemiskinan (P0) - {int(c_kes['tahun'])}", f"{c_kes['p0']:g}%", f"{c_kes['p0'] - p_kes['p0']:.2f}%", delta_color="inverse", border=True)
        k2.metric(f"IPM - {int(c_kes['tahun'])}", f"{c_kes['ipm']:.2f}", f"{c_kes['ipm'] - p_kes['ipm']:.2f}", border=True)
        k3.metric(f"TPT - {int(c_dem['tahun'])}", f"{c_dem['tpt']:g}%", f"{c_dem['tpt'] - p_dem['tpt']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### Perekonomian & Harga")
        e1, e2 = st.columns(2)
        e1.metric(f"Pertumbuhan Ekonomi - {int(c_pe['tahun'])}", f"{gwth:.2f}%", border=True)
        e2.metric(f"Inflasi YoY - {c_inf['bulan']} {int(c_inf['tahun'])}", f"{c_inf['inflasi_yoy']:g}%", f"{c_inf['inflasi_yoy'] - p_inf['inflasi_yoy']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### Demografi & Pangan")
        d1, d2 = st.columns(2)
        d1.metric(f"Total Penduduk - {int(c_dem['tahun'])}", f"{c_dem['jumlah_penduduk']:,.0f}".replace(",", "."), border=True)
        d2.metric(f"Luas Panen Padi - {int(c_pd['tahun'])}", f"{c_pd['luas_panen']:,.0f} Ha".replace(",", "."), border=True)

# ---------------------------------------------------------
# HALAMAN 2: SOSIAL & DEMOGRAFI (PETA TEMATIK & ASIMETRIS)
# ---------------------------------------------------------
elif menu == "Sosial & Demografi":
    st.title(":material/group: Demografi & Kesejahteraan Wilayah")
    t_dem, t_kem = st.tabs(["Kependudukan & Spasial", "Kesejahteraan & Benchmarking"])

    with t_dem:
        df_f = apply_filter(df_demo)
        if not df_f.empty:
            thn_akhir = df_f['tahun'].max()
            df_kec = df_f[(df_f['tahun'] == thn_akhir) & (df_f['kecamatan'].str.lower() != 'tanah laut')]
            
            # GRID ASIMETRIS (PETA vs SPARKLINE)
            c_map, c_spark = st.columns([2.5, 1.2])
            
            with c_map:
                if geo_data:
                    # RENDER PETA CHOROPLETH SPASIAL
                    map_data = [{"name": r['kecamatan'], "value": r['jumlah_penduduk']} for _, r in df_kec.iterrows()]
                    map_opts = {
                        "title": {"text": f"Sebaran Kepadatan Demografi ({int(thn_akhir)})", "left": "center", "textStyle": {"fontSize": 14}},
                        "tooltip": {"trigger": "item", "formatter": "{b}<br/>Populasi: {c}"},
                        "visualMap": {"min": df_kec['jumlah_penduduk'].min(), "max": df_kec['jumlah_penduduk'].max(), "left": "left", "top": "bottom", "text": ["Tinggi", "Rendah"], "calculable": True, "inRange": {"color": ["#1E3A8A", "#D4E6F1"]}},
                        "series": [{"type": "map", "map": "Tanah_Laut", "roam": True, "label": {"show": False}, "data": map_data}]
                    }
                    st_echarts(options=map_opts, map=Map("Tanah_Laut", geo_data), height="450px")
                else:
                    bar_opts = {
                        "title": {"text": f"Sebaran Penduduk per Kecamatan ({int(thn_akhir)})"},
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                        "xAxis": {"type": "value", "show": False},
                        "yAxis": {"type": "category", "data": df_kec.sort_values('jumlah_penduduk')['kecamatan'].tolist(), "axisLine": {"show": False}},
                        "series": [{"type": "bar", "data": df_kec.sort_values('jumlah_penduduk')['jumlah_penduduk'].tolist(), "itemStyle": {"color": COLORS[0]}, "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")}}]
                    }
                    st_echarts(options=bar_opts, height="450px")
                    
            with c_spark:
                # SPARKLINE PERTUMBUHAN AGREGAT
                df_kab = df_f[df_f['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
                spark_opts = {
                    "title": {"text": "Tren Agregat Kabupaten", "textStyle": {"fontSize": 14}},
                    "xAxis": {"type": "category", "show": False, "data": df_kab['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "show": False, "min": 'dataMin'},
                    "series": [{"type": "line", "data": df_kab['jumlah_penduduk'].tolist(), "smooth": True, "areaStyle": {"opacity": 0.2}, "itemStyle": {"color": COLORS[1]}}]
                }
                st_echarts(options=spark_opts, height="200px")
                st.caption("Porsi Gender")
                lk, pr = df_kab.iloc[-1]['lk'], df_kab.iloc[-1]['pr']
                st_echarts({"series": [{"type": "pie", "radius": ["40%", "70%"], "data": [{"name": "Laki-laki", "value": lk}, {"name": "Perempuan", "value": pr}], "itemStyle": {"borderRadius": 5}}], "color": [COLORS[0], COLORS[1]]}, height="200px")

    with t_kem:
        df_f = apply_filter(df_kes)
        if not df_f.empty:
            c_bench, c_radar = st.columns([1.8, 1])
            
            with c_bench:
                # BENCHMARKING (KOMPARASI REGIONAL)
                df_srt = df_f.sort_values('tahun')
                bench_opts = {
                    "title": {"text": "Benchmarking IPM: Tanah Laut vs Provinsi Kalsel", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": df_srt['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "min": 'dataMin'},
                    "series": [
                        {"name": "Tanah Laut", "type": "line", "smooth": True, "data": df_srt['ipm'].tolist(), "itemStyle": {"color": COLORS[0]}, "lineStyle": {"width": 3}},
                        {"name": "Provinsi Kalsel", "type": "line", "smooth": True, "data": df_srt['ipm_kalsel'].tolist(), "itemStyle": {"color": COLORS[1], "type": "dashed"}}
                    ]
                }
                st_echarts(options=bench_opts, height="350px")
                
            with c_radar:
                curr_ipm = df_f.sort_values('tahun').iloc[-1]
                radar_opts = {
                    "title": {"text": "Profil Dimensi IPM", "textStyle": {"fontSize": 14}},
                    "radar": {"indicator": [{"name": "UHH", "max": 80}, {"name": "HLS", "max": 15}, {"name": "RLS", "max": 12}]},
                    "series": [{"type": "radar", "data": [{"value": [curr_ipm['uhh'], curr_ipm['hls'], curr_ipm['rls']]}], "itemStyle": {"color": COLORS[2]}, "areaStyle": {"opacity": 0.3}}]
                }
                st_echarts(options=radar_opts, height="350px")
                
            # INTERACTIVE DATA TABLE
            download_csv(df_f, "kesejahteraan_tanahlaut.csv")

# ---------------------------------------------------------
# HALAMAN 3: PEREKONOMIAN (EARLY WARNING DASHBOARD)
# ---------------------------------------------------------
elif menu == "Perekonomian Daerah":
    st.title(":material/monitoring: Perekonomian & Early Warning")
    t_ew, t_pdrb = st.tabs(["🚦 Early Warning Matrix", "Eksplorasi ADHK Sektoral"])

    with t_ew:
        df_f = apply_filter(df_pdrb)
        if not df_f.empty:
            # KALKULASI MATRIKS PERINGATAN DINI (HEATMAP PDRB SEKTORAL)
            st.markdown("""<div class='insight-box' style='border-left-color: #DC2626;'>
            <div class='insight-title'>🚦 Sistem Peringatan Dini (Early Warning Dashboard)</div>
            <div class='insight-text'>Matriks di bawah merepresentasikan YoY Growth (Pertumbuhan Tahunan) setiap lapangan usaha. Area berwarna merah menunjukkan sektor yang sedang mengalami kontraksi historis parah dan membutuhkan intervensi strategis OPD terkait.</div></div>""", unsafe_allow_html=True)
            
            # Pivot dan Kalkulasi Pertumbuhan per Sektor
            df_pivot = df_f.pivot(index='tahun', columns='sektor', values='nilai_adhk')
            df_growth = df_pivot.pct_change() * 100
            df_growth = df_growth.dropna().reset_index()
            
            sektors = [c for c in df_growth.columns if c != 'tahun']
            years = df_growth['tahun'].astype(int).astype(str).tolist()
            
            heatmap_data = []
            for y_idx, row in df_growth.iterrows():
                for s_idx, s in enumerate(sektors):
                    heatmap_data.append([y_idx, s_idx, round(row[s], 2)])

            heat_opts = {
                "tooltip": {"position": "top", "formatter": JsCode("function(p){return 'Pertumbuhan: <b>' + p.data[2] + '%</b>'}")},
                "grid": {"top": "5%", "bottom": "15%", "left": "25%"},
                "xAxis": {"type": "category", "data": years, "splitArea": {"show": True}},
                "yAxis": {"type": "category", "data": sektors, "splitArea": {"show": True}},
                "visualMap": {"min": -5, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%", "inRange": {"color": ["#DC2626", "#FADBD8", "#1E3A8A"]}},
                "series": [{"type": "heatmap", "data": heatmap_data, "label": {"show": True, "formatter": JsCode("function(p){return p.data[2] + '%'}")}, "itemStyle": {"borderColor": "#fff", "borderWidth": 1}}]
            }
            st_echarts(options=heat_opts, height="450px")

    with t_pdrb:
        df_f = apply_filter(df_pdrb)
        if not df_f.empty:
            # KOMPARASI REGIONAL PDRB
            df_pe = df_f.groupby('tahun', as_index=False).agg({'nilai_adhk':'sum', 'pe_kalsel':'mean'})
            df_pe['pertumbuhan_tala'] = df_pe['nilai_adhk'].pct_change() * 100
            df_pe = df_pe.dropna()
            
            c_bar, c_bench = st.columns([1.2, 1.5])
            with c_bar:
                tahun_terbaru = df_f['tahun'].max()
                df_latest = df_f[df_f['tahun'] == tahun_terbaru].sort_values('nilai_adhk', ascending=True)
                bar_opts = {
                    "title": {"text": f"Pangsa Sektor ADHK ({int(tahun_terbaru)})", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "grid": {"left": "35%", "bottom": "10%"},
                    "xAxis": {"type": "value", "show": False},
                    "yAxis": {"type": "category", "data": df_latest['sektor'].tolist(), "axisLine": {"show": False}},
                    "series": [{"type": "bar", "data": df_latest['nilai_adhk'].tolist(), "itemStyle": {"color": COLORS[0]}}]
                }
                st_echarts(options=bar_opts, height="350px")
                
            with c_bench:
                bench_opts = {
                    "title": {"text": "Benchmarking Pertumbuhan Ekonomi", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": df_pe['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
                    "series": [
                        {"name": "Kab. Tanah Laut", "type": "bar", "data": df_pe['pertumbuhan_tala'].round(2).tolist(), "itemStyle": {"color": COLORS[1]}},
                        {"name": "Prov. Kalsel", "type": "line", "data": df_pe['pe_kalsel'].tolist(), "itemStyle": {"color": COLORS[3]}, "symbolSize": 10}
                    ]
                }
                st_echarts(options=bench_opts, height="350px")

            download_csv(df_f, "pdrb_tanahlaut.csv")

# ---------------------------------------------------------
# HALAMAN 4: PERTANIAN
# ---------------------------------------------------------
elif menu == "Sektor Pertanian":
    st.title(":material/agriculture: Ketahanan Pangan Daerah")
    df_f = apply_filter(df_pert)
    
    if not df_f.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        
        c_bar, c_pie = st.columns([2, 1])
        with c_bar:
            padi_opts = {
                "title": {"text": "Korelasi Luas Panen dan Produksi Padi", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Hektar", "splitLine": {"show":False}}, {"type": "value", "name": "Ton", "splitLine": {"lineStyle": {"color": "#eee"}}}],
                "series": [
                    {"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}},
                    {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}}
                ]
            }
            st_echarts(options=padi_opts, height="400px")
            
        with c_pie:
            df_jagung = df_f[df_f['komoditas'].str.lower() == 'jagung'].sort_values('tahun')
            pie_opts = {
                "title": {"text": f"Produksi Terakhir", "textStyle": {"fontSize": 14}, "left": "center"},
                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                "color": [COLORS[2], COLORS[1]],
                "series": [{"type": "pie", "radius": ["40%", "70%"], "data": [{"name": "Padi", "value": df_padi.iloc[-1]['produksi']}, {"name": "Jagung", "value": df_jagung.iloc[-1]['produksi']}], "itemStyle": {"borderRadius": 5}}]
            }
            st_echarts(options=pie_opts, height="400px")
            
        download_csv(df_f, "pertanian_tanahlaut.csv")