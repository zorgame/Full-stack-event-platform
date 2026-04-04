<script setup>
import InternalPanelLayout from '../../components/layout/InternalPanelLayout.vue'
import { ROUTES } from '../../config/routes'

const links = [
  { label: 'Dashboard Admin', to: ROUTES.admin },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
]
</script>

<template>
  <InternalPanelLayout title="Configuración administrativa" subtitle="Parámetros generales y reglas del sistema." :links="links">
    <div class="col-12">
      <article class="card border-0 shadow-sm">
        <div class="card-body">
          <h2 class="h5 fw-bold">Módulo preparado para escalar</h2>
          <p class="text-muted mb-0">
            Agrega aquí configuraciones de negocio, feature flags y reglas de operación por entorno.
          </p>
        </div>
      </article>
    </div>
  </InternalPanelLayout>
</template>
