# 🍽️ BomApettite

Sistema de gestión de pedidos para restaurantes mediante códigos QR. Permite a los clientes ordenar directamente desde sus dispositivos móviles, eliminando la necesidad de menús físicos y optimizando el proceso de toma de pedidos.

![Python](https://img.shields.io/badge/Python-3.8+-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt-41cd52?logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/Licencia-MIT-green)

---

## ✨ Características

- **📱 Menú Digital** — Carta interactiva optimizada para móviles con imágenes y descripciones
- **🪑 Gestión de Mesas** — Creación ilimitada de mesas con códigos QR únicos
- **⚡ Pedidos en Tiempo Real** — Recepción instantánea de órdenes con notificaciones sonoras
- **📊 Reportes y Estadísticas** — Exportación a Excel con análisis de ventas
- **🔄 Estados de Pedido** — Flujo completo: Pendiente → Preparando → Listo → Entregado
- **🌐 Funcionamiento Offline** — Red local sin necesidad de internet
- **💻 Multiplataforma** — Compatible con cualquier dispositivo con WiFi y navegador

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
|------|-------------|
| **Backend** | Python 3, FastAPI, SQLAlchemy, SQLite |
| **Frontend Desktop** | PySide6 (Qt6) |
| **Frontend Móvil** | HTML5, CSS3, JavaScript Vanilla |
| **Generación QR** | qrcode (PIL/Pillow) |
| **Servidor** | Uvicorn |
| **Reportes** | pandas, openpyxl |

---

## 📁 Estructura del Proyecto

```
bom-apettite/
├── config/                     # Configuración y base de datos
│   ├── database.py            # Conexión SQLAlchemy
│   ├── settings.py            # Rutas y constantes
│   └── local.json             # Configuración del local (generado)
│
├── core/                       # Lógica de negocio
│   ├── models/                # Modelos SQLAlchemy
│   ├── qr_generator.py        # Generador de códigos QR
│   └── reportes/              # Generadores de reportes
│       └── excel_generator.py
│
├── core/server/               # Servidor web FastAPI
│   ├── app.py                 # Aplicación principal
│   └── static/                # Assets web
│       ├── css/carta.css      # Estilos carta digital
│       └── js/carta.js        # Lógica frontend móvil
│
├── desktop/                   # Aplicación de escritorio
│   ├── main.py                # Punto de entrada
│   ├── main_window.py         # Ventana principal
│   ├── widgets/               # Paneles del sistema
│   │   ├── acerca_de.py
│   │   ├── configuracion.py
│   │   ├── estadisticas.py
│   │   ├── menu_editor.py
│   │   ├── mesa_manager.py
│   │   ├── pedido_monitor.py
│   │   └── reportes.py
│   └── dialogs/               # Diálogos modales
│       ├── mesa_dialog.py
│       ├── producto_dialog.py
│       └── qr_viewer.py
│
├── assets/                    # Archivos generados
│   ├── qr_codes/              # Códigos QR de mesas
│   ├── product_images/        # Imágenes del menú
│   └── sounds/                # Efectos de sonido
│
├── database/                  # Base de datos SQLite
│   └── bomapettite.db
│
├── exports/                   # Reportes generados
└── run.py                     # Script de ejecución
```

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Dragoland/bom-apettite.git
   cd bom-apettite
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

---

## 📋 Dependencias

Crear archivo `requirements.txt`:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pyside6>=6.6.0
qrcode[pil]>=7.4.0
pillow>=10.0.0
pandas>=2.0.0
openpyxl>=3.1.0
```

---

## 🎯 Uso

### Primeros Pasos

1. **Iniciar el servidor** desde el panel de control (botón verde "INICIAR SERVIDOR")
2. **Configurar el local** en la pestaña "⚙️ Configuración":
   - Nombre del restaurante
   - Eslogan y datos de contacto
   - Moneda y colores del tema
3. **Crear mesas** en "🪑 Mesas y Códigos QR":
   - Asignar número y nombre
   - Guardar/Imprimir el código QR generado
4. **Gestionar el menú** en "🍔 Gestión del Menú":
   - Agregar productos con imágenes
   - Organizar por categorías
5. **Monitorear pedidos** en "📋 Pedidos en Tiempo Real":
   - Recibir notificaciones sonoras
   - Actualizar estados de preparación

### Para los Clientes

1. Conectarse a la **misma red WiFi** del restaurante
2. Escanear el **código QR** de su mesa
3. Navegar el menú y **agregar productos** al carrito
4. **Confirmar pedido** y esperar en su mesa

---

## 🖼️ Capturas de Pantalla

| Panel de Control | Carta Digital | Monitor de Pedidos |
|:--:|:--:|:--:|
| *(incluir screenshot)* | *(incluir screenshot)* | *(incluir screenshot)* |

---

## 🔧 Configuración Avanzada

El archivo `config/local.json` almacena la configuración del local:

```json
{
  "nombre_local": "Mi Restaurante",
  "eslogan": "Comida casera desde 1985",
  "moneda": "$ (CUP)",
  "impuesto": 0,
  "color_primario": "#e94560",
  "mensaje_bienvenida": "¡Bienvenido! Escanea el menú y ordena desde tu móvil."
}
```

---

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| Puerto 8000 ocupado | El sistema detecta automáticamente y permite forzar cierre |
| QR no se genera | Verificar permisos de escritura en `assets/qr_codes/` |
| No se escucha el sonido de pedidos | Verificar que exista `assets/sounds/notification.wav` |
| Clientes no pueden conectarse | Asegurar que estén en la misma red WiFi |

---

## 👨‍💻 Desarrollador

**Dragoland**
- 🎓 Estudiante de 2do año de Ingeniería en Ciencias Informáticas
- 🏛️ Universidad de Ciencias Informáticas (UCI) — La Habana, Cuba
- 🐙 GitHub: [@Dragoland](https://github.com/Dragoland)
- ✈️ Telegram: [@Dragoland_OP](https://t.me/Dragoland_OP)

Proyecto desarrollado como parte de la formación académica en desarrollo de software.

---

## 📄 Licencia

Este software es **gratuito** para uso personal y comercial. Se distribuye con la esperanza de ser útil, pero sin garantía alguna.

```
MIT License - 2026 Dragoland
```

---

## 🙏 Agradecimientos

- Universidad de Ciencias Informáticas (UCI) por la formación académica
- Comunidad open source por las herramientas utilizadas
- Qt Company por el framework PySide6

---

<p align="center">
  <b>🍽️ BomApettite</b> — Modernizando la experiencia gastronómica
</p>