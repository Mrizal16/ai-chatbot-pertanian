import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv



# Load API Key dari file .env (jika ada)
load_dotenv()

# API Keys
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("⚠️ API Key Together AI tidak ditemukan! Pastikan sudah diset di environment variables atau file .env.")
if not OPENWEATHER_API_KEY:
    raise ValueError("⚠️ API Key OpenWeather tidak ditemukan! Pastikan sudah diset di environment variables atau file .env.")

# Inisialisasi Flask
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "message": "✅ Selamat datang di Chatbot AI Pertanian (Powered by Together AI)!",
        "endpoints": {
            "/chat": "Gunakan metode POST untuk bertanya ke chatbot.",
            "/weather": "Gunakan metode POST untuk mendapatkan informasi cuaca."
        }
    })

# === ✅ SISTEM PAKAR: Aturan IF-THEN ===
SISTEM_PAKAR = {
    # 1️⃣ Penyakit dan Hama Tanaman
    "tanaman padi saya terkena bercak coklat, apa penyebabnya?": 
        "🔬 Penyebab bercak coklat pada padi adalah jamur *Cochliobolus miyabeanus*. Penyakit ini bisa muncul karena kelembaban tinggi dan kekurangan kalium.",
    "bagaimana cara mengatasi wereng pada padi?": 
        "🛡️ Untuk mengatasi wereng, gunakan varietas tahan wereng, semprot insektisida berbahan aktif imidakloprid, dan jaga kebersihan lahan.",
    "apa gejala penyakit hawar daun bakteri (hdb)?": 
        "⚠️ Gejala HDB adalah daun menguning, ujung mengering, dan muncul garis coklat. Penyakit ini disebabkan oleh bakteri *Xanthomonas oryzae*.",
    "pestisida apa yang cocok untuk ulat grayak?": 
        "🐛 Pestisida yang efektif untuk ulat grayak adalah yang mengandung bahan aktif klorfenapir atau metomil.",
    "kapan waktu terbaik menanam padi?": 
        "📅 Waktu terbaik menanam padi adalah Oktober-Desember (musim hujan) dan Maret-Mei (musim kemarau dengan irigasi).",
    "kapan menanam jagung agar hasil optimal?": 
        "🌽 Jagung sebaiknya ditanam pada awal musim hujan (Oktober) atau akhir musim kemarau (Juli) untuk hasil maksimal.",


    # 2️⃣ Pemupukan & Nutrisi Tanaman
    "kapan waktu terbaik untuk memupuk padi?": 
        "🌱 Pemupukan padi sebaiknya dilakukan 3 tahap: (1) Pupuk dasar saat tanam, (2) Pupuk susulan saat umur 21 HST, (3) Pupuk tambahan saat 45 HST.",
    "berapa dosis pupuk urea untuk padi per hektar?": 
        "📌 Dosis pupuk urea untuk padi sawah adalah 200-250 kg/ha, diberikan dalam 2 tahap: 100 kg saat umur 7-10 HST dan sisanya saat 30-35 HST.",
    "pupuk apa yang mengandung nitrogen tinggi?": 
        "🧪 Pupuk dengan nitrogen tinggi antara lain Urea (N=46%), ZA (N=21%), dan pupuk organik dari kotoran ayam.",
    "bagaimana cara mengetahui tanaman kekurangan kalium?": 
        "🔎 Gejala kekurangan kalium: Daun menguning dari tepi, pertumbuhan terhambat, dan batang lemah.",

    # 3️⃣ Pengairan dan Irigasi
    "berapa tinggi air yang ideal untuk sawah padi?": 
        "💧 Tinggi air ideal untuk sawah padi adalah 2-5 cm saat pertumbuhan awal dan 5-10 cm saat pertumbuhan aktif.",
    "kapan waktu yang tepat untuk mengeringkan sawah?": 
        "🌞 Sawah perlu dikeringkan 10-14 hari sebelum panen agar kualitas gabah lebih baik dan mengurangi kadar air.",
    "bagaimana cara irigasi yang hemat air untuk padi?": 
        "🚰 Gunakan sistem irigasi berselang atau AWD (Alternate Wetting and Drying) untuk menghemat air hingga 30%.",
    "apa dampak kelebihan air pada tanaman?": 
        "⚠️ Kelebihan air menyebabkan akar busuk, pertumbuhan terhambat, dan meningkatkan risiko penyakit jamur.",

    # 4️⃣ Pola Tanam & Rotasi Tanaman
    "tanaman apa yang cocok ditanam setelah panen padi?": 
        "🌾 Setelah padi, cocok ditanam kacang hijau atau kedelai untuk meningkatkan kesuburan tanah.",
    "bagaimana cara mengurangi hama dengan tumpangsari?": 
        "🐞 Tumpangsari dengan tanaman pengusir hama seperti jagung dan kacang tanah bisa mengurangi serangan hama.",
    "apakah jagung cocok ditanam setelah padi?": 
        "🌽 Ya, jagung cocok ditanam setelah padi karena membutuhkan nitrogen lebih sedikit dibanding padi.",
    "apa keuntungan rotasi tanaman?": 
        "🔄 Rotasi tanaman mengurangi hama, meningkatkan kesuburan tanah, dan mengurangi ketergantungan pada pupuk kimia.",

    # 5️⃣ Cuaca dan Dampaknya pada Pertanian
    "apa dampak hujan berlebih pada padi?": 
        "🌧️ Hujan berlebih dapat menyebabkan busuk akar, penyakit jamur, dan menghambat penyerbukan.",
    "bagaimana cara melindungi tanaman dari cuaca panas?": 
        "☀️ Gunakan mulsa jerami, penyiraman pagi/sore, dan naungan untuk mengurangi dampak cuaca panas.",
    "kapan waktu tanam terbaik berdasarkan musim?": 
        "📅 Waktu tanam terbaik di musim hujan: Oktober-Desember, di musim kemarau: Maret-Mei.",
    "bagaimana cara mengatasi embun beku di tanaman?": 
        "❄️ Gunakan kabut buatan atau penyiraman malam untuk mengurangi efek embun beku."

    
}

def is_relevant_question(question):
    """Memeriksa apakah pertanyaan berhubungan dengan pertanian atau cuaca"""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in [
        "padi", "hama", "tanaman", "pupuk", "sawah", "cuaca", "iklim",
        "irigasi", "panen", "pertanian", "pestisida", "organik", "hujan"
    ])

@app.route("/fertilizer", methods=["POST"])
def fertilizer():
    """Hitung kebutuhan pupuk berdasarkan luas lahan dan jenis tanaman"""
    data = request.get_json()
    crop = data.get("crop", "").strip().lower()
    area = data.get("area", 0)  # Luas lahan dalam hektar

    if not crop or area <= 0:
        return jsonify({"response": "⚠️ Masukkan jenis tanaman dan luas lahan yang valid."})

    # Database dosis pupuk per hektar (contoh)
    DOSIS_PUPUK = {
        "padi": {"urea": 250, "sp36": 100, "kcl": 75},  # kg/ha
        "jagung": {"urea": 200, "sp36": 100, "kcl": 50},
        "kedelai": {"urea": 50, "sp36": 50, "kcl": 50}
    }

    if crop in DOSIS_PUPUK:
        kebutuhan = {k: v * area for k, v in DOSIS_PUPUK[crop].items()}
        response_text = f"📊 Kebutuhan pupuk untuk {area} ha {crop}:\n"
        response_text += "\n".join([f"🔹 {k.upper()}: {v} kg" for k, v in kebutuhan.items()])
        return jsonify({"response": response_text})

    return jsonify({"response": "⚠️ Maaf, data pupuk untuk tanaman ini belum tersedia."})

@app.route("/fertilizer_v2", methods=["POST"])
def fertilizer_v2():
    """Hitung kebutuhan pupuk berdasarkan luas lahan, jenis pupuk, dan target panen dengan rentang dosis"""
    data = request.get_json()
    crop = data.get("crop", "").strip().lower()
    area = data.get("area", 0)  # Luas lahan dalam hektar
    target_yield = data.get("target_yield", 0)  # Target hasil panen dalam ton/ha

    if not crop or area <= 0 or target_yield <= 0:
        return jsonify({"response": "⚠️ Masukkan jenis tanaman, luas lahan, dan target panen yang valid."})

    # Database dosis pupuk per ton target hasil panen (rentang min-max)
    PUPUK_PER_TON = {
        "padi": {"urea": (25, 30), "sp36": (10, 12), "kcl": (7, 9)},  # kg/ton per hektar
        "jagung": {"urea": (20, 25), "sp36": (8, 10), "kcl": (5, 7)},
        "kedelai": {"urea": (8, 10), "sp36": (6, 8), "kcl": (4, 5)}
    }

    if crop in PUPUK_PER_TON:
        kebutuhan = {
            k: (v[0] * target_yield * area, v[1] * target_yield * area) 
            for k, v in PUPUK_PER_TON[crop].items()
        }
        response_text = (
            f"📊 *Estimasi kebutuhan pupuk untuk {area} ha {crop} dengan target {target_yield} ton/ha:*\n"
        )
        response_text += "\n".join([f"🔹 {k.upper()}: {int(v[0])}-{int(v[1])} kg" for k, v in kebutuhan.items()])
        response_text += (
            "\n\n⚠️ *Catatan:* Dosis ini dapat bervariasi tergantung kondisi tanah, cuaca, dan varietas tanaman. "
            "Sebaiknya lakukan uji tanah atau konsultasi dengan penyuluh pertanian setempat.\n"
            "Semoga membantu! Jika ada pertanyaan lain, silakan tanyakan. 😊"
        )
        return jsonify({"response": response_text})

    return jsonify({"response": "⚠️ Maaf, data pupuk untuk tanaman ini belum tersedia."})

@app.route("/fertilizer_plan", methods=["POST"])
def fertilizer_plan():
    """Menghitung kebutuhan pupuk berdasarkan luas lahan & target hasil panen"""
    data = request.get_json()
    area = float(data.get("area", 0))  # Luas lahan dalam hektar
    target_yield = float(data.get("target_yield", 0))  # Target hasil panen dalam ton/ha

    if area <= 0 or target_yield <= 0:
        return jsonify({"response": "⚠️ Masukkan luas lahan dan target panen yang valid."})

    # Rekomendasi pupuk per hektar
    FERTILIZER_RECOMMENDATION = {
        "urea": {"min": 120, "max": 150},  # kg/ha
        "tsp": {"min": 60, "max": 80},  # kg/ha
        "kcl": {"min": 90, "max": 120}  # kg/ha
    }

    # Menghitung total pupuk yang dibutuhkan
    kebutuhan_pupuk = {
        pupuk: {"min": v["min"] * area, "max": v["max"] * area}
        for pupuk, v in FERTILIZER_RECOMMENDATION.items()
    }

    response_text = (
        f"📊 *Estimasi kebutuhan pupuk untuk {area} ha padi dengan target {target_yield} ton/ha:*\n"
    )
    response_text += "\n".join(
        [f"🔹 {pupuk.upper()}: {data['min']}-{data['max']} kg" for pupuk, data in kebutuhan_pupuk.items()]
    )

    response_text += (
        "\n\n🗓️ *Jadwal Pemupukan:*\n"
        "✅ **Pupuk Dasar (sebelum tanam):** 50% TSP + 30% Urea + 40% KCl\n"
        "✅ **Pupuk Susulan 1 (21 HST):** 40% Urea + 40% KCl\n"
        "✅ **Pupuk Susulan 2 (45 HST):** Sisa Urea\n\n"
        "🌿 *Alternatif Pupuk Organik:*\n"
        "- **Pupuk Kandang:** 2-3 ton/ha\n"
        "- **Kompos Jerami:** 4-5 ton/ha\n"
        "- **Biofertilizer:** Tambahkan mikroba tanah untuk meningkatkan efisiensi pupuk\n\n"
        "💡 *Tips:* Lakukan uji tanah untuk hasil lebih akurat!"
    )

    return jsonify({"response": response_text})

def rekomendasi_tanaman(musim=None, suhu=None, curah_hujan=None):
    rekomendasi = []

    if musim == "hujan":
        rekomendasi.extend(["Padi", "Jagung", "Kacang Tanah"])
    if musim == "kemarau":
        rekomendasi.extend(["Jagung", "Kedelai", "Ubi Kayu"])
    if suhu and suhu < 20:
        rekomendasi.extend(["Kentang", "Wortel", "Kubis"])
    if curah_hujan and curah_hujan > 200:  # Curah hujan tinggi dalam mm
        rekomendasi = [t for t in rekomendasi if t not in ["Cabai", "Bawang Merah"]]

    return rekomendasi if rekomendasi else ["Tidak ada rekomendasi spesifik"]

# Contoh penggunaan:
print(rekomendasi_tanaman(musim="kemarau", suhu=25, curah_hujan=100))
# Output: ['Jagung', 'Kedelai', 'Ubi Kayu']


@app.route("/chat", methods=["POST"])
def chat():
    """Chatbot AI untuk pertanian & cuaca"""
    data = request.get_json()
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"response": "⚠️ Mohon ketik sesuatu untuk bertanya."})

    # ✅ **Cek apakah ada jawaban di sistem pakar**
    if user_message in SISTEM_PAKAR:
        return jsonify({"response": SISTEM_PAKAR[user_message]})

    # ✅ **Cek apakah pertanyaan relevan dengan pertanian/cuaca**
    if not is_relevant_question(user_message):
        return jsonify({"response": "⚠️ Maaf, saya hanya menjawab pertanyaan tentang pertanian dan cuaca."})

    # Kirim ke Together AI
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": 
                "Anda adalah chatbot AI pertanian. Jawablah hanya tentang pertanian dan cuaca. "
                "Jika pertanyaan tidak terkait, jawab: '⚠️ Maaf, saya hanya menjawab pertanian dan cuaca.'"
            },
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1000,
        "temperature": 0.3
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        response_json = response.json()

        if response.status_code == 200 and "choices" in response_json:
            bot_response = response_json["choices"][0].get("message", {}).get("content", "").strip()
        else:
            bot_response = "⚠️ Tidak bisa mengambil data cuaca. Periksa koneksi atau coba lokasi lain."

    except Exception as e:
        bot_response = f"⚠️ Tidak bisa mengambil data cuaca. Periksa koneksi atau coba lokasi lain: {str(e)}"

    return jsonify({"response": bot_response})

@app.route("/weather", methods=["POST"])
def get_weather():
    """Endpoint untuk mendapatkan informasi cuaca dari OpenWeather"""
    data = request.get_json()
    city = data.get("city", "").strip()

    if not city:
        return jsonify({"response": "⚠️ Mohon masukkan nama kota untuk mendapatkan informasi cuaca."})
    if not city.isalpha():
        return jsonify({"response": "⚠️ Nama kota harus berupa huruf tanpa angka atau simbol."})

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=id"

    try:
        response = requests.get(url)
        weather_data = response.json()

        if response.status_code == 200:
            city_name = weather_data.get("name", "Tidak diketahui")
            weather_info = weather_data.get("weather", [{}])[0]
            description = weather_info.get("description", "Tidak tersedia").capitalize()
            temperature = weather_data.get("main", {}).get("temp", "Tidak tersedia")
            humidity = weather_data.get("main", {}).get("humidity", "Tidak tersedia")
            wind_speed = weather_data.get("wind", {}).get("speed", "Tidak tersedia")

            weather_report = (
                f"📍 *Cuaca di {city_name}:*\n"
                f"🌦️ *Kondisi:* {description}\n"
                f"🌡️ *Suhu:* {temperature}°C\n"
                f"💧 *Kelembapan:* {humidity}%\n"
                f"🌬️ *Kecepatan Angin:* {wind_speed} m/s\n"
                f"\n🔹 *Semoga informasi ini bermanfaat!* 😊"
            )
        else:
            weather_report = "⚠️ Kota tidak ditemukan. Mohon cek kembali nama kota Anda."

    except Exception as e:
        weather_report = f"⚠️ Maaf, layanan Together AI sedang sibuk. Coba lagi nanti: {str(e)}"

    return jsonify({"response": weather_report})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
