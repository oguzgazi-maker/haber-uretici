import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap

st.set_page_config(page_title="Hızlı Haber Üretici", layout="wide")

st.title("📸 Eş Zamanlı Instagram İçerik Üretim Paneli")

col1, col2 = st.columns([1, 1])

# 1. Orijinal Şablonu Yüklüyoruz
try:
    sablon_orjinal = Image.open("sablon.png").convert("RGBA")
    width, height = sablon_orjinal.size
except:
    st.error("Klasörde 'sablon.png' bulunamadı!")
    st.stop()

# --- HIZLANDIRMA MOTORU ---
# Eş zamanlı akış için önizleme boyutunu maksimum 600 piksele sabitleyip oranlıyoruz
onizleme_orani = 600.0 / max(width, height)
onizleme_w = int(width * onizleme_orani)
onizleme_h = int(height * onizleme_orani)
# --------------------------

with col1:
    st.header("⚙️ Tasarım Ayarları")
    
    uploaded_file = st.file_uploader("Alt Katman Resmi Seçin", type=["jpg", "jpeg", "png"])
    user_text = st.text_area("Haber Metni", placeholder="Haber başlığını buraya yazın...", height=120)
    
    st.subheader("🖼️ Resim Boyut ve Konum Ayarları")
    img_scale = st.slider("Resim Büyüklüğü (Ölçek)", min_value=0.1, max_value=5.0, value=1.0, step=0.02)
    img_x = st.slider("Resim Sağ/Sol Konumu", min_value=-width, max_value=width, value=0, step=5)
    img_y = st.slider("Resim Yukarı/Aşağı Konumu", min_value=-height, max_value=height, value=0, step=5)
    
    st.subheader("🔤 Yazı Ayarları")
    font_size = st.slider("Yazı Boyutu", min_value=10, max_value=1000, value=60, step=2)
    text_x = st.slider("Yazı Sağ/Sol Konumu (X)", min_value=0, max_value=width, value=int(width*0.05), step=5)
    text_y = st.slider("Yazı Yukarı/Aşağı Konumu (Y)", min_value=0, max_value=height, value=int(height*0.8), step=5)
    max_chars = st.slider("Satır Başına Maks Karakter", min_value=10, max_value=100, value=40)
    
    text_color_hex = st.color_picker("Yazı Rengi", "#FFFFFF")
    h = text_color_hex.lstrip('#')
    text_color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)

with col2:
    st.header("👁️ Canlı Önizleme")
    
    if uploaded_file:
        # Görsel birleştirme fonksiyonu (Hem önizleme hem indirme için ortak)
        def gorsel_olustur(is_preview=False):
            # Eğer önizleme ise boyutları küçültüp hızı uçuruyoruz
            current_w, current_h = (onizleme_w, onizleme_h) if is_preview else (width, height)
            current_scale = img_scale * onizleme_orani if is_preview else img_scale
            current_img_x = int(img_x * onizleme_orani) if is_preview else img_x
            current_img_y = int(img_y * onizleme_orani) if is_preview else img_y
            current_font_size = int(font_size * onizleme_orani) if is_preview else font_size
            current_text_x = int(text_x * onizleme_orani) if is_preview else text_x
            current_text_y = int(text_y * onizleme_orani) if is_preview else text_y
            
            # Katmanları hazırla
            sablon_current = sablon_orjinal.resize((current_w, current_h)) if is_preview else sablon_orjinal
            orjinal_resim = Image.open(uploaded_file).convert("RGBA")
            
            yeni_w = int(orjinal_resim.width * current_scale)
            yeni_h = int(orjinal_resim.height * current_scale)
            boyutlandirilmis_resim = orjinal_resim.resize((yeni_w, yeni_h))
            
            arka_plan = Image.new("RGBA", (current_w, current_h), (0, 0, 0, 0))
            arka_plan.paste(boyutlandirilmis_resim, (current_img_x, current_img_y), boyutlandirilmis_resim)
            sonuc = Image.alpha_composite(arka_plan, sablon_current)
            
            # Yazıyı ekle
            if user_text:
                draw = ImageDraw.Draw(sonuc)
                try:
                    font = ImageFont.truetype("font.ttf", current_font_size)
                except:
                    try:
                        font = ImageFont.truetype("font.otf", current_font_size)
                    except:
                        font = ImageFont.load_default()
                
                input_lines = user_text.splitlines()
                final_lines = []
                for line in input_lines:
                    if line.strip() == "":
                        final_lines.append("")
                    else:
                        final_lines.extend(textwrap.wrap(line, width=max_chars))
                
                curr_y = current_text_y
                for line in final_lines:
                    draw.text((current_text_x, curr_y), line, font=font, fill=text_color)
                    curr_y += int(current_font_size * 1.2)
            
            return sonuc

        # 1. CANLI ÖNİZLEME (Hafif ve Işık Hızında)
        gosterilecek_gorsel = gorsel_olustur(is_preview=True).convert("RGB")
        st.image(gosterilecek_gorsel, caption="Canlı Tasarım Alanı", use_container_width=False, width=onizleme_w)
        
        # 2. YÜKSEK KALİTELİ İNDİRME (Yalnızca butona basınca arkada üretilir)
        import io
        buf = io.BytesIO()
        
        # İndirme hazırlığı kullanıcıyı yavaşlatmasın diye bir "Oluştur" mekanizması kuruyoruz
        if st.button("🔥 Görseli Yüksek Kalitede Hazırla"):
            with st.spinner("Orijinal çözünürlükte işleniyor..."):
                yuksek_kalite = gorsel_olustur(is_preview=False).convert("RGB")
                yuksek_kalite.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 Bilgisayara / Telefona İndir",
                    data=byte_im,
                    file_name="instagram_haber_hq.jpg",
                    mime="image/jpeg"
                )
    else:
        st.info("Lütfen sol taraftan bir resim yükleyin.")