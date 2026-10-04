import time
import streamlit as st
import os # ini buat cek file ada apa nggak
import pandas as pd
import string 
import matplotlib.pyplot as plt 
import matplotlib.patches as patches
import datetime # 1. Import buat ambil tanggal hari ini
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas 
from reportlab.lib.utils import ImageReader 
from streamlit_drawable_canvas import st_canvas
import numpy as np

st.set_page_config(page_title="Kalkulator", layout="centered")

# ========== 1. FUNGSI BACA/TULIS FILE ==========
FILE_PASSWORD = "password.txt"
def baca_password():
    if os.path.exists(FILE_PASSWORD):
        with open(FILE_PASSWORD, "r") as f:
            return f.read().strip() # .strip() buat buang enter
    else:
        return "admin123" # password default kalau file belum ada

def simpan_password(pw_baru):
    with open(FILE_PASSWORD, "w") as f:
        f.write(pw_baru)

# ========== 1C. FUNGSI HITUNG LUAS & KELILING ==========
def hitung_luas(panjang, lebar):
    return panjang * lebar

def hitung_keliling(panjang, lebar):
    return 2 * (panjang + lebar)

# ========== 2. SETUP AWAL ==========
if "login" not in st.session_state: st.session_state.login = False
if 'tema_gelap' not in st.session_state: st.session_state.tema_gelap = False
if "riwayat" not in st.session_state: st.session_state.riwayat = []
if "hasil_psikologi" not in st.session_state: st.session_state.hasil_psikologi = "Belum dianalisis"
if "password_saat_ini" not in st.session_state: 
    st.session_state.password_saat_ini = baca_password() # NAH INI BEDANYA! Kita ambil dari file, bukan hardcoded

# ========== 3. GERBANG LOGIN ==========
if not st.session_state.login:
    st.title("🔒 Login")
    password = st.text_input("Masukkan Password", type="password", key="login_pw")
    if st.button("Login", key="btn_login"): # button juga dikasih key biar aman
        if password == st.session_state.password_saat_ini:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Password Salah!")

# ========== 4. ISI APP SETELAH LOGIN ============
else: 
    # HEADER + TOMBOL
    colA, colB = st.columns([3,1])
    with colA:
        if st.button("🌙 Mode Gelap" if not st.session_state.tema_gelap else "☀️ Mode Terang"):
            st.session_state.tema_gelap = not st.session_state.tema_gelap
            st.rerun()
    with colB:
        if st.button("Logout"):
            st.session_state.login = False
            st.rerun()

    st.title("🧮 ARSITEK ANTI BONCOS")
    st.markdown(""" **APLIKASI KALKULATOR** """)

    # ========== 1B. UPLOADER LOGO DI SIDEBAR ==========
    st.sidebar.title("⚙️ Pengaturan App")
    tampilkan_draft = st.sidebar.checkbox("Tampilkan watermark DRAFT", value=True)

    uploaded_logo = st.sidebar.file_uploader(
        "Upload Logo Perusahaan",
        type=["png", "jpg", "jpeg"],
        help="Upload logo transparan PNG supaya bagus di PDF"
        )

    logo_path = None
    if uploaded_logo is not None:
        # Simpan file upload ke folder sementara
        with open("temp_logo.png", "wb") as f:
            f.write(uploaded_logo.getbuffer())
            logo_path = "temp_logo.png"
            st.sidebar.success("Logo berhasil diupload!")
    else:
        st.sidebar.info("Pakai logo default jika tidak upload")

    # Ganti Password
    with st.expander("⚙️ Pengaturan Akun"): # biar rapih ketutup
        st.subheader("Ganti Password")  
        pass_lama = st.text_input("Password Lama", type="password", key="plama")
        pass_baru = st.text_input("Password Baru", type="password", key="pbaru", autocomplete="new-password")
        pass_baru_2 = st.text_input("Ulangi Password Baru", type="password", key="pbaru2", autocomplete="new-password")

        if st.button("Simpan Password Baru"):
            if pass_lama != st.session_state.password_saat_ini: 
                st.error("Password lama salah!")
            elif pass_baru != pass_baru_2: 
                st.error("Password baru tidak sama!")
            elif len(pass_baru) < 8: # sekalian naikin jadi 8 biar kuat
                st.error("Password minimal 8 karakter!")
            elif not any(char.isdigit() for char in pass_baru):
                st.error("❌ Password harus ada angkanya! 0-9")
            elif not any(char.isupper() for char in pass_baru): # <-- CEK HURUF BESAR
                st.error("❌ Password harus ada huruf BESAR! A-Z")
            elif not any(char in string.punctuation for char in pass_baru): # <-- CEK KARAKTER !@#
                st.error("❌ Password harus ada karakter spesial! !@#$")
            else:
                simpan_password(pass_baru)
                st.session_state.password_saat_ini = pass_baru
                st.success("✅ Password berhasil diganti!")
                st.info("Logout dulu biar aktif")

    # Tambahin ini 
    def reset_form():
        st.session_state.panjang = 0.0
        st.session_state.lebar = 0.0
        st.session_state.jumlah_kamar = 1
        st.session_state.jumlah_gedung = 1 # <-- TAMBAH INI
        st.session_state.jumlah_kamar_gedung = 1 # <-- TAMBAH INI
        st.session_state.harga_per_m2 = 5000000 # <-- TAMBAH INI
   
    # Input Baru: Pilih Mode Dulu
    mode = st.radio(
        "Mau bikin apa:",
        ["Rumah", "Hotel", "Kompleks"],
        key="mode"
    )

    # Input Kalkulator
    panjang = st.number_input("Masukkan Panjang", min_value=0.0, key="panjang")
    lebar = st.number_input("Masukkan Lebar", min_value=0.0, key="lebar")
    harga_per_m2 = st.number_input("Harga per m² (Rp)", min_value=0, value=5000000, step=100000)

    # Jumlah kamar nyesuain mode
    if mode == "Rumah":
        jumlah_kamar = st.number_input("Jumlah Kamar", min_value=1, value=1, key="jumlah_kamar") 
        max_kamar = 10
    elif mode == "Hotel":
        jumlah_kamar = st.number_input("Jumlah Kamar", min_value=1, value=1, key="jumlah_kamar")                              
        max_kamar = 30
    else: # Mode Kompleks
        jumlah_gedung = st.number_input("Jumlah Gedung", min_value=1, value=1, key="jumlah_gedung")
        jumlah_kamar_per_gedung = st.number_input("Jumlah Kamar per Gedung", min_value=1, value=1, key="jumlah_kamar_gedung")                          
        max_kamar = 150 # 5 gedung x 30 kamar

    pilihan = st.radio("Pilih mau hitung apa:", ["Luas", "Keliling", "Luas Banyak Kamar"])    

    # Input Psikologi Ruangan
    st.markdown("---") # garis pemisah
    st.header("🧠 Tab 2: Analisis Kepribadian Ruangan")
    st.write("Isi data di bawah buat tau kepribadian ruang ideal kamu")

    col_psiko1, col_psiko2 = st.columns([2,1]) # bikin 2 kolom biar rapih
    with col_psiko1:
        warna = st.selectbox("Warna kamar favorit kamu?", ["Biru", "Kuning", "Hijau", "Putih", "Abu-abu"])
        luas_ideal = st.slider("Luas kamar ideal menurut kamu? m2", 8, 40, 15)

    with col_psiko2:
        st.write("") # spacer
        st.write("")

    # PROSES - "IF ELSE"
    def analisis_kepribadian(warna, luas):
        if warna == "Biru" and luas > 20: # if = JIKA # JIKA warna biru DAN luas > 20m2     
            return "Kamu tipe 'The Calm Leader'. Tenang, suka mikir, butuh space buat me time."
        elif warna == "Kuning":     # elif = JIKA TIDAK, TAPI JIKA  # JIKA warna kuning
            return "Kamu tipe 'The Sunshine'. Ceria, kreatif, energi kamu bikin orang semangat."
        elif warna == "Hijau" and luas < 15:  # JIKA warna kuning # JIKA warna hijau DAN luas kecil
            return "Kamu tipe 'Cozy Nature'. Suka yang rapi, natural, dan hangat."
        else:  # else = JIKA LAINNYA, KALAU GA MASUK SEMUA DI ATAS
            return "Kamu tipe 'Minimalis Elegan'. Suka yang bersih, simpel, dan estetik."

    # TOMBOL BESAR
    if st.button("🔮 Analisis Kepribadian", type="primary", use_container_width=True):
        hasil = analisis_kepribadian(warna, luas_ideal)
        st.session_state.hasil_psikologi = hasil # SIMPEN BUAT PDF
        st.success(f"Hasil Analisis: {hasil}")
    
    # 1. TAMBAHIN INPUT NAMA & ALAMAT DULU, TARUH DI ATAS TOMBOL HITUNG
    st.subheader("Data Laporan")
    nama = st.text_input("Nama Pemilik", key="nama")
    alamat = st.text_input("Alamat Proyek", key="alamat")

    st.markdown("### ✍️ Tanda Tangan Digital")
    st.write("Tanda Tangan bisa memakai mouse atau jari di trackpad/screen")

    canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 0)",
    stroke_width=3,
    stroke_color="#000000",
    background_color="#ffffff",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
    )

    if canvas_result.image_data is not None:
        img = Image.fromarray(np.uint8(canvas_result.image_data))
        img = img.convert("RGBA") # Background transparan
        img.save("ttd.png")
        st.session_state['path_ttd'] = "ttd.png"
        st.success("TTD Tersimpan!")

    # MESIN HITUNG
    col1, col2 = st.columns(2)
    with col1:    
        if st.button ("📝 HITUNG!", type="primary", use_container_width=True):
            # Gerbang Validasi
            if panjang == 0 or lebar == 0:  
                st.warning("❌ Isi dulu panjang & lebarnya")
            elif panjang >1000:
                st.error("⚠️ Panjang tidak boleh lebih dari 1000 meter!")
            elif lebar > 1000:
                st.error("⚠️ Lebar tidak boleh lebih dari 1000 meter!")    
            elif mode == "Kompleks" and (jumlah_gedung * jumlah_kamar_per_gedung) > 150:     
                st.error("⚠️ Maksimal 150 kamar total! 5 Gedung x 30 Kamar")      
            elif mode == "Hotel" and jumlah_kamar > 30:     
                st.error("⚠️ Maksimal 30 kamar!")   
            elif mode == "Rumah" and jumlah_kamar > 10:
                st.error("⚠️ Maksimal 10 kamar!")
            else:                           
                # Gerbang 2: Kalau lolos semua, baru ngitung. 
                placeholder = st.empty()
                for i in range(3):  # animasi loading
                    placeholder.info("Sedang menghitung...")    
                    time.sleep(0.3)                             
                    placeholder.empty()                         
                    time.sleep(0.3)                                    

                luas_1_kamar = hitung_luas(panjang, lebar)
                keliling_1_kamar = hitung_keliling(panjang, lebar)

                # LOGIKA UTAMA: PILIH MODE 
                if mode == "Rumah":
                    if pilihan == "Luas":
                        hasil_total = luas_1_kamar
                        placeholder.success(f"Luas 1 Kamar: {hasil_total} m²")
                        total_biaya = hasil_total * harga_per_m2 # hitung juga biayanya
                        st.session_state.riwayat.append(f"Rumah 1 kamar {panjang}x{lebar} = {hasil_total:.2f}m² | Rp {total_biaya:,.0f}")
                    elif pilihan == "Keliling":
                        hasil_total = keliling_1_kamar
                        placeholder.success(f"Keliling 1 Kamar: {hasil_total} m")
                        total_biaya = hasil_total * harga_per_m2 # hitung juga biayanya
                        st.session_state.riwayat.append(f"Keliling 1 Kamar {panjang}x{lebar} = {hasil_total:.2f}m | Rp {total_biaya:,.0f}")
                    else: # Luas Banyak Kamar
                        hasil_total = luas_1_kamar * jumlah_kamar
                        placeholder.success(f"Luas 1 Kamar: {luas_1_kamar} m²")
                        st.success(f"Total Luas {jumlah_kamar} Kamar Rumah: {hasil_total} m²")    
                        # Tambahin ini
                        total_biaya = hasil_total * harga_per_m2
                        st.metric(label="💰 Estimasi Biaya Bangun", value=f"Rp {total_biaya:,.0f}")
                    
                        st.session_state.riwayat.append(f"Rumah {jumlah_kamar} kamar = {hasil_total:.2f}m² | Rp {total_biaya:,.0f}")

                elif mode == "Hotel":
                    hasil_total = luas_1_kamar * jumlah_kamar
                    placeholder.success(f"Luas 1 Kamar: {luas_1_kamar} m²")
                    st.success(f"Total Luas {jumlah_kamar} Kamar Hotel: {hasil_total} m²") # FIX TYPO
                    
                    # Tambahin ini 
                    total_biaya = hasil_total * harga_per_m2
                    st.metric(label="💰 Estimasi Biaya Bangun", value=f"Rp {total_biaya:,.0f}")    
                    
                    st.session_state.riwayat.append(f"Hotel {jumlah_kamar} kamar = {hasil_total:.2f}m² | Rp {total_biaya:,.0f}")

                else: # Mode Kompleks
                    hasil_per_gedung = luas_1_kamar * jumlah_kamar_per_gedung
                    hasil_total = hasil_per_gedung * jumlah_gedung
                    placeholder.success(f"Luas per Gedung: {hasil_per_gedung} m²")
                    st.success(f"Total Luas {jumlah_gedung} Gedung: {hasil_total} m²")
                    
                    total_biaya = hasil_total * harga_per_m2 
                    st.metric(label="💰 Estimasi Biaya Bangun", value=f"Rp {total_biaya:,.0f}")

                    st.session_state.riwayat.append(f"Kompleks {jumlah_gedung} gedung = {hasil_total:.2f}m² | Rp {total_biaya:,.0f}")
        
                # ==== GAMBAR DENAH + PINTU + JENDELA ====
                # Tentukan berapa kamar yang mau digambar
                if mode == "Kompleks":
                    jml_gambar = jumlah_gedung * jumlah_kamar_per_gedung
                else:
                    jml_gambar = jumlah_kamar

                # Biar tidak terlalu lebar, maksimal 5 kamar per baris
                lebar_gambar = min(jml_gambar, 5) * (panjang + 1.5)
                fig, ax = plt.subplots(figsize=(lebar_gambar, 5))
                jarak_antar_kamar = 1.5 # jarak 1.5 meter biar lega

                for i in range(jml_gambar):
                    x_pos = i * (panjang + jarak_antar_kamar)

                    # 1. Kotak Kamar
                    kamar = plt.Rectangle((x_pos, 0), panjang, lebar, edgecolor='blue', facecolor='lightblue', lw=2)
                    ax.add_patch(kamar)

                    # 2. Pintu
                    pintu = patches.Rectangle((x_pos + panjang/2 - 0.4, -0.2), 0.8, 0.2, edgecolor='brown', facecolor='saddlebrown')
                    ax.add_patch(pintu)
                    ax.text(x_pos + panjang/2, -0.7, "Pintu Depan", ha='center', fontsize=9)

                    # 3. Jendela
                    jendela = patches.Rectangle((x_pos + panjang/2 - 0.6, lebar), 1.2, 0.2, edgecolor='cyan', facecolor='lightcyan')
                    ax.add_patch(jendela)
                    ax.text(x_pos + panjang/2, lebar + 0.4, "Jendela", ha='center', fontsize=9)

                    # 4. Label
                    ax.text(x_pos + panjang/2, lebar/2, f"Kamar {i+1}\n{panjang}x{lebar}m", ha='center', va='center', fontweight='bold')

                ax.set_xlim(-1, jml_gambar * (panjang + jarak_antar_kamar))
                ax.set_ylim(-2, lebar + 1.5)
                ax.set_aspect('equal')
                ax.set_title(f"Denah {jml_gambar} Kamar - Mode {mode}")
                ax.axis('off')
                st.pyplot(fig)

                fig.savefig("denah_temp.png", dpi=300, bbox_inches='tight') # Save gambar jadi file - HD ga kepotong
                st.session_state['path_denah'] = "denah_temp.png" # Simpen alamat filenya
                plt.close(fig) 
                    
    # ===== TOMBOL DOWNLOAD PDF =====    
    def buat_pdf(nama, alamat, luas, biaya,
                 logo_file, mode, jumlah_gedung=1, jumlah_kamar_per_gedung=1,
                 jml_gambar=1, hasil_analisis="Belum dianalisis", show_draft=True):

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(595, 842))

        def gambar_draft():
            if show_draft:
                c.saveState()
                c.setFont("Helvetica-Bold", 70)
                c.setFillColorRGB(1, 0, 0, alpha=0.08)
                c.translate(300, 420)
                c.rotate(45)
                c.drawString(-110, 0, "DRAFT")
                c.restoreState()

        # LOGO
        if logo_file is not None:
            logo = ImageReader(logo_file)
            c.drawImage(st.logo, 40, 760, width=120, height=60, preserveAspectRatio=True, mask='auto')
        else:
            c.setFont("Helvetica-Bold", 16)
            c.setFillColorRGB(1, 0, 0)
            c.drawString(40, 780, "ARSITEK ANTI BONCOS")

        hari_ini = datetime.date.today().strftime("%d %B %Y")
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(400, 785, f"Tanggal: {hari_ini}")

        # ISI LAPORAN HALAMAN 1
        gambar_draft()
        c.setFont("Helvetica-Bold", 11)
        y = 700
        c.drawString(40, y, f"Nama: {nama}"); y -= 20
        c.drawString(40, y, f"Alamat: {alamat}"); y -= 20
        c.drawString(40, y, f"Luas Total: {luas:,.2f} m2"); y -= 20
        c.drawString(40, y, f"Mode: {mode}"); y -= 20

        if mode == "Kompleks":
            c.drawString(40, y, f"Jumlah: {jumlah_gedung} Gedung x {jumlah_kamar_per_gedung} Kamar ({jml_gambar} total)")
        else:
            c.drawString(40, y, f"Jumlah Kamar: {jml_gambar}")
            y -= 20

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, f"Total Estimasi: Rp {biaya:,.0f}"); y -= 25

        # ANALISIS
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Analisis Kepribadian:"); y -= 15
        c.setFont("Helvetica", 10)
        max_width = 500
        text = str(hasil_analisis)
        words = text.split(' ')
        line = ""
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                line = test_line
            else:
                c.drawString(40, y, line.strip())
                y -= 14
                line = word + " "
        c.drawString(40, y, line.strip())
        y -= 20
        c.line(40, y, 555, y); y -= 40

        # TTD
        c.setFont("Helvetica", 11)
        c.drawString(60, y, "Tanda Tangan Pemilik")
        c.drawString(360, y, "Hormat Kami,")
        y -= 90
        if 'path_ttd' in st.session_state and os.path.exists(st.session_state['path_ttd']):
            ttd = ImageReader(st.session_state['path_ttd'])
            c.drawImage(ttd, 60, y, width=130, height=70, preserveAspectRatio=True, mask='auto')
            y -= 15
            c.line(60, y, 210, y)
            c.line(360, y, 510, y)
            y -= 15
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"{nama}")
            c.drawString(360, y, "Arsitek Anti Boncos")

        # HALAMAN 2
        c.showPage()
        gambar_draft() 

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 800, f"Lampiran Denah - {jml_gambar} Kamar - Mode {mode}")
        c.setFont("Helvetica", 9)
        c.drawString(40, 785, f"Proyek: {alamat}")

        if 'path_denah' in st.session_state and os.path.exists(st.session_state['path_denah']):
            c.drawImage(st.session_state['path_denah'], 40, 250, width=515, height=500, preserveAspectRatio=True)
        else:
            c.drawString(40, 700, "Belum ada denah. Klik HITUNG dulu!")

        c.save()
        return buffer.getvalue(), hari_ini
   
    # TOMBOLNYA - DI LUAR "if st.button HITUNG!" 
    if st.button("Hitung & Buat PDF", type="primary", use_container_width=True):
        # 1. VALIDASI DULU
        if nama == "" or alamat == "":
             st.warning("Isi Nama dan Alamat dulu ya!")
        else:
            # 2. HITUNG DULU SEMUA VARIABEL
            luas_1_kamar = hitung_luas(panjang, lebar)
            if mode == "Kompleks":
                luas_total = luas_1_kamar * jumlah_gedung * jumlah_kamar_per_gedung
                jml_gambar_final = jumlah_gedung * jumlah_kamar_per_gedung
            else:
                luas_total = luas_1_kamar * jumlah_kamar
                jml_gambar_final = jumlah_kamar
            total_biaya = luas_total * harga_per_m2

            # 3. AMBIL HASIL PSIKOLOGI DARU SESSION STATE
            hasil_psiko = st.session_state.get('hasil_psikologi', "Belum dianalisis")
            
            # 4. PANGGIL FUNGSI PDF
            pdf_data, tanggal_file = buat_pdf(
                nama, alamat, luas_total, total_biaya,
                uploaded_logo, mode, 
                jumlah_gedung if mode=="Kompleks" else 1,
                jumlah_kamar_per_gedung if mode=="Kompleks" else 1,
                jml_gambar_final, hasil_psiko, 
                tampilkan_draft
            )

            # 5. TOMBOL DOWNLOAD
            st.download_button(
                label="📄 Download PDF", 
                data=pdf_data, 
                file_name=f"Laporan_{tanggal_file}.pdf", # Pake tanggal_file dari return 
                mime="application/pdf",
                use_container_width=True
            )
            
            st.balloons() # TAB 1x -- Sejajar sama "if panjang == 0" 

    with col2:
        if st.button ("🔁 RESET", use_container_width=True, on_click=reset_form):
           pass # Kosongin aja, tugasnya udah diambil alih on_click      

    # ========== 6. BAGIAN RIWAYAT ==============
    st.subheader("📜 Riwayat Perhitungan")
    if st.session_state.riwayat:
        for i, item in enumerate(st.session_state.riwayat):
            st.write(f"{i+1}. {item}")
    else: st.write("Belum ada riwayat")

    # BAGIAN GRAFIK
    st.subheader("📊 Grafik Riwayat")
    if st.session_state.riwayat:
        data_grafik = []
        for item in st.session_state.riwayat:
            try:
                # Ambil bagian sebelum | biar ga error
                bagian_luas = item.split("|")[0]
                hasil_angka = float(bagian_luas.split("=")[1].replace("m²","").strip())
                label = bagian_luas.split("=")[0].strip()
                data_grafik.append({"Perhitungan": label, "Hasil": hasil_angka})
            except: pass
        if data_grafik:
            df_grafik = pd.DataFrame(data_grafik)
            df_grafik = df_grafik.set_index("Perhitungan")
            st.bar_chart(df_grafik)
    else: st.info("Hitung dulu biar ada grafiknya 😁")

    # TOMBOL HAPUS + DOWNLOAD
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Hapus Riwayat"):
            st.session_state.riwayat = []
            st.rerun()
    with col2:
        if st.session_state.riwayat:
            df = pd.DataFrame(st.session_state.riwayat, columns=["Hasil"])
            st.download_button(
                label="📥 Download ke Excel",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='riwayat_kalkulator.csv',
                mime='text/csv',
            )

# ============= 5. CSS TEMA - TARUH PALING BAWAH =============
if st.session_state.tema_gelap:
 bg_color = "#0E1117"
 text_color = "#FAFAFA"
 btn_color = "#CC0000"
else:
 bg_color = "#FFFFFF"
 text_color = "#0E1117"
 btn_color = "#FF4B4B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
html, body {{ font-family: 'Poppins', sans-serif; }}
.stApp {{ background-color: {bg_color}; }}

/* INI KUNCINYA - PAKSA SEMUA TEKS GANTI WARNA */
h1, h2, h3, h4, h5, h6, p, label, span, div {{
 color: {text_color} !important;
}}

/* KHUSUS RADIO & TEXT INPUT LABEL */
.stRadio label,.stNumberInput label,.stTextInput label,.stSelectbox label {{
 color: {text_color} !important;
}}

.stButton>button {{
 background-color: {btn_color};
 color: white !important;
 transition: 0.3s;
 font-weight: 700;
 border: none;
 border-radius: 8px;
}}
.stButton>button:hover {{ transform: scale(1.05); }}

.stDownloadButton>button {{
 background-color: {btn_color};
 color: white !important;
 transition: 0.3s;
 font-weight: 700;
 border: none;
 border-radius: 8px;
}}
.stDownloadButton>button:hover {{ transform: scale(1.05); }}
</style>
""", unsafe_allow_html=True)

