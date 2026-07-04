import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts, JsCode
import datetime

st.set_page_config(page_title="Dashboard Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- GANTI DENGAN ID GOOGLE SHEETS DARI DATABASE_BPS_TIDY ---
SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"

COLORS = ['#1E3A8A', '#E67E22', '#059669', '#DC2626', '#8E44AD', '#16A085', '#F39C12']

st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 95% !important;}
[data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 800 !important; font-size: 2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1rem !important;}
.insight-box {background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 18px; border-radius: 8px; margin-bottom: 25px;}
.insight-title {font-weight: 800; color: #1E3A8A; margin-bottom: 8px; font-size: 1.1rem;}
.insight-text {font-size: 1rem; line-height: 1.6; color: #334155;}
.stTabs [data-baseweb="tab-list"] {gap: 24px;}
.stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: 600; padding-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# JS ECharts Formatter
FMT_ID = JsCode("""
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
            if col not in ['kecamatan', 'sektor', 'komoditas', 'bulan']: 
                df[col] = df[col].apply(clean_numeric)
        return df
    except: return pd.DataFrame()

def generate_nlg(df, col, name, unit="%", higher_is_good=True):
    if len(df) < 2: return ""
    curr, prev = df.iloc[-1], df.iloc[-2]
    diff = curr[col] - prev[col]
    
    arah = "mengalami kenaikan" if diff > 0 else "mengalami penurunan" if diff < 0 else "tercatat stagnan"
    is_positive = (diff > 0 and higher_is_good) or (diff < 0 and not higher_is_good)
    icon = "📌" if diff == 0 else "✅" if is_positive else "⚠️"
    implikasi = "Stagnasi struktural yang memerlukan intervensi terukur." if diff == 0 else "Tren positif yang merefleksikan fundamental kebijakan berada di jalur yang tepat." if is_positive else "Sinyal peringatan dini (early warning) yang menuntut re-evaluasi kebijakan sektoral oleh OPD."
    
    return f"""
    <div class='insight-box'>
        <div class='insight-title'>{icon} Analisis Eksekutif: {name}</div>
        <div class='insight-text'>Pada {int(curr['tahun'])}, {name} berada pada level <b>{curr[col]:g}{unit}</b>. Dibanding periode sebelumnya, indikator ini {arah} sebesar {abs(diff):.2f} {unit}.<br><i>{implikasi}</i></div>
    </div>
    """

with st.spinner("Sinkronisasi Database..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")

with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="160"></div>', unsafe_allow_html=True)
    menu = st.radio("Menu Navigasi", ["Ringkasan Eksekutif", "Sosial & Demografi", "Ekonomi Makro", "Sektor Pertanian"], label_visibility="collapsed")
    st.markdown("---")
    
    curr_yr = datetime.datetime.now().year
    f_tahun = st.slider("Rentang Analisis", 2020, curr_yr, (2020, curr_yr), label_visibility="collapsed")
    st.caption("BPS Kabupaten Tanah Laut")

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty:
        return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

# ---------------------------------------------------------
# HALAMAN 1: EKSEKUTIF (THE 7 KEY METRICS)
# ---------------------------------------------------------
if menu == "Ringkasan Eksekutif":
    st.title(":material/dashboard: Ringkasan 7 Indikator Makro Utama")
    st.markdown("Potret strategis yang menjadi acuan utama perumusan RKPD & RPJMD daerah.")
    
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf, df_pert]):
        df_kab = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
        c_dem, p_dem = df_kab.iloc[-1], df_kab.iloc[-2] if len(df_kab)>1 else df_kab.iloc[-1]
        
        df_k_srt = df_kes.sort_values('tahun')
        c_kes, p_kes = df_k_srt.iloc[-1], df_k_srt.iloc[-2] if len(df_k_srt)>1 else df_k_srt.iloc[-1]
        
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        c_pe, p_pe = df_pe.iloc[-1], df_pe.iloc[-2] if len(df_pe)>1 else df_pe.iloc[-1]
        gwth = ((c_pe['nilai_adhk'] - p_pe['nilai_adhk']) / p_pe['nilai_adhk']) * 100 if p_pe['nilai_adhk']!=0 else 0
        
        c_inf = df_inf.iloc[-1]
        p_inf = df_inf.iloc[-2] if len(df_inf)>1 else df_inf.iloc[-1]
        
        df_pd = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        c_pd, p_pd = df_pd.iloc[-1], df_pd.iloc[-2] if len(df_pd)>1 else df_pd.iloc[-1]

        st.markdown("#### Kesejahteraan & SDM")
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Kemiskinan (P0) - {int(c_kes['tahun'])}", f"{c_kes['p0']:g}%", f"{c_kes['p0'] - p_kes['p0']:.2f}%", delta_color="inverse", border=True)
        k2.metric(f"Indeks Pembangunan Manusia - {int(c_kes['tahun'])}", f"{c_kes['ipm']:.2f}", f"{c_kes['ipm'] - p_kes['ipm']:.2f}", border=True)
        k3.metric(f"Tingkat Pengangguran (TPT) - {int(c_dem['tahun'])}", f"{c_dem['tpt']:g}%", f"{c_dem['tpt'] - p_dem['tpt']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### Perekonomian & Harga")
        e1, e2 = st.columns(2)
        e1.metric(f"Pertumbuhan Ekonomi - {int(c_pe['tahun'])}", f"{gwth:.2f}%", border=True)
        e2.metric(f"Inflasi YoY - {c_inf['bulan']} {int(c_inf['tahun'])}", f"{c_inf['inflasi_yoy']:g}%", f"{c_inf['inflasi_yoy'] - p_inf['inflasi_yoy']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### Demografi & Pangan")
        d1, d2 = st.columns(2)
        d1.metric(f"Total Penduduk - {int(c_dem['tahun'])}", f"{c_dem['jumlah_penduduk']:,.0f}".replace(",", "."), f"{(c_dem['jumlah_penduduk'] - p_dem['jumlah_penduduk']):,.0f}".replace(",", "."), border=True)
        d2.metric(f"Luas Panen Padi - {int(c_pd['tahun'])}", f"{c_pd['luas_panen']:,.0f} Ha".replace(",", "."), f"{(c_pd['luas_panen'] - p_pd['luas_panen']):,.0f} Ha".replace(",", "."), border=True)

        st.markdown(f"""
        <div class='insight-box' style='border-left-color: #E67E22;'>
            <div class='insight-title'>💡 Sintesis Kondisi Makro</div>
            <div class='insight-text'>Perekonomian bertumbuh <b>{gwth:.2f}%</b> dengan inflasi di level <b>{c_inf['inflasi_yoy']}%</b>. IPM menyentuh angka <b>{c_kes['ipm']}</b> dengan rasio kemiskinan <b>{c_kes['p0']}%</b>.</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# HALAMAN 2: SOSIAL & DEMOGRAFI
# ---------------------------------------------------------
elif menu == "Sosial & Demografi":
    st.title(":material/group: Kondisi Sosial dan Demografi")
    t_kep, t_kem, t_ipm = st.tabs(["Kependudukan", "Kemiskinan", "Pembangunan Manusia (IPM)"])

    with t_kep:
        df_f = apply_filter(df_demo)
        if not df_f.empty:
            df_kab = df_f[df_f['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
            if len(df_kab) > 0:
                c_dem = df_kab.iloc[-1]
                st.metric(f"Total Penduduk ({int(c_dem['tahun'])})", f"{c_dem['jumlah_penduduk']:,.0f}".replace(",", "."), border=True)
                
                df_kec = df_f[(df_f['tahun'] == c_dem['tahun']) & (df_f['kecamatan'].str.lower() != 'tanah laut')].sort_values('jumlah_penduduk', ascending=True)
                if not df_kec.empty:
                    bar_opts = {
                        "title": {"text": "Sebaran Penduduk per Kecamatan"},
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                        "xAxis": {"type": "value", "show": False},
                        "yAxis": {"type": "category", "data": df_kec['kecamatan'].tolist(), "axisLine": {"show": False}, "axisTick": {"show": False}},
                        "series": [{"type": "bar", "data": df_kec['jumlah_penduduk'].tolist(), "itemStyle": {"color": COLORS[0]}, "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")}}]
                    }
                    st_echarts(options=bar_opts, height="400px")

    with t_kem:
        df_f = apply_filter(df_kes)
        if not df_f.empty and len(df_f) > 0:
            df_srt = df_f.sort_values('tahun')
            st.markdown(generate_nlg(df_srt, 'p0', 'Tingkat Kemiskinan (P0)', '%', False), unsafe_allow_html=True)
            
            dual_opts = {
                "title": {"text": "Garis Kemiskinan vs Jumlah Miskin"},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_srt['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Jiwa", "splitLine": {"show": False}}, {"type": "value", "name": "Rupiah", "splitLine": {"lineStyle": {"color": "#eee"}}}],
                "series": [
                    {"name": "Jumlah Miskin", "type": "bar", "data": df_srt['jml_miskin'].tolist(), "itemStyle": {"color": "#94A3B8"}},
                    {"name": "Garis Kemiskinan", "type": "line", "yAxisIndex": 1, "data": df_srt['garis_kemiskinan'].tolist(), "itemStyle": {"color": COLORS[0]}, "lineStyle": {"width": 3}}
                ]
            }
            st_echarts(options=dual_opts, height="450px")

    with t_ipm:
        df_f = apply_filter(df_kes)
        if not df_f.empty and len(df_f) > 0:
            df_srt = df_f.sort_values('tahun')
            st.markdown(generate_nlg(df_srt, 'ipm', 'Indeks Pembangunan Manusia (IPM)', '', True), unsafe_allow_html=True)
            
            ipm_opts = {
                "title": {"text": "Tren Perkembangan IPM"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": df_srt['tahun'].astype(int).astype(str).tolist()},
                "yAxis": {"type": "value", "min": 'dataMin'},
                "series": [{"name": "IPM", "type": "line", "smooth": True, "areaStyle": {"opacity": 0.2}, "data": df_srt['ipm'].tolist(), "itemStyle": {"color": COLORS[2]}, "label": {"show": True}}]
            }
            st_echarts(options=ipm_opts, height="400px")

# ---------------------------------------------------------
# HALAMAN 3: EKONOMI MAKRO
# ---------------------------------------------------------
elif menu == "Ekonomi Makro":
    st.title(":material/monitoring: Kondisi Ekonomi Makro")
    t_pdrb, t_ket, t_inf = st.tabs(["PDRB Sektoral", "Ketenagakerjaan", "Inflasi Daerah"])

    with t_pdrb:
        df_f = apply_filter(df_pdrb)
        if not df_f.empty:
            df_srt = df_f.sort_values('tahun')
            t_max = df_srt['tahun'].max()
            df_latest = df_srt[df_srt['tahun'] == t_max].sort_values('nilai_adhb', ascending=False)
            
            st.subheader("Eksplorasi Sektoral (Cross-Filtering)")
            st.caption("👈 **Klik batang sektor di grafik kiri** untuk melihat dinamika historis ADHB pada grafik kanan.")
            
            c_bar, c_line = st.columns([1.2, 1])
            with c_bar:
                bar_opts = {
                    "title": {"text": f"Pangsa Sektor ({int(t_max)})", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                    "grid": {"left": "35%", "right": "5%", "bottom": "10%"},
                    "xAxis": {"type": "value", "show": False},
                    "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}, "axisTick": {"show": False}},
                    "series": [{"type": "bar", "data": df_latest['nilai_adhb'].tolist()[::-1], "itemStyle": {"color": COLORS[0]}, "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")}}]
                }
                # EVENT KLIK BERJALAN SEMPURNA DI SINI
                clicked = st_echarts(options=bar_opts, events={"click": "function(p){return p.name}"}, height="400px", key="bar_x")
                
            with c_line:
                sel_sektor = clicked if clicked else df_latest.iloc[0]['sektor']
                df_tren = df_srt[df_srt['sektor'] == sel_sektor]
                
                line_opts = {
                    "title": {"text": f"Tren ADHB: {sel_sektor}", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "formatter": FMT_ID},
                    "xAxis": {"type": "category", "data": df_tren['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#eee"}}},
                    "series": [{"type": "line", "smooth": True, "data": df_tren['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}, "symbolSize": 8}]
                }
                st_echarts(options=line_opts, height="400px", key="line_x")

    with t_ket:
        df_f = apply_filter(df_demo)
        if not df_f.empty:
            df_kab = df_f[df_f['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun').dropna(subset=['tpt'])
            if len(df_kab) > 0:
                st.markdown(generate_nlg(df_kab, 'tpt', 'Tingkat Pengangguran Terbuka', '%', False), unsafe_allow_html=True)
                
                tpt_opts = {
                    "title": {"text": "Tren Tingkat Pengangguran Terbuka (TPT)"},
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": df_kab['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value"},
                    "series": [{"name": "TPT (%)", "type": "line", "smooth": True, "data": df_kab['tpt'].tolist(), "itemStyle": {"color": COLORS[3]}, "symbolSize": 8}]
                }
                st_echarts(options=tpt_opts, height="400px")

    with t_inf:
        df_f = apply_filter(df_inf)
        if not df_f.empty:
            df_f['periode'] = df_f['bulan'].astype(str) + " " + df_f['tahun'].astype(int).astype(str)
            
            inf_opts = {
                "title": {"text": "Dinamika Laju Inflasi Bulanan"},
                "tooltip": {"trigger": "axis"},
                "legend": {"bottom": 0},
                "dataZoom": [{"type": "slider", "bottom": 30}],
                "xAxis": {"type": "category", "data": df_f['periode'].tolist()},
                "yAxis": {"type": "value"},
                "series": [
                    {"name": "Inflasi YoY", "type": "line", "smooth": True, "data": df_f['inflasi_yoy'].tolist(), "itemStyle": {"color": COLORS[3]}, "areaStyle": {"opacity": 0.1}},
                    {"name": "Inflasi MtM", "type": "line", "smooth": True, "data": df_f['inflasi_mtm'].tolist(), "itemStyle": {"color": COLORS[0]}}
                ]
            }
            st_echarts(options=inf_opts, height="450px")

# ---------------------------------------------------------
# HALAMAN 4: PERTANIAN
# ---------------------------------------------------------
elif menu == "Sektor Pertanian":
    st.title(":material/agriculture: Ketahanan Pangan & Pertanian")
    
    df_f = apply_filter(df_pert)
    if not df_f.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        if len(df_padi) > 0:
            st.markdown(generate_nlg(df_padi, 'produksi', 'Produksi Padi Daerah', ' Ton', True), unsafe_allow_html=True)
            
            padi_opts = {
                "title": {"text": "Dinamika Luas Panen vs Produksi (Padi)"},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Hektar", "splitLine": {"show":False}}, {"type": "value", "name": "Ton", "splitLine": {"lineStyle": {"color": "#eee"}}}],
                "series": [
                    {"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}},
                    {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}}
                ]
            }
            st_echarts(options=padi_opts, height="450px")
            
    df_n = apply_filter(df_inf)
    if not df_n.empty and 'ntp' in df_n.columns:
        df_n['periode'] = df_n['bulan'].astype(str) + " " + df_n['tahun'].astype(int).astype(str)
        ntp_opts = {
            "title": {"text": "Perkembangan Nilai Tukar Petani (NTP)"},
            "tooltip": {"trigger": "axis"},
            "dataZoom": [{"type": "inside"}],
            "xAxis": {"type": "category", "data": df_n['periode'].tolist()},
            "yAxis": {"type": "value", "scale": True},
            "series": [{"name": "NTP", "type": "line", "data": df_n['ntp'].tolist(), "itemStyle": {"color": COLORS[4]}, "markLine": {"data": [{"yAxis": 100, "name": "Batas Sejahtera"}], "lineStyle": {"color": COLORS[3]}}}]
        }
        st_echarts(options=ntp_opts, height="450px")