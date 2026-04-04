export const TICKET_FORM_FIELDS = [
  { key: 'nombre', label: 'Nombre del ticket', type: 'text', required: true, placeholder: 'Ej: FIFA World Cup Quarterfinals' },
  { key: 'ubicacion', label: 'Ciudad / país', type: 'text', required: true, placeholder: 'Ej: Ciudad de México, México' },
  { key: 'estadio', label: 'Estadio', type: 'text', required: false, placeholder: 'Ej: Estadio Azteca' },
  {
    key: 'ubicacion_estadio',
    label: 'Ubicación del estadio',
    type: 'text',
    required: false,
    placeholder: 'Ej: Colonia, dirección o zona del estadio',
  },
  { key: 'fecha', label: 'Fecha y hora', type: 'datetime-local', required: false },
  { key: 'descripcion', label: 'Descripción', type: 'textarea', required: false, rows: 3, placeholder: 'Descripción comercial del ticket' },
  { key: 'is_active', label: 'Activo', type: 'switch', required: false },
]

export const CATEGORY_FORM_FIELDS = [
  { key: 'nombre', label: 'Nombre de categoría', type: 'text', required: true, placeholder: 'Ej: VIP' },
  { key: 'descripcion', label: 'Descripción', type: 'textarea', required: false, rows: 2 },
  { key: 'precio', label: 'Precio', type: 'number', required: true, min: 0.01, step: '0.01' },
  { key: 'moneda', label: 'Moneda', type: 'text', required: true, placeholder: 'USD' },
  { key: 'unidades_disponibles', label: 'Unidades disponibles', type: 'number', required: true, min: 0, step: '1' },
  { key: 'limite_por_usuario', label: 'Límite por usuario', type: 'number', required: false, min: 1, step: '1' },
  { key: 'activo', label: 'Visible para venta', type: 'switch', required: false },
  { key: 'is_active', label: 'Activo en sistema', type: 'switch', required: false },
]

export const USER_FORM_FIELDS = [
  { key: 'email', label: 'Email', type: 'email', required: true, placeholder: 'usuario@dominio.com' },
  { key: 'nombre', label: 'Nombre', type: 'text', required: false },
  { key: 'apellido', label: 'Apellido', type: 'text', required: false },
  { key: 'telefono', label: 'Teléfono', type: 'text', required: false },
  { key: 'pais', label: 'País', type: 'text', required: false },
  { key: 'password', label: 'Contraseña (opcional)', type: 'password', required: false, placeholder: 'Mínimo 20 caracteres con símbolos y números' },
  { key: 'is_active', label: 'Usuario activo', type: 'switch', required: false },
]
