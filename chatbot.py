import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import spacy

load_dotenv()

# API Keys
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("API Key Together AI tidak ditemukan! Pastikan sudah diset di environment variables atau file .env.")
if not OPENWEATHER_API_KEY:
    raise ValueError("API Key OpenWeather tidak ditemukan! Pastikan sudah diset di environment variables atau file .env.")

# Inisialisasi Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Inisialisasi model NLP
# Pastikan model ini sudah diunduh dengan: python -m spacy download xx_ent_wiki_sm
try:
    nlp = spacy.load("xx_ent_wiki_sm")
except OSError:
    print("Model 'xx_ent_wiki_sm' tidak ditemukan. Harap unduh dengan: python -m spacy download xx_ent_wiki_sm")
    # Alternatif: gunakan model yang lebih kecil atau berikan pesan error yang jelas
    nlp = None # Atau keluar dari aplikasi jika spaCy sangat krusial

@app.route("/")
def home():
    return jsonify({
        "message": "Selamat datang di Chatbot AI Pertanian (Powered by Together AI)!",
        "endpoints": {
            "/chat": "Gunakan metode POST untuk bertanya ke chatbot.",
            "/weather": "Gunakan metode POST untuk mendapatkan informasi cuaca.",
            "/recommend_crop": "Rekomendasi tanaman berdasarkan musim, suhu, dan curah hujan."
        }
    })


# === SISTEM PAKAR: Aturan IF-THEN ===
SISTEM_PAKAR = {
    # Penyakit dan Hama Tanaman
    "tanaman padi saya terkena bercak coklat, apa penyebabnya?":
        "Penyebab bercak coklat pada padi adalah jamur COCHLIOBOLUS MIYABEANUS. Penyakit ini bisa muncul karena kelembaban tinggi dan kekurangan kalium.",
    "bagaimana cara mengatasi wereng pada padi?":
        "Untuk mengatasi wereng, gunakan varietas tahan wereng, semprot insektisida berbahan aktif imidakloprid, dan jaga kebersihan lahan.",
    "apa gejala penyakit hawar daun bakteri (hdb)?":
        "Gejala HDB adalah daun menguning, ujung mengering, dan muncul garis coklat. Penyakit ini disebabkan oleh bakteri XANTHOMONAS ORYZAE.",
    "pestisida apa yang cocok untuk ulat grayak?":
        "Pestisida yang efektif untuk ulat grayak adalah yang mengandung bahan aktif klorfenapir atau metomil.",
    "kapan waktu terbaik menanam padi?":
        "Waktu terbaik menanam padi adalah Oktober-Desember (musim hujan) dan Maret-Mei (musim kemarau dengan irigasi).",
    "kapan menanam jagung agar hasil optimal?":
        "Jagung sebaiknya ditanam pada awal musim hujan (Oktober) atau akhir musim kemarau (Juli) untuk hasil maksimal.",
    "bagaimana cara mengatasi blast pada padi?":
        "Gunakan fungisida berbahan aktif triazol dan tanam varietas tahan penyakit seperti IR64 atau Inpari 32.",
    "apa gejala penyakit busuk batang pada jagung?":
        "Batang berwarna coklat kehitaman, lunak, mudah patah. Disebabkan oleh jamur FUSARIUM SPP.",
    "bagaimana mengendalikan tikus sawah?":
        "Gunakan trap mekanik, musuh alami seperti burung hantu, dan sanitasi lahan secara rutin.",
    "apa penyebab daun jagung menggulung?":
        "Kemungkinan karena kekurangan air, serangan penggerek daun, atau kekurangan kalium.",
    "mengapa daun padi berubah warna ungu?":
        "Daun ungu bisa jadi karena defisiensi fosfor, terutama pada tanah masam atau miskin hara.",

    # Pemupukan & Nutrisi Tanaman
    "kapan waktu terbaik untuk memupuk padi?":
        "Pemupukan padi sebaiknya dilakukan 3 tahap: (1) Pupuk dasar saat tanam, (2) Pupuk susulan saat umur 21 HST, (3) Pupuk tambahan saat 45 HST.",
    "berapa dosis pupuk urea untuk padi per hektar?":
        "Dosis pupuk urea untuk padi sawah adalah 200-250 kg/ha, diberikan dalam 2 tahap: 100 kg saat umur 7-10 HST dan sisanya saat 30-35 HST.",
    "pupuk apa yang mengandung nitrogen tinggi?":
        "Pupuk dengan nitrogen tinggi antara lain Urea (N=46%), ZA (N=21%), dan pupuk organik dari kotoran ayam.",
    "bagaimana cara mengetahui tanaman kekurangan kalium?":
        "Gejala kekurangan kalium: Daun menguning dari tepi, pertumbuhan terhambat, dan batang lemah.",
    "apa pupuk yang cocok untuk jagung saat awal tanam?":
        "Gunakan NPK seimbang (15:15:15) atau kombinasi Urea dan SP36 pada saat tanam.",
    "bagaimana ciri tanaman kekurangan fosfor?":
        "Daun tua berwarna ungu kebiruan, pertumbuhan lambat, dan akar kurang berkembang.",
    "berapa kebutuhan pupuk KCl untuk padi?":
        "Dosis KCl sekitar 100 kg/ha, diberikan bersamaan dengan pupuk susulan.",
    "apa manfaat pupuk kandang untuk tanaman?":
        "Meningkatkan struktur tanah, menambah hara makro dan mikro, serta meningkatkan aktivitas mikroba.",
    "bagaimana pupuk organik cair diaplikasikan?":
        "Disemprotkan ke daun saat pagi atau sore, biasanya setiap 7–10 hari sekali.",

    # Pengairan dan Irigasi
    "berapa tinggi air yang ideal untuk sawah padi?":
        "Tinggi air ideal untuk sawah padi adalah 2-5 cm saat pertumbuhan awal dan 5-10 cm saat pertumbuhan aktif.",
    "kapan waktu yang tepat untuk mengeringkan sawah?":
        "Sawah perlu dikeringkan 10-14 hari sebelum panen agar kualitas gabah lebih baik dan mengurangi kadar air.",
    "bagaimana cara irigasi yang hemat air untuk padi?":
        "Gunakan sistem irigasi berselang atau AWD (Alternate Wetting and Drying) untuk menghemat air hingga 30%.",
    "apa dampak kelebihan air pada tanaman?":
        "Kelebihan air menyebabkan akar busuk, pertumbuhan terhambat, dan meningkatkan risiko penyakit jamur.",
    "apa itu sistem irigasi tetes?":
        "Irigasi tetes mengalirkan air langsung ke akar tanaman secara perlahan, hemat air dan efisien.",
    "bagaimana cara mencegah genangan air di lahan pertanian?":
        "Buat saluran drainase yang baik dan hindari penanaman di cekungan.",
    "apakah hujan malam berdampak buruk pada pertumbuhan tanaman?":
        "Tidak secara langsung, tapi dapat meningkatkan kelembaban yang memicu penyakit jamur.",
    "bagaimana cara meningkatkan efisiensi penggunaan air di sawah?":
        "Gunakan metode AWD, sesuaikan tinggi air, dan tanam varietas tahan kering.",
    "berapa kebutuhan air untuk tanaman jagung per musim?":
        "Sekitar 500–800 mm selama siklus tanam, tergantung varietas dan cuaca.",

    # Pola Tanam & Rotasi Tanaman
    "tanaman apa yang cocok ditanam setelah panen padi?":
        "Setelah padi, cocok ditanam kacang hijau atau kedelai untuk meningkatkan kesuburan tanah.",
    "bagaimana cara mengurangi hama dengan tumpangsari?":
        "Tumpangsari dengan tanaman pengusir hama seperti jagung dan kacang tanah bisa mengurangi serangan hama.",
    "apakah jagung cocok ditanam setelah padi?":
        "Ya, jagung cocok ditanam setelah padi karena membutuhkan nitrogen lebih sedikit dibanding padi.",
    "apa keuntungan rotasi tanaman?":
        "Rotasi tanaman mengurangi hama, meningkatkan kesuburan tanah, dan mengurangi ketergantungan pada pupuk kimia.",
    "apa pola tanam terbaik untuk padi-jagung-kedelai?":
        "Gunakan rotasi tahunan: padi (musim hujan), jagung (kemarau I), kedelai (kemarau II).",
    "kenapa rotasi tanaman penting dilakukan?":
        "Mengurangi penumpukan patogen, memperbaiki struktur tanah, dan mengoptimalkan penggunaan hara.",
    "apa manfaat menanam tanaman legum setelah padi?":
        "Legum seperti kacang dapat menambat nitrogen dan memperbaiki kesuburan tanah.",
    "apa perbedaan tumpangsari dan rotasi tanaman?":
        "Tumpangsari menanam beberapa tanaman sekaligus, rotasi adalah bergantian antar musim.",
    "bagaimana cara menanam tumpangsari jagung dan kacang tanah?":
        "Tanam jagung dengan jarak 75x25 cm, dan selingi baris kacang tanah di antaranya.",

    # Cuaca dan Dampaknya pada Pertanian
    "apa dampak hujan berlebih pada padi?":
        "Hujan berlebih dapat menyebabkan busuk akar, penyakit jamur, dan menghambat penyerbukan.",
    "bagaimana cara melindungi tanaman dari cuaca panas?":
        "Gunakan mulsa jerami, penyiraman pagi/sore, dan naungan untuk mengurangi dampak cuaca panas.",
    "kapan waktu tanam terbaik berdasarkan musim?":
        "Waktu tanam terbaik di musim hujan: Oktober-Desember, di musim kemarau: Maret-Mei.",
    "bagaimana cara mengatasi embun beku di tanaman?":
        "Gunakan kabut buatan atau penyiraman malam untuk mengurangi efek embun beku.",

    # Gulma dan Pengendaliannya
    "bagaimana cara mengendalikan gulma pada sawah?":
        "Gunakan penyiangan manual saat umur 15 dan 30 HST, atau gunakan herbisida selektif seperti bispiribak sodium.",
    "apa herbisida yang aman untuk padi?":
        "Herbisida selektif seperti penoksulam atau oksadiazon aman untuk padi jika digunakan sesuai dosis.",
    "kapan waktu terbaik menyemprot herbisida?":
        "Waktu terbaik menyemprot herbisida adalah pagi hari saat cuaca cerah dan tidak berangin.",
    "apa dampak gulma jika tidak dikendalikan?":
        "Gulma bersaing dengan tanaman utama dalam hal air, nutrisi, dan cahaya sehingga menurunkan hasil panen.",

    # Pascapanen dan Penyimpanan
    "bagaimana cara menyimpan gabah agar tidak berjamur?":
        "Simpan gabah pada RH < 70%, suhu < 30°C, dan kelembapan < 14%. Gunakan karung berpori di tempat berventilasi.",
    "berapa kadar air gabah yang ideal untuk disimpan?":
        "Kadar air ideal gabah untuk disimpan adalah 12-14% agar tidak berjamur.",
    "apa penyebab gabah cepat busuk saat disimpan?":
        "Gabah cepat busuk karena kadar air tinggi dan penyimpanan di tempat lembap.",
    "bagaimana cara pengeringan gabah secara alami?":
        "Jemur gabah di bawah sinar matahari maksimal 6 jam/hari dengan dibolak-balik setiap 30 menit.",

    # Teknologi dan Mekanisasi Pertanian
    "apa manfaat menggunakan traktor tangan?":
        "Traktor tangan mempercepat pengolahan lahan, menghemat tenaga, dan meningkatkan efisiensi waktu.",
    "apa itu combine harvester?":
        "Combine harvester adalah mesin panen multifungsi yang bisa memanen, merontokkan, dan membersihkan gabah sekaligus.",
    "apakah drone bisa digunakan dalam pertanian?":
        "Ya, drone dapat digunakan untuk pemetaan lahan, monitoring pertumbuhan tanaman, dan penyemprotan pestisida.",
    "apa keuntungan menggunakan mesin tanam padi?":
        "Mesin tanam padi mempercepat proses tanam, meratakan jarak tanam, dan mengurangi kelelahan petani.",

    # Pertanian Organik dan Ramah Lingkungan
    "bagaimana cara membuat kompos dari jerami padi?":
        "Jerami direndam dan dicampur EM4, ditumpuk bertahap dengan bahan hijau, lalu dibalik tiap minggu selama 3-4 minggu.",
    "apa itu pupuk hayati?":
        "Pupuk hayati mengandung mikroorganisme yang membantu menyuburkan tanah dan meningkatkan penyerapan unsur hara.",
    "apa manfaat pupuk kandang fermentasi?":
        "Pupuk kandang fermentasi lebih higienis, kaya mikroba baik, dan tidak berbau menyengat.",
    "bagaimana cara mengurangi penggunaan pestisida kimia?":
        "Gunakan musuh alami hama, rotasi tanaman, dan pestisida nabati dari daun mimba atau bawang putih.",

    # Pertanyaan Umum dan Praktik Baik Pertanian
    "apa itu HST dalam pertanian?":
        "HST adalah singkatan dari Hari Setelah Tanam, digunakan untuk menentukan waktu pemupukan, penyemprotan, dan panen.",
    "bagaimana cara mengetahui pH tanah?":
        "Gunakan alat pH meter digital atau kertas lakmus, idealnya pH tanah padi 5.5–6.5.",
    "kenapa padi rebah sebelum panen?":
        "Padi rebah karena angin kencang, batang lemah, atau pemupukan nitrogen berlebih.",
    "apa penyebab daun padi menguning?":
        "Daun padi menguning bisa disebabkan kekurangan nitrogen, serangan wereng, atau genangan air berlebih.",
    "apa perbedaan pupuk organik dan anorganik?":
        "Pupuk organik berasal dari bahan alami dan lambat diserap, sedangkan pupuk anorganik buatan pabrik dan cepat diserap.",
    "kapan waktu panen terbaik untuk padi?":
        "Panen padi saat 85-95% bulir menguning dan kadar air sekitar 20-25%.",
    "apa itu konservasi tanah dan air dalam pertanian?":
        "Konservasi tanah dan air adalah upaya menjaga kesuburan tanah dan ketersediaan air melalui terasering, penanaman penutup tanah, dan pengelolaan air hujan.",
    "bagaimana pengaruh kadar pH tanah terhadap tanaman?":
        "pH tanah mempengaruhi ketersediaan unsur hara. Tanaman umumnya tumbuh optimal pada pH 5,5–7.",
    "bagaimana cara meningkatkan pH tanah yang terlalu asam?":
        "Gunakan kapur pertanian (dolomit atau kalsit) sesuai dosis untuk menaikkan pH tanah.",
    "apa itu pertanian berbasis teknologi digital (smart farming)?":
        "Smart farming menggunakan sensor, drone, dan analitik data untuk meningkatkan efisiensi dan hasil pertanian.",
    "apa kelebihan sistem tanam tanpa olah tanah (TOT)?":
        "TOT menjaga struktur tanah, mengurangi erosi, dan meningkatkan kandungan bahan organik.",
    "apa bahaya residu pestisida dalam pertanian?":
        "Residu pestisida berlebih mencemari lingkungan, membahayakan kesehatan, dan memicu resistensi hama.",
    "bagaimana pengaruh pupuk berlebih terhadap lingkungan?":
        "Pupuk berlebih menyebabkan eutrofikasi, pencemaran air tanah, dan kerusakan ekosistem.",
    "apa itu pestisida nabati?":
        "Pestisida nabati berasal dari tanaman seperti daun mimba, serai wangi, atau tembakau, aman dan ramah lingkungan.",
    "bagaimana cara mengukur kadar kelembaban tanah?":
        "Gunakan alat tensiometer atau sensor kelembaban tanah digital untuk pengukuran akurat.",
    "apa itu sistem irigasi tetes dan manfaatnya?":
        "Irigasi tetes menyalurkan air langsung ke akar tanaman, menghemat air dan mengurangi pertumbuhan gulma.",
    "apa pentingnya diversifikasi tanaman?":
        "Diversifikasi mengurangi risiko gagal panen, meningkatkan pendapatan petani, dan menjaga kesuburan tanah.",
    "bagaimana cara mengatasi tanah yang terlalu padat?":
        "Gunakan cangkul atau bajak untuk menggemburkan, tambahkan kompos, dan hindari injakan berlebih.",
    "apa itu mulsa dan manfaatnya?":
        "Mulsa adalah bahan penutup tanah (organik/anorganik) untuk menjaga kelembaban, menekan gulma, dan menstabilkan suhu.",
    "bagaimana cara deteksi awal penyakit tanaman?":
        "Pantau perubahan warna daun, bentuk tanaman, dan gunakan aplikasi deteksi penyakit berbasis AI atau kamera.",
    "apa itu sistem pertanian terpadu?":
        "Pertanian terpadu menggabungkan peternakan, perikanan, dan pertanian untuk saling mendukung dan meningkatkan efisiensi.",
    "bagaimana cara menjaga keanekaragaman hayati di lahan pertanian?":
        "Tanam berbagai jenis tanaman, pelihara tanaman pagar hidup, dan hindari penggunaan pestisida sintetis berlebih.",
    "apa itu pupuk hayati dan kelebihannya?":
        "Pupuk hayati mengandung mikroba baik yang membantu ketersediaan unsur hara. Ramah lingkungan dan memperbaiki struktur tanah.",
    "bagaimana pengaruh rotasi tanaman terhadap gulma?":
        "Rotasi tanaman memutus siklus hidup gulma spesifik, mengurangi infestasi dan resistensi terhadap herbisida.",
    "apa fungsi tanaman penutup tanah?":
        "Menjaga kelembaban, mengurangi erosi, menambah bahan organik, dan menekan gulma.",
    "apa itu sistem pertanian konservasi?":
        "Pertanian konservasi meliputi minimal olah tanah, penanaman berkelanjutan, dan penutup tanah untuk menjaga ekosistem dan hasil jangka panjang.",
    "bagaimana cara membuat pestisida alami dari bawang putih?":
        "Haluskan 100g bawang putih, campur dengan 1L air dan 1 sdm sabun cair. Diamkan 24 jam dan saring sebelum semprotkan.",
    "apa itu teknik pemangkasan dan manfaatnya?":
        "Pemangkasan adalah memotong bagian tanaman untuk merangsang pertumbuhan, produksi, dan mencegah penyakit.",
    "bagaimana mengatasi kekeringan di lahan tadah hujan?":
        "Gunakan embung, mulsa, irigasi tetes, dan tanam varietas tahan kering.",
    "apa itu sistem tumpang gilir tanaman?":
        "Tumpang gilir adalah menanam dua tanaman secara bergiliran pada lahan yang sama untuk efisiensi dan pemulihan tanah.",
    "apa manfaat menggunakan biochar?":
        "Biochar meningkatkan kapasitas tukar kation, menyerap racun, memperbaiki struktur tanah, dan menyimpan karbon.",
        # 101 - 120
    "bagaimana cara mengendalikan gulma secara mekanik?":
        "Pengendalian mekanik dilakukan dengan mencabut manual, menggunakan alat bajak, atau mencangkul secara rutin untuk menghilangkan gulma.",
    "apa itu pestisida selektif dan keuntungannya?":
        "Pestisida selektif hanya membunuh hama tertentu tanpa merusak tanaman atau organisme lain, sehingga ramah lingkungan.",
    "bagaimana pengaruh penggunaan pestisida terhadap kualitas tanah?":
        "Penggunaan pestisida berlebihan dapat menurunkan aktivitas mikroba tanah dan mengganggu keseimbangan ekosistem tanah.",
    "apa itu biopestisida dan contohnya?":
        "Biopestisida adalah pestisida berbahan dasar mikroorganisme atau ekstrak alami, misal Bacillus thuringiensis untuk mengendalikan ulat.",
    "bagaimana cara budidaya tanaman organik?":
        "Budidaya organik menggunakan pupuk alami, pestisida nabati, rotasi tanaman, dan tidak menggunakan bahan kimia sintetis.",
    "apa itu tanaman penarik hama (trap crop)?":
        "Tanaman yang sengaja ditanam untuk menarik hama agar tidak menyerang tanaman utama, contohnya jagung untuk wereng padi.",
    "bagaimana cara meningkatkan kualitas benih?":
        "Pilih benih unggul, lakukan penyimpanan dengan benar, dan perlakukan benih dengan fungisida atau perangsang tumbuh.",
    "apa itu sistem agroforestry?":
        "Agroforestry menggabungkan tanaman perkebunan dengan pohon, meningkatkan keanekaragaman hayati dan konservasi tanah.",
    "bagaimana cara menjaga kualitas air irigasi?":
        "Jaga kebersihan sumber air, hindari pencemaran limbah, dan lakukan filtrasi bila perlu untuk menjaga kualitas air.",
    "apa itu hara makro dan mikro?":
        "Hara makro dibutuhkan tanaman dalam jumlah besar (N, P, K), sedangkan hara mikro dibutuhkan sedikit (Fe, Zn, Mn, Cu).",
    "bagaimana cara memerangi resistensi hama terhadap pestisida?":
        "Rotasi jenis pestisida, gunakan dosis tepat, dan kombinasikan dengan metode pengendalian hayati.",
    "apa itu teknik penyemaian benih secara presisi?":
        "Penyemaian dengan jarak dan kedalaman seragam untuk mempercepat pertumbuhan dan memudahkan perawatan.",
    "bagaimana cara mengelola limbah pertanian?":
        "Limbah bisa dijadikan kompos, biogas, atau bahan baku pupuk organik untuk mengurangi pencemaran.",
    "apa manfaat mikroorganisme dekomposer di tanah?":
        "Mikroorganisme ini membantu menguraikan bahan organik menjadi nutrisi yang mudah diserap tanaman.",
    "bagaimana cara menggunakan teknologi drone dalam pertanian?":
        "Drone dapat digunakan untuk pemantauan lahan, penyemprotan pestisida, dan pemetaan tanaman secara efisien.",
    "apa itu tanaman penutup musim hujan dan manfaatnya?":
        "Tanaman yang ditanam untuk menutupi tanah selama musim hujan guna mencegah erosi dan meningkatkan kesuburan.",
    "bagaimana cara mengatasi serangan hama tanpa pestisida kimia?":
        "Gunakan predator alami, tanaman pengusir hama, dan teknik kultur teknis seperti rotasi tanaman dan sanitasi lahan.",
    "apa itu fertirigasi dan keunggulannya?":
        "Pemberian pupuk melalui sistem irigasi, meningkatkan efisiensi penggunaan pupuk dan distribusi nutrisi.",
    "bagaimana cara meningkatkan produktivitas tanah marginal?":
        "Tambah bahan organik, gunakan pupuk hayati, rotasi tanaman, dan teknik konservasi tanah yang tepat.",
    "apa pentingnya sertifikasi organik bagi produk pertanian?":
        "Sertifikasi menjamin produk bebas bahan kimia sintetis, meningkatkan nilai jual dan kepercayaan konsumen.",
        # 121 - 150
    "apa manfaat penggunaan pupuk organik cair?":
        "Pupuk organik cair mempercepat penyerapan nutrisi, meningkatkan kesuburan tanah, dan ramah lingkungan.",
    "bagaimana cara mendeteksi serangan hama tikus di sawah?":
        "Tanda serangan tikus meliputi lubang di sekitar tanaman, batang tanaman terpotong, dan jejak kaki di tanah basah.",
    "apa itu pengendalian hayati hama?":
        "Pengendalian hayati menggunakan musuh alami hama seperti predator, parasitoid, atau patogen untuk mengendalikan populasi hama.",
    "bagaimana cara mengatasi serangan penyakit embun tepung pada tanaman?":
        "Gunakan varietas tahan, semprot fungisida berbahan aktif sulfur, dan hindari kelembaban berlebih pada daun.",
    "apa itu pupuk hijau dan fungsinya?":
        "Pupuk hijau adalah tanaman yang ditanam untuk kemudian dibajak ke tanah sebagai sumber nitrogen dan bahan organik.",
    "bagaimana pengaruh suhu terhadap pertumbuhan tanaman?":
        "Suhu optimal mempercepat fotosintesis dan pertumbuhan, sedangkan suhu ekstrem dapat menghambat atau merusak tanaman.",
    "apa itu sistem tanam jajar legowo?":
        "Sistem tanam dengan pengaturan jarak tertentu agar tanaman mendapat cahaya dan udara cukup untuk hasil maksimal.",
    "bagaimana cara mengatasi kekeringan pada tanaman jagung?":
        "Lakukan penyiraman teratur, gunakan mulsa, dan pilih varietas tahan kekeringan.",
    "apa itu erosi tanah dan bagaimana cara mencegahnya?":
        "Erosi adalah hilangnya lapisan atas tanah oleh air atau angin; pencegahan dengan penanaman penutup, terasering, dan mulsa.",
    "bagaimana cara membuat pupuk kompos dari limbah pertanian?":
        "Kumpulkan limbah organik, susun berlapis dengan bahan hijau dan coklat, jaga kelembaban, dan aduk secara berkala sampai matang.",
    "apa itu mikroba pelarut fosfat?":
        "Mikroba yang membantu melarutkan fosfat tanah menjadi bentuk yang mudah diserap tanaman.",
    "bagaimana cara mengendalikan hama wereng dengan metode non-kimia?":
        "Gunakan predator alami seperti capung, tanaman pengusir hama, dan sanitasi lahan.",
    "apa itu sistem pertanian konservasi?":
        "Praktik pertanian yang menjaga kondisi tanah dan ekosistem dengan minim gangguan seperti tanpa olah tanah berat.",
    "bagaimana cara memperbaiki tanah yang asam?":
        "Tambahkan kapur (dolomit) untuk menaikkan pH tanah dan meningkatkan kesuburan.",
    "apa peran cacing tanah dalam kesuburan tanah?":
        "Cacing tanah membantu mengurai bahan organik dan memperbaiki struktur tanah sehingga akar mudah berkembang.",
    "bagaimana cara memanen padi yang benar?":
        "Panen saat biji berwarna kuning keemasan, gunakan alat tajam, dan keringkan gabah sebelum penyimpanan.",
    "apa itu tanaman refugia dalam pengendalian hama?":
        "Tanaman yang ditanam untuk menyediakan habitat bagi musuh alami hama agar tetap ada di lahan pertanian.",
    "bagaimana cara mengatasi serangan penyakit layu pada tanaman?":
        "Penggunaan varietas tahan, sanitasi lahan, dan rotasi tanaman bisa mengurangi serangan layu.",
    "apa itu teknik budidaya hidroponik?":
        "Budidaya tanaman tanpa media tanah menggunakan larutan nutrisi sebagai pengganti tanah.",
    "bagaimana cara mengelola irigasi tetes untuk tanaman hortikultura?":
        "Atur jadwal penyiraman berdasarkan kebutuhan tanaman, gunakan filter untuk mencegah penyumbatan, dan periksa sistem secara berkala.",
    "apa itu tanaman penangkal angin dan manfaatnya?":
        "Tanaman yang ditanam untuk mengurangi kecepatan angin, melindungi tanaman utama dari kerusakan fisik.",
    "bagaimana cara mencegah kerusakan akibat embun beku pada tanaman sayur?":
        "Gunakan penutup plastik, semprot air pada malam hari untuk membentuk lapisan pelindung, dan pilih waktu tanam yang tepat.",
    "apa itu sistem pertanian organik terpadu?":
        "Sistem yang menggabungkan budidaya tanaman, peternakan, perikanan, dan pengelolaan sumber daya secara berkelanjutan.",
    "bagaimana cara menentukan waktu panen yang tepat untuk sayuran?":
        "Perhatikan ukuran, warna, dan tekstur sesuai varietas serta kondisi pasar.",
    "apa itu sistem pertanian berkelanjutan?":
        "Pertanian yang memenuhi kebutuhan saat ini tanpa mengorbankan kemampuan generasi mendatang dengan menjaga keseimbangan lingkungan.",
    "bagaimana cara memanfaatkan limbah ternak sebagai pupuk?":
        "Proses melalui fermentasi atau komposting untuk menghasilkan pupuk kandang yang kaya nutrisi.",
    "apa itu biofertilizer dan keuntungannya?":
        "Biofertilizer adalah pupuk berbasis mikroorganisme yang meningkatkan kesuburan tanah dan pertumbuhan tanaman secara alami.",
    "bagaimana cara mengurangi emisi gas rumah kaca dari pertanian?":
        "Optimalkan penggunaan pupuk, gunakan varietas tahan perubahan iklim, dan praktikkan pertanian konservasi.",
    "apa itu tanaman penangkap karbon dan fungsinya?":
        "Tanaman yang menyerap karbon dioksida dari atmosfer untuk mengurangi dampak perubahan iklim."

}

def nlp_extract_entities(text):
    doc = nlp(text)
    entities = [(ent.label_, ent.text) for ent in doc.ents]
    lemmas = [token.lemma_ for token in doc if token.pos_ in ["VERB", "NOUN"]]
    return {
        "entities": entities,
        "lemmas": lemmas
    }

def is_relevant_question(question):
    """Memeriksa apakah pertanyaan berhubungan dengan pertanian atau cuaca"""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in [
        "padi", "hama", "tanaman", "pupuk", "sawah", "cuaca", "iklim",
        "irigasi", "panen", "pertanian", "pestisida", "organik", "hujan"
    ])

def fuzzy_match_spacy(user_message, threshold=0.85):
    """Fuzzy match pakai similarity spaCy NLP"""
    if nlp is None: # Pastikan nlp sudah terinisialisasi
        return None
    user_doc = nlp(user_message)
    best_score = 0
    best_key = None
    for key in SISTEM_PAKAR:
        key_doc = nlp(key)
        score = user_doc.similarity(key_doc)
        if score > best_score:
            best_score = score
            best_key = key
    if best_score >= threshold:
        return best_key
    return None

def summarize_answer(answer):
    "Fungsi untuk meringkas jawaban panjang menjadi versi pendek."
    lines = answer.split('\n')
    return '\n'.join(lines[:3]) + "..." if len(lines) > 3 else answer

def rekomendasi_tanaman(musim=None, suhu=None, curah_hujan=None):
    rekomendasi = []

    if musim == "hujan":
        rekomendasi.extend(["Padi", "Jagung", "Kacang Tanah"])
    if musim == "kemarau":
        rekomendasi.extend(["Jagung", "Kedelai", "Ubi Kayu"])
    if suhu and suhu < 20:
        rekomendasi.extend(["Kentang", "Wortel", "Kubis"])
    if curah_hujan and curah_hujan > 200:
        rekomendasi = [t for t in rekomendasi if t not in ["Cabai", "Bawang Merah"]]

    return rekomendasi if rekomendasi else ["Tidak ada rekomendasi spesifik"]

# Contoh penggunaan:
# print(rekomendasi_tanaman(musim="kemarau", suhu=25, curah_hujan=100))
# Output: ['Jagung', 'Kedelai', 'Ubi Kayu']

@app.route("/recommend_crop", methods=["POST"])
def recommend_crop():
    """Memberikan rekomendasi tanaman berdasarkan musim, suhu, dan curah hujan"""
    data = request.get_json()
    musim = data.get("musim", "").strip().lower()
    suhu = float(data.get("suhu", 0))
    curah_hujan = float(data.get("curah_hujan", 0))

    if not musim or suhu <= 0 or curah_hujan <= 0:
        return jsonify({"response": "Masukkan data musim, suhu, dan curah hujan yang valid."})

    rekomendasi = rekomendasi_tanaman(musim=musim, suhu=suhu, curah_hujan=curah_hujan)
    return jsonify({
        "response": f"Rekomendasi tanaman untuk kondisi tersebut: {', '.join(rekomendasi)}"
    })


last_response = ""  # Simpan jawaban untuk bisa diringkas

@app.route("/chat", methods=["POST"])
def chat():
    global last_response
    data = request.get_json()
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"response": "Ketik untuk bertanya."})

    # Jika pengguna ingin merangkum jawaban sebelumnya
    if "ringkas jawabannya" in user_message or "persingkat jawabannya" in user_message:
        if last_response:
            summarized_response = summarize_answer(last_response)
            return jsonify({"response": summarized_response})
        else:
            return jsonify({"response": "Tidak ada jawaban sebelumnya untuk diringkas."})

    # Inisialisasi bot_response di awal, ini yang menyebabkan UnboundLocalError sebelumnya
    bot_response = None

    # Cek apakah pertanyaan ada di sistem pakar (Exact Match)
    if user_message in SISTEM_PAKAR:
        bot_response = SISTEM_PAKAR[user_message]
    else:
        # Cek Fuzzy Match di SISTEM_PAKAR
        matched_key = fuzzy_match_spacy(user_message)
        if matched_key:
            bot_response = SISTEM_PAKAR[matched_key]

    # Jika sistem pakar tidak ada match, coba ke AI (Together AI)
    if bot_response is None: # Baris ini sekarang aman karena bot_response selalu terinisialisasi
        if not is_relevant_question(user_message):
            bot_response = "Maaf, saya hanya menjawab pertanyaan tentang pertanian dan cuaca."
        else:
            try:
                # Pastikan get_answer_from_ai mengembalikan string
                bot_response = get_answer_from_ai(user_message)
                if not isinstance(bot_response, str) or not bot_response.strip():
                    bot_response = "Maaf, AI tidak dapat memberikan jawaban untuk saat ini."
            except Exception as e:
                print(f"Error saat memanggil Together AI atau memproses AI response: {e}")
                bot_response = "Maaf, ada masalah teknis saat memproses permintaan AI. Coba lagi nanti."

    last_response = bot_response if bot_response is not None else "Maaf, saya tidak bisa menemukan jawaban."
    return jsonify({"response": last_response})


def get_answer_from_ai(user_message):
    "Fungsi untuk mendapatkan jawaban dari Together AI."
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "Anda adalah chatbot AI yang ahli di bidang pertanian dan cuaca. Jawablah dengan penjelasan singkat dan mudah dipahami."},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1000,
        "temperature": 0.3
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        response_json = response.json()

        if response.status_code == 200 and "choices" in response_json:
            return response_json["choices"][0].get("message", {}).get("content", "").strip()
        else:
            # Lebih detail error handling dari Together AI
            error_message = response_json.get("error", {}).get("message", "Unknown error from Together AI")
            return f"Tidak bisa mengambil jawaban dari AI: {error_message}. Status: {response.status_code}"
    except Exception as e:
        return f"Terjadi kesalahan saat menghubungkan AI: {str(e)}"


@app.route("/weather", methods=["POST"])
def get_weather():
    """Endpoint untuk mendapatkan informasi cuaca dari OpenWeather"""
    data = request.get_json()
    city = data.get("city", "").strip()

    if not city:
        return jsonify({"response": "Masukkan nama kota untuk mendapatkan informasi cuaca."})
    if not city.isalpha():
        return jsonify({"response": "Nama kota harus berupa huruf tanpa angka atau simbol."})

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
            wind_speed = weather_data.get("wind", {}).get("wind", {}).get("speed", "Tidak tersedia") # Fixed: Use wind_speed instead of wind

            weather_report = (
                f"Cuaca di {city_name}\n"
                f"Kondisi: {description}\n"
                f"Suhu: {temperature}°C\n"
                f"Kelembapan: {humidity}%\n"
                f"Kecepatan Angin: {wind_speed} m/s\n"
                f"\n Semoga informasi ini bermanfaat! "
            )
            return jsonify({"response": weather_report}) # <--- INI SUDAH DIHAPUS KOMENTARNYA
        else:
            weather_report = "Kota tidak ditemukan. Mohon cek kembali nama kota Anda."

    except Exception as e:
        weather_report = f" Maaf, terjadi kesalahan saat mengambil data cuaca: {str(e)}"

    return jsonify({"response": weather_report}) # Ini akan dijalankan jika ada error di try/except

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)