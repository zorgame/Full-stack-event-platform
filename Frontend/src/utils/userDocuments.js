import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable/es'
import JsBarcode from 'jsbarcode'
import QRCode from 'qrcode'

const DATE_FORMATTER = new Intl.DateTimeFormat('es-DO', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const moneyFormatterCache = new Map()

function asNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function safeText(value, fallback = 'No disponible') {
  const normalized = String(value ?? '').trim()
  return normalized || fallback
}

function formatDate(value) {
  if (!value) return 'No disponible'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No disponible'
  return DATE_FORMATTER.format(date)
}

function getCurrencyFormatter(currency = 'USD') {
  const key = String(currency || 'USD').trim().toUpperCase() || 'USD'
  if (!moneyFormatterCache.has(key)) {
    moneyFormatterCache.set(
      key,
      new Intl.NumberFormat('es-DO', {
        style: 'currency',
        currency: key,
        maximumFractionDigits: 2,
      }),
    )
  }
  return moneyFormatterCache.get(key)
}

function formatMoney(value, currency = 'USD') {
  return getCurrencyFormatter(currency).format(asNumber(value))
}

function createBarcodeDataUrl(value) {
  const canvas = document.createElement('canvas')
  JsBarcode(canvas, String(value || 'ETX-0000'), {
    format: 'CODE128',
    width: 1.4,
    height: 40,
    displayValue: true,
    margin: 0,
    fontSize: 12,
    textMargin: 2,
  })
  return canvas.toDataURL('image/png')
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('No se pudo convertir la imagen a data URL'))
    reader.readAsDataURL(blob)
  })
}

async function blobToPngDataUrl(blob) {
  if (typeof document === 'undefined') {
    return blobToDataUrl(blob)
  }

  const objectUrl = URL.createObjectURL(blob)

  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('No se pudo decodificar la imagen cargada'))
      img.src = objectUrl
    })

    const canvas = document.createElement('canvas')
    const width = Number(image.naturalWidth || image.width || 1)
    const height = Number(image.naturalHeight || image.height || 1)
    canvas.width = width > 0 ? width : 1
    canvas.height = height > 0 ? height : 1

    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('No se pudo crear un contexto de imagen para el PDF')
    }

    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL('image/png')
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

function getDataUrlFormat(value) {
  const source = String(value || '').trim()
  const match = source.match(/^data:image\/([a-zA-Z0-9.+-]+);base64,/i)
  const subtype = String(match?.[1] || '').toLowerCase()

  if (subtype === 'jpeg' || subtype === 'jpg') return 'JPEG'
  if (subtype === 'webp') return 'WEBP'
  if (subtype === 'gif') return 'GIF'
  return 'PNG'
}

function addImageSafe(doc, dataUrl, x, y, width, height) {
  const source = String(dataUrl || '').trim()
  if (!source) return
  doc.addImage(source, getDataUrlFormat(source), x, y, width, height)
}

async function loadImageDataUrl(path) {
  const source = String(path || '').trim()
  if (!source) return ''

  const response = await fetch(source)
  if (!response.ok) {
    throw new Error(`No se pudo cargar logo: ${source}`)
  }

  const blob = await response.blob()
  return blobToPngDataUrl(blob)
}

async function createQrDataUrl(payload) {
  return QRCode.toDataURL(JSON.stringify(payload), {
    margin: 1,
    width: 280,
    errorCorrectionLevel: 'M',
    color: {
      dark: '#0B2F4F',
      light: '#FFFFFF',
    },
  })
}

function drawHeader(doc, { brandName, title, subtitle, documentCode, logos = {} }) {
  doc.setFillColor(10, 59, 84)
  doc.rect(0, 0, 210, 30, 'F')

  doc.setFillColor(248, 180, 0)
  doc.rect(0, 30, 210, 1.8, 'F')

  doc.setTextColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(14)
  doc.text(brandName, 14, 12)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9.5)
  doc.text('Centro de tickets y facturacion', 14, 18)

  if (logos.eventLogoDataUrl) {
    addImageSafe(doc, logos.eventLogoDataUrl, 153, 5.8, 16, 16)
  }
  if (logos.brandLogoDataUrl) {
    addImageSafe(doc, logos.brandLogoDataUrl, 173, 5.6, 22, 18)
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.setTextColor(17, 24, 39)
  doc.text(title, 14, 39)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(53, 79, 82)
  doc.setFontSize(10)
  doc.text(subtitle, 14, 45)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(17, 24, 39)
  doc.setFontSize(9)
  doc.text(`Codigo de control: ${documentCode}`, 14, 51)
}

function drawFooters(doc, footerText) {
  const totalPages = doc.getNumberOfPages()
  for (let page = 1; page <= totalPages; page += 1) {
    doc.setPage(page)
    doc.setDrawColor(220, 226, 232)
    doc.line(14, 286, 196, 286)

    doc.setFont('helvetica', 'normal')
    doc.setTextColor(86, 102, 115)
    doc.setFontSize(8.5)
    doc.text(footerText, 14, 291)
    doc.text(`Pagina ${page} de ${totalPages}`, 196, 291, { align: 'right' })
  }
}

function buildTicketRows(tickets) {
  return tickets.map((item, index) => [
    String(index + 1),
    safeText(item.eventoNombre || item.evento || 'Evento'),
    safeText(item.categoriaNombre || item.categoria || 'Categoria'),
    String(asNumber(item.cantidad)),
    formatMoney(item.precio, item.moneda || 'USD'),
    String(item.moneda || 'USD').toUpperCase(),
    safeText(item.codigo || item.key || item.id),
  ])
}

function buildOrderRows(pedidos) {
  return pedidos.map((pedido, index) => [
    String(index + 1),
    safeText(pedido.referencia),
    formatDate(pedido.fecha_creacion || pedido.fechaCreacion),
    safeText(pedido.estado || 'pendiente').toUpperCase(),
    formatMoney(pedido.total, 'USD'),
  ])
}

function buildBillingDetailRows(pedidos) {
  const rows = []
  for (const pedido of pedidos) {
    for (const detalle of pedido.detalles || []) {
      rows.push([
        safeText(pedido.referencia),
        safeText(detalle?.categoria?.nombre || 'Categoria'),
        String(asNumber(detalle.cantidad)),
        formatMoney(detalle.precio_unitario, detalle?.categoria?.moneda || 'USD'),
        formatMoney(detalle.subtotal, detalle?.categoria?.moneda || 'USD'),
      ])
    }
  }
  return rows
}

function normalizeFileToken(value, fallback = 'documento') {
  const token = String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9-_]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase()
  return token || fallback
}

export async function downloadTicketReportPdf({
  brandName = 'EventTix',
  brandLogoPath = '/assets/eventtix-logo.png',
  eventLogoPath = '',
  user,
  ticket,
  tickets = [],
  pedidos = [],
}) {
  const issueDate = new Date()
  const ticketCodeSource = safeText(ticket?.codigo || ticket?.id || ticket?.categoriaId || 'ticket')
  const documentCode = `TKN-${ticketCodeSource}-${issueDate.getTime()}`

  const qrPayload = {
    document_type: 'ticket_report',
    generated_at: issueDate.toISOString(),
    user: {
      id: user?.id ?? null,
      email: safeText(user?.email),
      full_name: safeText(`${user?.nombre || ''} ${user?.apellido || ''}`.trim(), user?.email),
    },
    ticket: {
      id: ticket?.id ?? null,
      category: safeText(ticket?.categoriaNombre || ticket?.categoria),
      event: safeText(ticket?.eventoNombre || ticket?.evento),
      quantity: asNumber(ticket?.cantidad),
      code: ticketCodeSource,
    },
  }

  const [qrDataUrl, barcodeDataUrl, brandLogoDataUrl, eventLogoDataUrl] = await Promise.all([
    createQrDataUrl(qrPayload),
    Promise.resolve(createBarcodeDataUrl(documentCode)),
    loadImageDataUrl(brandLogoPath).catch(() => ''),
    loadImageDataUrl(eventLogoPath).catch(() => ''),
  ])

  const logos = {
    brandLogoDataUrl,
    eventLogoDataUrl,
  }

  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  drawHeader(doc, {
    brandName,
    title: 'Resumen de tickets',
    subtitle: 'Detalle de titularidad, verificacion y trazabilidad de acceso.',
    documentCode,
    logos,
  })

  const customerRows = [
    ['Titular', safeText(`${user?.nombre || ''} ${user?.apellido || ''}`.trim(), user?.email)],
    ['Correo', safeText(user?.email)],
    ['Telefono', safeText(user?.telefono)],
    ['Pais', safeText(user?.pais)],
    ['Ticket seleccionado', safeText(ticket?.categoriaNombre || ticket?.categoria)],
    ['Evento', safeText(ticket?.eventoNombre || ticket?.evento)],
    ['Cantidad', String(asNumber(ticket?.cantidad))],
    ['Generado', formatDate(issueDate.toISOString())],
  ]

  autoTable(doc, {
    startY: 56,
    head: [['Campo', 'Detalle']],
    body: customerRows,
    styles: { fontSize: 9, textColor: [27, 38, 44], cellPadding: 2.5 },
    headStyles: { fillColor: [15, 76, 117], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 248, 252] },
    columnStyles: { 0: { cellWidth: 44, fontStyle: 'bold' }, 1: { cellWidth: 132 } },
    margin: { left: 14, right: 14 },
  })

  const summaryY = (doc.lastAutoTable?.finalY || 120) + 8
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(17, 24, 39)
  doc.text('Validacion visual y codigos de acceso', 14, summaryY)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(59, 71, 82)
  doc.setFontSize(9.5)
  doc.text(
    'Este documento integra codigo QR y codigo de barras para reforzar control interno, soporte al cliente y trazabilidad digital.',
    14,
    summaryY + 5,
    { maxWidth: 182 },
  )

  addImageSafe(doc, qrDataUrl, 14, summaryY + 10, 36, 36)
  addImageSafe(doc, barcodeDataUrl, 58, summaryY + 14, 136, 22)

  doc.setDrawColor(226, 232, 240)
  doc.roundedRect(14, summaryY + 50, 182, 18, 2, 2, 'S')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9.5)
  doc.text('Nota de seguridad', 18, summaryY + 56)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.text(
    'Transferencias oficiales a FIFA: habilitadas unicamente dentro de la ventana de 15 dias previos al evento por proteccion antifraude.',
    18,
    summaryY + 61,
    { maxWidth: 172 },
  )

  doc.addPage()
  drawHeader(doc, {
    brandName,
    title: 'Inventario del titular',
    subtitle: 'Relacion de tickets activos y sus categorias.',
    documentCode,
    logos,
  })

  autoTable(doc, {
    startY: 56,
    head: [['#', 'Evento', 'Categoria', 'Cant.', 'Precio', 'Moneda', 'Codigo']],
    body: buildTicketRows(tickets.length ? tickets : [ticket]),
    styles: { fontSize: 8.2, textColor: [24, 35, 44], cellPadding: 2.2, overflow: 'linebreak' },
    headStyles: { fillColor: [17, 138, 178], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [247, 250, 252] },
    margin: { left: 14, right: 14 },
    tableWidth: 'auto',
  })

  const orderRows = buildOrderRows(pedidos)
  const orderTitleY = (doc.lastAutoTable?.finalY || 120) + 9
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10.5)
  doc.setTextColor(17, 24, 39)
  doc.text('Pedidos asociados', 14, orderTitleY)

  autoTable(doc, {
    startY: orderTitleY + 3,
    head: [['#', 'Referencia', 'Fecha', 'Estado', 'Total']],
    body: orderRows.length ? orderRows : [['-', 'Sin pedidos relacionados', '-', '-', '-']],
    styles: { fontSize: 8.5, textColor: [28, 37, 43], cellPadding: 2.1, overflow: 'linebreak' },
    headStyles: { fillColor: [66, 92, 112], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [249, 251, 253] },
    margin: { left: 14, right: 14 },
    tableWidth: 'auto',
  })

  drawFooters(
    doc,
    `${brandName} - Documento del titular. Sujeto a terminos y condiciones vigentes.`,
  )

  const fileToken = normalizeFileToken(ticketCodeSource, 'ticket')
  doc.save(`eventtix-${fileToken}.pdf`)
}

export async function downloadBillingReportPdf({
  brandName = 'EventTix',
  brandLogoPath = '/assets/eventtix-logo.png',
  eventLogoPath = '',
  user,
  pedidos = [],
}) {
  const issueDate = new Date()
  const documentCode = `BILL-${safeText(user?.id, 'cliente')}-${issueDate.getTime()}`
  const userFullName = safeText(`${user?.nombre || ''} ${user?.apellido || ''}`.trim(), user?.email)

  const paidOrders = pedidos.filter((pedido) => String(pedido?.estado || '').toLowerCase() === 'pagado')
  const totalPaid = paidOrders.reduce((acc, order) => acc + asNumber(order.total), 0)
  const pendingOrders = pedidos.filter((pedido) => String(pedido?.estado || '').toLowerCase() === 'pendiente')
  const totalPending = pendingOrders.reduce((acc, order) => acc + asNumber(order.total), 0)

  const qrPayload = {
    document_type: 'billing_report',
    generated_at: issueDate.toISOString(),
    account: {
      id: user?.id ?? null,
      email: safeText(user?.email),
      holder: userFullName,
    },
    totals: {
      paid_orders: paidOrders.length,
      paid_amount: totalPaid,
      pending_orders: pendingOrders.length,
      pending_amount: totalPending,
    },
  }

  const [qrDataUrl, barcodeDataUrl, brandLogoDataUrl, eventLogoDataUrl] = await Promise.all([
    createQrDataUrl(qrPayload),
    Promise.resolve(createBarcodeDataUrl(documentCode)),
    loadImageDataUrl(brandLogoPath).catch(() => ''),
    loadImageDataUrl(eventLogoPath).catch(() => ''),
  ])

  const logos = {
    brandLogoDataUrl,
    eventLogoDataUrl,
  }

  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  drawHeader(doc, {
    brandName,
    title: 'Resumen de facturacion',
    subtitle: 'Consolidado de datos fiscales, pedidos y detalle transaccional.',
    documentCode,
    logos,
  })

  autoTable(doc, {
    startY: 56,
    head: [['Campo', 'Detalle']],
    body: [
      ['Titular de cuenta', userFullName],
      ['Correo de facturacion', safeText(user?.email)],
      ['Telefono', safeText(user?.telefono)],
      ['Pais', safeText(user?.pais)],
      ['Pedidos pagados', String(paidOrders.length)],
      ['Monto pagado', formatMoney(totalPaid, 'USD')],
      ['Pedidos pendientes', String(pendingOrders.length)],
      ['Monto pendiente', formatMoney(totalPending, 'USD')],
      ['Fecha de emision', formatDate(issueDate.toISOString())],
    ],
    styles: { fontSize: 9, textColor: [27, 38, 44], cellPadding: 2.5 },
    headStyles: { fillColor: [15, 76, 117], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 248, 252] },
    columnStyles: { 0: { cellWidth: 48, fontStyle: 'bold' }, 1: { cellWidth: 128 } },
    margin: { left: 14, right: 14 },
  })

  const billingSummaryY = (doc.lastAutoTable?.finalY || 120) + 8
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(17, 24, 39)
  doc.text('Sellos de control', 14, billingSummaryY)

  addImageSafe(doc, qrDataUrl, 14, billingSummaryY + 4, 34, 34)
  addImageSafe(doc, barcodeDataUrl, 56, billingSummaryY + 8, 138, 22)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(59, 71, 82)
  doc.text(
    'Este reporte puede ser utilizado para conciliacion interna, soporte al cliente y verificacion de transacciones.',
    14,
    billingSummaryY + 43,
    { maxWidth: 182 },
  )

  doc.addPage()
  drawHeader(doc, {
    brandName,
    title: 'Detalle de pedidos y conceptos',
    subtitle: 'Desglose de facturacion por operacion y categoria.',
    documentCode,
    logos,
  })

  autoTable(doc, {
    startY: 56,
    head: [['#', 'Referencia', 'Fecha', 'Estado', 'Total']],
    body: buildOrderRows(pedidos).length
      ? buildOrderRows(pedidos)
      : [['-', 'Sin pedidos registrados', '-', '-', '-']],
    styles: { fontSize: 8.4, textColor: [28, 37, 43], cellPadding: 2.1, overflow: 'linebreak' },
    headStyles: { fillColor: [66, 92, 112], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [249, 251, 253] },
    margin: { left: 14, right: 14 },
    tableWidth: 'auto',
  })

  autoTable(doc, {
    startY: (doc.lastAutoTable?.finalY || 120) + 8,
    head: [['Pedido', 'Concepto', 'Cant.', 'Precio Unitario', 'Subtotal']],
    body: buildBillingDetailRows(pedidos).length
      ? buildBillingDetailRows(pedidos)
      : [['-', 'No hay conceptos para mostrar', '-', '-', '-']],
    styles: { fontSize: 8.2, textColor: [30, 41, 59], cellPadding: 2, overflow: 'linebreak' },
    headStyles: { fillColor: [6, 95, 70], textColor: [255, 255, 255], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [247, 251, 249] },
    margin: { left: 14, right: 14 },
    tableWidth: 'auto',
  })

  drawFooters(
    doc,
    `${brandName} - Facturacion generada automaticamente para control y soporte.`,
  )

  const fileToken = normalizeFileToken(userFullName, 'facturacion')
  doc.save(`facturacion-${fileToken}.pdf`)
}