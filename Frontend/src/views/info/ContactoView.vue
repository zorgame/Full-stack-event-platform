<script setup>
import PageHeading from '../../components/common/PageHeading.vue'
import { BRANDING, CONTACT_INFO } from '../../config/constants'
import { usePageMeta } from '../../utils/usePageMeta'

usePageMeta({
  title: 'Contacto Corporativo | Tickets Nova',
  description:
    'Canales oficiales de Tickets Nova para soporte comercial, cumplimiento y continuidad operativa de compras.',
})

const mailToHref = `mailto:${CONTACT_INFO.email}`
const whatsappHref = `https://wa.me/${CONTACT_INFO.whatsappDigits}`

const supportTracks = [
  {
    title: 'Atencion de compras',
    summary: 'Estado de orden, validaciones y entregables de acceso.',
    sla: 'Respuesta inicial: 30-90 min',
  },
  {
    title: 'Soporte tecnico',
    summary: 'Problemas de cuenta, acceso, links y trazabilidad.',
    sla: 'Respuesta inicial: 15-60 min',
  },
  {
    title: 'Cumplimiento y auditoria',
    summary: 'Requerimientos formales, evidencia y conciliaciones.',
    sla: 'Respuesta inicial: mismo dia habil',
  },
]

const escalationFlow = [
  'Creacion y clasificacion del caso por prioridad y riesgo.',
  'Asignacion a equipo especializado segun canal y tipo de incidencia.',
  'Seguimiento con evidencia trazable hasta el cierre formal.',
]
</script>

<template>
  <div class="contact-page-root">
    <PageHeading
      title="Contacto"
      subtitle="Canales oficiales para soporte comercial, validaciones de compra y seguimiento postventa."
    />

    <section class="container pb-5 contact-page-shell">
      <div class="contact-hero card border-0 shadow-sm">
        <div class="card-body p-4 p-lg-5">
          <div class="row g-4 align-items-center">
            <div class="col-12 col-lg-8">
              <p class="contact-kicker mb-2">Centro de soporte Tickets Nova</p>
              <h2 class="h3 fw-bold mb-3">Mesa de atencion especializada y trazable</h2>
              <p class="text-muted mb-0">
                Centralizamos incidencias de compra, validacion de pagos, soporte de cuenta y procesos de cumplimiento
                con trazabilidad completa y tiempos de respuesta definidos por prioridad.
              </p>
            </div>

            <div class="col-12 col-lg-4">
              <div class="contact-brand-box">
                <img :src="BRANDING.logoPath" :alt="BRANDING.name" class="contact-brand-logo" />
                <p class="mb-1 fw-semibold">{{ BRANDING.name }}</p>
                <p class="mb-0 text-muted small">Atencion oficial para operaciones y postventa.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4 mt-1">
        <div class="col-12 col-lg-8 d-grid gap-4">
          <article class="card border-0 shadow-sm">
            <div class="card-body p-4">
              <h3 class="h5 fw-bold mb-3">Canales oficiales</h3>
              <p class="text-muted mb-3">
                Utiliza estos accesos para mantener un canal verificable de atencion y seguimiento.
              </p>

              <div class="contact-channel-grid">
                <a v-if="CONTACT_INFO.facebook" class="contact-channel-btn" :href="CONTACT_INFO.facebook" target="_blank" rel="noopener noreferrer">
                  <span class="channel-badge">Social</span>
                  <strong>Facebook</strong>
                  <small>Mensajeria y comunicados oficiales.</small>
                </a>

                <a class="contact-channel-btn" :href="whatsappHref" target="_blank" rel="noopener noreferrer">
                  <span class="channel-badge">Rapido</span>
                  <strong>WhatsApp {{ CONTACT_INFO.whatsappDisplay }}</strong>
                  <small>Atencion operativa y seguimiento de casos.</small>
                </a>

                <a class="contact-channel-btn" :href="mailToHref">
                  <span class="channel-badge">Formal</span>
                  <strong>{{ CONTACT_INFO.email }}</strong>
                  <small>Canal recomendado para auditorias y solicitudes formales.</small>
                </a>
              </div>

              <div class="contact-hours mt-4">
                <p class="mb-1"><strong>Horario operativo:</strong> Lunes a viernes, 9:00 a.m. - 6:00 p.m. (ET)</p>
                <p class="mb-0 text-muted small">En requerimientos de cumplimiento, conserva numero de pedido, fecha e identificacion del titular.</p>
              </div>
            </div>
          </article>

          <article class="card border-0 shadow-sm">
            <div class="card-body p-4">
              <h3 class="h5 fw-bold mb-3">Protocolos de escalamiento</h3>
              <ol class="escalation-list mb-0">
                <li v-for="step in escalationFlow" :key="step">{{ step }}</li>
              </ol>
            </div>
          </article>
        </div>

        <div class="col-12 col-lg-4">
          <article class="card border-0 shadow-sm h-100">
            <div class="card-body p-4">
              <h3 class="h5 fw-bold mb-3">Tiempos de respuesta</h3>
              <div class="support-track-grid">
                <article v-for="track in supportTracks" :key="track.title" class="support-track-card">
                  <h4 class="h6 fw-bold mb-1">{{ track.title }}</h4>
                  <p class="text-muted small mb-2">{{ track.summary }}</p>
                  <p class="mb-0 support-track-sla">{{ track.sla }}</p>
                </article>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.contact-page-root {
  background:
    radial-gradient(circle at 0% 0%, rgba(8, 145, 178, 0.08), transparent 36%),
    radial-gradient(circle at 100% 8%, rgba(245, 158, 11, 0.1), transparent 32%),
    linear-gradient(180deg, #f7fafc 0%, #ffffff 50%);
}

.contact-page-shell {
  display: grid;
  gap: 1rem;
}

.contact-hero {
  border: 1px solid #d7e2ee;
  border-radius: 1.25rem;
  background:
    linear-gradient(140deg, rgba(7, 89, 133, 0.08), rgba(255, 255, 255, 0.9) 45%),
    #ffffff;
}

.contact-kicker {
  color: #0b4f64;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.contact-brand-box {
  border: 1px solid #c6d7e7;
  border-radius: 0.9rem;
  background: #f8fbff;
  padding: 0.9rem;
  text-align: center;
}

.contact-brand-logo {
  width: 54px;
  height: 54px;
  object-fit: contain;
  border-radius: 50%;
  margin-bottom: 0.55rem;
}

.contact-channel-grid {
  display: grid;
  gap: 0.65rem;
}

.contact-channel-btn {
  display: grid;
  gap: 0.18rem;
  justify-items: center;
  text-align: center;
  text-decoration: none;
  border: 1px solid #c9d8e8;
  border-radius: 0.9rem;
  background: #ffffff;
  color: #11253b;
  padding: 0.8rem 0.9rem;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.contact-channel-btn:hover {
  transform: translateY(-2px);
  border-color: #0f4c5c;
  box-shadow: 0 16px 25px -22px rgba(15, 76, 92, 0.9);
}

.channel-badge {
  width: fit-content;
  margin-inline: auto;
  padding: 0.16rem 0.5rem;
  border-radius: 999px;
  background: #e7f3ff;
  color: #0b4f64;
  font-size: 0.68rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-weight: 700;
}

.contact-hours {
  border-top: 1px solid #e4edf5;
  padding-top: 0.9rem;
}

.support-track-grid {
  display: grid;
  gap: 0.6rem;
}

.support-track-card {
  border: 1px solid #d2dfec;
  border-radius: 0.85rem;
  background: #fbfdff;
  padding: 0.7rem 0.75rem;
}

.support-track-sla {
  color: #0f4c5c;
  font-size: 0.78rem;
  font-weight: 700;
}

.escalation-list {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.55rem;
  color: #334155;
}

@media (max-width: 991.98px) {
  .contact-brand-box {
    text-align: left;
    display: flex;
    align-items: center;
    gap: 0.85rem;
  }

  .contact-brand-logo {
    margin-bottom: 0;
  }
}
</style>
