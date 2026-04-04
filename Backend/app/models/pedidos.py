from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base

class Pedidos(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    referencia = Column(String(50), nullable=False, unique=True)
    estado = Column(String(50), nullable=False, default="pendiente")
    total = Column(Numeric(10, 2), nullable=False, default=0)
    correo_electronico = Column(String(255), nullable=True)
    nombre_completo = Column(String(180), nullable=True)
    telefono = Column(String(60), nullable=True)
    pais = Column(String(120), nullable=True)
    documento = Column(String(80), nullable=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuario = relationship("Usuarios", back_populates="pedidos")
    detalles = relationship(
        "DetallePedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )
