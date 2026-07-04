import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts, JsCode
import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA ENTERPRISE ECHARTS
# ==============================================================================
st.set_page_config(page_title="Dashboard Data Strategis BPS", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- MASUKKAN ID GOOGLE SHEETS DARI DATABASE_BPS_TIDY ---
SHEET_ID = "1nQh8AezWpM8TfsaknlNO922yqqBWWBfDKah4fm9tpHU"

# Palet Warna Data-Viz Standar BPS
COLORS = ['#1E3A8A', '#E67E22', '#059669', '#DC2626', '#8E44AD', '#16A085', '#F39C12']

st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 96% !important;}
[data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 800 !important; font-size: 2.2rem !important;}
[data-testid="stMetricDelta"] {font-size: 1rem !important;}
.insight-box {background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 18px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
.insight-title {font-weight: 800; color: #1E3A8A; margin-bottom: 8px; font-size: 1.1rem;}
.insight-text {font-size: 1rem; line-height: 1.6; color: #334155;}
.stTabs [data-baseweb="tab-list"] {gap: 24px;}
.stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: 600; padding-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# Helper JS untuk Tooltip Ribuan/Desimal Indonesia
FMT_ID = JsCode("""
function(params) {
    if (!Array.isArray(params)) {
        return params.name + '<br/>' + params.seriesName + ': <b>' + Number(params.value).toLocaleString('id-ID') + '</b>';
    }
    let res = '<b>' + params[0].name + '</b>';
    for (let i = 0; i < params.length; i++) {
        let val = Number(params[i].value).toLocaleString('id-ID');
        res += '<br/>' + params[i].marker + params[i].seriesName + ': <b>' + val + '</b>';
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

def generate_analytical_insight(df, indicator_col, name, unit="%", higher_is_good=True):
    if len(df) < 2: return ""
    curr, prev = df.iloc[-1], df.iloc[-2]
    val_curr, val_prev = curr[indicator_col], prev[indicator_col]
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
        
    val_fmt = f"{int(val_curr):,}".replace(",", ".") if val_curr >= 1000 else f"{val_curr:g}"

    return f"""
    <div class='insight-box'>
        <div class='insight-title'>{icon} Analisis Eksekutif: {name}</div>
        <div class='insight-text'>
            Pada tahun {int(curr['tahun'])}, {name} berada pada level <b>{val_fmt}{unit}</b>. 
            Dibandingkan periode {int(prev['tahun'])}, indikator ini {arah}{poin}. <br>
            <i>{implikasi}</i>
        </div>
    </div>
    """

with st.spinner("Sinkronisasi Database BPS..."):
    df_demo = fetch_data("Demografi")
    df_kes = fetch_data("Kesejahteraan")
    df_pdrb = fetch_data("PDRB")
    df_inf = fetch_data("Inflasi_NTP")
    df_pert = fetch_data("Pertanian")

# ==============================================================================
# 3. SIDEBAR & GLOBAL TIME FILTER
# ==============================================================================
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg/512px-Logo_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg.png" width="160"></div>', unsafe_allow_html=True)
    st.markdown("### 🧭 Navigasi Strategis")
    menu = st.radio("Menu", ["Ringkasan Eksekutif", "Sosial & Kemiskinan", "Perekonomian Daerah (PDRB)", "Sektor Pertanian"], label_visibility="collapsed")
    st.markdown("---")
    
    st.markdown("### ⏳ Filter Periode Waktu")
    min_year = int(df_demo['tahun'].min()) if not df_demo.empty else 2010
    curr_year = datetime.datetime.now().year
    
    f_tahun = st.slider("Rentang Analisis", min_year, curr_year, (min_year, curr_year), label_visibility="collapsed")
    st.caption("Sesuaikan rentang waktu di seluruh grafik dashboard.")
    st.markdown("---")
    st.caption(f"© {curr_year} BPS Kabupaten Tanah Laut")

def apply_filter(df):
    if 'tahun' in df.columns and not df.empty:
        return df[(df['tahun'] >= f_tahun[0]) & (df['tahun'] <= f_tahun[1])]
    return df

# ==============================================================================
# 4. HALAMAN DASHBOARD INTERAKTIF
# ==============================================================================

# ----------------- HALAMAN 1: EKSEKUTIF -----------------
if menu == "Ringkasan Eksekutif":
    st.title(":material/dashboard: Command Center Makro Daerah")
    st.markdown("Potret makro strategis Kabupaten Tanah Laut yang menjadi acuan utama perumusan kebijakan daerah.")
    
    if not all(df.empty for df in [df_demo, df_kes, df_pdrb, df_inf, df_pert]):
        df_kab = df_demo[df_demo['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
        curr_d, prev_d = df_kab.iloc[-1], df_kab.iloc[-2] if len(df_kab)>1 else df_kab.iloc[-1]
        
        df_k_sorted = df_kes.sort_values('tahun')
        curr_k, prev_k = df_k_sorted.iloc[-1], df_k_sorted.iloc[-2] if len(df_k_sorted)>1 else df_k_sorted.iloc[-1]
        
        df_pe = df_pdrb.groupby('tahun', as_index=False)['nilai_adhk'].sum().sort_values('tahun')
        curr_pe, prev_pe = df_pe.iloc[-1], df_pe.iloc[-2] if len(df_pe)>1 else df_pe.iloc[-1]
        growth_ekonomi = ((curr_pe['nilai_adhk'] - prev_pe['nilai_adhk']) / prev_pe['nilai_adhk']) * 100 if prev_pe['nilai_adhk']!=0 else 0
        
        curr_inf = df_inf.iloc[-1]
        prev_inf = df_inf.iloc[-2] if len(df_inf)>1 else df_inf.iloc[-1]
        
        df_padi = df_pert[df_pert['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        curr_p, prev_p = df_padi.iloc[-1], df_padi.iloc[-2] if len(df_padi)>1 else df_padi.iloc[-1]

        st.markdown("#### 1️⃣ Kesejahteraan & Sumber Daya Manusia")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Kemiskinan (P0) - {int(curr_k['tahun'])}", f"{curr_k['p0']:g}%", f"{curr_k['p0'] - prev_k['p0']:.2f}%", delta_color="inverse", border=True)
        c2.metric(f"Indeks Pembangunan Manusia - {int(curr_k['tahun'])}", f"{curr_k['ipm']:.2f}", f"{curr_k['ipm'] - prev_k['ipm']:.2f}", border=True)
        c3.metric(f"Tingkat Pengangguran (TPT) - {int(curr_d['tahun'])}", f"{curr_d['tpt']:g}%", f"{curr_d['tpt'] - prev_d['tpt']:.2f}%", delta_color="inverse", border=True)

        st.markdown("#### 2️⃣ Perekonomian, Dinamika Harga & Pangan")
        c4, c5, c6 = st.columns(3)
        c4.metric(f"Pertumbuhan Ekonomi - {int(curr_pe['tahun'])}", f"{growth_ekonomi:.2f}%", border=True)
        c5.metric(f"Inflasi YoY - {curr_inf['bulan']} {int(curr_inf['tahun'])}", f"{curr_inf['inflasi_yoy']:g}%", f"{curr_inf['inflasi_yoy'] - prev_inf['inflasi_yoy']:.2f}%", delta_color="inverse", border=True)
        c6.metric(f"Luas Panen Padi - {int(curr_p['tahun'])}", f"{curr_p['luas_panen']:,.0f} Ha".replace(",", "."), f"{(curr_p['luas_panen'] - prev_p['luas_panen']):,.0f} Ha".replace(",", "."), border=True)

        st.markdown(f"""
        <div class='insight-box' style='border-left-color: #E67E22;'>
            <div class='insight-title'>💡 Sintesis Kondisi Makro Tanah Laut</div>
            <div class='insight-text'>Secara agregat, perekonomian Kabupaten Tanah Laut bertumbuh <b>{growth_ekonomi:.2f}%</b> pada tahun terakhir, diiringi inflasi sebesar <b>{curr_inf['inflasi_yoy']}%</b>. Dari sisi kesejahteraan, Indeks Pembangunan Manusia menyentuh angka <b>{curr_k['ipm']}</b> dengan persentase penduduk miskin di level <b>{curr_k['p0']}%</b>.</div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- HALAMAN 2: PEREKONOMIAN & PDRB -----------------
elif menu == "Perekonomian Daerah (PDRB)":
    st.title(":material/monitoring: Perekonomian Daerah & Inflasi")
    t_pdrb, t_inf = st.tabs(["Distribusi & Tren PDRB", "Laju Inflasi Bulanan"])

    with t_pdrb:
        df_f = apply_filter(df_pdrb)
        if not df_f.empty:
            df_pe = df_f.groupby('tahun', as_index=False)['nilai_adhk'].sum()
            df_pe['pertumbuhan'] = df_pe['nilai_adhk'].pct_change() * 100
            st.markdown(generate_analytical_insight(df_pe.dropna(), 'pertumbuhan', 'Pertumbuhan Ekonomi (ADHK)', '%', True), unsafe_allow_html=True)
            
            tahun_terbaru = df_f['tahun'].max()
            df_latest = df_f[df_f['tahun'] == tahun_terbaru].sort_values('nilai_adhb', ascending=False)
            
            c_bar, c_tree, c_line = st.columns([1.2, 1, 1.2])
            
            with c_bar:
                bar_opts = {
                    "title": {"text": f"Pangsa Sektor ({int(tahun_terbaru)})", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                    "grid": {"left": "35%", "right": "5%", "top": "15%", "bottom": "10%"},
                    "xAxis": {"type": "value", "show": False},
                    "yAxis": {"type": "category", "data": df_latest['sektor'].tolist()[::-1], "axisLine": {"show": False}, "axisTick": {"show": False}},
                    "series": [{"type": "bar", "data": df_latest['nilai_adhb'].tolist()[::-1], "itemStyle": {"color": COLORS[0]}, "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")}}]
                }
                bar_click = st_echarts(options=bar_opts, height="380px", key="pdrb_bar", on_select="rerun", selection_mode="points")

            with c_tree:
                tree_data = [{"name": s, "value": v} for s, v in zip(df_latest['sektor'], df_latest['nilai_adhb'])]
                tree_opts = {
                    "title": {"text": "Treemap Komposisi Ekonomi", "textStyle": {"fontSize": 14}},
                    "tooltip": {"formatter": "{b}: {c}"},
                    "series": [{"type": "treemap", "data": tree_data, "roam": False, "label": {"show": True, "formatter": "{b}"}, "itemStyle": {"borderColor": "#fff", "borderWidth": 2}, "color": COLORS}]
                }
                st_echarts(options=tree_opts, height="380px")

            with c_line:
                selected_sektor = df_latest.iloc[0]['sektor'] 
                if bar_click and "selection" in bar_click and bar_click["selection"].get("point_indices"):
                    selected_sektor = df_latest['sektor'].tolist()[::-1][bar_click["selection"]["point_indices"][0]]
                
                df_trend_sektor = df_f[df_f['sektor'] == selected_sektor].sort_values('tahun')
                line_opts = {
                    "title": {"text": f"Tren ADHB: {selected_sektor}", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "formatter": FMT_ID},
                    "xAxis": {"type": "category", "data": df_trend_sektor['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#EAECEE"}}, "axisLabel": {"formatter": JsCode("function(v){return (v/1000000).toFixed(1) + ' T'}")}},
                    "series": [{"type": "line", "smooth": True, "data": df_trend_sektor['nilai_adhb'].tolist(), "itemStyle": {"color": COLORS[1]}, "areaStyle": {"opacity": 0.1}, "symbolSize": 8}]
                }
                st_echarts(options=line_opts, height="380px", key="pdrb_line")

            with st.expander("Tabel Data PDRB (Detail)"):
                st.dataframe(df_f, use_container_width=True)

    with t_inf:
        df_f = apply_filter(df_inf)
        if not df_f.empty:
            df_f['periode'] = df_f['bulan'].astype(str) + " " + df_f['tahun'].astype(int).astype(str)
            curr = df_f.iloc[-1]
            
            c_gauge, c_line = st.columns([1, 2.5])
            with c_gauge:
                gauge_opts = {
                    "title": {"text": "Inflasi YoY Terkini", "left": "center", "textStyle": {"fontSize": 14}},
                    "series": [{"type": "gauge", "progress": {"show": True, "width": 15, "itemStyle": {"color": COLORS[3]}}, "axisLine": {"lineStyle": {"width": 15}}, "axisTick": {"show": False}, "splitLine": {"show": False}, "axisLabel": {"show": False}, "detail": {"valueAnimation": True, "formatter": "{value}%", "fontSize": 24}, "data": [{"value": curr['inflasi_yoy'], "name": ""}]}]
                }
                st_echarts(options=gauge_opts, height="350px")
                
            with c_line:
                inf_opts = {
                    "title": {"text": "Dinamika Laju Inflasi Bulanan", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"bottom": 0},
                    "dataZoom": [{"type": "slider", "bottom": 30}],
                    "xAxis": {"type": "category", "data": df_f['periode'].tolist()},
                    "yAxis": {"type": "value"},
                    "series": [{"name": "Inflasi YoY", "type": "line", "smooth": True, "data": df_f['inflasi_yoy'].tolist(), "itemStyle": {"color": COLORS[3]}, "areaStyle": {"opacity": 0.1}}, {"name": "Inflasi MtM", "type": "line", "smooth": True, "data": df_f['inflasi_mtm'].tolist(), "itemStyle": {"color": COLORS[0]}}]
                }
                st_echarts(options=inf_opts, height="380px")

# ----------------- HALAMAN 3: SOSIAL & KEMISKINAN -----------------
elif menu == "Sosial & Kemiskinan":
    st.title(":material/group: Demografi & Kesejahteraan")
    t_dem, t_kem = st.tabs(["Kependudukan & SDM", "Kemiskinan"])

    with t_dem:
        df_f = apply_filter(df_demo)
        df_ipm = apply_filter(df_kes)
        if not df_f.empty and not df_ipm.empty:
            df_kab = df_f[df_f['kecamatan'].str.lower() == 'tanah laut'].sort_values('tahun')
            
            c_bar, c_pie, c_radar = st.columns([1.5, 1, 1])
            with c_bar:
                df_kec = df_f[(df_f['tahun'] == df_kab.iloc[-1]['tahun']) & (df_f['kecamatan'].str.lower() != 'tanah laut')].sort_values('jumlah_penduduk', ascending=True)
                bar_opts = {
                    "title": {"text": "Sebaran Penduduk per Kecamatan", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter": FMT_ID},
                    "xAxis": {"type": "value", "show": False},
                    "yAxis": {"type": "category", "data": df_kec['kecamatan'].tolist(), "axisLine": {"show": False}, "axisTick": {"show": False}},
                    "series": [{"type": "bar", "data": df_kec['jumlah_penduduk'].tolist(), "itemStyle": {"color": COLORS[0]}, "label": {"show": True, "position": "right", "formatter": JsCode("function(p){return Number(p.value).toLocaleString('id-ID')}")}}]
                }
                st_echarts(options=bar_opts, height="400px")
                
            with c_pie:
                tot_lk, tot_pr = float(df_kab.iloc[-1]['lk']), float(df_kab.iloc[-1]['pr'])
                pie_opts = {
                    "title": {"text": "Komposisi Gender", "textStyle": {"fontSize": 14}, "left": "center"},
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                    "color": [COLORS[0], COLORS[1]],
                    "series": [{"type": "pie", "radius": ["40%", "70%"], "data": [{"name": "Laki-laki", "value": tot_lk}, {"name": "Perempuan", "value": tot_pr}], "itemStyle": {"borderRadius": 5, "borderColor": "#fff", "borderWidth": 2}, "label": {"show": True, "formatter": "{b}\n{d}%"}}]
                }
                st_echarts(options=pie_opts, height="400px")

            with c_radar:
                curr_ipm = df_ipm.sort_values('tahun').iloc[-1]
                radar_opts = {
                    "title": {"text": "Dimensi IPM Daerah", "textStyle": {"fontSize": 14}, "left": "center"},
                    "radar": {"indicator": [{"name": "UHH", "max": 80}, {"name": "HLS", "max": 15}, {"name": "RLS", "max": 12}, {"name": "Pengeluaran", "max": 15000}]},
                    "series": [{"type": "radar", "data": [{"value": [curr_ipm['uhh'], curr_ipm['hls'], curr_ipm['rls'], curr_ipm['pengeluaran']], "name": "Indikator"}], "itemStyle": {"color": COLORS[2]}, "areaStyle": {"opacity": 0.3}}]
                }
                st_echarts(options=radar_opts, height="400px")

    with t_kem:
        df_f = apply_filter(df_kes)
        if not df_f.empty:
            df_k = df_f.sort_values('tahun')
            st.markdown(generate_analytical_insight(df_k, 'p0', 'Persentase Penduduk Miskin (P0)', '%', False), unsafe_allow_html=True)
            
            c_line, c_dual = st.columns([1, 1.5])
            with c_line:
                line_opts = {
                    "title": {"text": "Tren Indeks Kedalaman (P1) & Keparahan (P2)", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": df_k['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": {"type": "value"},
                    "series": [{"name": "P1 (Kedalaman)", "type": "line", "smooth": True, "data": df_k['p1'].tolist(), "itemStyle": {"color": COLORS[1]}}, {"name": "P2 (Keparahan)", "type": "line", "smooth": True, "data": df_k['p2'].tolist(), "itemStyle": {"color": COLORS[3]}}]
                }
                st_echarts(options=line_opts, height="400px")
                
            with c_dual:
                dual_opts = {
                    "title": {"text": "Garis Kemiskinan vs Jumlah Miskin", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                    "legend": {"bottom": 0},
                    "xAxis": {"type": "category", "data": df_k['tahun'].astype(int).astype(str).tolist()},
                    "yAxis": [{"type": "value", "name": "Jiwa", "splitLine": {"show": False}}, {"type": "value", "name": "Rupiah", "splitLine": {"lineStyle": {"color": "#EAECEE"}}}],
                    "series": [{"name": "Jumlah Miskin", "type": "bar", "data": df_k['jml_miskin'].tolist(), "itemStyle": {"color": "#94A3B8"}}, {"name": "Garis Kemiskinan", "type": "line", "yAxisIndex": 1, "data": df_k['garis_kemiskinan'].tolist(), "itemStyle": {"color": COLORS[0]}, "lineStyle": {"width": 3}}]
                }
                st_echarts(options=dual_opts, height="400px")
                
            with st.expander("Tabel Data Kesejahteraan (Detail)"):
                st.dataframe(df_f, use_container_width=True)

# ----------------- HALAMAN 4: PERTANIAN -----------------
elif menu == "Sektor Pertanian":
    st.title(":material/agriculture: Ketahanan Pangan & Pertanian")
    
    df_f = apply_filter(df_pert)
    df_n = apply_filter(df_inf)
    
    if not df_f.empty:
        df_padi = df_f[df_f['komoditas'].str.lower() == 'padi'].sort_values('tahun')
        df_jagung = df_f[df_f['komoditas'].str.lower() == 'jagung'].sort_values('tahun')
        
        st.markdown(generate_analytical_insight(df_padi, 'produksi', 'Produksi Padi Daerah', ' Ton', True), unsafe_allow_html=True)
        
        c_bar, c_line, c_pie = st.columns([1.2, 1.2, 1])
        with c_bar:
            padi_opts = {
                "title": {"text": "Luas Panen vs Produksi (Padi)", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}, "formatter": FMT_ID},
                "legend": {"bottom": 0},
                "xAxis": {"type": "category", "data": df_padi['tahun'].astype(int).astype(str).tolist()},
                "yAxis": [{"type": "value", "name": "Ha", "splitLine": {"show":False}}, {"type": "value", "name": "Ton", "splitLine": {"lineStyle": {"color": "#EAECEE"}}}],
                "series": [{"name": "Luas Panen", "type": "bar", "data": df_padi['luas_panen'].tolist(), "itemStyle": {"color": "#D4E6F1"}}, {"name": "Produksi", "type": "line", "yAxisIndex": 1, "data": df_padi['produksi'].tolist(), "itemStyle": {"color": COLORS[2]}, "lineStyle": {"width": 3}, "symbolSize": 8}]
            }
            st_echarts(options=padi_opts, height="380px")
            
        with c_line:
            if not df_n.empty and 'ntp' in df_n.columns:
                df_n['periode'] = df_n['bulan'].astype(str) + " " + df_n['tahun'].astype(int).astype(str)
                ntp_opts = {
                    "title": {"text": "Perkembangan Nilai Tukar Petani (NTP)", "textStyle": {"fontSize": 14}},
                    "tooltip": {"trigger": "axis"},
                    "dataZoom": [{"type": "inside"}],
                    "xAxis": {"type": "category", "data": df_n['periode'].tolist()},
                    "yAxis": {"type": "value", "scale": True},
                    "series": [{"name": "NTP", "type": "line", "data": df_n['ntp'].tolist(), "itemStyle": {"color": COLORS[4]}, "markLine": {"data": [{"yAxis": 100, "name": "Batas Sejahtera"}], "lineStyle": {"color": COLORS[3]}}}]
                }
                st_echarts(options=ntp_opts, height="380px")

        with c_pie:
            c_padi = df_padi.iloc[-1]['produksi']
            c_jagung = df_jagung.iloc[-1]['produksi'] if len(df_jagung) > 0 else 0
            pie_opts = {
                "title": {"text": f"Share Produksi ({int(df_padi.iloc[-1]['tahun'])})", "textStyle": {"fontSize": 14}, "left": "center"},
                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                "color": [COLORS[2], COLORS[1]],
                "series": [{"type": "pie", "radius": "60%", "data": [{"name": "Padi", "value": c_padi}, {"name": "Jagung", "value": c_jagung}], "itemStyle": {"borderColor": "#fff", "borderWidth": 2}, "label": {"show": True, "formatter": "{b}\n{d}%"}}]
            }
            st_echarts(options=pie_opts, height="380px")
            
        with st.expander("Tabel Data Pertanian & NTP (Detail)"):
            c_tb1, c_tb2 = st.columns(2)
            c_tb1.dataframe(df_f, use_container_width=True)
            c_tb2.dataframe(df_n, use_container_width=True)