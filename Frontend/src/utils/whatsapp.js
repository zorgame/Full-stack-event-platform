import { CHECKOUT_WHATSAPP_BASE_URL } from '../config/checkout'

export function construirEnlaceWhatsapp(numeroTelefono, mensaje) {
  const telefono = String(numeroTelefono || '').replace(/\D/g, '')
  if (!telefono) return ''

  const baseUrl = String(CHECKOUT_WHATSAPP_BASE_URL || '').replace(/\/+$/, '')
  if (!baseUrl) return ''

  const texto = String(mensaje || '').trim()

  if (!texto) {
    return `${baseUrl}/${telefono}`
  }

  return `${baseUrl}/${telefono}?text=${encodeURIComponent(texto)}`
}
