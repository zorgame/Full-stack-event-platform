export const ROUTES = {
  home: '/',
  login: '/login',
  ticketCategorias: '/tickets/:ticketId/categorias',
  privacidad: '/privacy',
  terminos: '/terms',
  reembolsos: '/refunds',
  contacto: '/contact',
  payment: '/payment/:paymentToken',
  legacyPrivacidad: '/privacidad',
  legacyTerminos: '/terminos',
  legacyReembolsos: '/reembolsos',
  legacyContacto: '/contacto',
  admin: '/admin',
  adminConfig: '/admin/config',
  adminUsuarios: '/admin/usuarios',
  adminPedidos: '/admin/pedidos',
  adminMetricas: '/admin/metricas',
  user: '/user',
  userHistorial: '/user/historial',
  unauthorized: '/acceso-denegado',
  notFound: '/:pathMatch(.*)*',
}

export function ticketCategoriasPath(ticketId) {
  return `/tickets/${ticketId}/categorias`
}

export function paymentPath(paymentToken) {
  return `/payment/${encodeURIComponent(String(paymentToken || '').trim())}`
}
