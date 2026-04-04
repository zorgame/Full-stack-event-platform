export const fadeIn = {
  name: 'anim-fade-in',
}

export const fadeUp = {
  name: 'anim-fade-up',
}

export const scaleIn = {
  name: 'anim-scale-in',
}

export function stagger(indice, pasoMs = 70) {
  return {
    '--indice-escalonado': String(indice ?? 0),
    '--paso-escalonado': `${pasoMs}ms`,
  }
}

export const hoverScale = {
  class: 'anim-hover-scale',
}

export const clickFeedback = {
  class: 'anim-click-feedback',
}

export const transicionRuta = {
  name: 'anim-ruta',
  mode: 'out-in',
}

export const transicionModal = {
  name: 'anim-modal',
}

