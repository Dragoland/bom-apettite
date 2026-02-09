# core/qr_generator.py (versión corregida completa)
import qrcode
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

class GeneradorQR:
    def __init__(self, output_dir=None):
        if output_dir is None:
            from config.settings import Settings
            self.output_dir = Settings.QR_DIR
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generar_qr_mesa(self, mesa_id: int, ip_local: str, puerto: int, nombre_mesa: str):
        """Genera un código QR para una mesa específica"""
        try:
            url = f"http://{ip_local}:{puerto}/?mesa={mesa_id}"
            
            # Crear QR - CORREGIDO: usar colores estándar, no hexadecimales
            qr = qrcode.QRCode(
                version=3,  # Aumentar versión para más datos
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=12,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Crear imagen QR con colores estándar (no hex)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a RGB si es necesario
            if img_qr.mode != 'RGB':
                img_qr = img_qr.convert('RGB')
            
            # Añadir espacio para texto
            ancho, alto = img_qr.size
            espacio_texto = 100
            nuevo_alto = alto + espacio_texto
            
            # Crear imagen final con fondo oscuro (usando RGB, no hex en make_image)
            img_final = Image.new('RGB', (ancho, nuevo_alto), (26, 26, 46))  # #1a1a2e en RGB
            
            # Pegar QR (que tiene fondo blanco)
            img_final.paste(img_qr, (0, 0))
            
            # Añadir texto
            draw = ImageDraw.Draw(img_final)
            
            # Fuentes
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 32)
                    font_url = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 14)
                except:
                    font = ImageFont.load_default()
                    font_url = font
            
            # Dibujar nombre de mesa (color blanco)
            texto = f"{nombre_mesa}"
            bbox = draw.textbbox((0, 0), texto, font=font)
            texto_ancho = bbox[2] - bbox[0]
            draw.text(
                ((ancho - texto_ancho) / 2, alto + 20), 
                texto, 
                fill=(255, 255, 255),  # Blanco en RGB
                font=font
            )
            
            # Dibujar URL (color gris claro)
            bbox_url = draw.textbbox((0, 0), url, font=font_url)
            url_ancho = bbox_url[2] - bbox_url[0]
            draw.text(
                ((ancho - url_ancho) / 2, alto + 60),
                url,
                fill=(189, 195, 199),  # #bdc3c7 en RGB
                font=font_url
            )
            
            # Guardar
            ruta = self.output_dir / f"mesa_{mesa_id}.png"
            img_final.save(ruta, quality=95)
            
            print(f"✅ QR generado exitosamente: {ruta}")
            return str(ruta), url
            
        except Exception as e:
            print(f"❌ Error generando QR: {e}")
            import traceback
            traceback.print_exc()
            raise

