import { getEnvString } from './env'

const BRAND_NAME = getEnvString('VITE_BRAND_NAME', 'EventTix')

function normalizeBaseUrl(value, fallback) {
  const normalized = String(value || '').trim().replace(/\/+$/, '')
  if (normalized) return normalized
  return String(fallback || '').trim().replace(/\/+$/, '')
}

function normalizeTwitterHandle(value) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  return raw.startsWith('@') ? raw : `@${raw}`
}

const SITE_URL = normalizeBaseUrl(getEnvString('VITE_SITE_URL', ''), 'https://eventtix.example.com')

export const SITE_CONFIG = {
  brand: {
    name: BRAND_NAME,
    legalName: getEnvString('VITE_BRAND_LEGAL_NAME', BRAND_NAME),
    logoPath: getEnvString('VITE_BRAND_LOGO_PATH', '/assets/eventtix-logo.png'),
    faviconPath: getEnvString('VITE_BRAND_FAVICON_PATH', '/assets/eventtix-logo.png'),
    ogImagePath: getEnvString('VITE_BRAND_OG_IMAGE_PATH', '/assets/eventtix-logo.png'),
  },
  contact: {
    email: getEnvString('VITE_SUPPORT_EMAIL', 'contact@eventtix.example'),
    whatsappDisplay: getEnvString('VITE_SUPPORT_WHATSAPP_DISPLAY', '+1 (555) 000-0000'),
    whatsappDigits: getEnvString('VITE_SUPPORT_WHATSAPP_DIGITS', '15550000000').replace(/\D/g, ''),
  },
  social: {
    facebook: getEnvString('VITE_FACEBOOK_URL', ''),
  },
  site: {
    url: SITE_URL,
    language: getEnvString('VITE_SITE_LANGUAGE', 'es'),
    locale: getEnvString('VITE_SITE_LOCALE', 'es_DO'),
  },
  seo: {
    defaultTitle: getEnvString('VITE_SEO_DEFAULT_TITLE', `${BRAND_NAME} | Compra segura de tickets`),
    defaultDescription: getEnvString(
      'VITE_SEO_DEFAULT_DESCRIPTION',
      'Plataforma profesional para compra segura de tickets, seguimiento de pagos y soporte especializado.'
    ),
    defaultImagePath: getEnvString('VITE_BRAND_OG_IMAGE_PATH', '/assets/eventtix-logo.png'),
    robotsPolicy: getEnvString(
      'VITE_SEO_ROBOTS',
      'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'
    ),
    themeColor: getEnvString('VITE_SEO_THEME_COLOR', '#0b2f4f'),
    twitterSite: normalizeTwitterHandle(getEnvString('VITE_SEO_TWITTER_SITE', '')),
    twitterCreator: normalizeTwitterHandle(getEnvString('VITE_SEO_TWITTER_CREATOR', '')),
    googleSiteVerification: getEnvString('VITE_SEO_GOOGLE_SITE_VERIFICATION', ''),
    bingSiteVerification: getEnvString('VITE_SEO_BING_SITE_VERIFICATION', ''),
  },
}
