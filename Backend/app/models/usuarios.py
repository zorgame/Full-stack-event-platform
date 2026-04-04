from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Usuarios(Base):
	__tablename__ = "usuarios"

	id = Column(Integer, primary_key=True, index=True)
	email = Column(String(255), unique=True, index=True, nullable=False)
	telefono = Column(String(30), nullable=True)
	nombre = Column(String(120), nullable=True)
	apellido = Column(String(120), nullable=True)
	pais = Column(String(100), nullable=True)
	hashed_password = Column(String(255), nullable=False)
	is_active = Column(Boolean, nullable=False, server_default=text("1"))
	is_admin = Column(Boolean, nullable=False, server_default=text("0"))
	created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
	updated_at = Column(
		DateTime(timezone=True),
		nullable=False,
		server_default=func.now(),
		onupdate=func.now(),
	)

	pedidos = relationship("Pedidos", back_populates="usuario")
	tickets = relationship("UsuarioTickets", back_populates="usuario", cascade="all, delete-orphan")
