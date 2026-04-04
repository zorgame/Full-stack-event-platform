<script setup>
import InternalPanelLayout from '../../components/layout/InternalPanelLayout.vue'
import { ROUTES } from '../../config/routes'

const links = [
  { label: 'Dashboard Admin', to: ROUTES.admin },
  { label: 'Configuración', to: ROUTES.adminConfig },
]
</script>

<template>
  <InternalPanelLayout title="Gestión de usuarios" subtitle="Vista base para administración de cuentas." :links="links">
    <div class="col-12">
      <article class="card border-0 shadow-sm">
        <div class="card-body">
          <h2 class="h5 fw-bold">Próximo módulo</h2>
          <p class="text-muted mb-0">
            Esta sección está lista para conectar listado, edición de roles y auditoría de usuarios.
          </p>
        </div>
      </article>
    </div>
  </InternalPanelLayout>
</template>
