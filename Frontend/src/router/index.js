import { createRouter, createWebHistory } from 'vue-router'
import { ROUTES } from '../config/routes'
import { SITE_CONFIG } from '../config/site'
import { useAuthStore } from '../stores/auth'
import { applySeo, createBreadcrumbStructuredData } from '../utils/seo'
import { trackRouteVisit } from '../services/visitorMetricsService'
import HomeView from '../views/HomeView.vue'
import TicketCategoriasView from '../views/TicketCategoriasView.vue'
import PrivacidadView from '../views/info/PrivacidadView.vue'
import TerminosView from '../views/info/TerminosView.vue'
import ReembolsosView from '../views/info/ReembolsosView.vue'
import ContactoView from '../views/info/ContactoView.vue'
import LoginView from '../views/LoginView.vue'
import PaymentView from '../views/PaymentView.vue'
import TicketsConfigView from '../views/admin/config/TicketsConfigView.vue'
import UsuariosConfigView from '../views/admin/config/UsuariosConfigView.vue'
import PedidosConfigView from '../views/admin/config/PedidosConfigView.vue'
import UserDashboardView from '../views/user/UserDashboardView.vue'
import UnauthorizedView from '../views/UnauthorizedView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  { path: ROUTES.home, name: 'home', component: HomeView },
  { path: ROUTES.ticketCategorias, name: 'ticket-categorias', component: TicketCategoriasView },
  {
    path: ROUTES.privacidad,
    alias: [ROUTES.legacyPrivacidad],
    name: 'privacidad',
    component: PrivacidadView,
  },
  {
    path: ROUTES.terminos,
    alias: [ROUTES.legacyTerminos],
    name: 'terminos',
    component: TerminosView,
  },
  {
    path: ROUTES.reembolsos,
    alias: [ROUTES.legacyReembolsos],
    name: 'reembolsos',
    component: ReembolsosView,
  },
  {
    path: ROUTES.contacto,
    alias: [ROUTES.legacyContacto],
    name: 'contacto',
    component: ContactoView,
  },
  {
    path: ROUTES.payment,
    name: 'payment',
    component: PaymentView,
  },
  {
    path: ROUTES.login,
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: ROUTES.admin,
    name: 'admin',
    redirect: ROUTES.adminConfig,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: ROUTES.adminConfig,
    name: 'admin-config',
    component: TicketsConfigView,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: ROUTES.adminUsuarios,
    name: 'admin-usuarios',
    component: UsuariosConfigView,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: ROUTES.adminPedidos,
    name: 'admin-pedidos',
    component: PedidosConfigView,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: ROUTES.adminMetricas,
    name: 'admin-metricas',
    component: () => import('../views/admin/config/MetricasConfigView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: ROUTES.user,
    name: 'user',
    component: UserDashboardView,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: ROUTES.userHistorial,
    name: 'user-historial',
    redirect: { path: ROUTES.user, query: { section: 'tickets' } },
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: ROUTES.unauthorized,
    name: 'unauthorized',
    component: UnauthorizedView,
  },
  {
    path: ROUTES.notFound,
    name: 'not-found',
    component: NotFoundView,
  },
]

function encodePathSegment(value) {
  return encodeURIComponent(String(value || '').trim())
}

function resolvePathForSeo(to) {
  if (to.name === 'home') return ROUTES.home
  if (to.name === 'contacto') return ROUTES.contacto
  if (to.name === 'privacidad') return ROUTES.privacidad
  if (to.name === 'terminos') return ROUTES.terminos
  if (to.name === 'reembolsos') return ROUTES.reembolsos

  if (to.name === 'ticket-categorias') {
    const ticketId = encodePathSegment(to.params?.ticketId)
    return ticketId ? `/tickets/${ticketId}/categorias` : '/tickets'
  }

  if (to.name === 'payment') {
    const token = encodePathSegment(to.params?.paymentToken)
    return token ? `/payment/${token}` : '/payment'
  }

  return to.path || '/'
}

function resolveSeoForRoute(to) {
  const path = resolvePathForSeo(to)
  const base = {
    path,
    title: SITE_CONFIG.seo.defaultTitle,
    description: SITE_CONFIG.seo.defaultDescription,
    indexable: true,
    pageType: 'WebPage',
  }

  switch (to.name) {
    case 'home':
      return {
        ...base,
        title: SITE_CONFIG.seo.defaultTitle,
        description: SITE_CONFIG.seo.defaultDescription,
      }
    case 'ticket-categorias':
      return {
        ...base,
        title: `Categorias de tickets | ${SITE_CONFIG.brand.name}`,
        description:
          'Explora categorias, disponibilidad y precios de tickets para elegir tu mejor ubicacion de forma segura.',
      }
    case 'contacto':
      return {
        ...base,
        title: `Contacto oficial | ${SITE_CONFIG.brand.name}`,
        description:
          'Canales oficiales de soporte de EventTix para compras, validaciones y seguimiento postventa.',
        pageType: 'ContactPage',
      }
    case 'terminos':
      return {
        ...base,
        title: `Terminos y condiciones | ${SITE_CONFIG.brand.name}`,
        description:
          'Condiciones de uso, pagos y responsabilidades para operar con seguridad en EventTix.',
      }
    case 'privacidad':
      return {
        ...base,
        title: `Politica de privacidad | ${SITE_CONFIG.brand.name}`,
        description:
          'Consulta como EventTix protege datos personales y aplica controles de seguridad y cumplimiento.',
      }
    case 'reembolsos':
      return {
        ...base,
        title: `Politica de reembolsos | ${SITE_CONFIG.brand.name}`,
        description:
          'Revisa condiciones, plazos y requisitos para solicitudes de reembolso en EventTix.',
      }
    case 'login':
      return {
        ...base,
        title: `Acceso seguro | ${SITE_CONFIG.brand.name}`,
        description:
          'Inicia sesion de forma segura para gestionar pedidos, tickets y configuraciones de cuenta.',
        indexable: false,
      }
    case 'payment':
      return {
        ...base,
        title: `Pago seguro | ${SITE_CONFIG.brand.name}`,
        description: 'Finaliza y consulta el estado de tu pago con trazabilidad en tiempo real.',
        indexable: false,
      }
    case 'admin':
    case 'admin-config':
    case 'admin-usuarios':
    case 'admin-pedidos':
    case 'admin-metricas':
      return {
        ...base,
        title: `Panel administrativo | ${SITE_CONFIG.brand.name}`,
        description: 'Area administrativa protegida para gestion operativa de la plataforma.',
        indexable: false,
      }
    case 'user':
    case 'user-historial':
      return {
        ...base,
        title: `Panel de usuario | ${SITE_CONFIG.brand.name}`,
        description: 'Area privada del usuario para gestionar tickets, pedidos y configuraciones.',
        indexable: false,
      }
    case 'unauthorized':
      return {
        ...base,
        title: `Acceso denegado | ${SITE_CONFIG.brand.name}`,
        description: 'No cuentas con permisos para acceder a esta seccion.',
        indexable: false,
      }
    case 'not-found':
      return {
        ...base,
        title: `Pagina no encontrada | ${SITE_CONFIG.brand.name}`,
        description: 'La ruta solicitada no existe o fue movida.',
        indexable: false,
      }
    default:
      return base
  }
}

function resolveBreadcrumbForRoute(to, path) {
  switch (to.name) {
    case 'home':
      return null
    case 'ticket-categorias':
      return createBreadcrumbStructuredData([
        { name: 'Inicio', path: ROUTES.home },
        { name: 'Categorias de tickets', path },
      ])
    case 'contacto':
      return createBreadcrumbStructuredData([
        { name: 'Inicio', path: ROUTES.home },
        { name: 'Contacto', path: ROUTES.contacto },
      ])
    case 'terminos':
      return createBreadcrumbStructuredData([
        { name: 'Inicio', path: ROUTES.home },
        { name: 'Terminos', path: ROUTES.terminos },
      ])
    case 'privacidad':
      return createBreadcrumbStructuredData([
        { name: 'Inicio', path: ROUTES.home },
        { name: 'Privacidad', path: ROUTES.privacidad },
      ])
    case 'reembolsos':
      return createBreadcrumbStructuredData([
        { name: 'Inicio', path: ROUTES.home },
        { name: 'Reembolsos', path: ROUTES.reembolsos },
      ])
    default:
      return null
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0, behavior: 'smooth' }
  },
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.isInitialized) {
    await authStore.init()
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return authStore.isAdmin ? ROUTES.admin : ROUTES.user
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: ROUTES.login,
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.role === 'admin' && !authStore.isAdmin) {
    return authStore.isAuthenticated ? ROUTES.user : ROUTES.login
  }

  if (to.meta.role === 'user' && authStore.isAdmin) {
    return ROUTES.admin
  }

  return true
})

router.afterEach((to) => {
  const seo = resolveSeoForRoute(to)
  const breadcrumb = resolveBreadcrumbForRoute(to, seo.path)
  const structuredData = breadcrumb ? [breadcrumb] : []

  trackRouteVisit(to, { indexable: seo.indexable })

  applySeo({
    title: seo.title,
    description: seo.description,
    path: seo.path,
    indexable: seo.indexable,
    pageType: seo.pageType,
    structuredData,
  })
})

export default router
