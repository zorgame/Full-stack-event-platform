import { ROUTES } from './routes'
import { getEnvString } from './env'
import { SITE_CONFIG } from './site'

function isLoopbackHost(value) {
  const host = String(value || '').trim().toLowerCase()
  return host === 'localhost' || host === '127.0.0.1'
}

function resolveApiBaseUrl() {
  const configured = getEnvString('VITE_API_BASE_URL', '')
  if (!configured) return ''

  const isDev = typeof import.meta !== 'undefined' && Boolean(import.meta.env?.DEV)
  if (!isDev) return configured

  const browserHost = typeof window !== 'undefined' ? String(window.location.hostname || '').trim() : ''

  try {
    const url = new URL(configured)
    if (browserHost && isLoopbackHost(url.hostname) && isLoopbackHost(browserHost) && url.hostname !== browserHost) {
      url.hostname = browserHost
      return url.toString().replace(/\/$/, '')
    }
  } catch {
  }

  return configured
}

export const API_CONFIG = {
  baseURL: resolveApiBaseUrl(),
  timeoutMs: 15000,
}

export const STORAGE_KEYS = {
  token: 'tickets_auth_token',
  user: 'tickets_auth_user',
}

export const CACHE_CONFIG = {
  productsTtlMs: 300_000,
  categoriesTtlMs: 300_000,
  meTtlMs: 60_000,
}

export const SECTION_NAMES = {
  hero: 'Inicio',
  catalog: 'Tickets disponibles',
  footer: 'Confianza y soporte',
}

export const UI_TEXTS = {
  appName: SITE_CONFIG.brand.name,
  nav: {
    home: 'Inicio',
    contacto: 'Contacto',
    privacidad: 'Privacidad',
    terminos: 'Términos',
    reembolsos: 'Reembolsos',
  },
  hero: {
    badge: 'Cada ticket protegido',
    title: 'FIFA World Cup 2026 tickets',
    subtitle:
      'Compra con confianza en una experiencia optimizada, moderna y segura para cada partido.',
    cta: 'Ver tickets',
  },
  catalog: {
    title: 'Etapas disponibles',
    subtitle: 'Selecciona una etapa y revisa sus categorias y disponibilidad',
    action: 'Ver categorías',
    empty: 'No hay tickets disponibles en este momento.',
  },
  login: {
    title: 'Ingreso seguro',
    subtitle: 'Acceso privado por enlace directo',
    emailLabel: 'Correo electrónico',
    passwordLabel: 'Contraseña',
    submit: 'Iniciar sesión',
    loading: 'Validando credenciales...',
    invalid: 'Credenciales inválidas, inténtalo de nuevo.',
  },
  userPanel: {
    title: 'Panel de usuario',
    subtitle: 'Perfil, tickets, settings y facturacion en un solo lugar',
  },
  adminPanel: {
    title: 'Panel administrativo',
    subtitle: 'Gestión operativa y configuración',
  },
  footer: {
    claim: 'Custodia operativa, pagos auditables y trazabilidad completa para cada ticket y cada cliente.',
    copyright: `© ${new Date().getFullYear()} ${SITE_CONFIG.brand.legalName}. Todos los derechos reservados.`,
  },
}

export const BRANDING = SITE_CONFIG.brand

export const CONTACT_INFO = {
  email: SITE_CONFIG.contact.email,
  whatsappDisplay: SITE_CONFIG.contact.whatsappDisplay,
  whatsappDigits: SITE_CONFIG.contact.whatsappDigits,
  facebook: SITE_CONFIG.social.facebook,
}

export const FOOTER_LINKS = [
  { label: UI_TEXTS.nav.contacto, to: ROUTES.contacto },
  { label: UI_TEXTS.nav.privacidad, to: ROUTES.privacidad },
  { label: UI_TEXTS.nav.terminos, to: ROUTES.terminos },
  { label: UI_TEXTS.nav.reembolsos, to: ROUTES.reembolsos },
]

export const SDK_ENDPOINTS = {
  authLogin: '/auth/login',
  authMe: '/auth/me',
  productos: '/productos',
  categorias: '/categorias',
}
