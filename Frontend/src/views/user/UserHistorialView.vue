<script setup>
import InternalPanelLayout from '../../components/layout/InternalPanelLayout.vue'
import { ROUTES } from '../../config/routes'

const links = [{ label: 'Mi panel', to: ROUTES.user }]
</script>

<template>
  <InternalPanelLayout title="Historial" subtitle="Seguimiento de actividad y compras." :links="links">
    <div class="col-12">
      <article class="card border-0 shadow-sm">
        <div class="card-body">
          <h2 class="h5 fw-bold">Historial de usuario</h2>
          <p class="text-muted mb-0">
            Vista lista para conectar pedidos, tickets asignados y detalles de transacciones.
          </p>
        </div>
      </article>
    </div>
  </InternalPanelLayout>
</template>
