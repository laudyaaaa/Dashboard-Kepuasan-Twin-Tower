# dashboard_twin_tower_modern_full.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textwrap import dedent

# ===============================
# Page config + basic CSS (dark gradient + cards)
# ===============================
st.set_page_config(page_title="Dashboard Twin Tower", layout="wide")
st.markdown(
    """
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0c1d, #4b3b5b);
        color: #fff;
    }
    /* Card look */
    .card {
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        margin-bottom: 18px;
    }
    /* Metric */
    div[data-testid="stMetricValue"] {
        color: #00ffff !important;
        font-size: 32px;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #ff77c0 !important;
        font-weight:600;
    }
    /* Header */
    h1, h2, h3, h4 {
        color: #ff77c0;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(20,20,30,0.9);
        color: white;
        padding: 1rem;
        border-radius: 10px;
    }
    /* Tabs style */
    .stTabs [data-baseweb="tab-list"] { justify-content:center; }
    .stTabs [data-baseweb="tab"] { border-radius:10px; background: rgba(255,255,255,0.04); padding:8px 16px; margin:0 6px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg,#ff77c0,#00ffff); color:black; font-weight:700; }
    /* Minor text */
    .small { font-size:13px; color:#d0d0d0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title
st.markdown("<h1 style='text-align:center;'>🏢 Dashboard Analisis Fasilitas Twin Tower</h1>", unsafe_allow_html=True)
st.markdown("<hr style='border:1px solid #ff77c0;'>", unsafe_allow_html=True)

# ===============================
# Load data (local preferred)
# ===============================
DATA_FILENAME = "processed_survey_data.csv"
df = None
if os.path.exists(DATA_FILENAME):
    try:
        df = pd.read_csv(DATA_FILENAME)
        st.sidebar.success(f"✅ Memuat file lokal: {DATA_FILENAME}")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca {DATA_FILENAME}: {e}")

if df is None:
    uploaded_file = st.file_uploader("📂 Upload file hasil survei (CSV) — atau letakkan processed_survey_data.csv di folder script", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.sidebar.success("✅ File CSV berhasil diunggah.")
        except Exception as e:
            st.error(f"Gagal membaca file yang diunggah: {e}")
            st.stop()
    else:
        st.info("Silakan unggah file CSV atau letakkan file 'processed_survey_data.csv' di folder yang sama dengan script ini.")
        st.stop()

# ===============================
# Column normalization (preserve original logic)
# ===============================
col_renames = {}
if "Program_Studi" in df.columns and "Prodi" not in df.columns:
    col_renames["Program_Studi"] = "Prodi"
if "Program Studi" in df.columns and "Prodi" not in df.columns:
    col_renames["Program Studi"] = "Prodi"
if "ProgramStudy" in df.columns and "Prodi" not in df.columns:
    col_renames["ProgramStudy"] = "Prodi"
if "Kepuasan" in df.columns and "Kepuasan_Keseluruhan" not in df.columns:
    col_renames["Kepuasan"] = "Kepuasan_Keseluruhan"
if col_renames:
    df = df.rename(columns=col_renames)

# Ensure required columns exist
required_min = ["Fakultas", "Kepuasan_Keseluruhan"]
missing = [c for c in required_min if c not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan di file CSV: {missing}. Pastikan file mengandung kolom tersebut.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filter Global")
fakultas_opts = ["Semua"] + sorted(df["Fakultas"].dropna().unique().tolist()) if "Fakultas" in df.columns else ["Semua"]
fakultas = st.sidebar.selectbox("Pilih Fakultas:", fakultas_opts)
prodi_opts = ["Semua"] + sorted(df["Prodi"].dropna().unique().tolist()) if "Prodi" in df.columns else ["Semua"]
prodi = st.sidebar.selectbox("Pilih Program Studi:", prodi_opts)

# Apply filters
df_filtered = df.copy()
if fakultas != "Semua" and "Fakultas" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Fakultas"] == fakultas]
if prodi != "Semua" and "Prodi" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Prodi"] == prodi]

if df_filtered.empty:
    st.warning("Tidak ada data setelah filter. Menampilkan seluruh data asli.")
    df_filtered = df.copy()

# Candidate factor list (same as awal)
candidate_factors = [
    "Kualitas_Internet", "Ketersediaan_Fasilitas", "Jam_Operasional", "Peningkatan_Motivasi",
    "Lingkungan_Lebih_Baik", "Fasilitas_Difabel", "Diskusi_Kelompok", "Peningkatan_Citra"
]
available_factors = [c for c in candidate_factors if c in df_filtered.columns]

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Summary", "🔧 Analisis Faktor", "📊 Distribusi & Korelasi"])

# ---------------------------
# TAB 1: Summary
# ---------------------------
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Summary")
    col1, col2, col3 = st.columns(3)
    total_responden = len(df_filtered)
    avg_kepuasan = round(df_filtered["Kepuasan_Keseluruhan"].mean(), 2)
    avg_internet = round(df_filtered["Kualitas_Internet"].mean(), 2) if "Kualitas_Internet" in df_filtered.columns else "N/A"
    avg_kep = df_filtered["Kepuasan_Keseluruhan"].mean()

    with col1:
        st.metric("👥 Total Responden", total_responden, help="Jumlah mahasiswa yang disurvei")
    with col2:
        st.metric("⭐ Rata-rata Kepuasan", avg_kepuasan, help="Rata-rata kepuasan dari 1 (tidak puas) hingga 5 (sangat puas)")
    with col3:
        st.metric("🌐 Rata-rata Internet", avg_internet, help="Rata-rata kualitas internet")
    st.markdown("</div>", unsafe_allow_html=True)

    # explanatory text + gauge
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(
            dedent(f"""
            <div style="text-align:left;">
                <h3 style="color:#00ffff; margin:0;">Tingkat Kepuasan & Dampaknya</h3>
                <p class="small">Rata-rata kepuasan: <strong style="color:#ff77c0;">{avg_kep:.2f} / 5</strong>. Interpretasi: nilai lebih besar dari 3.5 menunjukkan kepuasan umum.</p>
            </div>
            """),
            unsafe_allow_html=True
        )
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_kepuasan,
            number={'font': {'size': 44}},
            gauge={
                'axis': {'range': [0, 5]},
                'bar': {'color': "#00FFFF"},
                'steps': [
                    {'range': [0, 2.5], 'color': "#ff4d4d"},
                    {'range': [2.5, 3.5], 'color': "#ffb84d"},
                    {'range': [3.5, 5], 'color': "#00ff99"}
                ],
                'threshold': {'line': {'color': "white", 'width': 4}, 'value': avg_kepuasan}
            }
        ))
        fig_gauge.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=20,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_right:
        st.markdown("### Grafik Peningkatan Motivasi")
        if "Peningkatan_Motivasi" in df_filtered.columns:
            motiv_counts = df_filtered["Peningkatan_Motivasi"].value_counts().sort_index()
            df_motiv = pd.DataFrame({
                "Skor": motiv_counts.index.astype(str),
                "Jumlah": motiv_counts.values
            })

            fig_motiv = px.bar(
                df_motiv,
                x="Skor",
                y="Jumlah",
                text="Jumlah",
                labels={"Skor": "Skor Motivasi", "Jumlah": "Jumlah Responden"},
                title="",
                color_discrete_sequence=["#ff77c0"]
            )

            fig_motiv.update_traces(
                textposition="outside",
                marker_line_color="white",
                marker_line_width=0.5
            )

            fig_motiv.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",   # area plot transparan
                paper_bgcolor="rgba(0,0,0,0)",  # latar belakang luar juga transparan
                font_color="white",              # teks putih
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False)
            )

            st.plotly_chart(fig_motiv, use_container_width=True)

        else:
            if available_factors:
                means = (
                    df_filtered[available_factors]
                    .mean()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                means.columns = ["Faktor", "Rata-rata"]

                fig_motiv = px.bar(
                    means.head(5),
                    x="Faktor",
                    y="Rata-rata",
                    text="Rata-rata",
                    title="",
                    color_discrete_sequence=["#ff77c0"]
                )

                fig_motiv.update_traces(
                    textposition="outside",
                    marker_line_color="white",
                    marker_line_width=0.5
                )

                fig_motiv.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False)
                )

                st.plotly_chart(fig_motiv, use_container_width=True)
            else:
                st.info("Tidak ada data motivasi atau faktor untuk ditampilkan.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border:1px solid rgba(255,119,192,0.25)'>", unsafe_allow_html=True)

    # Top & Bottom factors (clean version - hide long decimals)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Perbandingan Faktor dengan Skor Kepuasan Tertinggi dan Terendah")

    if available_factors:
        factor_means = (
            df_filtered[available_factors]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )
        factor_means.columns = ["Faktor", "Rata_rata_Skor"]

        # Bulatkan skor rata-rata biar tampil rapi
        factor_means["Rata_rata_Skor"] = factor_means["Rata_rata_Skor"].round(2)

        top_factors = factor_means.head(5)
        bottom_factors = factor_means.tail(5)

        col1, col2 = st.columns(2)

        # Grafik Faktor Terbaik
        with col1:
            st.subheader("Faktor dengan Skor Tertinggi")
            fig_top = px.bar(
                top_factors,
                y="Faktor",
                x="Rata_rata_Skor",
                orientation="h",
                color_discrete_sequence=["#ff77c0"]
            )
            fig_top.update_traces(
                text=None,  # hilangkan teks di batang
                marker_line_color="white",
                marker_line_width=0.5
            )
            fig_top.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, title="Rata-rata Skor"),
                yaxis=dict(showgrid=False, title="Faktor")
            )
            st.plotly_chart(fig_top, use_container_width=True)

        # Grafik Faktor Terendah
        with col2:
            st.subheader("Faktor dengan Skor Terendah")
            fig_bottom = px.bar(
                bottom_factors,
                y="Faktor",
                x="Rata_rata_Skor",
                orientation="h",
                color_discrete_sequence=["#ff77c0"]
            )
            fig_bottom.update_traces(
                text=None,  # hilangkan angka di batang
                marker_line_color="white",
                marker_line_width=0.5
            )
            fig_bottom.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, title="Rata-rata Skor"),
                yaxis=dict(showgrid=False, title="Faktor")
            )
            st.plotly_chart(fig_bottom, use_container_width=True)

        st.markdown(
            "<p style='color:#ffb6d9; font-size:14px;'>"
            "Kiri: Faktor terbaik dengan skor kepuasan tertinggi.<br>"
            "Kanan: Faktor yang memerlukan peningkatan."
            "</p>",
            unsafe_allow_html=True
        )
    else:
        st.info("Tidak ada faktor numerik untuk membandingkan.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        "<hr style='border:1px solid rgba(255,119,192,0.12)'>",
        unsafe_allow_html=True
    )

    # ===============================
    # Rata-rata kepuasan per fakultas 
    # ===============================
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📚 Rata-rata Kepuasan per Fakultas")

    if "Fakultas" in df_filtered.columns and "Kepuasan_Keseluruhan" in df_filtered.columns:
        avg_per_fak = (
            df_filtered.groupby("Fakultas")["Kepuasan_Keseluruhan"]
            .mean()
            .reset_index()
            .sort_values(by="Kepuasan_Keseluruhan", ascending=False)
        )

        fig_fak = px.bar(
            avg_per_fak,
            x="Fakultas",
            y="Kepuasan_Keseluruhan",
            text=avg_per_fak["Kepuasan_Keseluruhan"].round(2),
            title="",
            color_discrete_sequence=["#FF69B4"],
        )

        fig_fak.update_traces(
            textposition="outside",
            textfont=dict(color="white", size=14),
            marker=dict(line=dict(color="white", width=1.5)),
        )

        fig_fak.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            xaxis=dict(title="", tickangle=0, color="white", showgrid=False, showline=False),
            yaxis=dict(title="Rata-rata Kepuasan", color="white", showgrid=False, showline=False),
            margin=dict(t=10, b=40, l=40, r=40),
            hoverlabel=dict(bgcolor="#222", font_color="white"),
            bargap=0.3,
        )

        fig_fak.update_traces(hovertemplate="<b>%{x}</b><br>Skor: %{y:.2f}<extra></extra>")
        st.plotly_chart(fig_fak, use_container_width=True)
    else:
        st.info("Kolom 'Fakultas' atau 'Kepuasan_Keseluruhan' tidak tersedia.")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# TAB 2: Analisis Faktor
# ---------------------------
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Analisis Faktor (Proporsi & Dampak Faktor)")
    st.markdown(" ")
    # Pie chart proporsi responden per fakultas (preserved)
    st.subheader("Proporsi Responden per Fakultas")
    if "Fakultas" in df_filtered.columns:
        pie_data = df_filtered["Fakultas"].value_counts().reset_index()
        pie_data.columns = ["Fakultas", "Jumlah"]
        fig_pie = px.pie(pie_data, values="Jumlah", names="Fakultas", title="", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("**Penjelasan**: Menunjukkan distribusi responden antar fakultas.")
    else:
        st.info("Kolom 'Fakultas' tidak ada.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Stacked contribution (preserved)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Kontribusi Faktor per Fakultas (Rata-rata skor)")
    selected_for_stacked = [c for c in ["Kualitas_Internet","Ketersediaan_Fasilitas","Jam_Operasional","Peningkatan_Motivasi"] if c in available_factors]
    if selected_for_stacked:
        stacked_data = df_filtered.groupby("Fakultas")[selected_for_stacked].mean().reset_index()
        stacked_melted = stacked_data.melt(id_vars="Fakultas", var_name="Faktor", value_name="Skor")
        fig_stacked = px.bar(stacked_melted, x="Fakultas", y="Skor", color="Faktor", barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_stacked.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_stacked, use_container_width=True)
    else:
        st.info("Kolom faktor utama tidak tersedia untuk analisis stacked.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Scatter factor vs kepuasan (preserved)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Hubungan Faktor dengan Kepuasan (Scatter + Trendline)")
    if available_factors and "Kepuasan_Keseluruhan" in df_filtered.columns:
        factor_choice = st.selectbox("Pilih Faktor untuk scatter:", available_factors, key="scatter_factor")
        fig_scatter = px.scatter(df_filtered, x=factor_choice, y="Kepuasan_Keseluruhan",
                                 color="Fakultas" if "Fakultas" in df_filtered.columns else None,
                                 trendline="ols", color_discrete_sequence=px.colors.qualitative.Set1)
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("**Penjelasan**: Titik = responden; garis = trend (OLS).")
    else:
        st.info("Tidak ada faktor numerik atau kolom 'Kepuasan_Keseluruhan' untuk scatter.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Radar (preserved)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Perbandingan Semua Faktor (Radar)")
    if available_factors:
        radar_data = df_filtered[available_factors].mean().reset_index()
        radar_data.columns = ["Faktor", "Skor"]
        fig_radar = go.Figure(data=go.Scatterpolar(r=radar_data["Skor"], theta=radar_data["Faktor"], fill='toself', line_color="#00FFFF"))
        fig_radar.update_layout(polar={'radialaxis': {'range': [0, 5]}}, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("**Penjelasan**: Semakin besar area, semakin kuat dampak faktor.")
    else:
        st.info("Tidak ada faktor numerik untuk radar.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# TAB 3: Distribusi & Korelasi
# ---------------------------
with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Distribusi & Korelasi")
    st.markdown(" ")
    # Histogram (preserved)
    st.subheader("Seberapa Banyak Mahasiswa Puas?")
    if "Kepuasan_Keseluruhan" in df_filtered.columns:
        avg_all = df_filtered["Kepuasan_Keseluruhan"].mean()
        fig_hist = px.histogram(df_filtered, x="Kepuasan_Keseluruhan", nbins=10, title="", color_discrete_sequence=["#ff77c0"])
        fig_hist.add_vline(x=avg_all, line_dash="dash", line_color="#00FFFF", annotation_text=f"Rata-rata: {avg_all:.2f}", annotation_position="top right")
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("**Penjelasan**: Garis biru menunjukkan rata-rata keseluruhan.")
    else:
        st.info("Kolom 'Kepuasan_Keseluruhan' tidak tersedia.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Heatmap korelasi (preserved)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Hubungan Antar Faktor (Heatmap Korelasi dengan Angka)")
    heat_cols = available_factors + (["Kepuasan_Keseluruhan"] if "Kepuasan_Keseluruhan" in df_filtered.columns else [])
    if len(heat_cols) > 1:
        corr = df_filtered[heat_cols].corr()
        fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="RdYlGn", aspect="auto")
        fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10,b=10))
        st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown("**Penjelasan**: Angka di tiap kotak adalah koefisien korelasi (Pearson).", unsafe_allow_html=True)
    else:
        st.info("Tidak cukup kolom numerik untuk membuat heatmap korelasi.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Footer: download + sample data
# ---------------------------
st.markdown("<hr style='border:1px solid rgba(255,119,192,0.12)'>", unsafe_allow_html=True)
with st.expander("📥 Download / Lihat Data (sample)"):
    st.download_button("Unduh CSV (filtered)", df_filtered.to_csv(index=False), "data_kepuasan_filtered.csv")
    st.dataframe(df_filtered.head(20))

st.caption("Dashboard dibuat untuk analisis cepat. Jika nama kolom di file CSV berbeda, beri tahu nama kolomnya agar aku sesuaikan kodenya.")
