import { applySeo } from './seo'

export function usePageMeta({
  title,
  description,
  image,
  ogType,
  indexable,
  structuredData,
  pageType,
} = {}) {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/'
  const currentRobots =
    typeof document !== 'undefined'
      ? String(document.head.querySelector('meta[name="robots"]')?.getAttribute('content') || '').toLowerCase()
      : ''
  const resolvedIndexable =
    typeof indexable === 'boolean' ? indexable : !currentRobots.includes('noindex')

  applySeo({
    title,
    description,
    image,
    ogType,
    indexable: resolvedIndexable,
    structuredData,
    pageType,
    path,
  })
}
