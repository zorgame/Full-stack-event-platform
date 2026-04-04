<script setup>
import InternalPanelLayout from '../../components/layout/InternalPanelLayout.vue'
import { ROUTES } from '../../config/routes'
import { UI_TEXTS } from '../../config/constants'

const links = [
  { label: 'Panel admin', to: ROUTES.admin },
  { label: 'Configuración', to: ROUTES.adminConfig },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
]
</script>

<template>
  <InternalPanelLayout :title="UI_TEXTS.adminPanel.title" :subtitle="UI_TEXTS.adminPanel.subtitle" :links="links">
    <div class="col-12 col-md-6">
      <article class="card border-0 shadow-sm h-100">
        <div class="card-body">
          <h2 class="h5 fw-bold">Métricas de operación</h2>
          <p class="text-muted mb-0">
            Estructura lista para integrar KPIs de ventas, disponibilidad y estados de pedidos.
          </p>
        </div>
      </article>
    </div>
    <div class="col-12 col-md-6">
      <article class="card border-0 shadow-sm h-100">
        <div class="card-body">
          <h2 class="h5 fw-bold">Acciones rápidas</h2>
          <p class="text-muted mb-0">
            Desde aquí podrás conectar futuros módulos de gestión sin romper la arquitectura actual.
          </p>
        </div>
      </article>
    </div>
  </InternalPanelLayout>
</template>
