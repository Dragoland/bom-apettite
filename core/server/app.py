# core/server/app.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import shutil
import json
import time
from datetime import datetime

from config.database import SessionLocal, engine
from config.settings import Settings
from core.models.models import Base, Mesa, Producto, Pedido, DetallePedido

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BomApettite Server", version="1.0.0")

# ===== MIDDLEWARE ANTI-CACHÉ =====
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        if request.url.path.startswith(('/static/', '/images/')):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

app.add_middleware(NoCacheMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(Settings.BASE_DIR / "core" / "server" / "static")), name="static")
app.mount("/images", StaticFiles(directory=str(Settings.IMAGES_DIR)), name="images")
app.mount("/assets", StaticFiles(directory=str(Settings.ASSETS_DIR)), name="assets")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_config():
    config_file = Settings.BASE_DIR / "config" / "local.json"
    default_config = {
        "nombre_local": "BomApettite",
        "eslogan": "Sistema de Pedidos QR",
        "moneda": "$",
        "impuesto": 0,
        "propina_sugerida": "No sugerir",
        "tiempo_estimado": 20,
        "color_primario": "#e94560",
        "mensaje_bienvenida": "¡Bienvenido! Escanea el menú y ordena desde tu móvil.",
        "direccion": "",
        "telefono": ""
    }
    
    if not config_file.exists():
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return {**default_config, **config}
    except Exception as e:
        print(f"Error cargando config: {e}")
        return default_config
    
@app.get("/api/logo")
def obtener_logo():
    """Retorna la URL del logo configurado"""
    config = get_config()
    logo_path = config.get("logo_path")
    
    if logo_path and Path(logo_path).exists():
        # Retornar URL relativa
        nombre_archivo = Path(logo_path).name
        return {"url": f"/assets/{nombre_archivo}", "existe": True}
    
    return {"url": None, "existe": False}

@app.get("/", response_class=HTMLResponse)
async def carta_principal():
    config = get_config()
    nombre = config.get("nombre_local", "BomApettite")
    eslogan = config.get("eslogan", "")
    mensaje = config.get("mensaje_bienvenida", "¡Bienvenido!")
    color = config.get("color_primario", "#e94560")
    if "(" in color:
        color = color.split("(")[1].replace(")", "")
    moneda = config.get("moneda", "$").split()[0]
    
    # Verificar logo
    logo_url = None
    logo_path = config.get("logo_path")
    if logo_path and Path(logo_path).exists():
        logo_url = f"/assets/{Path(logo_path).name}"
    
    timestamp = int(time.time())
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="{color}">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    
    <title>{nombre} - Carta Digital</title>
    
    <link rel="stylesheet" href="/static/css/carta.css?v={timestamp}">
    
    <style>
        :root {{
            --primary-color: {color};
        }}
        
        .header {{
            background: linear-gradient(135deg, {color}, {color}dd);
        }}
        
        .logo-header {{
            width: 80px;
            height: 80px;
            object-fit: contain;
            margin-bottom: 0.5rem;
            border-radius: 12px;
            background: rgba(255,255,255,0.1);
            padding: 8px;
        }}
        
        .btn-agregar, .btn-confirmar, .btn-primario {{
            background-color: {color};
        }}
        
        .btn-agregar:active {{
            background-color: {color}dd;
        }}
        
        .precio, .mesa-badge, .filtro-btn.activo {{
            color: {color};
        }}
        
        .mensaje-bienvenida {{
            border-left-color: {color};
        }}
        
        .categoria h2 {{
            border-left-color: {color};
        }}
        
        .search-box:focus {{
            border-color: {color};
            box-shadow: 0 0 0 3px {color}20;
        }}
        
        .modal-contenido {{
            border-color: {color};
        }}
        
        .modal-contenido h3 {{
            color: {color};
        }}
        
        .filtro-btn.activo {{
            background-color: {color};
            border-color: {color};
            color: white;
        }}
        
        .contador {{
            background-color: {color};
        }}
    </style>
</head>
<body>
    <div id="app">
        <header class="header">
            {f'<img src="{logo_url}?v={timestamp}" class="logo-header" alt="Logo">' if logo_url else ''}
            <h1>🍽️ {nombre}</h1>
            {f"<p class='eslogan'>{eslogan}</p>" if eslogan else ""}
            <div class="mesa-badge">Mesa <span id="mesa-num">-</span></div>
        </header>
        
        <div class="mensaje-bienvenida">
            <p>💡 {mensaje}</p>
        </div>
        
        <div class="controles">
            <div class="search-container">
                <input type="text" 
                       id="search-input" 
                       class="search-box" 
                       placeholder="🔍 Buscar producto..." 
                       autocomplete="off" 
                       inputmode="search">
                <button id="btn-limpiar" 
                        class="btn-limpiar" 
                        data-action="limpiar-busqueda"
                        type="button">✕</button>
            </div>
            <div id="filtros-categorias" class="filtros-container"></div>
        </div>
        
        <main id="menu-container" class="menu-container">
            <div class="loading-spinner">Cargando menú...</div>
        </main>
        
        <div id="sin-resultados" class="sin-resultados">
            <span class="emoji">😕</span>
            <h3>No se encontraron productos</h3>
            <p>Intenta con otra búsqueda o categoría</p>
            <button data-action="limpiar-busqueda" 
                    class="btn-agregar" 
                    type="button">
                Ver todo el menú
            </button>
        </div>
        
        <div id="carrito-overlay" class="carrito-overlay"></div>
        
        <div id="carrito-panel" class="carrito-panel hidden">
            <div class="carrito-header">
                <h3>Tu Pedido</h3>
                <button data-action="cerrar-carrito" 
                        class="btn-cerrar" 
                        type="button">×</button>
            </div>
            <div id="carrito-items" class="carrito-items"></div>
            <div class="carrito-footer">
                <div class="total">
                    Total: <span id="carrito-total">0.00</span>
                </div>
                <button data-action="confirmar-pedido" 
                        class="btn-confirmar" 
                        type="button">
                    Confirmar Pedido
                </button>
            </div>
        </div>
        
        <button id="btn-carrito" 
                class="btn-flotante vacio" 
                data-action="abrir-carrito"
                type="button">
            🛒
            <span id="contador-carrito" class="contador">0</span>
        </button>
    </div>
    
    <div id="toast-container" class="toast-container"></div>
    <div id="modal-container"></div>
    
    <script>
        window.MONEDA = "{moneda}";
    </script>
    <script src="/static/js/carta.js?v={timestamp}"></script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)

@app.get("/api/menu")
def obtener_menu(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre"),
    db: Session = Depends(get_db)
):
    config = get_config()
    moneda = config.get("moneda", "$").split()[0]
    
    query = db.query(Producto).filter(Producto.disponible == True)
    
    if categoria and categoria != "Todas":
        query = query.filter(Producto.categoria == categoria)
    
    if busqueda:
        busqueda = busqueda.lower()
        query = query.filter(Producto.nombre.ilike(f"%{busqueda}%"))
    
    productos = query.order_by(Producto.categoria, Producto.nombre).all()
    
    menu = {}
    categorias = set()
    
    for p in productos:
        cat = p.categoria or "General"
        categorias.add(cat)
        if cat not in menu:
            menu[cat] = []
        menu[cat].append({
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "moneda": moneda,
            "categoria": p.categoria,
            "imagen": f"/images/{Path(p.imagen_path).name}" if p.imagen_path else None
        })
    
    return {
        "menu": menu,
        "categorias": sorted(list(categorias))
    }

@app.get("/api/categorias")
def obtener_categorias(db: Session = Depends(get_db)):
    categorias = db.query(Producto.categoria).filter(
        Producto.disponible == True
    ).distinct().all()
    
    return sorted([cat[0] or "General" for cat in categorias])

class PedidoItem(BaseModel):
    producto_id: int
    cantidad: int

class PedidoRequest(BaseModel):
    items: List[PedidoItem]
    notas: Optional[str] = None

@app.post("/api/pedido/{mesa_id}")
def crear_pedido(mesa_id: int, request: PedidoRequest, db: Session = Depends(get_db)):
    config = get_config()
    moneda = config.get("moneda", "$").split()[0]
    
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id, Mesa.activa == True).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada o inactiva")
    
    if not request.items:
        raise HTTPException(status_code=400, detail="El pedido está vacío")
    
    nuevo_pedido = Pedido(
        mesa_id=mesa_id,
        estado='pendiente',
        notas=request.notas
    )
    db.add(nuevo_pedido)
    db.flush()
    
    total = 0
    for item in request.items:
        producto = db.query(Producto).filter(
            Producto.id == item.producto_id,
            Producto.disponible == True
        ).first()
        
        if not producto:
            continue
            
        cantidad = item.cantidad
        detalle = DetallePedido(
            pedido_id=nuevo_pedido.id,
            producto_id=producto.id,
            cantidad=cantidad,
            precio_unitario=producto.precio
        )
        db.add(detalle)
        total += producto.precio * cantidad
    
    if total == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudieron agregar productos al pedido")
    
    nuevo_pedido.total = total
    db.commit()
    
    return {
        "success": True,
        "pedido_id": nuevo_pedido.id,
        "mesa": mesa.nombre,
        "total": total,
        "moneda": moneda,
        "mensaje": "Pedido recibido correctamente"
    }

@app.get("/api/pedidos/pendientes")
def get_pedidos_pendientes(db: Session = Depends(get_db)):
    pedidos = db.query(Pedido).filter(Pedido.estado == 'pendiente').order_by(Pedido.fecha_hora.desc()).all()
    return [{
        "id": p.id,
        "mesa_id": p.mesa_id,
        "mesa_nombre": p.mesa.nombre,
        "total": p.total,
        "hora": p.fecha_hora.strftime("%H:%M"),
        "notas": p.notas,
        "items": [{"nombre": d.producto.nombre, "cantidad": d.cantidad} for d in p.detalles]
    } for p in pedidos]

@app.post("/api/pedido/{pedido_id}/estado")
def actualizar_estado(pedido_id: int, estado: str, db: Session = Depends(get_db)):
    if estado not in Pedido.ESTADOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    pedido.estado = estado
    db.commit()
    return {"success": True}

@app.get("/api/version")
def get_version():
    return {"version": str(int(time.time()))}

def iniciar_servidor(host="0.0.0.0", port=8000):
    uvicorn.run(app, host=host, port=port, log_level="warning")