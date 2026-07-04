import streamlit as st
import pandas as pd
import json
import os
import datetime
from streamlit_echarts import st_echarts, JsCode, Map

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA
# ==============================================================================
st.set_page_config(page_title="Dashboard Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"
COLORS = ['#1E3A8A', '#E67E22', '#059669', '#DC2626', '#8E44AD', '#16A085']

st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 96% !important;}
[data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 900 !important; font-size: 2.2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1.1rem !important; font-weight: 600;}
.insight-box {background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 18px; border-radius: 6px; margin-bottom: 25px;}
.insight-title {font-weight: 800; color: #1E3A8A; margin-bottom: 8px; font-size: 1.1rem;}
.insight-text {font-size: 1.05rem; line-height: 1.6; color: #334155;}
</style>
""", unsafe_allow_html=True)

# JS ECharts Formatter yang Bulletproof (Anti-Error)
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
    # Mengambil file yang sudah diperbaiki atribut 'name'-nya
    if os.path.exists("tanah_laut.geojson"):
        with open("tanah_laut.geojson", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def download_csv(df, filename):
    st.download_button("📥 Unduh Dataset Lengkap (CSV)", data=df.to_csv(index=False).encode('utf-8'), file_name=filename, mime='text/csv')

def nlg_insight(df, col, name, unit="%", is_good=True):
    if len(df) < 2: return ""
    c, p = df.iloc[-1], df.iloc[-2]
    diff = c[col] - p[col]
    
    trend = "naik" if diff > 0 else "turun" if diff < 0 else "stagnan"
    positive = (diff > 0 and is_good) or (diff < 0 and not is_good)
    icon = "✅" if positive else "📌" if diff == 0 else "⚠️"
    
    return f"""
    <div class='insight-box'>
        <div class='insight-title'>{icon} Interpretasi Eksekutif: {name}</div>
        <div class='insight-text'>Pada {int(c['tahun'])}, {name} berada di angka <b>{c[col]:g}{unit}</b>, {trend} <b>{abs(diff):.2f}{unit}</b> dari tahun sebelumnya. Ini mengindikasikan {'perkembangan struktural yang positif bagi daerah.' if positive else 'kondisi yang membutuhkan atensi khusus dalam RKPD.'}</div>
    </div>
    """

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
    menu = st.radio("Navigasi", ["Ringkasan Eksekutif", "Demografi & Kemiskinan", "Perekonomian & Inflasi", "Sektor Pertanian"], label_visibility="collapsed")
    st.markdown("---")
    
    min_year = int(df_demo['tahun'].min()) if not df_demo.empty else 2010
    curr_year = datetime.datetime.now().year
    f_tahun = st.slider("Rentang Evaluasi", min_year, curr_year, (min_year, curr_year), label_visibility="collapsed")
    st.markdown("---")

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty: return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

# ==============================================================================
# 4. HALAMAN DASHBOARD
# ==============================================================================

if menu == "Ringkasan Eksekutif":
    st.title(":material/dashboard: Command Center Daerah")
    
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf, df_pert]):
        c_dem = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun').iloc[-1]
        p_dem = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun').iloc[-2]
        
        c_kes, p_kes = df_kes.sort_values('tahun').iloc[-1], df_kes.sort_values('tahun').iloc[-2]
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        c_pe, p_pe = df_pe.iloc[-1], df_pe.iloc[-2]
        pe_growth = ((c_pe['nilai_adhk'] - p_pe['nilai_adhk']) / p_pe['nilai_adhk']) * 100
        
        c_inf, p_inf = df_inf.iloc[-1], df_inf.iloc[-2]
        c_pd, p_pd = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun').iloc[-1], df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun').iloc[-2]

        st.markdown("#### Kesejahteraan & Ketenagakerjaan")
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Kemiskinan P0 ({int(c_kes['tahun'])})", f"{c_kes['p0']:g}%", f"{c_kes['p0'] - p_kes['p0']:.2f}%", delta_color="inverse", border=True)
        k2.metric(f"IPM ({int(c_kes['tahun'])})", f"{c_kes['ipm']:.2f}", f"{c_kes['ipm'] - p_kes['ipm']:.2f}", border=True)
        k3.metric(f"TPT ({int(c_dem['tahun'])})", f"{c_dem['tpt']:g}%", f"{c_dem['tpt'] - p_dem['tpt']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### Ekonomi, Harga, & Pangan")
        e1, e2, e3 = st.columns(3)
        e1.metric(f"Pertumbuhan Ekonomi ({int(c_pe['tahun'])})", f"{pe_growth:.2f}%", border=True)
        e2.metric(f"Inflasi YoY ({c_inf['bulan']} {int(c_inf['tahun'])})", f"{c_inf['inflasi_yoy']:g}%", f"{c_inf['inflasi_yoy'] - p_inf['inflasi_yoy']:.2f}%", delta_color="inverse", border=True)
        e3.metric(f"Luas Panen Padi ({int(c_pd['tahun'])})", f"{c_pd['luas_panen']:,.0f} Ha".replace(",", "."), border=True)

        st.markdown(f"""
        <div class='insight-box' style='border-left-color: #E67E22;'>
            <div class='insight-title'>💡 Sintesis Kondisi Makro</div>
            <div class='insight-text'>Perekonomian bertumbuh <b>{pe_growth:.2f}%</b> dengan tingkat inflasi daerah di level <b>{c_inf['inflasi_yoy']}%</b>. Indeks Pembangunan Manusia tercatat sebesar <b>{c_kes['ipm']}</b> dengan rasio kemiskinan di <b>{c_kes['p0']}%</b>.</div>
        </div>
        """, unsafe_allow_html=True)

elif menu == "Demografi & Kemiskinan":
    st.title(":material/group: Demografi & Kesejahteraan")
    t_spasial, t_kesejahteraan = st.tabs(["Distribusi Spasial Penduduk", "Benchmarking Kesejahteraan"])

    with t_spasial:
        df_f = apply_filter(df_demo)
        if not df_f.empty:
            t_akhir = df_f['tahun'].max()
            df_kec = df_f[(df_f['tahun'] == t_akhir) & (df_f['kecamatan'].str.lower() != 'tanah laut')]
            
            # GRID ASIMETRIS (Peta mengambil ruang dominan, grafik komposisi di sisi kanan)
            c_map, c_spark = st.columns([7, 3])
            
            with c_map:
                if geo_data:
                    # PASTIKAN GeoJSON sudah diperbaiki atribut 'name'-nya!
                    map_data = [{"name": r['kecamatan'], "value": r['jumlah_penduduk']} for _, r in df_kec.iterrows()]
                    map_opts = {
                        "title": {"text": f"Peta Persebaran Demografi ({int(t_akhir)})", "left": "center", "textStyle": {"fontSize": 15}},
                        "tooltip": {"trigger": "item", "formatter": "{b}<br/>Penduduk: <b>{c} Jiwa</b>"},
                        "visualMap": {"min": df_kec['jumlah_penduduk'].min(), "max": df_kec['jumlah_penduduk'].max(), "left": "left", "top": "bottom", "text": ["Tinggi", "Rendah"], "calculable": True, "inRange": {"color": ["#D4E6F1", "#1E3A8A"]}},
                        "series": [{"type": "map", "map": "TALA", "roam": True, "label": {"show": False}, "data": map_data}]
                    }
                    st_echarts(options=map_opts, map=Map("TALA", geo_data), height="500px")
                else:
                    st.warning("Menunggu file tanah_laut.geojson")
                    
            with c_spark:
                df_kab = df_f[df_f['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
                spark_opts = {
                    "title": {"text": "Tren Agregat Kabupaten", "textStyle": {"fontSize": 13}},
                    "xAxis": {"type": "category", "show": False, "data": df_kab['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "show": False, "min": 'dataMin'},
                    "series": [{"type": "line", "data": df_kab['jumlah_penduduk'].tolist(), "smooth": True, "areaStyle": {"opacity": 0.2}, "itemStyle": {"color": COLORS[1]}}]
                }
                st_echarts(options=spark_opts, height="200px")
                
                pie_opts = {
                    "title": {"text": "Porsi Gender", "textStyle": {"fontSize": 13}},
                    "tooltip": {"trigger": "item"},
                    "color": [COLORS[0], COLORS[1]],
                    "series": [{"type": "pie", "radius": ["40%", "70%"], "data": [{"name": "Laki-laki", "value": df_kab.iloc[-1]['lk']}, {"name": "Perempuan", "value": df_kab.iloc[-1]['pr']}], "itemStyle": {"borderRadius": 5}, "label": {"show": False}}]
                }
                st_echarts(options=pie_opts, height="200px")

    with t_kesejahteraan:
        df_f = apply_filter(df_kes)
        if not df_f.empty:
            st.markdown(nlg_insight(df_f.sort_values('tahun'), 'ipm', 'IPM Tanah Laut', '', True), unsafe_allow_html=True)
            
            c_bench, c_radar = st.columns([1.8, 1])
            with c_bench:
                # BENCHMARKING PROVINSI
                df_srt = df_f.sort_values('tahun')
                bench_opts = {
                    "title": {"text": "Benchmarking IPM: Kabupaten vs Provinsi Kalsel", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": df_srt['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "min": 'dataMin'},
                    "series": [
                        {"name": "Tanah Laut", "type": "line", "smooth": True, "data": df_srt['ipm'].tolist(), "itemStyle": {"color": COLORS[0]}, "lineStyle": {"width": 3}, "symbolSize": 8},
                        {"name": "Provinsi Kalsel", "type": "line", "smooth": True, "data": df_srt['ipm_kalsel'].tolist(), "itemStyle": {"color": COLORS[1], "type": "dashed"}}
                    ]
                }
                st_echarts(options=bench_opts, height="400px")
                
            with c_radar:
                curr_ipm = df_srt.iloc[-1]
                radar_opts = {
                    "title": {"text": "Jaring Dimensi IPM", "textStyle": {"fontSize": 14}},
                    "radar": {"indicator": [{"name": "UHH", "max": 80}, {"name": "HLS", "max": 15}, {"name": "RLS", "max": 12}]},
                    "series": [{"type": "radar", "data": [{"value": [curr_ipm['uhh'], curr_ipm['hls'], curr_ipm['rls']]}], "itemStyle": {"color": COLORS[2]}, "areaStyle": {"opacity": 0.3}}]
                }
                st_echarts(options=radar_opts, height="400px")
            
            download_csv(df_f, "data_kesejahteraan.csv")

elif menu == "Perekonomian & Inflasi":
    st.title(":material/monitoring: Perekonomian Daerah & Inflasi")
    t_pdrb, t_quad, t_ew = st.tabs(["Eksplorasi Sektoral", "Kuadran Portofolio", "Early Warning System"])

    with t_pdrb:
        df_f = apply_filter(df_pdrb)
        if not df_f.empty:
            df_pe = df_f.groupby('tahun', as_index=False)['nilai_adhk'].sum()
            df_pe['pe'] = df_pe['nilai_adhk'].pct_change() * 100
            st.markdown(nlg_insight(df_pe.dropna(), 'pe', 'Pertumbuhan Ekonomi', '%', True), unsafe_allow_html=True)
            
            tahun_terbaru = df_f['tahun'].max()
            df_latest = df_f[df_f['tahun'] == tahun_terbaru].sort_values('nilai_adhb', ascending=False)
            
            c_bar, c_line = st.columns([1.2, 1])
            with c_bar:
                bar_opts = {
                    "title": {"text": f"Pangsa Sektor ({int(tahun_terbaru)})", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                    "grid": {"left": "35%", "bottom": "10%"},
                    "xAxis": {"type": "value", "show": False},
                    "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}, "axisTick": {"show": False}},
                    "series": [{"type": "bar", "data": df_latest['nilai_adhb'].tolist()[::-1], "itemStyle": {"color": COLORS[0]}}]
                }
                # CROSS FILTERING ECHARTS (KLIK BATANG -> LINE BERUBAH)
                clicked = st_echarts(options=bar_opts, height="400px", events={"click": "function(p){return p.name}"})
                
            with c_line:
                # Default sektor ke urutan pertama jika belum diklik
                sel_sektor = clicked if clicked else df_latest.iloc[0]['sektor']
                df_tren = df_f[df_f['sektor'] == sel_sektor].sort_values('tahun')
                
                line_opts = {
                    "title": {"text": f"Tren ADHB: {sel_sektor}", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "formatter": FMT_ID},
                    "xAxis": {"type": "category", "data": df_tren['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#eee"}}, "axisLabel": {"formatter": JsCode("function(v){return (v/1000000).toFixed(1) + ' T'}")}},
                    "series": [{"type": "line", "smooth": True, "data": df_tren['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}, "symbolSize": 8}]
                }
                st_echarts(options=line_opts, height="400px")
            
            download_csv(df_f, "data_pdrb.csv")

    with t_quad:
        if not df_f.empty:
            st.markdown("""<div class='insight-box' style='border-left-color: #8E44AD;'>
            <div class='insight-title'>📈 Analisis Kuadran Kinerja Sektoral</div>
            <div class='insight-text'>Sumbu X (Bawah): <b>Pangsa/Kontribusi</b>. Sumbu Y (Kiri): <b>Pertumbuhan</b>. Sektor di Kanan Atas adalah penggerak utama. Sektor di Kiri Bawah berisiko menjadi beban.</div></div>""", unsafe_allow_html=True)

            t_akhir = df_f['tahun'].max()
            df_now = df_f[df_f['tahun'] == t_akhir].copy()
            df_prev = df_f[df_f['tahun'] == (t_akhir - 1)].copy()
            
            df_m = pd.merge(df_now, df_prev, on='sektor', suffixes=('_curr', '_prev'))
            tot = df_m['nilai_adhb_curr'].sum()
            df_m['pangsa'] = (df_m['nilai_adhb_curr'] / tot) * 100
            df_m['pertumbuhan'] = ((df_m['nilai_adhk_curr'] - df_m['nilai_adhk_prev']) / df_m['nilai_adhk_prev']) * 100
            
            avg_p, avg_g = df_m['pangsa'].mean(), df_m['pertumbuhan'].mean()
            scat_data = [{"name": r['sektor'], "value": [round(r['pangsa'], 2), round(r['pertumbuhan'], 2)]} for _, r in df_m.iterrows()]

            scatter_opts = {
                "tooltip": {"trigger": "item", "formatter": JsCode("function(p){return '<b>' + p.data.name + '</b><br/>Pangsa: ' + p.data.value[0] + '%<br/>Growth: ' + p.data.value[1] + '%';}")},
                "xAxis": {"type": "value", "name": "Pangsa PDRB (%)", "nameLocation": "middle", "nameGap": 30},
                "yAxis": {"type": "value", "name": "Pertumbuhan (%)", "nameLocation": "middle", "nameGap": 40},
                "series": [{
                    "type": "scatter", "symbolSize": 20, "itemStyle": {"color": COLORS[2], "opacity": 0.8}, "data": scat_data,
                    "label": {"show": True, "formatter": "{b}", "position": "right", "fontSize": 11},
                    "markLine": {"animation": False, "lineStyle": {"type": "dashed", "color": "#7F8C8D"}, "label": {"show": False}, "data": [{"xAxis": avg_p}, {"yAxis": avg_g}]}
                }]
            }
            st_echarts(options=scatter_opts, height="450px")

    with t_ew:
        if not df_f.empty:
            st.markdown("""<div class='insight-box' style='border-left-color: #DC2626;'>
            <div class='insight-title'>🚦 Heatmap Peringatan Dini (Early Warning)</div>
            <div class='insight-text'>Area merah menunjukkan sektor yang sedang atau pernah mengalami kontraksi pertumbuhan.</div></div>""", unsafe_allow_html=True)
            
            df_piv = df_f.pivot(index='tahun', columns='sektor', values='nilai_adhk').pct_change() * 100
            df_piv = df_piv.dropna().reset_index()
            
            sektors = [c for c in df_piv.columns if c != 'tahun']
            years = df_piv['tahun'].astype(int).astype(str).tolist()
            
            heat_data = [[y_idx, s_idx, round(row[s], 2)] for y_idx, row in df_piv.iterrows() for s_idx, s in enumerate(sektors)]

            heat_opts = {
                "tooltip": {"position": "top", "formatter": JsCode("function(p){return 'Pertumbuhan: <b>' + p.data[2] + '%</b>'}")},
                "grid": {"top": "5%", "bottom": "15%", "left": "30%"},
                "xAxis": {"type": "category", "data": years, "splitArea": {"show": True}},
                "yAxis": {"type": "category", "data": sektors, "splitArea": {"show": True}},
                "visualMap": {"min": -5, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%", "inRange": {"color": ["#DC2626", "#FADBD8", "#1E3A8A"]}},
                "series": [{"type": "heatmap", "data": heat_data, "label": {"show": True, "formatter": JsCode("function(p){return p.data[2] + '%'}")}, "itemStyle": {"borderColor": "#fff", "borderWidth": 1}}]
            }
            st_echarts(options=heat_opts, height="500px")

elif menu == "Sektor Pertanian":
    st.title(":material/agriculture: Ketahanan Pangan Daerah")
    df_f = apply_filter(df_pert)
    df_n = apply_filter(df_inf)
    
    if not df_f.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        st.markdown(nlg_insight(df_padi, 'produksi', 'Produksi Padi Daerah', ' Ton', True), unsafe_allow_html=True)
        
        c_bar, c_line = st.columns([1.5, 1])
        with c_bar:
            padi_opts = {
                "title": {"text": "Luas Panen vs Produksi (Padi)", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Ha", "splitLine": {"show":False}}, {"type": "value", "name": "Ton", "splitLine": {"lineStyle": {"color": "#eee"}}}],
                "series": [{"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}}, {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}}]
            }
            st_echarts(options=padi_opts, height="450px")
            
        with c_line:
            if not df_n.empty and 'ntp' in df_n.columns:
                df_n['periode'] = df_n['bulan'].astype(str) + " " + df_n['tahun'].astype(int).astype(str)
                ntp_opts = {
                    "title": {"text": "Nilai Tukar Petani (NTP)", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "dataZoom": [{"type": "inside"}],
                    "xAxis": {"type": "category", "data": df_n['periode'].tolist()},
                    "yAxis": {"type": "value", "scale": True},
                    "series": [{"name": "NTP", "type": "line", "data": df_n['ntp'].tolist(), "itemStyle": {"color": COLORS[4]}, "markLine": {"data": [{"yAxis": 100, "name": "Batas Sejahtera"}], "lineStyle": {"color": COLORS[3]}}}]
                }
                st_echarts(options=ntp_opts, height="450px")
                
        download_csv(df_f, "pertanian_tanahlaut.csv")