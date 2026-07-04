import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts, JsCode
import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA ENTERPRISE ECHARTS
# ==============================================================================
st.set_page_config(page_title="Dashboard Data Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"

# Palet Warna Data-Viz Standar BPS
COLORS = ['#1E3A8A', '#E67E22', '#059669', '#DC2626', '#8E44AD', '#16A085', '#F39C12']

st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 95% !important;}
[data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 800 !important; font-size: 2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1rem !important;}
.insight-box {background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 18px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
.insight-title {font-weight: 800; color: #1E3A8A; margin-bottom: 8px; font-size: 1.1rem;}
.insight-text {font-size: 1rem; line-height: 1.6; color: #334155;}
.stTabs [data-baseweb="tab-list"] {gap: 24px;}
.stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: 600; padding-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# Helper JS untuk Tooltip Ribuan/Desimal Indonesia
TOOLTIP_FORMATTER = JsCode("""
function(params) {
    if (!Array.isArray(params)) {
        return params.name + '<br/>' + params.seriesName + ': <b>' + Number(params.value).toLocaleString('id-ID') + '</b>';
    }
    let res = '<b>' + params[0].name + '</b>';
    for (let i = 0; i < params.length; i++) {
        res += '<br/>' + params[i].marker + params[i].seriesName + ': <b>' + Number(params[i].value).toLocaleString('id-ID') + '</b>';
    }
    return res;
}
""")

# ==============================================================================
# 2. DATA INGESTION ENGINE
# ==============================================================================
def clean_numeric(val):
    if pd.isna(val): return 0.0
    val_str = str(val).strip().replace(' ', '')
    if val_str.lower() in ['nan', 'none', 'null', '-', '']: return 0.0
    if ',' in val_str and '.' in val_str: val_str = val_str.replace(',', '')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        text_cols = ['kecamatan', 'sektor', 'komoditas', 'bulan']
        for col in df.columns:
            if col not in text_cols: df[col] = df[col].apply(clean_numeric)
        return df
    except: return pd.DataFrame()

def generate_analytical_insight(df, indicator_col, name, unit="%", higher_is_good=True, context_col=None):
    if len(df) < 2: return ""
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    val_curr = curr[indicator_col]
    val_prev = prev[indicator_col]
    diff = val_curr - val_prev
    
    arah = "mengalami kenaikan" if diff > 0 else "mengalami penurunan" if diff < 0 else "tercatat stagnan"
    poin = f" sebesar {abs(diff):.2f} {unit}" if diff != 0 else ""
    
    is_positive = (diff > 0 and higher_is_good) or (diff < 0 and not higher_is_good)
    if diff == 0:
        implikasi = "Kondisi ini mengindikasikan stagnasi struktural yang memerlukan intervensi terukur agar tidak tertinggal dari proyeksi daerah."
        icon = "📌"
    elif is_positive:
        implikasi = "Tren positif ini merefleksikan fundamental kebijakan daerah yang berjalan di jalur yang tepat (<i>on the right track</i>)."
        icon = "✅"
    else:
        implikasi = "Dinamika ini menjadi sinyal peringatan (*early warning*) yang menuntut re-evaluasi kebijakan sektoral oleh OPD terkait."
        icon = "⚠️"

    html = f"""
    <div class='insight-box'>
        <div class='insight-title'>{icon} Analisis Eksekutif: {name}</div>
        <div class='insight-text'>
            Pada tahun {int(curr['tahun'])}, {name} Kabupaten Tanah Laut berada pada level <b>{val_curr:g}{unit}</b>. 
            Dibandingkan periode sebelumnya ({int(prev['tahun'])}), indikator ini {arah}{poin}. <br>
            <i>{implikasi}</i>
        </div>
    </div>
    """
    return html

with st.spinner("Sinkronisasi Database BPS..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")

# ==============================================================================
# 3. SIDEBAR (NAVIGASI FLAT YANG MUDAH DIAKSES)
# ==============================================================================
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="160"></div>', unsafe_allow_html=True)
    st.markdown("### 🧭 Navigasi Strategis")
    menu = st.radio("Menu", ["Ringkasan Eksekutif", "Sosial & Kemiskinan", "Perekonomian Daerah (PDRB)", "Sektor Pertanian"], label_visibility="collapsed")
    st.markdown("---")
    curr_year = datetime.datetime.now().year
    st.caption(f"© {curr_year} BPS Kabupaten Tanah Laut")

# ==============================================================================
# 4. HALAMAN DASHBOARD INTERAKTIF
# ==============================================================================

# ----------------- HALAMAN 1: EKSEKUTIF (THE 7 KEY METRICS) -----------------
if menu == "Ringkasan Eksekutif":
    st.title(":material/dashboard: Ringkasan 7 Indikator Makro Utama")
    st.markdown("Potret makro strategis Kabupaten Tanah Laut yang menjadi acuan utama perumusan kebijakan daerah.")
    
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf, df_pert]):
        # Data Ekstraksi untuk 7 Metrik Utama
        df_kab = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
        curr_d, prev_d = df_kab.iloc[-1], df_kab.iloc[-2]
        
        df_k_sorted = df_kes.sort_values('tahun')
        curr_k, prev_k = df_k_sorted.iloc[-1], df_k_sorted.iloc[-2]
        
        # Kalkulasi Pertumbuhan Ekonomi (Berdasarkan ADHK)
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        curr_pe, prev_pe = df_pe.iloc[-1], df_pe.iloc[-2]
        growth_ekonomi = ((curr_pe['nilai_adhk'] - prev_pe['nilai_adhk']) / prev_pe['nilai_adhk']) * 100
        prev_growth = ((prev_pe['nilai_adhk'] - df_pe.iloc[-3]['nilai_adhk']) / df_pe.iloc[-3]['nilai_adhk']) * 100 if len(df_pe) > 2 else 0

        curr_inf = df_inf.iloc[-1]
        prev_inf = df_inf.iloc[-2]
        
        df_padi = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        curr_p, prev_p = df_padi.iloc[-1], df_padi.iloc[-2]

        st.markdown("#### 1️⃣ Kesejahteraan & Sumber Daya Manusia")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Kemiskinan (P0) - {int(curr_k['tahun'])}", f"{curr_k['p0']:g}%", f"{curr_k['p0'] - prev_k['p0']:.2f}%", delta_color="inverse", border=True)
        c2.metric(f"Indeks Pembangunan Manusia - {int(curr_k['tahun'])}", f"{curr_k['ipm']:.2f}", f"{curr_k['ipm'] - prev_k['ipm']:.2f}", border=True)
        c3.metric(f"Tingkat Pengangguran (TPT) - {int(curr_d['tahun'])}", f"{curr_d['tpt']:g}%", f"{curr_d['tpt'] - prev_d['tpt']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### 2️⃣ Perekonomian & Dinamika Harga")
        c4, c5 = st.columns(2)
        c4.metric(f"Pertumbuhan Ekonomi - {int(curr_pe['tahun'])}", f"{growth_ekonomi:.2f}%", f"{growth_ekonomi - prev_growth:.2f}% (Poin)", border=True)
        c5.metric(f"Inflasi YoY - {curr_inf['bulan']} {int(curr_inf['tahun'])}", f"{curr_inf['inflasi_yoy']:g}%", f"{curr_inf['inflasi_yoy'] - prev_inf['inflasi_yoy']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### 3️⃣ Demografi & Pangan Daerah")
        c6, c7 = st.columns(2)
        c6.metric(f"Total Penduduk - {int(curr_d['tahun'])}", f"{curr_d['jumlah_penduduk']:,.0f} Jiwa".replace(",", "."), f"{(curr_d['jumlah_penduduk'] - prev_d['jumlah_penduduk']):,.0f} Jiwa".replace(",", "."), border=True)
        c7.metric(f"Luas Panen Padi - {int(curr_p['tahun'])}", f"{curr_p['luas_panen']:,.0f} Ha".replace(",", "."), f"{(curr_p['luas_panen'] - prev_p['luas_panen']):,.0f} Ha".replace(",", "."), border=True)

        html_summary = f"""
        <div class='insight-box' style='border-left-color: #E67E22;'>
            <div class='insight-title'>💡 Sintesis Kondisi Makro Tanah Laut</div>
            <div class='insight-text'>
                Secara agregat, perekonomian Kabupaten Tanah Laut bertumbuh sebesar <b>{growth_ekonomi:.2f}%</b> pada tahun terakhir, diiringi dengan tingkat inflasi daerah yang berada pada level <b>{curr_inf['inflasi_yoy']}%</b>. Dari sisi kesejahteraan, Indeks Pembangunan Manusia menyentuh angka <b>{curr_k['ipm']}</b> dengan persentase penduduk miskin di level <b>{curr_k['p0']}%</b>.
            </div>
        </div>
        """
        st.markdown(html_summary, unsafe_allow_html=True)

# ----------------- HALAMAN 2: PEREKONOMIAN & PDRB -----------------
elif menu == "Perekonomian Daerah (PDRB)":
    st.title(":material/monitoring: Perekonomian Daerah (PDRB)")
    
    if not df_pdrb.empty:
        tahun_terbaru = df_pdrb['tahun'].max()
        df_latest = df_pdrb[df_pdrb['tahun'] == tahun_terbaru].sort_values('nilai_adhb', ascending=False)
        
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum()
        df_pe['pertumbuhan'] = df_pe['nilai_adhk'].pct_change() * 100
        
        st.markdown(generate_analytical_insight(df_pe.dropna(), 'pertumbuhan', 'Pertumbuhan Ekonomi (ADHK)', '%', True), unsafe_allow_html=True)
        
        st.subheader("Eksplorasi Sektoral (Cross-Filtering)")
        st.caption("👈 **Klik batang sektor di grafik kiri** untuk melihat dinamika historisnya pada grafik kanan.")
        
        col_bar, col_line = st.columns([1.2, 1])
        
        with col_bar:
            bar_opts = {
                "title": {"text": f"Pangsa Sektor ({int(tahun_terbaru)})", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "grid": {"left": "35%", "right": "5%", "top": "15%", "bottom": "10%"},
                "xAxis": {"type": "value", "show": False},
                "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}, "axisTick": {"show": False}},
                "series": [{
                    "type": "bar", 
                    "data": df_latest['nilai_adhb'].tolist()[::-1], 
                    "itemStyle": {"color": COLORS[0]},
                    "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")},
                    "emphasis": {"focus": "self", "itemStyle": {"color": COLORS[1]}}
                }]
            }
            # PERBAIKAN: selection_mode="points"
            bar_click = st_echarts(options=bar_opts, height="400px", key="pdrb_bar", on_select="rerun", selection_mode="points")

        with col_line:
            selected_sektor = df_latest.iloc[0]['sektor'] 
            # Menggunakan point_indices sesuai dengan ECharts API Documentation
            if bar_click and "selection" in bar_click and bar_click["selection"].get("point_indices"):
                clicked_index = bar_click["selection"]["point_indices"][0]
                selected_sektor = df_latest['sektor'].tolist()[::-1][clicked_index]
            
            df_trend_sektor = df_pdrb[df_pdrb['sektor'] == selected_sektor].sort_values('tahun')
            
            line_opts = {
                "title": {"text": f"Tren ADHB: {selected_sektor}", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis", "formatter": TOOLTIP_FORMATTER},
                "xAxis": {"type": "category", "data": df_trend_sektor['tahun'].astype(int).astype(str).tolist()},
                "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#EAECEE"}}, "axisLabel": {"formatter": JsCode("function(v){return (v/1000000).toFixed(1) + ' T'}")}},
                "series": [{"type": "line", "smooth": True, "data": df_trend_sektor['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}, "symbolSize": 8}]
            }
            st_echarts(options=line_opts, height="400px", key="pdrb_line")

# ----------------- HALAMAN 3: SOSIAL & KEMISKINAN -----------------
elif menu == "Sosial & Kemiskinan":
    st.title(":material/group: Kondisi Sosial & Kemiskinan")
    
    if not df_kes.empty:
        df_k = df_kes.sort_values('tahun')
        st.markdown(generate_analytical_insight(df_k, 'p0', 'Tingkat Kemiskinan (P0)', '%', False), unsafe_allow_html=True)
        
        dual_opts = {
            "title": {"text": "Garis Kemiskinan vs Jumlah Miskin", "left": "center"},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "legend": {"bottom": 0},
            "xAxis": {"type": "category", "data": df_k['tahun'].astype(int).astype(str).tolist()},
            "yAxis": [
                {"type": "value", "name": "Jiwa", "splitLine": {"show": False}},
                {"type": "value", "name": "Rupiah", "splitLine": {"lineStyle": {"color": "#EAECEE"}}}
            ],
            "series": [
                {"name": "Jumlah Miskin", "type": "bar", "data": df_k['jml_miskin'].tolist(), "itemStyle": {"color": "#94A3B8"}},
                {"name": "Garis Kemiskinan", "type": "line", "yAxisIndex": 1, "data": df_k['garis_kemiskinan'].tolist(), "itemStyle": {"color": COLORS[0]}, "lineStyle": {"width": 3}}
            ]
        }
        st_echarts(options=dual_opts, height="450px")

# ----------------- HALAMAN 4: PERTANIAN -----------------
elif menu == "Sektor Pertanian":
    st.title(":material/agriculture: Sektor Pertanian & Ketahanan Pangan")
    if not df_pert.empty:
        df_padi = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        
        st.markdown(generate_analytical_insight(df_padi, 'produksi', 'Produksi Padi Daerah', 'Ton', True), unsafe_allow_html=True)
        
        padi_opts = {
            "title": {"text": "Dinamika Luas Panen vs Produksi (Padi)", "left": "center"},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": TOOLTIP_FORMATTER},
            "legend": {"bottom": 0},
            "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
            "yAxis": [
                {"type": "value", "name": "Hektar", "splitLine": {"show":False}}, 
                {"type": "value", "name": "Ton", "splitLine": {"lineStyle": {"color": "#EAECEE"}}}
            ],
            "series": [
                {"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}},
                {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}, "symbolSize": 8}
            ]
        }
        st_echarts(options=padi_opts, height="450px")