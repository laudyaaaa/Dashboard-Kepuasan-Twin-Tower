import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textwrap import dedent

# === KONFIGURASI DASHBOARD ===
st.set_page_config(page_title="Dashboard Twin Tower", layout="wide")
st.title("🏢 Dashboard Kepuasan Mahasiswa Terhadap Twin Tower")
st.markdown("---")  # Pemisah untuk tampilan rapi

# ---------------------
# Load data: prefer processed_survey_data.csv if exists, otherwise ask upload
# ---------------------
DATA_FILENAME = "processed_survey_data.csv"

df = None
# 1) coba baca file lokal bernama processed_survey_data.csv
if os.path.exists(DATA_FILENAME):
    try:
        df = pd.read_csv(DATA_FILENAME)
        st.sidebar.success(f"✅ Memuat file lokal: {DATA_FILENAME}")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca {DATA_FILENAME}: {e}")

# 2) jika belum ada/bermasalah, minta upload
if df is None:
    uploaded_file = st.file_uploader("📂 Upload file hasil survei (CSV) — atau taruh file processed_survey_data.csv di folder yang sama", type=["csv"])
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

# ---------------------
# Normalisasi nama kolom umum (jika ada variasi)
# ---------------------
# Jika kolom bernama Program_Studi / Program Studi -> ubah ke 'Prodi' untuk konsistensi
col_renames = {}
if "Program_Studi" in df.columns and "Prodi" not in df.columns:
    col_renames["Program_Studi"] = "Prodi"
if "Program Studi" in df.columns and "Prodi" not in df.columns:
    col_renames["Program Studi"] = "Prodi"
if "ProgramStudy" in df.columns and "Prodi" not in df.columns:
    col_renames["ProgramStudy"] = "Prodi"
# Some datasets might use different name for overall satisfaction
if "Kepuasan" in df.columns and "Kepuasan_Keseluruhan" not in df.columns:
    col_renames["Kepuasan"] = "Kepuasan_Keseluruhan"
if col_renames:
    df = df.rename(columns=col_renames)

# Pastikan kolom penting minimal ada
required_min = ["Fakultas", "Kepuasan_Keseluruhan"]
missing = [c for c in required_min if c not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan di file CSV: {missing}. Pastikan file mengandung kolom tersebut.")
    st.stop()

# ---------------------
# Sidebar filters (global)
# ---------------------
st.sidebar.header("Filter Global")
fakultas_opts = ["Semua"] + sorted(df["Fakultas"].dropna().unique().tolist()) if "Fakultas" in df.columns else ["Semua"]
fakultas = st.sidebar.selectbox("Pilih Fakultas:", fakultas_opts)

prodi_opts = ["Semua"] + sorted(df["Prodi"].dropna().unique().tolist()) if "Prodi" in df.columns else ["Semua"]
prodi = st.sidebar.selectbox("Pilih Program Studi:", prodi_opts)

# apply filters
df_filtered = df.copy()
if fakultas != "Semua" and "Fakultas" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Fakultas"] == fakultas]
if prodi != "Semua" and "Prodi" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Prodi"] == prodi]

if df_filtered.empty:
    st.warning("Tidak ada data setelah filter. Menampilkan seluruh data asli.")
    df_filtered = df.copy()

# define available factor columns (common names) — akan dipakai untuk analisis
candidate_factors = [
    "Kualitas_Internet", "Ketersediaan_Fasilitas", "Jam_Operasional", "Peningkatan_Motivasi",
    "Lingkungan_Lebih_Baik", "Fasilitas_Difabel", "Diskusi_Kelompok", "Peningkatan_Citra"
]
available_factors = [c for c in candidate_factors if c in df_filtered.columns]

# ---------------------
# Tabs
# ---------------------
tab1, tab2, tab3 = st.tabs(["📋 Summary", "🔧 Analisis Faktor", "📊 Distribusi & Korelasi"])

# ---------- TAB 1: Summary ----------
with tab1:
    st.header("📋 Summary")
    st.markdown("")  # spacing

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

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown(
            dedent(f"""
            <div style="text-align:left; margin-bottom:10px;">
                <h1 style="color:#0d6efd; font-size:40px; margin:0; line-height:1.05;">
                    💬 Ternyata, tingkat kepuasan mahasiswa terhadap fasilitas Twin Tower itu tinggi
                </h1>
                <p style="color:#333; font-size:18px; margin-top:8px;">
                    Rata-rata kepuasan: <strong style="color:#ff7f50; font-size:22px;">{avg_kep:.2f} / 5</strong>
                </p>
            </div>
            """),
            unsafe_allow_html=True
        )

        # Grafik gauge langsung di bawah teks
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_kepuasan,
            number={'font': {'size': 48}},
            gauge={
                'axis': {'range': [0, 5]},
                'bar': {'color': "green" if avg_kepuasan >= 3.5 else "orange"},
                'steps': [
                    {'range': [0, 2.5], 'color': "red"},
                    {'range': [2.5, 3.5], 'color': "orange"},
                    {'range': [3.5, 5], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.8,
                    'value': avg_kepuasan
                }
            }
        ))

        # Layout gauge
        fig_gauge.update_layout(
            height=250,
            margin=dict(t=20, b=0, l=0, r=0),
            template="plotly_white"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Penjelasan kecil
        st.markdown(
            "<p style='font-size:14px; color:#aaa;'>"
            "Penjelasan: Ini menunjukkan level kepuasan secara keseluruhan. "
            "Jika jarum di hijau, berarti mahasiswa umumnya puas."
            "</p>",
            unsafe_allow_html=True
        )

    
    with col_right:
        st.markdown("### 🔥 Yang menyebabkan peningkatan motivasi mahasiswa dalam belajar")
        if "Peningkatan_Motivasi" in df_filtered.columns:
            motiv_counts = df_filtered["Peningkatan_Motivasi"].value_counts().sort_index()
            df_motiv = pd.DataFrame({"Skor": motiv_counts.index.astype(str), "Jumlah": motiv_counts.values})
            fig_motiv = px.bar(df_motiv, x="Skor", y="Jumlah", text="Jumlah",
                               labels={"Skor":"Skor Motivasi","Jumlah":"Jumlah Responden"},
                               title="")
            fig_motiv.update_layout(margin=dict(t=10,b=10))
            st.plotly_chart(fig_motiv, use_container_width=True, height=250)
        else:
            if available_factors:
                means = df_filtered[available_factors].mean().sort_values(ascending=False).reset_index()
                means.columns = ["Faktor", "Rata-rata"]
                fig_motiv = px.bar(means.head(5), x="Faktor", y="Rata-rata", text="Rata-rata", title="")
                fig_motiv.update_layout(margin=dict(t=10,b=10))
                st.plotly_chart(fig_motiv, use_container_width=True, height=250)
            else:
                st.info("Tidak ada data motivasi atau faktor untuk ditampilkan.")

    st.markdown("---")

    # Ranking faktor terbaik (top 5)
    st.header("🏆 Top Faktor Terbaik & Terburuk")
    if available_factors:
        factor_means = df_filtered[available_factors].mean().sort_values(ascending=False).reset_index()
        factor_means.columns = ["Faktor", "Rata_rata_Skor"]
        top_factors = factor_means.head(5)
        bottom_factors = factor_means.tail(5)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_top = px.bar(top_factors, y="Faktor", x="Rata_rata_Skor", orientation="h", color_discrete_sequence=["#FF69B4"])
            fig_top.update_layout(template="plotly_white")
            st.plotly_chart(fig_top, use_container_width=True)
        with col2:
            fig_bottom = px.bar(bottom_factors, y="Faktor", x="Rata_rata_Skor", orientation="h", color_discrete_sequence=["#FF69B4"])
            fig_bottom.update_layout(template="plotly_white")
            st.plotly_chart(fig_bottom, use_container_width=True)
        st.markdown("**Penjelasan**: Bagian kiri menunjukkan faktor terbaik (skor tinggi), bagian kanan menunjukkan yang perlu diperbaiki (skor rendah).")
    
    st.markdown("---")

    # Diagram rata-rata kepuasan per fakultas (bar)
    st.subheader("📊 Rata-rata Kepuasan per Fakultas")
    if "Fakultas" in df_filtered.columns and "Kepuasan_Keseluruhan" in df_filtered.columns:
        avg_per_fak = df_filtered.groupby("Fakultas")["Kepuasan_Keseluruhan"].mean().reset_index().sort_values(by="Kepuasan_Keseluruhan", ascending=False)
        fig_fak = px.bar(avg_per_fak, x="Fakultas", y="Kepuasan_Keseluruhan", text=avg_per_fak["Kepuasan_Keseluruhan"].round(2), title="")
        fig_fak.update_layout(xaxis_title="", yaxis_title="Rata-rata Kepuasan", margin=dict(t=10))
        st.plotly_chart(fig_fak, use_container_width=True)
    else:
        st.info("Kolom 'Fakultas' atau 'Kepuasan_Keseluruhan' tidak tersedia.")

# ---------- TAB 2: Analisis Faktor ----------
with tab2:
    st.header("🔧 Analisis Faktor (Proporsi & Dampak Faktor)")
    st.markdown(" ")

    # Piechart proporsi responden per fakultas
    st.subheader("🥧 Proporsi Responden per Fakultas")
    if "Fakultas" in df_filtered.columns:
        pie_data = df_filtered["Fakultas"].value_counts().reset_index()
        pie_data.columns = ["Fakultas", "Jumlah"]
        fig_pie = px.pie(pie_data, values="Jumlah", names="Fakultas", title="", color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("**Penjelasan**: Menunjukkan distribusi responden antar fakultas.")
    else:
        st.info("Kolom 'Fakultas' tidak ada.")

    st.markdown("---")

    # Stacked contribution of selected factors per fakultas
    st.subheader("📈 Kontribusi Faktor per Fakultas (Rata-rata skor)")
    selected_for_stacked = [c for c in ["Kualitas_Internet","Ketersediaan_Fasilitas","Jam_Operasional","Peningkatan_Motivasi"] if c in available_factors]
    if selected_for_stacked:
        stacked_data = df_filtered.groupby("Fakultas")[selected_for_stacked].mean().reset_index()
        stacked_melted = stacked_data.melt(id_vars="Fakultas", var_name="Faktor", value_name="Skor")
        fig_stacked = px.bar(stacked_melted, x="Fakultas", y="Skor", color="Faktor", barmode="stack")
        fig_stacked.update_layout(margin=dict(t=10))
        st.plotly_chart(fig_stacked, use_container_width=True)
    else:
        st.info("Kolom faktor utama tidak tersedia untuk analisis stacked.")

    st.markdown("---")

    # Scatter factor vs kepuasan (allow user choose factor)
    st.subheader("🔍 Hubungan Faktor dengan Kepuasan (Scatter + Trendline)")
    if available_factors and "Kepuasan_Keseluruhan" in df_filtered.columns:
        factor_choice = st.selectbox("Pilih Faktor untuk scatter:", available_factors)
        fig_scatter = px.scatter(df_filtered, x=factor_choice, y="Kepuasan_Keseluruhan", color="Fakultas" if "Fakultas" in df_filtered.columns else None, trendline="ols")
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("**Penjelasan**: Titik = responden; garis = trend (OLS).")
    else:
        st.info("Tidak ada faktor numerik atau kolom 'Kepuasan_Keseluruhan' untuk scatter.")

    st.markdown("---")

    # Radar (spider) of all available factors (mean)
    st.subheader("📡 Radar: Perbandingan Semua Faktor (Rata-rata skor)")
    if available_factors:
        radar_df = df_filtered[available_factors].mean().reset_index()
        radar_df.columns = ["Faktor", "Skor"]
        fig_rad = go.Figure(data=go.Scatterpolar(r=radar_df["Skor"], theta=radar_df["Faktor"], fill='toself'))
        fig_rad.update_layout(polar={'radialaxis': {'range':[0,5]}}, margin=dict(t=10))
        st.plotly_chart(fig_rad, use_container_width=True)
        st.markdown("**Penjelasan**: Area lebih besar = faktor lebih kuat.")
    else:
        st.info("Tidak ada faktor untuk radar chart.")

# ---------- TAB 3: Distribusi & Korelasi ----------
with tab3:
    st.header("📊 Distribusi & Korelasi")
    st.markdown(" ")

    # Histogram kepuasan with average vline
    st.subheader("🎯 Seberapa Banyak Mahasiswa Puas?")
    if "Kepuasan_Keseluruhan" in df_filtered.columns:
        avg_all = df_filtered["Kepuasan_Keseluruhan"].mean()
        fig_hist = px.histogram(df_filtered, x="Kepuasan_Keseluruhan", nbins=10, title="")
        fig_hist.add_vline(x=avg_all, line_dash="dash", line_color="red", annotation_text=f"Rata-rata: {avg_all:.2f}", annotation_position="top right")
        st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("**Penjelasan**: Garis merah menunjukkan rata-rata keseluruhan.")
    else:
        st.info("Kolom 'Kepuasan_Keseluruhan' tidak tersedia.")

    st.markdown("---")

    # Boxplot by faculty
    st.subheader("📦 Variasi Kepuasan di Setiap Fakultas (Boxplot)")
    if "Fakultas" in df_filtered.columns and "Kepuasan_Keseluruhan" in df_filtered.columns:
        fig_box = px.box(df_filtered, x="Fakultas", y="Kepuasan_Keseluruhan", points="all", title="")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("Kolom yang dibutuhkan tidak tersedia untuk boxplot.")

    st.markdown("---")

    # Scatter factor vs kepuasan (selectable)
    st.subheader("🔍 Hubungan Faktor dan Kepuasan (Pilih Faktor)")
    if available_factors and "Kepuasan_Keseluruhan" in df_filtered.columns:
        factor_for_dist = st.selectbox("Pilih Faktor untuk melihat distribusi hubungannya:", available_factors, key="dist_factor")
        fig_sc2 = px.scatter(df_filtered, x=factor_for_dist, y="Kepuasan_Keseluruhan", trendline="ols")
        st.plotly_chart(fig_sc2, use_container_width=True)
    else:
        st.info("Tidak ada faktor numerik atau kolom kepuasan untuk analisis ini.")

    st.markdown("---")

    # Heatmap korelasi with numbers in each block
    st.subheader("🔥 Hubungan Antar Faktor (Heatmap Korelasi dengan Angka)")
    heat_cols = available_factors + (["Kepuasan_Keseluruhan"] if "Kepuasan_Keseluruhan" in df_filtered.columns else [])
    if len(heat_cols) > 1:
        corr = df_filtered[heat_cols].corr()
        fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="RdYlGn", aspect="auto")
        fig_heat.update_layout(margin=dict(t=10))
        st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown("**Penjelasan**: Angka di tiap kotak adalah koefisien korelasi (Pearson). Nilai dekat 1/-1 menunjukkan korelasi kuat.")
    else:
        st.info("Tidak cukup kolom numerik untuk membuat heatmap korelasi.")

# ---------------------
# Download / footer
# ---------------------
st.markdown("---")
with st.expander("📥 Download / Lihat Data (sample)"):
    st.download_button("Unduh CSV (filtered)", df_filtered.to_csv(index=False), "data_kepuasan_filtered.csv")
    st.dataframe(df_filtered.head(20))

st.caption("Dashboard dibuat untuk analisis cepat. Jika nama kolom di file CSV berbeda, beri tahu nama kolomnya agar aku sesuaikan kodenya.")
