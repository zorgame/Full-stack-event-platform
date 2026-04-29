<script setup>
import PageHeading from '../../components/common/PageHeading.vue'
import { CONTACT_INFO } from '../../config/constants'
import { usePageMeta } from '../../utils/usePageMeta'

usePageMeta({
  title: 'Términos y Condiciones | EventTix',
  description:
    'Revisa los términos y condiciones de EventTix para uso del servicio, pagos, responsabilidades y cumplimiento.',
})

const lastUpdated = '4 de abril de 2026'

const legalSections = [
  {
    id: 'objeto-alcance',
    title: 'Objeto y alcance contractual',
    paragraphs: [
      'Estos Términos regulan la relación jurídica entre EventTix y cualquier persona natural o jurídica que acceda, navegue, cotice, compre o gestione tickets a través de nuestros canales digitales.',
      'El alcance cubre funcionalidades de búsqueda, selección de categoría, checkout, confirmación de compra, atención posterior, gestión documental y soporte de incidencias en torno a cada transacción.',
    ],
  },
  {
    id: 'definiciones-operativas',
    title: 'Definiciones operativas relevantes',
    paragraphs: [
      'Para efectos interpretativos, se entiende por pedido el registro transaccional generado por el usuario durante el proceso de compra, sujeto a validación financiera y de seguridad.',
      'Se entiende por ticket la unidad de acceso digital o físico a un evento, y por disponibilidad reportada el inventario técnicamente sincronizado entre plataforma, proveedores y reglas activas de comercialización.',
    ],
  },
  {
    id: 'registro-verificacion',
    title: 'Registro de cuenta y verificación de identidad',
    paragraphs: [
      'El usuario se obliga a suministrar información veraz, completa y actualizada durante el alta de cuenta, compra, validación de titularidad o requerimientos de soporte operativo.',
      'EventTix podrá requerir pruebas adicionales de identidad o titularidad del pago cuando detecte inconsistencias, patrones atípicos de riesgo o alertas técnicas en los sistemas de control interno.',
    ],
  },
  {
    id: 'credenciales-seguridad',
    title: 'Credenciales, acceso y deberes de seguridad',
    paragraphs: [
      'La custodia de credenciales es responsabilidad del titular de la cuenta. El usuario debe mantener mecanismos de autenticación robustos y evitar compartir claves, enlaces de acceso o tokens de sesión.',
      'Cualquier actividad ejecutada desde una sesión autenticada se presume autorizada por el titular, sin perjuicio de los procedimientos de reporte y validación de incidentes establecidos por la plataforma.',
    ],
  },
  {
    id: 'transferencia-fifa-seguridad',
    title: 'Transferencia a FIFA y ventana de seguridad operativa',
    paragraphs: [
      'Para proteger al titular de la cuenta y reducir fraude, suplantación o transferencias no autorizadas, la opción de transferir tickets a FIFA se habilita únicamente durante los 15 días previos al evento asociado.',
      'Fuera de esa ventana, la funcionalidad permanece restringida por controles preventivos de seguridad, validación de identidad y trazabilidad, conforme a las políticas internas y condiciones vigentes de EventTix.',
    ],
  },
  {
    id: 'compra-pedido',
    title: 'Proceso de compra y perfeccionamiento del pedido',
    paragraphs: [
      'Un pedido se considera perfeccionado solo cuando los controles antifraude y la pasarela de pagos emiten resultado aprobado y el sistema registra confirmación definitiva de la operación.',
      'Estados pendientes, observados, rechazados o revertidos impiden la consolidación del pedido. En esos escenarios, la plataforma podrá suspender la entrega hasta que exista validación suficiente.',
    ],
  },
  {
    id: 'precios-cargos-impuestos',
    title: 'Precios, cargos de servicio e impuestos aplicables',
    paragraphs: [
      'Los precios publicados pueden incluir o desglosar cargos operativos, comisiones de procesamiento y conceptos tributarios según jurisdicción, tipo de evento y estructura comercial vigente.',
      'El usuario acepta revisar el detalle económico antes de confirmar su compra, incluyendo valores finales, moneda de liquidación, costos de servicio y políticas de reajuste cuando aplique.',
    ],
  },
  {
    id: 'entrega-asignacion',
    title: 'Disponibilidad, asignación y entrega de tickets',
    paragraphs: [
      'La disponibilidad es dinámica y puede cambiar por demanda, reservas concurrentes, contingencias de proveedor o reglas de capacidad del organizador del evento.',
      'La asignación de tickets se realiza bajo criterios de disponibilidad efectiva, equivalencia de categoría y cumplimiento de pago, pudiendo incluir procesos de validación documental antes de la liberación final.',
    ],
  },
  {
    id: 'cambios-evento',
    title: 'Cancelaciones, aplazamientos y cambios de evento',
    paragraphs: [
      'Las decisiones sobre cancelación, reprogramación, cambios de sede, horarios o condiciones de acceso corresponden al organizador del evento y/o a los operadores autorizados.',
      'EventTix gestionará comunicación y lineamientos aplicables conforme la información oficial disponible, sin asumir control directo sobre decisiones externas a la infraestructura de la plataforma.',
    ],
  },
  {
    id: 'uso-permitido-restricciones',
    title: 'Uso permitido y restricciones tecnológicas',
    paragraphs: [
      'Se prohíbe expresamente el uso de bots, scraping, automatización abusiva, ingeniería inversa, suplantación de identidad o manipulación de inventarios para alterar condiciones de compra.',
      'El incumplimiento habilita medidas preventivas y correctivas, incluyendo suspensión de cuenta, bloqueo de transacciones, invalidación de operaciones y remisión a autoridades competentes cuando corresponda.',
    ],
  },
  {
    id: 'propiedad-intelectual',
    title: 'Propiedad intelectual y activos de plataforma',
    paragraphs: [
      'Los signos distintivos, diseños, software, flujos de compra, contenidos y componentes tecnológicos de EventTix están protegidos por normas de propiedad intelectual y uso autorizado.',
      'Ningún usuario adquiere derechos de explotación, sublicenciamiento o reproducción comercial sobre dichos activos por el mero uso de la plataforma o la ejecución de una compra.',
    ],
  },
  {
    id: 'terceros-integraciones',
    title: 'Integraciones de terceros y alcance de responsabilidad',
    paragraphs: [
      'La operación puede involucrar servicios externos de pagos, mensajería, analítica, validación de identidad y conectores de inventario, cada uno sujeto a sus propios términos de servicio.',
      'EventTix responde por su capa de gestión y trazabilidad interna, pero no garantiza disponibilidad absoluta ni tiempos homogéneos de terceros sobre los que no tiene control directo.',
    ],
  },
  {
    id: 'crossmint-pagos-compliance',
    title: 'Procesamiento de pagos con Crossmint y cumplimiento',
    paragraphs: [
      'Cuando el usuario inicia una transacción, EventTix puede utilizar la infraestructura de pagos de Crossmint para orquestar cobros, validaciones, prevención de fraude y controles de cumplimiento financiero.',
      'Al aceptar estos Términos y continuar con el checkout, el usuario autoriza el intercambio de datos estrictamente necesarios con Crossmint y proveedores vinculados al flujo de pago, incluyendo validaciones de identidad y riesgo cuando corresponda.',
    ],
  },
  {
    id: 'crossmint-kyc-geo-restricciones',
    title: 'KYC, geografía y actividades restringidas',
    paragraphs: [
      'Dependiendo del método de pago, monto, jurisdicción o señales de riesgo, Crossmint podrá requerir KYC adicional, revisión manual o comprobaciones reforzadas antes de permitir la finalización de la operación.',
      'No se permite utilizar la plataforma para actividades prohibidas, uso desde geografías sancionadas o finalidades contrarias a normativa AML/CTF. EventTix podrá bloquear operaciones y cuentas cuando exista riesgo de incumplimiento.',
    ],
  },
  {
    id: 'fraude-monitoreo',
    title: 'Prevención de fraude, monitoreo y control interno',
    paragraphs: [
      'La plataforma ejecuta monitoreo continuo de señales de riesgo transaccional, patrones de comportamiento, consistencia documental y resultados de autenticación en distintos puntos del flujo.',
      'Con base en dichos controles, EventTix podrá solicitar verificaciones adicionales, aplicar retenciones preventivas o cancelar operaciones cuando existan indicios razonables de riesgo elevado.',
    ],
  },
  {
    id: 'crossmint-contracargos-disputas',
    title: 'Contracargos, disputas y trazabilidad del pago',
    paragraphs: [
      'Las disputas de pago y contracargos se gestionan conforme a las reglas de la red financiera y de los proveedores que participan en la operación, incluyendo los flujos habilitados por Crossmint.',
      'La apertura de un contracargo no implica reconocimiento automático de reembolso por parte de EventTix. Cada caso se resuelve con evidencia transaccional, reglas del emisor y políticas de reembolso vigentes.',
    ],
  },
  {
    id: 'responsabilidad-indemnidad',
    title: 'Limitación de responsabilidad e indemnidad',
    paragraphs: [
      'La responsabilidad de EventTix se limita a la prestación diligente de su infraestructura digital, registros de evidencia y gestión operativa dentro del marco técnico y normativo aplicable.',
      'El usuario será responsable por la autenticidad de la información aportada y por cualquier perjuicio derivado de actuaciones contrarias a estos Términos o a la legislación vigente.',
    ],
  },
  {
    id: 'suspension-terminacion',
    title: 'Suspensión, terminación y medidas correctivas',
    paragraphs: [
      'EventTix podrá suspender temporal o definitivamente accesos y funcionalidades cuando se detecten incumplimientos contractuales, uso indebido de la plataforma o riesgos de seguridad.',
      'La adopción de medidas correctivas no limita el ejercicio de acciones legales adicionales ni la implementación de controles complementarios para proteger usuarios, proveedores y operación.',
    ],
  },
  {
    id: 'ley-aplicable-contacto',
    title: 'Ley aplicable, controversias y canal legal',
    paragraphs: [
      'Estos Términos se interpretan conforme al marco jurídico aplicable al domicilio operacional informado por EventTix, sin perjuicio de normas imperativas de protección al consumidor.',
      `Para consultas de cumplimiento, requerimientos jurídicos o notificaciones formales, el canal oficial es ${CONTACT_INFO.email}.`,
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
      title="Términos y condiciones"
      subtitle="Marco contractual para el uso de plataforma, pagos, seguridad operativa y responsabilidades de las partes."
    />
    <section class="container pb-5 legal-page">
      <div class="card border-0 shadow-sm legal-doc-shell">
        <aside class="legal-doc-index">
          <p class="legal-doc-index-label mb-1">Documento legal</p>
          <h2 class="legal-doc-index-title mb-2">Contenido</h2>
          <p class="legal-doc-index-date mb-3">Actualizado: {{ lastUpdated }}</p>
          <nav class="legal-doc-index-links" aria-label="Índice de términos">
            <a v-for="item in legalIndex" :key="item.id" :href="`#${item.id}`">{{ item.label }}</a>
          </nav>
        </aside>

        <article class="p-4 p-lg-5 info-content legal-doc-content">
          <p class="legal-doc-kicker mb-2">Documento corporativo</p>
          <p class="legal-doc-updated mb-4">Última actualización: {{ lastUpdated }}</p>

          <p class="legal-doc-intro">
            El presente documento establece condiciones extensivas de uso y define criterios de gobernanza
            operacional para compras de tickets, verificación de transacciones, control de seguridad,
            trazabilidad documental y atención de contingencias asociadas al ciclo comercial.
          </p>
          <p class="legal-doc-intro mb-4">
            La lectura íntegra es obligatoria antes de operar en la plataforma. Al utilizar EventTix,
            el usuario reconoce haber comprendido el alcance de estas cláusulas y acepta su aplicación en
            todas las interacciones contractuales, técnicas y de soporte.
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
