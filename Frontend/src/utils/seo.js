import { SITE_CONFIG } from '../config/site'

const NOINDEX_ROBOTS_POLICY = 'noindex, nofollow, noarchive'

function safeText(value, fallback = '') {
  const normalized = String(value || '').trim()
  return normalized || fallback
}

function normalizePath(pathname = '/') {
  const text = String(pathname || '/').trim()
  if (!text) return '/'
  return text.startsWith('/') ? text : `/${text}`
}

function isAbsoluteUrl(value) {
  const text = String(value || '').trim()
  return text.startsWith('http://') || text.startsWith('https://')
}

function upsertMeta({ attr, key, content }) {
  const value = String(content || '').trim()
  if (!value) return

  const selector = `meta[${attr}="${key}"]`
  let tag = document.head.querySelector(selector)
  if (!tag) {
    tag = document.createElement('meta')
    tag.setAttribute(attr, key)
    document.head.appendChild(tag)
  }

  tag.setAttribute('content', value)
}

function upsertLink(rel, href) {
  const value = String(href || '').trim()
  if (!value) return

  let tag = document.head.querySelector(`link[rel="${rel}"]`)
  if (!tag) {
    tag = document.createElement('link')
    tag.setAttribute('rel', rel)
    document.head.appendChild(tag)
  }

  tag.setAttribute('href', value)
}

function clearManagedJsonLd() {
  document
    .querySelectorAll('script[type="application/ld+json"][data-seo-managed="true"]')
    .forEach((node) => node.remove())
}

function appendJsonLd(payload, key) {
  if (!payload || typeof payload !== 'object') return

  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.setAttribute('data-seo-managed', 'true')
  script.setAttribute('data-seo-key', key)
  script.textContent = JSON.stringify(payload)
  document.head.appendChild(script)
}

export function buildAbsoluteUrl(pathname = '/') {
  const base = String(SITE_CONFIG.site.url || '').trim().replace(/\/+$/, '')
  const normalizedPath = normalizePath(pathname)

  if (!base) {
    return normalizedPath
  }

  return normalizedPath === '/' ? `${base}/` : `${base}${normalizedPath}`
}

export function toAbsoluteAssetUrl(assetPath = '') {
  const source = safeText(assetPath, SITE_CONFIG.brand.ogImagePath)
  if (!source) return ''
  if (isAbsoluteUrl(source)) return source
  return buildAbsoluteUrl(source)
}

function buildOrganizationStructuredData() {
  const sameAs = []
  if (SITE_CONFIG.social.facebook) {
    sameAs.push(SITE_CONFIG.social.facebook)
  }

  const contactPoint = {
    '@type': 'ContactPoint',
    contactType: 'customer support',
    areaServed: 'Worldwide',
    availableLanguage: ['es', 'en'],
  }

  if (SITE_CONFIG.contact.email) {
    contactPoint.email = SITE_CONFIG.contact.email
  }

  if (SITE_CONFIG.contact.whatsappDigits) {
    contactPoint.telephone = `+${SITE_CONFIG.contact.whatsappDigits}`
  }

  const payload = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: SITE_CONFIG.brand.legalName || SITE_CONFIG.brand.name,
    url: SITE_CONFIG.site.url,
    logo: toAbsoluteAssetUrl(SITE_CONFIG.brand.logoPath),
    email: SITE_CONFIG.contact.email || undefined,
    sameAs: sameAs.length ? sameAs : undefined,
    contactPoint: contactPoint.email || contactPoint.telephone ? [contactPoint] : undefined,
  }

  return payload
}

function buildWebsiteStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_CONFIG.brand.name,
    url: SITE_CONFIG.site.url,
    inLanguage: SITE_CONFIG.site.language,
  }
}

export function createWebPageStructuredData({
  path = '/',
  title,
  description,
  pageType = 'WebPage',
}) {
  return {
    '@context': 'https://schema.org',
    '@type': pageType,
    name: safeText(title, SITE_CONFIG.seo.defaultTitle),
    description: safeText(description, SITE_CONFIG.seo.defaultDescription),
    url: buildAbsoluteUrl(path),
    inLanguage: SITE_CONFIG.site.language,
    isPartOf: {
      '@type': 'WebSite',
      name: SITE_CONFIG.brand.name,
      url: SITE_CONFIG.site.url,
    },
  }
}

export function createBreadcrumbStructuredData(items = []) {
  const list = items
    .map((item, index) => {
      const name = safeText(item?.name)
      const path = safeText(item?.path)
      if (!name || !path) return null

      return {
        '@type': 'ListItem',
        position: index + 1,
        name,
        item: buildAbsoluteUrl(path),
      }
    })
    .filter(Boolean)

  if (!list.length) return null

  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: list,
  }
}

export function buildDefaultStructuredData() {
  return [
    buildOrganizationStructuredData(),
    buildWebsiteStructuredData(),
  ]
}

export function applySeo({
  title,
  description,
  path,
  canonicalUrl,
  image,
  ogType = 'website',
  indexable = true,
  structuredData = [],
  pageType = 'WebPage',
}) {
  if (typeof document === 'undefined') return

  const finalTitle = safeText(title, SITE_CONFIG.seo.defaultTitle)
  const finalDescription = safeText(description, SITE_CONFIG.seo.defaultDescription)
  const finalPath = safeText(path, normalizePath(window.location.pathname || '/'))
  const finalCanonical = safeText(canonicalUrl, buildAbsoluteUrl(finalPath))
  const finalImage = safeText(image, SITE_CONFIG.seo.defaultImagePath)
  const finalImageUrl = toAbsoluteAssetUrl(finalImage)
  const robotsPolicy = indexable
    ? safeText(SITE_CONFIG.seo.robotsPolicy, 'index, follow')
    : NOINDEX_ROBOTS_POLICY

  document.title = finalTitle
  document.documentElement.setAttribute('lang', safeText(SITE_CONFIG.site.language, 'es'))

  upsertMeta({ attr: 'name', key: 'description', content: finalDescription })
  upsertMeta({ attr: 'name', key: 'robots', content: robotsPolicy })
  upsertMeta({ attr: 'name', key: 'googlebot', content: robotsPolicy })
  upsertMeta({ attr: 'name', key: 'author', content: SITE_CONFIG.brand.legalName || SITE_CONFIG.brand.name })
  upsertMeta({ attr: 'name', key: 'application-name', content: SITE_CONFIG.brand.name })
  upsertMeta({ attr: 'name', key: 'theme-color', content: SITE_CONFIG.seo.themeColor })

  upsertMeta({ attr: 'property', key: 'og:type', content: ogType || 'website' })
  upsertMeta({ attr: 'property', key: 'og:title', content: finalTitle })
  upsertMeta({ attr: 'property', key: 'og:description', content: finalDescription })
  upsertMeta({ attr: 'property', key: 'og:url', content: finalCanonical })
  upsertMeta({ attr: 'property', key: 'og:image', content: finalImageUrl })
  upsertMeta({ attr: 'property', key: 'og:site_name', content: SITE_CONFIG.brand.name })
  upsertMeta({ attr: 'property', key: 'og:locale', content: SITE_CONFIG.site.locale })

  upsertMeta({ attr: 'name', key: 'twitter:card', content: 'summary_large_image' })
  upsertMeta({ attr: 'name', key: 'twitter:title', content: finalTitle })
  upsertMeta({ attr: 'name', key: 'twitter:description', content: finalDescription })
  upsertMeta({ attr: 'name', key: 'twitter:image', content: finalImageUrl })

  if (SITE_CONFIG.seo.twitterSite) {
    upsertMeta({ attr: 'name', key: 'twitter:site', content: SITE_CONFIG.seo.twitterSite })
  }

  if (SITE_CONFIG.seo.twitterCreator) {
    upsertMeta({ attr: 'name', key: 'twitter:creator', content: SITE_CONFIG.seo.twitterCreator })
  }

  if (SITE_CONFIG.seo.googleSiteVerification) {
    upsertMeta({
      attr: 'name',
      key: 'google-site-verification',
      content: SITE_CONFIG.seo.googleSiteVerification,
    })
  }

  if (SITE_CONFIG.seo.bingSiteVerification) {
    upsertMeta({
      attr: 'name',
      key: 'msvalidate.01',
      content: SITE_CONFIG.seo.bingSiteVerification,
    })
  }

  upsertLink('canonical', finalCanonical)

  const dynamicSchemas = []

  const defaultSchemas = buildDefaultStructuredData()
  for (const schema of defaultSchemas) {
    dynamicSchemas.push(schema)
  }

  dynamicSchemas.push(
    createWebPageStructuredData({
      path: finalPath,
      title: finalTitle,
      description: finalDescription,
      pageType,
    }),
  )

  for (const item of structuredData) {
    if (item) {
      dynamicSchemas.push(item)
    }
  }

  clearManagedJsonLd()
  dynamicSchemas.forEach((schema, index) => {
    appendJsonLd(schema, `schema-${index + 1}`)
  })
}
