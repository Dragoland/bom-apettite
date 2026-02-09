# core/models/models.py 
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Mesa(Base):
    __tablename__ = 'mesas'
    
    id = Column(Integer, primary_key=True)
    numero = Column(Integer, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    activa = Column(Boolean, default=True)
    qr_code_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    
    pedidos = relationship("Pedido", back_populates="mesa", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Mesa {self.numero}: {self.nombre}>"

class Producto(Base):
    __tablename__ = 'productos'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    categoria = Column(String(50), default='General')
    imagen_path = Column(String(255))
    disponible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    detalles_pedido = relationship("DetallePedido", back_populates="producto")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio': self.precio,
            'categoria': self.categoria,
            'imagen': self.imagen_path,
            'disponible': self.disponible
        }

class Pedido(Base):
    __tablename__ = 'pedidos'
    
    ESTADOS = ['pendiente', 'preparando', 'listo', 'entregado', 'cancelado']
    
    id = Column(Integer, primary_key=True)
    mesa_id = Column(Integer, ForeignKey('mesas.id'))
    fecha_hora = Column(DateTime, default=datetime.now)
    estado = Column(String(20), default='pendiente')
    total = Column(Float, default=0.0)
    notas = Column(Text)
    
    mesa = relationship("Mesa", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    
    def calcular_total(self):
        total = sum(d.cantidad * d.precio_unitario for d in self.detalles)
        self.total = total
        return total

class DetallePedido(Base):
    __tablename__ = 'detalles_pedido'
    
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False)
    
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_pedido")
    
    def subtotal(self):
        return self.cantidad * self.precio_unitario