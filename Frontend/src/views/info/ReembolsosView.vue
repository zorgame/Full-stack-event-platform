<script setup>
import PageHeading from '../../components/common/PageHeading.vue'
import { CONTACT_INFO } from '../../config/constants'
import { usePageMeta } from '../../utils/usePageMeta'

usePageMeta({
  title: 'Política de Reembolsos | EventTix',
  description:
    'Consulta las condiciones, plazos y procedimiento para solicitudes de reembolso en EventTix.',
})

const lastUpdated = '4 de abril de 2026'

const legalSections = [
  {
    id: 'principios-generales',
    title: 'Principios generales de reembolso',
    paragraphs: [
      'La política de reembolsos de EventTix se rige por criterios de trazabilidad, evidencia verificable, validación financiera y cumplimiento de condiciones publicadas al momento de la compra.',
      'Cada caso se analiza individualmente, considerando naturaleza de la incidencia, estado del pedido, documentación disponible y reglas del evento o proveedor involucrado.',
    ],
  },
  {
    id: 'elegibilidad-reembolso',
    title: 'Condiciones de elegibilidad',
    paragraphs: [
      'Puede existir elegibilidad cuando se acredite cobro duplicado, error operativo atribuible a plataforma, imposibilidad de entrega por causa verificada o cancelación oficial del evento.',
      'La elegibilidad no es automática ni presunta; requiere evaluación técnica y documental con base en registros de sistema, respuesta de pasarela y evidencia aportada por el titular.',
    ],
  },
  {
    id: 'causales-no-elegibles',
    title: 'Causales no elegibles',
    paragraphs: [
      'No son elegibles solicitudes basadas en errores de compra imputables al usuario, cambios de preferencia, inasistencia voluntaria o presentación extemporánea sin justificación suficiente.',
      'Tampoco procede reembolso cuando la transacción fue correctamente aprobada y entregada conforme a condiciones vigentes, salvo mandato legal aplicable en sentido contrario.',
    ],
  },
  {
    id: 'documentacion-requerida',
    title: 'Documentación requerida',
    paragraphs: [
      'La solicitud debe incluir identificación del pedido, referencia de pago, correo asociado, relato cronológico del incidente y soportes que permitan verificar consistencia de los hechos.',
      'EventTix podrá requerir documentos complementarios para acreditar titularidad, evitar fraude, completar conciliación o resolver discrepancias entre sistemas internos y externos.',
    ],
  },
  {
    id: 'radicacion-trazabilidad',
    title: 'Radicación y trazabilidad de la solicitud',
    paragraphs: [
      'Toda solicitud se radica por canal oficial y recibe un identificador de seguimiento para registrar hitos, comunicaciones, requerimientos adicionales y estado de análisis.',
      'El solicitante debe conservar dicho identificador para consultas futuras y atender oportunamente solicitudes de información dentro de los plazos comunicados por soporte.',
    ],
  },
  {
    id: 'evaluacion-tecnica',
    title: 'Evaluación técnica y validación financiera',
    paragraphs: [
      'El análisis combina revisión de eventos de sistema, logs de operación, estados de pago, evidencia documental y reglas de cumplimiento asociadas a cada tipo de transacción.',
      'Cuando sea necesario, se coordina revisión con proveedor de pagos, operador externo o área de cumplimiento para confirmar causal y determinar monto susceptible de devolución.',
    ],
  },
  {
    id: 'crossmint-flujo-disputas',
    title: 'Pagos Crossmint, disputas y contracargos',
    paragraphs: [
      'Si el pago se procesó mediante Crossmint, la gestión de disputa puede involucrar verificaciones adicionales con el procesador, el adquirente y la red financiera correspondiente.',
      'La existencia de protección de contracargo del proveedor no reemplaza la revisión documental del caso por EventTix ni garantiza por sí sola la devolución automática al usuario.',
    ],
  },
  {
    id: 'crossmint-kyc-cumplimiento',
    title: 'KYC, cumplimiento y tiempos adicionales',
    paragraphs: [
      'En ciertos escenarios, el flujo de pago puede requerir KYC o validaciones de cumplimiento antes de la confirmación final. Estas verificaciones pueden extender los tiempos de resolución.',
      'Asimismo, operaciones detectadas como de alto riesgo o provenientes de jurisdicciones restringidas pueden ser observadas, pausadas o rechazadas conforme políticas de cumplimiento.',
    ],
  },
  {
    id: 'decision-comunicacion',
    title: 'Decisión y comunicación formal',
    paragraphs: [
      'La decisión final puede resultar en aprobación total, aprobación parcial o rechazo debidamente motivado, con explicación basada en evidencia y reglas aplicables al caso.',
      'La respuesta se emite por canales institucionales y contiene estado de la solicitud, fundamentos de decisión y próximos pasos cuando proceda actuación adicional del titular.',
    ],
  },
  {
    id: 'tiempos-estimados',
    title: 'Tiempos de gestión y plazos estimados',
    paragraphs: [
      'El tiempo de evaluación inicial suele ubicarse entre 5 y 15 días hábiles, pudiendo extenderse en escenarios con validaciones externas, alto volumen o evidencia incompleta.',
      'Los tiempos de abono final dependen del método de pago, entidad emisora y ciclos de compensación de la red financiera, factores que están fuera de control directo de la plataforma.',
    ],
  },
  {
    id: 'metodos-devolucion',
    title: 'Métodos de devolución y conciliación',
    paragraphs: [
      'La devolución se procesa preferiblemente hacia el medio de pago original, salvo limitaciones técnicas, regulatorias o instrucciones de proveedor que exijan canal alternativo válido.',
      'En todos los casos se conservan evidencias de conciliación y constancias de ejecución para auditoría, soporte posterior y cierre formal del expediente de reembolso.',
    ],
  },
  {
    id: 'contracargos-disputas',
    title: 'Contracargos, disputas y reservas de derechos',
    paragraphs: [
      'Si el usuario inicia contracargo ante su entidad financiera, EventTix podrá suspender revisión paralela hasta contar con definición del proceso en la red de pagos correspondiente.',
      'La plataforma se reserva el derecho de aportar evidencia documental y técnica en defensa de transacciones válidas, conforme normativa aplicable y reglas de marca.',
    ],
  },
  {
    id: 'contacto-reembolsos',
    title: 'Canal oficial de reembolsos',
    paragraphs: [
      `Para radicar solicitudes o ampliar información, el correo institucional de reembolsos es ${CONTACT_INFO.email}.`,
      'Toda comunicación debe enviarse desde una cuenta identificable y contener información suficiente para facilitar una respuesta completa y verificable.',
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
      title="Política de reembolsos"
      subtitle="Condiciones de elegibilidad, validación documental y tiempos de respuesta para solicitudes de devolución."
    />
    <section class="container pb-5 legal-page">
      <div class="card border-0 shadow-sm legal-doc-shell">
        <aside class="legal-doc-index">
          <p class="legal-doc-index-label mb-1">Documento legal</p>
          <h2 class="legal-doc-index-title mb-2">Contenido</h2>
          <p class="legal-doc-index-date mb-3">Actualizado: {{ lastUpdated }}</p>
          <nav class="legal-doc-index-links" aria-label="Índice de reembolsos">
            <a v-for="item in legalIndex" :key="item.id" :href="`#${item.id}`">{{ item.label }}</a>
          </nav>
        </aside>

        <article class="p-4 p-lg-5 info-content legal-doc-content">
          <p class="legal-doc-kicker mb-2">Documento corporativo</p>
          <p class="legal-doc-updated mb-4">Última actualización: {{ lastUpdated }}</p>

          <p class="legal-doc-intro">
            Esta política describe en profundidad las condiciones, etapas y criterios de evaluación aplicables
            a solicitudes de devolución económica relacionadas con operaciones realizadas en EventTix.
          </p>
          <p class="legal-doc-intro mb-4">
            Su objetivo es garantizar un proceso predecible, técnico y verificable para usuarios, áreas
            internas y proveedores externos que participan en la conciliación de pagos y resolución de
            incidencias comerciales.
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
