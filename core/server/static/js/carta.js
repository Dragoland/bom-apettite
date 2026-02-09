/**
 * BOM_APETITE - CARTA DIGITAL v2.0
 * Sistema táctil robusto con delegación de eventos
 */

class CartaApp {
    constructor() {
        this.mesaId = null;
        this.carrito = [];
        this.menuCompleto = {};
        this.categorias = [];
        this.categoriaActiva = 'Todas';
        this.terminoBusqueda = '';
        
        // Referencias DOM cacheadas
        this.refs = {};
        
        // Flags para prevenir doble ejecución
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        // Obtener mesa de URL
        const params = new URLSearchParams(window.location.search);
        this.mesaId = params.get('mesa');
        
        if (!this.mesaId) {
            this.mostrarError('Escanea el código QR desde tu mesa');
            return;
        }

        // Cachear referencias DOM
        this.cachearReferencias();
        
        // Actualizar UI inicial
        this.refs.mesaNum.textContent = this.mesaId;
        
        // Configurar event listeners (delegación)
        this.setupEventListeners();
        
        // Cargar datos
        this.cargarMenu();
    }

    cachearReferencias() {
        this.refs = {
            mesaNum: document.getElementById('mesa-num'),
            searchInput: document.getElementById('search-input'),
            btnLimpiar: document.getElementById('btn-limpiar'),
            filtrosContainer: document.getElementById('filtros-categorias'),
            menuContainer: document.getElementById('menu-container'),
            sinResultados: document.getElementById('sin-resultados'),
            carritoPanel: document.getElementById('carrito-panel'),
            carritoOverlay: document.getElementById('carrito-overlay'),
            carritoItems: document.getElementById('carrito-items'),
            carritoTotal: document.getElementById('carrito-total'),
            contadorCarrito: document.getElementById('contador-carrito'),
            btnCarrito: document.getElementById('btn-carrito'),
            toastContainer: document.getElementById('toast-container'),
            modalContainer: document.getElementById('modal-container')
        };
    }

    setupEventListeners() {
        // === DELEGACIÓN DE EVENTOS PRINCIPAL ===
        // Usamos un solo listener en document para todo, filtrando por data-action
        
        // Click/Touch principal - Usamos solo 'click' (funciona para touch y mouse)
        document.addEventListener('click', (e) => this.handleGlobalClick(e));
        
        // Input de búsqueda
        if (this.refs.searchInput) {
            this.refs.searchInput.addEventListener('input', (e) => {
                this.terminoBusqueda = e.target.value.trim();
                this.actualizarBotonLimpiar();
                this.actualizarVista();
            });
            
            this.refs.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.limpiarBusqueda();
                }
            });
        }

        // Scroll horizontal con drag en filtros
        this.setupDragScroll(this.refs.filtrosContainer);
        
        // Cerrar carrito al hacer click en overlay
        if (this.refs.carritoOverlay) {
            this.refs.carritoOverlay.addEventListener('click', () => this.cerrarCarrito());
        }
        
        // Prevenir zoom en gestos de iOS
        document.addEventListener('gesturestart', (e) => e.preventDefault());
        document.addEventListener('gesturechange', (e) => e.preventDefault());
        document.addEventListener('gestureend', (e) => e.preventDefault());
    }

    handleGlobalClick(e) {
        // Buscar el elemento con data-action más cercano
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const action = target.dataset.action;
        const id = target.dataset.id ? parseInt(target.dataset.id) : null;
        
        // Prevenir comportamiento por defecto solo si es necesario
        if (action === 'agregar' || action === 'filtrar' || action === 'cerrar-carrito') {
            e.preventDefault();
        }
        
        // Ejecutar acción
        switch(action) {
            case 'agregar':
                if (id) {
                    const nombre = target.dataset.nombre;
                    const precio = parseFloat(target.dataset.precio);
                    this.agregarProducto(id, nombre, precio);
                }
                break;
                
            case 'filtrar':
                const categoria = target.dataset.categoria;
                this.filtrarPorCategoria(categoria);
                break;
                
            case 'limpiar-busqueda':
                this.limpiarBusqueda();
                break;
                
            case 'abrir-carrito':
                this.abrirCarrito();
                break;
                
            case 'cerrar-carrito':
                this.cerrarCarrito();
                break;
                
            case 'cambiar-cantidad':
                if (id) {
                    const delta = parseInt(target.dataset.delta);
                    this.cambiarCantidad(id, delta);
                }
                break;
                
            case 'confirmar-pedido':
                this.enviarPedido();
                break;
                
            case 'resolver-notas':
                const valor = target.dataset.valor === 'null' ? null : 
                             (document.getElementById('notas-input')?.value || '');
                this.resolverNotas(valor);
                break;
                
            case 'cerrar-toast':
                target.closest('.toast')?.remove();
                break;
                
            case 'recargar':
                location.reload();
                break;
        }
    }

    setupDragScroll(element) {
        if (!element) return;
        
        let isDown = false;
        let startX;
        let scrollLeft;
        let isDragging = false;
        let startTime;
        
        const handleStart = (e) => {
            isDown = true;
            isDragging = false;
            startTime = Date.now();
            element.style.cursor = 'grabbing';
            startX = (e.pageX || e.touches[0].pageX) - element.offsetLeft;
            scrollLeft = element.scrollLeft;
        };
        
        const handleEnd = () => {
            isDown = false;
            element.style.cursor = 'grab';
            // Si fue un drag corto, no prevenimos el click
            setTimeout(() => { isDragging = false; }, 10);
        };
        
        const handleMove = (e) => {
            if (!isDown) return;
            e.preventDefault();
            isDragging = true;
            const x = (e.pageX || e.touches[0].pageX) - element.offsetLeft;
            const walk = (x - startX) * 1.5;
            element.scrollLeft = scrollLeft - walk;
        };
        
        // Mouse events
        element.addEventListener('mousedown', handleStart);
        element.addEventListener('mouseleave', handleEnd);
        element.addEventListener('mouseup', handleEnd);
        element.addEventListener('mousemove', handleMove);
        
        // Touch events
        element.addEventListener('touchstart', handleStart, {passive: true});
        element.addEventListener('touchend', handleEnd);
        element.addEventListener('touchmove', handleMove, {passive: true});
        
        // Prevenir click en los botones si se está arrastrando
        element.addEventListener('click', (e) => {
            if (isDragging || (Date.now() - startTime > 200)) {
                e.stopPropagation();
            }
        }, true);
    }

    // ==========================================
    // LÓGICA DE DATOS
    // ==========================================

    async cargarMenu() {
        try {
            this.mostrarCargando();
            
            const response = await fetch('/api/menu');
            if (!response.ok) throw new Error('Error al cargar menú');
            
            const data = await response.json();
            this.menuCompleto = data.menu;
            this.categorias = data.categorias;
            
            this.generarFiltros();
            this.renderizarMenu();
            
        } catch (error) {
            console.error('Error:', error);
            this.mostrarError('Error al cargar el menú. Toca para recargar.');
        }
    }

    mostrarCargando() {
        if (this.refs.menuContainer) {
            this.refs.menuContainer.innerHTML = `
                <div class="loading-spinner">
                    Cargando menú...
                </div>
            `;
        }
    }

    // ==========================================
    // RENDERIZADO
    // ==========================================

    generarFiltros() {
        if (!this.refs.filtrosContainer) return;
        
        const html = [
            this.crearBotonFiltroHTML('Todas', '🍽️ Todas', true),
            ...this.categorias.map(cat => {
                const emoji = this.getEmojiCategoria(cat);
                return this.crearBotonFiltroHTML(cat, `${emoji} ${cat}`, false);
            })
        ].join('');
        
        this.refs.filtrosContainer.innerHTML = html;
    }

    crearBotonFiltroHTML(valor, texto, activo) {
        return `
            <button class="filtro-btn ${activo ? 'activo' : ''}" 
                    data-action="filtrar" 
                    data-categoria="${valor}"
                    type="button">
                ${texto}
            </button>
        `;
    }

    getEmojiCategoria(categoria) {
        const emojis = {
            'Entrantes': '🥗', 'Entradas': '🥗', 'Aperitivos': '🥗',
            'Principales': '🍽️', 'Platos Fuertes': '🍽️', 'Carnes': '🥩',
            'Postres': '🍰', 'Dulces': '🍰',
            'Bebidas': '🥤', 'Bebida': '🥤', 'Refrescos': '🥤',
            'Café': '☕', 'Cafeteria': '☕',
            'Desayunos': '🍳', 'Almuerzos': '🍛', 'Cenas': '🌙',
            'Snack': '🍿', 'Snacks': '🍿',
            'General': '🍴', 'Otros': '🍴'
        };
        return emojis[categoria] || '🍽️';
    }

    renderizarMenu() {
        if (!this.refs.menuContainer) return;
        
        const html = Object.entries(this.menuCompleto).map(([categoria, productos], catIndex) => {
            const emoji = this.getEmojiCategoria(categoria);
            
            return `
                <div class="categoria" style="animation-delay: ${catIndex * 0.1}s">
                    <div class="categoria-header">
                        <h2>${emoji} ${categoria}</h2>
                        <span class="contador-cat">${productos.length} items</span>
                    </div>
                    ${productos.map((prod, prodIndex) => this.crearProductoHTML(prod, catIndex, prodIndex)).join('')}
                </div>
            `;
        }).join('');
        
        this.refs.menuContainer.innerHTML = html;
    }

    crearProductoHTML(producto, catIndex, prodIndex) {
        const moneda = producto.moneda || window.MONEDA || '$';
        // Escapar comillas para atributos data
        const nombreEscapado = producto.nombre.replace(/"/g, '&quot;');
        
        return `
            <div class="producto" style="animation-delay: ${(catIndex * 0.1) + (prodIndex * 0.05)}s">
                ${producto.imagen ? `
                    <img src="${producto.imagen}" 
                         class="producto-imagen" 
                         alt="${producto.nombre}" 
                         loading="lazy">
                ` : ''}
                <div class="producto-info">
                    <h3>${producto.nombre}</h3>
                    ${producto.descripcion ? `
                        <p class="producto-desc">${producto.descripcion}</p>
                    ` : ''}
                    <div class="producto-footer">
                        <span class="precio">${moneda}${producto.precio.toFixed(2)}</span>
                        <button class="btn-agregar" 
                                data-action="agregar"
                                data-id="${producto.id}"
                                data-nombre="${nombreEscapado}"
                                data-precio="${producto.precio}"
                                type="button">
                            <span>+</span> Añadir
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderizarProductosFiltrados(menu) {
        if (!this.refs.menuContainer) return;
        
        const html = Object.entries(menu).map(([categoria, productos], catIndex) => {
            const emoji = this.getEmojiCategoria(categoria);
            
            return `
                <div class="categoria">
                    <div class="categoria-header">
                        <h2>${emoji} ${categoria}</h2>
                        <span class="contador-cat">${productos.length} items</span>
                    </div>
                    ${productos.map((prod, prodIndex) => this.crearProductoHTML(prod, catIndex, prodIndex)).join('')}
                </div>
            `;
        }).join('');
        
        this.refs.menuContainer.innerHTML = html;
    }

    // ==========================================
    // FILTRADO Y BÚSQUEDA
    // ==========================================

    filtrarPorCategoria(categoria) {
        this.categoriaActiva = categoria;
        
        // Actualizar UI de botones
        const botones = this.refs.filtrosContainer?.querySelectorAll('.filtro-btn');
        botones?.forEach(btn => {
            const esActivo = btn.dataset.categoria === categoria;
            btn.classList.toggle('activo', esActivo);
        });
        
        this.actualizarVista();
    }

    limpiarBusqueda() {
        this.terminoBusqueda = '';
        this.categoriaActiva = 'Todas';
        
        if (this.refs.searchInput) {
            this.refs.searchInput.value = '';
            this.refs.searchInput.blur();
        }
        
        this.actualizarBotonLimpiar();
        
        // Resetear filtros visuales
        const botones = this.refs.filtrosContainer?.querySelectorAll('.filtro-btn');
        botones?.forEach((btn, index) => {
            btn.classList.toggle('activo', index === 0);
        });
        
        this.actualizarVista();
    }

    actualizarBotonLimpiar() {
        if (this.refs.btnLimpiar) {
            this.refs.btnLimpiar.classList.toggle('visible', !!this.terminoBusqueda);
        }
    }

    actualizarVista() {
        let productosFiltrados = {};
        let totalProductos = 0;
        
        Object.entries(this.menuCompleto).forEach(([categoria, productos]) => {
            if (this.categoriaActiva !== 'Todas' && categoria !== this.categoriaActiva) {
                return;
            }
            
            const filtrados = productos.filter(p => {
                if (!this.terminoBusqueda) return true;
                const termino = this.terminoBusqueda.toLowerCase();
                return p.nombre.toLowerCase().includes(termino) ||
                       (p.descripcion && p.descripcion.toLowerCase().includes(termino));
            });
            
            if (filtrados.length > 0) {
                productosFiltrados[categoria] = filtrados;
                totalProductos += filtrados.length;
            }
        });
        
        // Mostrar/ocultar mensaje de sin resultados
        const hayResultados = totalProductos > 0;
        
        if (this.refs.sinResultados) {
            this.refs.sinResultados.classList.toggle('visible', !hayResultados);
        }
        
        if (this.refs.menuContainer) {
            this.refs.menuContainer.style.display = hayResultados ? 'block' : 'none';
        }
        
        if (hayResultados) {
            this.renderizarProductosFiltrados(productosFiltrados);
        }
    }

    // ==========================================
    // CARRITO
    // ==========================================

    agregarProducto(id, nombre, precio) {
        // Feedback táctil
        if (navigator.vibrate) navigator.vibrate(40);
        
        const existente = this.carrito.find(item => item.id === id);
        if (existente) {
            existente.cantidad++;
        } else {
            this.carrito.push({ id, nombre, precio, cantidad: 1 });
        }
        
        this.actualizarCarritoUI();
        this.mostrarToast(`✓ ${nombre} añadido`);
    }

    cambiarCantidad(id, delta) {
        const item = this.carrito.find(i => i.id === id);
        if (!item) return;
        
        item.cantidad += delta;
        if (item.cantidad <= 0) {
            this.carrito = this.carrito.filter(i => i.id !== id);
        }
        
        this.actualizarCarritoUI();
    }

    actualizarCarritoUI() {
        const totalItems = this.carrito.reduce((sum, item) => sum + item.cantidad, 0);
        const totalPrecio = this.carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
        const moneda = window.MONEDA || '$';
        
        // Actualizar contador flotante
        if (this.refs.contadorCarrito) {
            this.refs.contadorCarrito.textContent = totalItems;
        }
        
        // Mostrar/ocultar botón flotante
        if (this.refs.btnCarrito) {
            this.refs.btnCarrito.classList.toggle('vacio', totalItems === 0);
            this.refs.btnCarrito.classList.toggle('tiene-items', totalItems > 0);
        }
        
        // Renderizar items en panel
        if (this.refs.carritoItems) {
            if (this.carrito.length === 0) {
                this.refs.carritoItems.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                        <p style="font-size: 2rem; margin-bottom: 0.5rem;">🛒</p>
                        <p>Tu carrito está vacío</p>
                    </div>
                `;
            } else {
                this.refs.carritoItems.innerHTML = this.carrito.map(item => `
                    <div class="item-carrito">
                        <div class="item-info">
                            <h4>${item.nombre}</h4>
                            <div class="item-precio">${moneda}${item.precio.toFixed(2)} c/u</div>
                        </div>
                        <div class="cantidad-control">
                            <button type="button" 
                                    data-action="cambiar-cantidad" 
                                    data-id="${item.id}" 
                                    data-delta="-1"
                                    aria-label="Disminuir">−</button>
                            <span>${item.cantidad}</span>
                            <button type="button" 
                                    data-action="cambiar-cantidad" 
                                    data-id="${item.id}" 
                                    data-delta="1"
                                    aria-label="Aumentar">+</button>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        // Actualizar total
        if (this.refs.carritoTotal) {
            this.refs.carritoTotal.textContent = totalPrecio.toFixed(2);
        }
    }

    abrirCarrito() {
        if (this.carrito.length === 0) {
            this.mostrarToast('Agrega productos primero', true);
            return;
        }
        
        if (this.refs.carritoOverlay) {
            this.refs.carritoOverlay.classList.add('abierto');
        }
        if (this.refs.carritoPanel) {
            this.refs.carritoPanel.classList.remove('hidden');
            // Forzar reflow
            void this.refs.carritoPanel.offsetWidth;
            this.refs.carritoPanel.classList.add('abierto');
        }
        
        document.body.style.overflow = 'hidden';
    }

    cerrarCarrito() {
        if (this.refs.carritoPanel) {
            this.refs.carritoPanel.classList.remove('abierto');
        }
        
        setTimeout(() => {
            if (this.refs.carritoOverlay) {
                this.refs.carritoOverlay.classList.remove('abierto');
            }
            if (this.refs.carritoPanel) {
                this.refs.carritoPanel.classList.add('hidden');
            }
            document.body.style.overflow = '';
        }, 300);
    }

    // ==========================================
    // ENVÍO DE PEDIDO
    // ==========================================

    async enviarPedido() {
        if (this.carrito.length === 0 || this.isProcessing) return;
        
        const notas = await this.mostrarDialogoNotas();
        if (notas === null) return; // Usuario canceló
        
        this.isProcessing = true;
        
        const btn = document.querySelector('[data-action="confirmar-pedido"]');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Enviando...';
        }

        try {
            const response = await fetch(`/api/pedido/${this.mesaId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    items: this.carrito.map(({id, cantidad}) => ({producto_id: id, cantidad})),
                    notas: notas
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.mostrarToast('🎉 ¡Pedido enviado correctamente!');
                this.carrito = [];
                this.actualizarCarritoUI();
                this.cerrarCarrito();
            } else {
                throw new Error(data.mensaje || 'Error al enviar');
            }
        } catch (error) {
            this.mostrarToast('❌ ' + error.message, true);
        } finally {
            this.isProcessing = false;
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Confirmar Pedido';
            }
        }
    }

    mostrarDialogoNotas() {
        return new Promise((resolve) => {
            this.resolveNotas = resolve;
            
            if (this.refs.modalContainer) {
                this.refs.modalContainer.innerHTML = `
                    <div class="modal-overlay" id="modal-notas">
                        <div class="modal-contenido">
                            <h3>📝 Notas del Pedido</h3>
                            <p>¿Alguna indicación especial?</p>
                            <textarea id="notas-input" 
                                      placeholder="Ej: Sin cebolla, bien cocido, alergia a maní..."
                                      rows="3"></textarea>
                            <div class="modal-botones">
                                <button type="button" 
                                        class="btn-secundario" 
                                        data-action="resolver-notas"
                                        data-valor="null">
                                    Omitir
                                </button>
                                <button type="button" 
                                        class="btn-primario" 
                                        data-action="resolver-notas"
                                        data-valor="input">
                                    Agregar
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Mostrar modal
                requestAnimationFrame(() => {
                    document.getElementById('modal-notas')?.classList.add('abierto');
                });
                
                // Focus en textarea
                setTimeout(() => {
                    document.getElementById('notas-input')?.focus();
                }, 100);
            } else {
                resolve('');
            }
        });
    }

    resolverNotas(valor) {
        // Cerrar modal
        const modal = document.getElementById('modal-notas');
        if (modal) {
            modal.classList.remove('abierto');
            setTimeout(() => {
                if (this.refs.modalContainer) {
                    this.refs.modalContainer.innerHTML = '';
                }
            }, 300);
        }
        
        // Resolver promise
        if (this.resolveNotas) {
            this.resolveNotas(valor);
            this.resolveNotas = null;
        }
    }

    // ==========================================
    // NOTIFICACIONES
    // ==========================================

    mostrarToast(mensaje, esError = false) {
        if (!this.refs.toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${esError ? 'error' : ''}`;
        toast.innerHTML = `
            <span>${mensaje}</span>
            <button type="button" 
                    class="toast-cerrar" 
                    data-action="cerrar-toast"
                    aria-label="Cerrar">×</button>
        `;
        
        this.refs.toastContainer.appendChild(toast);
        
        // Animar entrada
        requestAnimationFrame(() => {
            toast.classList.add('visible');
        });
        
        // Auto-cerrar
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    mostrarError(mensaje) {
        if (this.refs.menuContainer) {
            this.refs.menuContainer.innerHTML = `
                <div class="sin-resultados visible">
                    <span class="emoji">📱</span>
                    <h3>${mensaje}</h3>
                    <p style="color: var(--text-muted); margin: 1rem 0;">
                        Asegúrate de escanear el código QR desde tu mesa
                    </p>
                    <button class="btn-agregar" 
                            data-action="recargar"
                            type="button"
                            style="margin-top: 1rem;">
                        🔄 Recargar página
                    </button>
                </div>
            `;
        }
    }
}

// ==========================================
// INICIALIZACIÓN
// ==========================================

let app;

function iniciarApp() {
    app = new CartaApp();
}

// Iniciar cuando DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarApp);
} else {
    iniciarApp();
}