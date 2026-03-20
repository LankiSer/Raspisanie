<template>
  <div class="min-h-screen flex flex-col bg-gray-50">

    <!-- Gov-style top stripe -->
    <div class="bg-gov-700 text-white py-4">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-3">
        <div class="w-10 h-10 rounded bg-white/20 flex items-center justify-center">
          <CalendarDaysIcon class="w-6 h-6" />
        </div>
        <div>
          <div class="font-bold text-base leading-tight">ВКСИТ</div>
          <div class="text-gov-200 text-xs leading-tight">Вологодский колледж связи и информационных технологий</div>
        </div>
      </div>
    </div>

    <!-- Card -->
    <div class="flex-1 flex items-start justify-center px-4 py-10">
      <div class="w-full max-w-md">

        <div class="text-center mb-6">
          <h1 class="text-2xl font-bold text-gray-900">Система расписания</h1>
          <p class="text-gray-500 text-sm mt-1">Управление расписанием занятий</p>
        </div>

        <div class="card">
          <!-- Tabs -->
          <div class="flex border-b border-gray-200">
            <button
              @click="activeTab = 'login'"
              :class="activeTab === 'login'
                ? 'border-gov-600 text-gov-700 font-semibold'
                : 'border-transparent text-gray-500 hover:text-gray-700'"
              class="flex-1 py-3 text-sm text-center border-b-2 transition-colors"
            >
              Вход
            </button>
            <button
              @click="activeTab = 'register'"
              :class="activeTab === 'register'
                ? 'border-gov-600 text-gov-700 font-semibold'
                : 'border-transparent text-gray-500 hover:text-gray-700'"
              class="flex-1 py-3 text-sm text-center border-b-2 transition-colors"
            >
              Регистрация
            </button>
          </div>

          <div class="p-6">
            <!-- Alert -->
            <div v-if="error" class="alert-error mb-4">{{ error }}</div>

            <!-- Login Form -->
            <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-4">
              <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  id="email"
                  v-model="loginForm.email"
                  type="email"
                  autocomplete="email"
                  required
                  class="form-input"
                  placeholder="admin@vksit.ru"
                />
              </div>

              <div>
                <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
                <input
                  id="password"
                  v-model="loginForm.password"
                  type="password"
                  autocomplete="current-password"
                  required
                  class="form-input"
                  placeholder="••••••••"
                />
              </div>

              <button type="submit" :disabled="loading" class="btn-primary w-full mt-2">
                <span v-if="loading">Входим…</span>
                <span v-else>Войти</span>
              </button>
            </form>

            <!-- Register Form -->
            <form v-else @submit.prevent="handleRegister" class="space-y-4">
              <div>
                <label for="org-name" class="block text-sm font-medium text-gray-700 mb-1">Название организации</label>
                <input
                  id="org-name"
                  v-model="registerForm.organizationName"
                  type="text"
                  required
                  class="form-input"
                  placeholder="ВКСИТ"
                />
              </div>

              <div>
                <label for="reg-email" class="block text-sm font-medium text-gray-700 mb-1">Email администратора</label>
                <input
                  id="reg-email"
                  v-model="registerForm.email"
                  type="email"
                  autocomplete="email"
                  required
                  class="form-input"
                  placeholder="admin@vksit.ru"
                />
              </div>

              <div>
                <label for="reg-password" class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
                <input
                  id="reg-password"
                  v-model="registerForm.password"
                  type="password"
                  autocomplete="new-password"
                  required
                  minlength="6"
                  class="form-input"
                  placeholder="Минимум 6 символов"
                />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label for="locale" class="block text-sm font-medium text-gray-700 mb-1">Язык</label>
                  <select id="locale" v-model="registerForm.locale" class="form-select">
                    <option value="ru">Русский</option>
                    <option value="en">English</option>
                  </select>
                </div>
                <div>
                  <label for="timezone" class="block text-sm font-medium text-gray-700 mb-1">Часовой пояс</label>
                  <select id="timezone" v-model="registerForm.tz" class="form-select">
                    <option value="Europe/Moscow">Москва (UTC+3)</option>
                    <option value="Asia/Almaty">Алматы (UTC+6)</option>
                    <option value="Europe/Minsk">Минск (UTC+3)</option>
                  </select>
                </div>
              </div>

              <button type="submit" :disabled="loading" class="btn-primary w-full mt-2">
                <span v-if="loading">Создаём организацию…</span>
                <span v-else>Создать организацию</span>
              </button>
            </form>
          </div>
        </div>

        <p class="text-center text-xs text-gray-400 mt-6">
          © {{ new Date().getFullYear() }} АПОУ ВО «Вологодский колледж связи и информационных технологий»
        </p>
      </div>
    </div>

    <!-- Footer stripe -->
    <div class="bg-gray-100 border-t border-gray-200 py-2">
      <div class="max-w-7xl mx-auto px-4 text-center text-xs text-gray-400">
        160011, г. Вологда, ул. Первомайская, 42 &nbsp;·&nbsp; 8 (817) 226-70-90 &nbsp;·&nbsp; contact@vksit.ru
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarDaysIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'Login',
  components: { CalendarDaysIcon },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const activeTab = ref('login')
    const loading = ref(false)
    const error = ref('')

    const loginForm = ref({ email: '', password: '' })
    const registerForm = ref({
      organizationName: '',
      email: '',
      password: '',
      locale: 'ru',
      tz: 'Europe/Moscow',
    })

    const handleLogin = async () => {
      loading.value = true
      error.value = ''
      try {
        await authStore.login(loginForm.value.email, loginForm.value.password)
        router.push('/dashboard')
      } catch (err) {
        error.value = err.response?.data?.detail || err.message || 'Ошибка входа'
      } finally {
        loading.value = false
      }
    }

    const handleRegister = async () => {
      loading.value = true
      error.value = ''
      try {
        await authStore.register(
          registerForm.value.organizationName,
          registerForm.value.email,
          registerForm.value.password,
          registerForm.value.locale,
          registerForm.value.tz,
        )
        router.push('/dashboard')
      } catch (err) {
        error.value = err.response?.data?.detail || err.message || 'Ошибка регистрации'
      } finally {
        loading.value = false
      }
    }

    return { activeTab, loading, error, loginForm, registerForm, handleLogin, handleRegister }
  },
}
</script>
