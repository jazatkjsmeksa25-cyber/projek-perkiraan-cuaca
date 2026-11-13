
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import sqlite3
from datetime import datetime

# ==================================================
# 1. KONFIGURASI UTAMA
# ==================================================

NAMA_SEKOLAH = "SMKN 1 KOTA KEDIRI"

LATITUDE = "-7.8035"
LONGITUDE = "112.0229"

# Masukkan API Key OpenWeatherMap asli
API_KEY = "ef395ec10d8e7a3a6e41f0b9d58ae7c3"

DATABASE = "cuaca_sekolah.db"

URL_API = "https://api.openweathermap.org/data/2.5/weather"


# ==================================================
# 2. DATABASE SQLITE
# ==================================================

def koneksi_database():
    return sqlite3.connect(DATABASE)


def buat_database():
    conn = koneksi_database()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat_cuaca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suhu REAL NOT NULL,
            kelembapan INTEGER NOT NULL,
            angin REAL NOT NULL,
            kondisi TEXT NOT NULL,
            deskripsi TEXT NOT NULL,
            waktu TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def simpan_data(suhu, kelembapan, angin, kondisi, deskripsi):
    conn = koneksi_database()
    cursor = conn.cursor()

    waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cursor.execute("""
        INSERT INTO riwayat_cuaca
        (suhu, kelembapan, angin, kondisi, deskripsi, waktu)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        suhu,
        kelembapan,
        angin,
        kondisi,
        deskripsi,
        waktu
    ))

    conn.commit()
    conn.close()


def tampilkan_riwayat():

    for item in tabel.get_children():
        tabel.delete(item)

    conn = koneksi_database()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, suhu, kelembapan, angin,
               kondisi, deskripsi, waktu
        FROM riwayat_cuaca
        ORDER BY id DESC
        LIMIT 50
    """)

    data = cursor.fetchall()
    conn.close()

    for row in data:
        tabel.insert("", "end", values=row)


# ==================================================
# 3. MENGAMBIL DATA CUACA ASLI
# ==================================================

def dapatkan_cuaca():

    if not API_KEY or API_KEY == "ef395ec10d8e7a3a6e41f0b9d58ae7c3":
        messagebox.showerror(
            "API Key Belum Diisi",
            "Silakan masukkan API Key OpenWeatherMap "
            "pada bagian konfigurasi program."
        )
        return

    btn_refresh.config(
        state="disabled",
        text="MENGAMBIL DATA..."
    )

    label_status_api.config(
        text="Menghubungkan ke server cuaca...",
        fg="#f1c40f"
    )

    root.update_idletasks()

    parameter = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }

    try:

        respon = requests.get(
            URL_API,
            params=parameter,
            timeout=15
        )

        data = respon.json()

        if respon.status_code != 200:

            pesan = data.get(
                "message",
                "Tidak diketahui"
            )

            label_status_api.config(
                text="Gagal mengambil data cuaca",
                fg="#e74c3c"
            )

            messagebox.showerror(
                "Error OpenWeatherMap",
                f"Status HTTP: {respon.status_code}\n"
                f"Keterangan: {pesan}"
            )

            return

        # Mengambil data asli dari API
        suhu = float(data["main"]["temp"])

        kelembapan = int(
            data["main"]["humidity"]
        )

        angin = float(
            data["wind"]["speed"]
        )

        kondisi = data["weather"][0]["main"]

        deskripsi = data["weather"][0]["description"].capitalize()

        # Memproses dan menyimpan data asli
        proses_data(
            suhu,
            kelembapan,
            angin,
            kondisi,
            deskripsi
        )

        label_status_api.config(
            text="Terhubung - Data cuaca berhasil diperbarui",
            fg="#2ecc71"
        )

    except requests.Timeout:

        label_status_api.config(
            text="Koneksi timeout",
            fg="#e74c3c"
        )

        messagebox.showerror(
            "Timeout",
            "Server cuaca terlalu lama merespons."
        )

    except requests.ConnectionError:

        label_status_api.config(
            text="Tidak ada koneksi internet",
            fg="#e74c3c"
        )

        messagebox.showerror(
            "Koneksi Gagal",
            "Periksa koneksi internet Anda."
        )

    except requests.exceptions.JSONDecodeError:

        label_status_api.config(
            text="Respons server tidak valid",
            fg="#e74c3c"
        )

        messagebox.showerror(
            "Error Data",
            "Server mengirimkan respons yang tidak valid."
        )

    except (KeyError, IndexError, TypeError, ValueError):

        label_status_api.config(
            text="Format data cuaca tidak valid",
            fg="#e74c3c"
        )

        messagebox.showerror(
            "Error Data",
            "Data cuaca dari server tidak lengkap "
            "atau tidak dapat dibaca."
        )

    except sqlite3.Error as error:

        label_status_api.config(
            text="Gagal menyimpan data",
            fg="#e74c3c"
        )

        messagebox.showerror(
            "Database Error",
            str(error)
        )

    finally:

        btn_refresh.config(
            state="normal",
            text="REFRESH DATA CUACA"
        )


# ==================================================
# 4. MEMPROSES DATA CUACA
# ==================================================

def proses_data(
    suhu,
    kelembapan,
    angin,
    kondisi,
    deskripsi
):

    # Simpan data ke database SQLite
    simpan_data(
        suhu,
        kelembapan,
        angin,
        kondisi,
        deskripsi
    )

    # Perbarui tampilan suhu
    label_suhu.config(
        text=f"{suhu:.1f}°C"
    )

    label_status_cuaca.config(
        text=deskripsi
    )

    label_kelembapan_val.config(
        text=f"{kelembapan}%"
    )

    label_angin_val.config(
        text=f"{angin:.1f} m/s"
    )

    # Waktu pembaruan
    waktu = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    label_waktu.config(
        text=f"Terakhir diperbarui: {waktu}"
    )

    # Rekomendasi kegiatan sekolah
    if kondisi in [
        "Rain",
        "Drizzle",
        "Thunderstorm"
    ]:

        rekomendasi = (
            "HUJAN: Kegiatan olahraga dan upacara "
            "di luar ruangan sebaiknya dialihkan "
            "ke aula atau ruangan tertutup."
        )

        warna = "#c0392b"

    elif suhu >= 33:

        rekomendasi = (
            "PANAS: Kurangi aktivitas luar ruangan "
            "yang berat dan pastikan kebutuhan air "
            "minum tetap terpenuhi."
        )

        warna = "#e67e22"

    elif kondisi == "Clear":

        rekomendasi = (
            "CERAH: Cuaca mendukung kegiatan sekolah "
            "di luar ruangan dengan tetap memperhatikan "
            "kondisi lingkungan."
        )

        warna = "#27ae60"

    else:

        rekomendasi = (
            "CUACA BERAWAN: Kegiatan sekolah dapat "
            "dilaksanakan dengan tetap memperhatikan "
            "perubahan cuaca."
        )

        warna = "#2980b9"

    label_rekomendasi.config(
        text=rekomendasi,
        bg=warna
    )

    # Perbarui tabel riwayat
    tampilkan_riwayat()


# ==================================================
# 5. MEMBUAT JENDELA UTAMA
# ==================================================

buat_database()

root = tk.Tk()

root.title(
    "SICUACA - SMKN 1 Kota Kediri"
)

root.geometry("850x780")

root.minsize(700, 650)

root.configure(
    bg="#1e272e"
)


# ==================================================
# 6. HEADER APLIKASI
# ==================================================

frame_header = tk.Frame(
    root,
    bg="#1e272e"
)

frame_header.pack(pady=15)

title_lbl = tk.Label(
    frame_header,
    text="SISTEM INFORMASI CUACA",
    font=("Helvetica", 14, "bold"),
    fg="#00d2d3",
    bg="#1e272e"
)

title_lbl.pack()

school_lbl = tk.Label(
    frame_header,
    text=NAMA_SEKOLAH,
    font=("Helvetica", 19, "bold"),
    fg="#ffffff",
    bg="#1e272e"
)

school_lbl.pack(pady=5)

coord_lbl = tk.Label(
    frame_header,
    text=f"Koordinat: {LATITUDE}, {LONGITUDE}",
    font=("Helvetica", 9, "italic"),
    fg="#bdc3c7",
    bg="#1e272e"
)

coord_lbl.pack()


# ==================================================
# 7. TAMPILAN SUHU UTAMA
# ==================================================

label_suhu = tk.Label(
    root,
    text="--°C",
    font=("Helvetica", 55, "bold"),
    fg="#00d2d3",
    bg="#1e272e"
)

label_suhu.pack(pady=5)


label_status_cuaca = tk.Label(
    root,
    text="Menunggu data cuaca...",
    font=("Helvetica", 17),
    fg="#ffffff",
    bg="#1e272e"
)

label_status_cuaca.pack()


label_waktu = tk.Label(
    root,
    text="Belum ada pembaruan data",
    font=("Helvetica", 9),
    fg="#bdc3c7",
    bg="#1e272e"
)

label_waktu.pack(pady=5)


# ==================================================
# 8. DETAIL INFORMASI CUACA
# ==================================================

frame_detail = tk.Frame(
    root,
    bg="#2d3436"
)

frame_detail.pack(
    pady=15,
    padx=30,
    fill="x"
)


# Kelembapan
tk.Label(
    frame_detail,
    text="KELEMBAPAN",
    font=("Helvetica", 11),
    fg="#b2bec3",
    bg="#2d3436"
).grid(
    row=0,
    column=0,
    padx=30,
    pady=10
)

label_kelembapan_val = tk.Label(
    frame_detail,
    text="--",
    font=("Helvetica", 17, "bold"),
    fg="#ffffff",
    bg="#2d3436"
)

label_kelembapan_val.grid(
    row=1,
    column=0,
    padx=30,
    pady=5
)


# Kecepatan angin
tk.Label(
    frame_detail,
    text="KECEPATAN ANGIN",
    font=("Helvetica", 11),
    fg="#b2bec3",
    bg="#2d3436"
).grid(
    row=0,
    column=1,
    padx=30,
    pady=10
)

label_angin_val = tk.Label(
    frame_detail,
    text="--",
    font=("Helvetica", 17, "bold"),
    fg="#ffffff",
    bg="#2d3436"
)

label_angin_val.grid(
    row=1,
    column=1,
    padx=30,
    pady=5
)

frame_detail.grid_columnconfigure(
    0,
    weight=1
)

frame_detail.grid_columnconfigure(
    1,
    weight=1
)


# ==================================================
# 9. REKOMENDASI KEGIATAN SEKOLAH
# ==================================================

label_rekomendasi = tk.Label(
    root,
    text="Menunggu data cuaca...",
    font=("Helvetica", 10, "bold"),
    fg="#ffffff",
    bg="#7f8c8d",
    wraplength=700,
    justify="center",
    padx=15,
    pady=12
)

label_rekomendasi.pack(
    pady=12,
    padx=30,
    fill="x"
)


# ==================================================
# 10. STATUS KONEKSI API
# ==================================================

label_status_api = tk.Label(
    root,
    text="Menunggu koneksi ke server cuaca...",
    font=("Helvetica", 9, "bold"),
    fg="#f1c40f",
    bg="#1e272e"
)

label_status_api.pack(pady=5)


# ==================================================
# 11. TOMBOL REFRESH
# ==================================================

btn_refresh = tk.Button(
    root,
    text="REFRESH DATA CUACA",
    font=("Helvetica", 11, "bold"),
    fg="#ffffff",
    bg="#0984e3",
    activebackground="#74b9ff",
    activeforeground="#ffffff",
    bd=0,
    padx=25,
    pady=10,
    cursor="hand2",
    command=dapatkan_cuaca
)

btn_refresh.pack(pady=10)


# ==================================================
# 12. TABEL RIWAYAT CUACA SQLITE
# ==================================================

tk.Label(
    root,
    text="RIWAYAT DATA CUACA",
    font=("Helvetica", 13, "bold"),
    fg="#00d2d3",
    bg="#1e272e"
).pack(pady=10)


frame_tabel = tk.Frame(
    root,
    bg="#2d3436"
)

frame_tabel.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)


kolom = (
    "id",
    "suhu",
    "kelembapan",
    "angin",
    "kondisi",
    "deskripsi",
    "waktu"
)


tabel = ttk.Treeview(
    frame_tabel,
    columns=kolom,
    show="headings",
    height=8
)


judul = {
    "id": "ID",
    "suhu": "Suhu (°C)",
    "kelembapan": "Kelembapan",
    "angin": "Angin (m/s)",
    "kondisi": "Kondisi",
    "deskripsi": "Deskripsi",
    "waktu": "Waktu"
}


lebar = {
    "id": 45,
    "suhu": 85,
    "kelembapan": 100,
    "angin": 100,
    "kondisi": 100,
    "deskripsi": 130,
    "waktu": 150
}


for col in kolom:

    tabel.heading(
        col,
        text=judul[col]
    )

    tabel.column(
        col,
        width=lebar[col],
        anchor="center"
    )


scrollbar_y = ttk.Scrollbar(
    frame_tabel,
    orient="vertical",
    command=tabel.yview
)

scrollbar_x = ttk.Scrollbar(
    frame_tabel,
    orient="horizontal",
    command=tabel.xview
)


tabel.configure(
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)


tabel.grid(
    row=0,
    column=0,
    sticky="nsew"
)

scrollbar_y.grid(
    row=0,
    column=1,
    sticky="ns"
)

scrollbar_x.grid(
    row=1,
    column=0,
    sticky="ew"
)


frame_tabel.grid_rowconfigure(
    0,
    weight=1
)

frame_tabel.grid_columnconfigure(
    0,
    weight=1
)


# ==================================================
# 13. MENAMPILKAN DATA LAMA
# ==================================================

tampilkan_riwayat()


# ==================================================
# 14. MENGAMBIL DATA CUACA SAAT APLIKASI DIBUKA
# ==================================================

root.after(
    500,
    dapatkan_cuaca
)


# ==================================================
# 15. MENJALANKAN APLIKASI
# ==================================================

root.mainloop()
ef395ec10d8e7a3a6e41f0b9d58ae7c3