from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Categorias(Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("producto_id", "nombre", name="uq_producto_nombre_categoria"),)

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="USD")
    unidades_disponibles = Column(Integer, nullable=False, default=0)
    limite_por_usuario = Column(Integer, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    producto = relationship("Productos", back_populates="categorias")
    detalles_pedido = relationship("DetallePedido", back_populates="categoria")
    usuarios_tickets = relationship("UsuarioTickets", back_populates="categoria")