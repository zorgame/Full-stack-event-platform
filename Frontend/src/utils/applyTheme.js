import { THEME } from '../config/theme'

export function applyTheme() {
  const root = document.documentElement
  const palette = THEME.brand

  root.style.setProperty('--color-primary', palette.primary)
  root.style.setProperty('--color-secondary', palette.secondary)
  root.style.setProperty('--color-accent', palette.accent)
  root.style.setProperty('--color-gold', palette.gold)
  root.style.setProperty('--color-dark', palette.dark)
  root.style.setProperty('--color-light', palette.light)
  root.style.setProperty('--color-surface', palette.surface)
  root.style.setProperty('--color-text', palette.text)
  root.style.setProperty('--color-muted', palette.muted)
  root.style.setProperty('--hero-gradient', THEME.gradients.hero)
  root.style.setProperty('--card-gradient', THEME.gradients.card)
  root.style.setProperty('--footer-gradient', THEME.gradients.footer)
  root.style.setProperty('--font-heading', THEME.fontFamily.heading)
  root.style.setProperty('--font-body', THEME.fontFamily.body)
}
