<script setup>
import PageHeading from '../../components/common/PageHeading.vue'
import { CONTACT_INFO } from '../../config/constants'
import { usePageMeta } from '../../utils/usePageMeta'

usePageMeta({
  title: 'Política de Privacidad | Tickets Nova',
  description:
    'Conoce cómo Tickets Nova recopila, usa y protege datos personales para compras, soporte y prevención de fraude.',
})

const lastUpdated = '4 de abril de 2026'

const legalSections = [
  {
    id: 'alcance-politica',
    title: 'Alcance de esta política',
    paragraphs: [
      'Esta Política describe el tratamiento de datos personales realizado por Tickets Nova en calidad de responsable y, cuando aplica, en coordinación con encargados tecnológicos y financieros.',
      'El alcance cubre web, canales de soporte, formularios operativos, herramientas de atención, pasarelas integradas y registros internos vinculados al ciclo de compra y postventa.',
    ],
  },
  {
    id: 'datos-recopilados',
    title: 'Categorías de datos recopilados',
    paragraphs: [
      'Podemos tratar datos de identificación, contacto, información transaccional, referencias de pago, eventos de autenticación y metadatos técnicos necesarios para operación y seguridad.',
      'La recopilación responde a criterios de necesidad, proporcionalidad y finalidad, evitando solicitudes excesivas cuando no exista una justificación funcional o regulatoria verificable.',
    ],
  },
  {
    id: 'fuentes-informacion',
    title: 'Fuentes de obtención de información',
    paragraphs: [
      'La información puede provenir directamente del titular durante registro o compra, de integraciones autorizadas por el usuario o de validaciones requeridas por procesos antifraude.',
      'En casos de soporte e investigación operativa, también podemos incorporar evidencia documental remitida por el titular para resolver incidencias o acreditar titularidad transaccional.',
    ],
  },
  {
    id: 'finalidades-tratamiento',
    title: 'Finalidades del tratamiento',
    paragraphs: [
      'Los datos se emplean para habilitar el servicio, gestionar pedidos, validar pagos, prevenir fraude, atender solicitudes, emitir comunicaciones operativas y dar continuidad al soporte.',
      'Adicionalmente, se utilizan para mejorar estabilidad, auditoría interna, cumplimiento normativo y análisis de desempeño de procesos, sin comercialización de datos a terceros no autorizados.',
    ],
  },
  {
    id: 'bases-legitimacion',
    title: 'Bases de legitimación jurídica',
    paragraphs: [
      'El tratamiento se sustenta en la ejecución de la relación contractual, el cumplimiento de obligaciones legales y el interés legítimo de seguridad, continuidad y prevención de abuso.',
      'Cuando una finalidad requiera consentimiento específico, Tickets Nova implementará mecanismos de aceptación explícita y trazabilidad para su posterior revocatoria o actualización.',
    ],
  },
  {
    id: 'decisiones-automatizadas',
    title: 'Decisiones automatizadas y evaluación de riesgo',
    paragraphs: [
      'Algunas operaciones pueden someterse a reglas automáticas de riesgo para detectar inconsistencias de pago, patrones anómalos o señales de comportamiento potencialmente fraudulento.',
      'Estas evaluaciones se utilizan como soporte de decisión operativa y pueden activar revisiones humanas adicionales antes de confirmar, observar o bloquear una transacción.',
    ],
  },
  {
    id: 'proveedores-encargados',
    title: 'Proveedores, encargados y acceso controlado',
    paragraphs: [
      'Tickets Nova trabaja con proveedores de infraestructura, mensajería, identidad y pago bajo esquemas contractuales que exigen confidencialidad, seguridad y limitación de propósito.',
      'El acceso de terceros se restringe por principio de mínima necesidad, controles de rol y monitoreo de actividad, evitando exposiciones innecesarias de información personal.',
    ],
  },
  {
    id: 'crossmint-tratamiento-pagos',
    title: 'Tratamiento de datos en pagos Crossmint',
    paragraphs: [
      'En operaciones cursadas por Crossmint, pueden procesarse datos de contacto, información transaccional, identificadores de wallet, señales de dispositivo/red y datos requeridos para controles antifraude y AML.',
      'Estas validaciones pueden incluir perfiles de riesgo y análisis automatizados con revisión humana cuando una decisión pueda impactar materialmente al usuario, conforme exigencias regulatorias aplicables.',
    ],
  },
  {
    id: 'transferencias-internacionales',
    title: 'Transferencias internacionales de datos',
    paragraphs: [
      'Cuando la operación técnica requiera procesamiento fuera de la jurisdicción local, Tickets Nova adopta salvaguardas contractuales y controles de seguridad equivalentes.',
      'Toda transferencia se limita a finalidades compatibles con esta Política y se revisa periódicamente para mantener estándares de protección adecuados.',
    ],
  },
  {
    id: 'seguridad-informacion',
    title: 'Seguridad de la información',
    paragraphs: [
      'Implementamos medidas técnicas y organizativas como cifrado en tránsito, segregación de entornos, autenticación reforzada, control de privilegios y auditoría de eventos críticos.',
      'Si bien ningún sistema es absolutamente inmune, aplicamos monitoreo continuo y planes de respuesta para reducir impacto, contener incidentes y preservar evidencia forense.',
    ],
  },
  {
    id: 'retencion-eliminacion',
    title: 'Retención, conservación y eliminación',
    paragraphs: [
      'Los datos se conservan durante el plazo requerido para cumplimiento contractual, conciliación financiera, defensa ante controversias y obligaciones regulatorias aplicables.',
      'Cumplidas dichas finalidades, se aplican procesos de anonimización, seudonimización o supresión segura, conforme políticas internas y estándares razonables de seguridad.',
    ],
  },
  {
    id: 'derechos-titular',
    title: 'Derechos del titular y gestión de solicitudes',
    paragraphs: [
      'El titular puede solicitar acceso, actualización, corrección, supresión y demás derechos reconocidos por la normativa aplicable, sujeto a verificaciones de identidad.',
      'Las solicitudes se atienden por canales oficiales y pueden requerir información adicional para evitar divulgación indebida a personas no autorizadas.',
    ],
  },
  {
    id: 'cookies-analitica',
    title: 'Cookies, analítica y preferencias técnicas',
    paragraphs: [
      'Podemos utilizar cookies y tecnologías equivalentes para funcionamiento esencial, diagnóstico de errores, seguridad de sesión y medición agregada de desempeño de la plataforma.',
      'El usuario puede ajustar sus preferencias desde herramientas del navegador, entendiendo que ciertas desactivaciones pueden afectar disponibilidad o calidad de algunas funciones.',
    ],
  },
  {
    id: 'actualizaciones-politica',
    title: 'Actualizaciones de esta política',
    paragraphs: [
      'Tickets Nova podrá actualizar esta Política por cambios normativos, evolución de servicios, nuevas integraciones o fortalecimiento de medidas de cumplimiento y seguridad.',
      'Las versiones vigentes se publicarán en esta ruta con su fecha de actualización para facilitar control documental y transparencia frente a usuarios y terceros interesados.',
    ],
  },
  {
    id: 'contacto-privacidad',
    title: 'Canal de privacidad y cumplimiento',
    paragraphs: [
      `Para requerimientos de protección de datos, ejercicio de derechos o consultas de cumplimiento, el canal institucional es ${CONTACT_INFO.email}.`,
      'Las comunicaciones formales deben incluir identificación básica del titular y contexto suficiente para permitir una gestión diligente, verificable y trazable.',
    ],
  },
]

const legalIndex = legalSections.map((section, index) => ({
  id: section.id,
  label: `${index + 1}. ${section.title}`,
}))
</script>

<template>
  <div>
    <PageHeading
      title="Política de privacidad"
      subtitle="Lineamientos de recopilación, uso, custodia y protección de datos personales en Tickets Nova."
    />
    <section class="container pb-5 legal-page">
      <div class="card border-0 shadow-sm legal-doc-shell">
        <aside class="legal-doc-index">
          <p class="legal-doc-index-label mb-1">Documento legal</p>
          <h2 class="legal-doc-index-title mb-2">Contenido</h2>
          <p class="legal-doc-index-date mb-3">Actualizado: {{ lastUpdated }}</p>
          <nav class="legal-doc-index-links" aria-label="Índice de privacidad">
            <a v-for="item in legalIndex" :key="item.id" :href="`#${item.id}`">{{ item.label }}</a>
          </nav>
        </aside>

        <article class="p-4 p-lg-5 info-content legal-doc-content">
          <p class="legal-doc-kicker mb-2">Documento corporativo</p>
          <p class="legal-doc-updated mb-4">Última actualización: {{ lastUpdated }}</p>

          <p class="legal-doc-intro">
            Esta Política ofrece una visión integral sobre la forma en que Tickets Nova administra información
            personal, incluyendo gobierno de datos, controles técnicos, roles de acceso, continuidad
            operativa y mecanismos de respuesta ante requerimientos de titulares.
          </p>
          <p class="legal-doc-intro mb-4">
            Al utilizar nuestros servicios, el usuario reconoce la necesidad de estos tratamientos para
            habilitar operaciones seguras, verificables y conformes al marco legal, así como para proteger
            la integridad de la plataforma frente a fraude y uso indebido.
          </p>

          <section v-for="(section, index) in legalSections" :key="section.id" class="legal-doc-section">
            <h2 :id="section.id">{{ index + 1 }}. {{ section.title }}</h2>
            <p v-for="(paragraph, paragraphIndex) in section.paragraphs" :key="`${section.id}-${paragraphIndex}`">
              {{ paragraph }}
            </p>
          </section>
        </article>
      </div>
    </section>
  </div>
</template>
