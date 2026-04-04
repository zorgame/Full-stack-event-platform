import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')
const publicDir = path.join(projectRoot, 'public')

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}

  const content = fs.readFileSync(filePath, 'utf8')
  const variables = {}

  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue

    const separatorIndex = trimmed.indexOf('=')
    if (separatorIndex === -1) continue

    const rawKey = trimmed.slice(0, separatorIndex).trim()
    const rawValue = trimmed.slice(separatorIndex + 1).trim()
    if (!rawKey) continue

    const cleanedValue = rawValue
      .replace(/^"(.*)"$/, '$1')
      .replace(/^'(.*)'$/, '$1')

    variables[rawKey] = cleanedValue
  }

  return variables
}

function loadEnvVariables() {
  const merged = {}
  const files = ['.env', '.env.local', '.env.production', '.env.production.local']

  for (const fileName of files) {
    Object.assign(merged, parseEnvFile(path.join(projectRoot, fileName)))
  }

  return { ...merged, ...process.env }
}

function normalizeBaseUrl(value) {
  const normalized = String(value || '').trim().replace(/\/+$/, '')
  if (!normalized) return 'https://ticketsnova.com'

  try {
    const parsed = new URL(normalized)
    return parsed.toString().replace(/\/+$/, '')
  } catch {
    return 'https://ticketsnova.com'
  }
}

function buildRobotsTxt(siteUrl) {
  return [
    'User-agent: *',
    'Allow: /',
    '',
    '# Areas privadas',
    'Disallow: /admin',
    'Disallow: /user',
    'Disallow: /login',
    'Disallow: /payment',
    'Disallow: /acceso-denegado',
    '',
    `Sitemap: ${siteUrl}/sitemap.xml`,
    '',
  ].join('\n')
}

function buildSitemapXml(siteUrl) {
  const now = new Date().toISOString()
  const routes = [
    { path: '/', changefreq: 'daily', priority: '1.0' },
    { path: '/contact', changefreq: 'weekly', priority: '0.8' },
    { path: '/terms', changefreq: 'monthly', priority: '0.7' },
    { path: '/privacy', changefreq: 'monthly', priority: '0.7' },
    { path: '/refunds', changefreq: 'monthly', priority: '0.7' },
  ]

  const urls = routes
    .map((route) => {
      const absoluteUrl = route.path === '/' ? `${siteUrl}/` : `${siteUrl}${route.path}`
      return [
        '  <url>',
        `    <loc>${absoluteUrl}</loc>`,
        `    <lastmod>${now}</lastmod>`,
        `    <changefreq>${route.changefreq}</changefreq>`,
        `    <priority>${route.priority}</priority>`,
        '  </url>',
      ].join('\n')
    })
    .join('\n')

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    urls,
    '</urlset>',
    '',
  ].join('\n')
}

function main() {
  const env = loadEnvVariables()
  const siteUrl = normalizeBaseUrl(env.VITE_SITE_URL)

  fs.mkdirSync(publicDir, { recursive: true })

  const robotsPath = path.join(publicDir, 'robots.txt')
  const sitemapPath = path.join(publicDir, 'sitemap.xml')

  fs.writeFileSync(robotsPath, buildRobotsTxt(siteUrl), 'utf8')
  fs.writeFileSync(sitemapPath, buildSitemapXml(siteUrl), 'utf8')

  console.log(`SEO files generated for ${siteUrl}`)
}

main()
