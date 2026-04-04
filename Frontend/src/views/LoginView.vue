<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { UI_TEXTS } from '../config/constants'
import { ROUTES } from '../config/routes'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const errorMessage = ref('')

async function onSubmit() {
  errorMessage.value = ''
  try {
    const user = await authStore.login({
      email: email.value,
      password: password.value,
    })

    const redirectTarget = route.query.redirect
    if (typeof redirectTarget === 'string' && redirectTarget) {
      await router.push(redirectTarget)
      return
    }

    await router.push(user.is_admin ? ROUTES.admin : ROUTES.user)
  } catch (error) {
    errorMessage.value = error?.message || UI_TEXTS.login.invalid
  }
}
</script>

<template>
  <section class="login-wrapper py-5">
    <div class="container py-4">
      <div class="row justify-content-center">
        <div class="col-12 col-md-8 col-lg-5">
          <article class="card border-0 shadow-lg login-card">
            <div class="card-body p-4 p-lg-5">
              <h1 class="h3 fw-bold mb-2">{{ UI_TEXTS.login.title }}</h1>
              <p class="text-muted mb-4">{{ UI_TEXTS.login.subtitle }}</p>

              <form class="d-grid gap-3" @submit.prevent="onSubmit">
                <div>
                  <label for="email" class="form-label">{{ UI_TEXTS.login.emailLabel }}</label>
                  <input
                    id="email"
                    v-model="email"
                    type="email"
                    class="form-control"
                    required
                    autocomplete="email"
                  />
                </div>
                <div>
                  <label for="password" class="form-label">{{ UI_TEXTS.login.passwordLabel }}</label>
                  <input
                    id="password"
                    v-model="password"
                    type="password"
                    class="form-control"
                    required
                    autocomplete="current-password"
                  />
                </div>

                <div v-if="errorMessage" class="alert alert-danger py-2 mb-0" role="alert">
                  {{ errorMessage }}
                </div>

                <button class="btn btn-primary fw-semibold" type="submit" :disabled="authStore.isLoading">
                  {{ authStore.isLoading ? UI_TEXTS.login.loading : UI_TEXTS.login.submit }}
                </button>
              </form>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>
