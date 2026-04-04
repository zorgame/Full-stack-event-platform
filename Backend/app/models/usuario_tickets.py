from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class UsuarioTickets(Base):
    __tablename__ = "usuario_tickets"
    __table_args__ = (
        UniqueConstraint("usuario_id", "categoria_id", name="uq_usuario_categoria_ticket"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad = Column(Integer, nullable=False, default=1)
    nota = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    usuario = relationship("Usuarios", back_populates="tickets")
    categoria = relationship("Categorias", back_populates="usuarios_tickets")
