from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func, text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Productos(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    fecha = Column(DateTime(timezone=True), nullable=True)
    ubicacion = Column(String(255), nullable=False)
    estadio = Column(String(255), nullable=True)
    ubicacion_estadio = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)
    imagen = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    categorias = relationship("Categorias", back_populates="producto", cascade="all, delete-orphan")