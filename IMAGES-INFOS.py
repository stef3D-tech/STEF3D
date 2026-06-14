import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fpdf import FPDF
from staticmap import StaticMap, CircleMarker

def get_decimal_from_dms(dms, ref):
    degrees = float(dms[0])
    minutes = float(dms[1]) / 60.0
    seconds = float(dms[2]) / 3600.0
    if ref in ['S', 'W']:
        return -(degrees + minutes + seconds)
    return degrees + minutes + seconds

class MetadataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BromeAI - Image Analyzer Pro")
        self.root.geometry("400x250")
        
        tk.Label(root, text="Analyseur d'Image avec GPS & Carte", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Button(root, text="Sélectionner une Image", command=self.process_image, height=2, width=25, bg="#007AFF").pack(pady=20)

    def process_image(self):
        img_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not img_path: return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not save_path: return

        try:
            img = Image.open(img_path)
            exif = img._getexif()
            metadata = {}
            lat, lon = None, None

            if exif:
                for tag, value in exif.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        gps_data = {}
                        for t in value:
                            sub_tag = GPSTAGS.get(t, t)
                            gps_data[sub_tag] = value[t]
                        
                        if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                            lat = get_decimal_from_dms(gps_data["GPSLatitude"], gps_data["GPSLatitudeRef"])
                            lon = get_decimal_from_dms(gps_data["GPSLongitude"], gps_data["GPSLongitudeRef"])
                    else:
                        metadata[str(decoded)] = str(value)

            # --- Génération du PDF ---
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Rapport d'Analyse d'Image", ln=True, align='C')
            
            # 1. Ajout de la miniature (Thumbnail)
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Miniature de l'image :", ln=True)
            # Sauvegarde temporaire de la miniature
            thumb_path = "temp_thumb.jpg"
            img.thumbnail((400, 400))
            img.save(thumb_path)
            pdf.image(thumb_path, x=10, y=pdf.get_y(), w=50)
            pdf.set_y(pdf.get_y() + 60)

            # 2. Ajout de la carte GPS si disponible
            if lat and lon:
                pdf.cell(0, 10, f"Localisation GPS : {lat:.5f}, {lon:.5f}", ln=True)
                m = StaticMap(300, 200)
                m.add_marker(CircleMarker((lon, lat), "red", 10))
                map_img = m.render()
                map_img.save("temp_map.png")
                pdf.image("temp_map.png", x=10, y=pdf.get_y(), w=80)
                pdf.set_y(pdf.get_y() + 65)

            # 3. Métadonnées textuelles
            pdf.set_font("Arial", size=8)
            for k, v in list(metadata.items())[:30]: # Limité pour éviter un PDF trop long
                text = f"{k}: {v}".encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, text)

            pdf.output(save_path)
            messagebox.showinfo("Succès", "Le PDF avec carte et miniature a été généré !")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MetadataApp(root)
    root.mainloop()
