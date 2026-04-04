<script setup>
import { RouterLink } from 'vue-router'
import { CONTACT_INFO, FOOTER_LINKS, UI_TEXTS } from '../../config/constants'

const mailToHref = `mailto:${CONTACT_INFO.email}`
const whatsappHref = `https://wa.me/${CONTACT_INFO.whatsappDigits}`

const professionalLegalTitles = [
  'Política de Privacidad y Tratamiento de Datos',
  'Términos de Servicio y Condiciones Generales',
  'Política de Reembolsos, Devoluciones y Contracargos',
]

const professionalLegalLinks = FOOTER_LINKS.slice(1).map((item, index) => ({
  ...item,
  label: professionalLegalTitles[index] || item.label,
}))
</script>

<template>
  <footer class="app-footer mt-3 mt-lg-5">
    <div class="container py-4 py-lg-5">
      <div class="row g-4">
        <div class="col-12 col-md-5">
          <p class="footer-kicker mb-2">Plataforma oficial de ticketing</p>
          <h5 class="text-white mb-3">{{ UI_TEXTS.appName }}</h5>
          <p class="footer-muted mb-3 footer-brand-copy">
            Infraestructura digital para operaciones de venta con disponibilidad validada,
            pagos verificados y trazabilidad completa de punta a punta.
          </p>

          <div class="footer-pill-row mb-3" role="list" aria-label="Pilares operativos">
            <span class="footer-pill" role="listitem">Disponibilidad en tiempo real</span>
            <span class="footer-pill" role="listitem">Pagos auditables</span>
            <span class="footer-pill" role="listitem">Soporte especializado</span>
          </div>

          <ul class="footer-prof-list mb-0">
            <li>Monitoreo continuo de inventario, checkout y confirmaciones transaccionales.</li>
            <li>Control documental por pedido para auditoría, cumplimiento y postventa.</li>
            <li>Atención operativa para incidencias críticas con foco en continuidad comercial.</li>
          </ul>
        </div>
        <div class="col-6 col-md-3">
          <h6 class="text-uppercase text-white-50">Gobernanza normativa</h6>
          <p class="footer-muted small mb-2">Instrumentos contractuales y políticas vigentes de la plataforma.</p>
          <ul class="list-unstyled mb-0 d-grid gap-2">
            <li v-for="item in professionalLegalLinks" :key="item.to">
              <RouterLink class="footer-link" :to="item.to">{{ item.label }}</RouterLink>
            </li>
          </ul>
        </div>
        <div class="col-6 col-md-4">
          <h6 class="text-uppercase text-white-50">Canales oficiales</h6>
          <p class="footer-muted small mb-2">Atención directa por canal para soporte y comunicaciones formales.</p>
          <div class="footer-contact-actions mt-2">
            <a class="footer-contact-btn footer-contact-btn-fb" :href="CONTACT_INFO.facebook" target="_blank" rel="noopener noreferrer" aria-label="Facebook oficial">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M14.4 8.2H16.5V5.5H14.1C11.7 5.5 10.4 6.9 10.4 9.3V11.1H8.3V13.8H10.4V18.5H13.1V13.8H15.4L15.8 11.1H13.1V9.6C13.1 8.8 13.4 8.2 14.4 8.2Z" fill="currentColor"/>
              </svg>
              Facebook
            </a>
            <a class="footer-contact-btn footer-contact-btn-wa" :href="whatsappHref" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M12 4.6C7.9 4.6 4.6 7.8 4.6 11.8C4.6 13.2 5 14.5 5.8 15.6L5 19.4L8.9 18.7C10 19.4 11.2 19.8 12.4 19.8C16.5 19.8 19.8 16.5 19.8 12.5C19.8 8.5 16.1 4.6 12 4.6Z" stroke="currentColor" stroke-width="1.6"/>
                <path d="M9.1 9.6C9.3 9.1 9.5 9 9.8 9H10.3C10.4 9 10.6 9.1 10.7 9.3L11.4 10.9C11.5 11.1 11.5 11.3 11.3 11.5L10.8 12.1C10.7 12.3 10.8 12.5 10.9 12.6C11.3 13.2 11.9 13.7 12.5 14.1C12.6 14.2 12.8 14.2 13 14.1L13.6 13.6C13.8 13.5 14 13.5 14.2 13.6L15.7 14.3C15.9 14.4 16 14.6 16 14.8V15.3C16 15.6 15.9 15.8 15.5 16C15 16.2 14.5 16.2 14.1 16.1C13.2 15.8 12.4 15.2 11.6 14.4C10.8 13.7 10.3 12.9 10 12C9.9 11.6 9.9 11.1 10.1 10.6" fill="currentColor"/>
              </svg>
              WhatsApp
            </a>
            <a class="footer-contact-btn footer-contact-btn-mail" :href="mailToHref" aria-label="Correo oficial">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <rect x="3" y="5.5" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.6"/>
                <path d="M4.2 7.3L12 13L19.8 7.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              Correo oficial
            </a>
          </div>
        </div>
      </div>
      <hr class="border-light-subtle my-4" />
      <p class="footer-muted mb-0 text-center">{{ UI_TEXTS.footer.copyright }}</p>
    </div>
  </footer>
</template>
