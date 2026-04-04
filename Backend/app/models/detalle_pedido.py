from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    pedido = relationship("Pedidos", back_populates="detalles")
    categoria = relationship("Categorias", back_populates="detalles_pedido")
