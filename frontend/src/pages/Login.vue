<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Schedule
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Система управления расписанием учебных заведений
        </p>
      </div>
      
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <!-- Tabs -->
        <div class="flex mb-6">
          <button
            @click="activeTab = 'login'"
            :class="{
              'border-blue-500 text-blue-600': activeTab === 'login',
              'border-transparent text-gray-500 hover:text-gray-700': activeTab !== 'login'
            }"
            class="w-1/2 py-2 px-1 text-center border-b-2 font-medium text-sm"
          >
            Вход
          </button>
          <button
            @click="activeTab = 'register'"
            :class="{
              'border-blue-500 text-blue-600': activeTab === 'register',
              'border-transparent text-gray-500 hover:text-gray-700': activeTab !== 'register'
            }"
            class="w-1/2 py-2 px-1 text-center border-b-2 font-medium text-sm"
          >
            Регистрация
          </button>
        </div>

        <!-- Login Form -->
        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-6">
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email
            </label>
            <div class="mt-1">
              <input
                id="email"
                v-model="loginForm.email"
                name="email"
                type="email"
                autocomplete="email"
                required
                class="form-input"
                placeholder="your@email.com"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Пароль
            </label>
            <div class="mt-1">
              <input
                id="password"
                v-model="loginForm.password"
                name="password"
                type="password"
                autocomplete="current-password"
                required
                class="form-input"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              :disabled="loading"
              class="btn-primary w-full"
            >
              <span v-if="loading">Входим...</span>
              <span v-else>Войти</span>
            </button>
          </div>
          
          <div class="mt-4">
            <button
              type="button"
              @click="handleDemoLogin"
              :disabled="loading"
              class="btn-secondary w-full"
            >
              <span v-if="loading">Входим...</span>
              <span v-else>Войти как демо</span>
            </button>
          </div>
        </form>

        <!-- Register Form -->
        <form v-else @submit.prevent="handleRegister" class="space-y-6">
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
          </div>

          <div>
            <label for="org-name" class="block text-sm font-medium text-gray-700">
              Название организации
            </label>
            <div class="mt-1">
              <input
                id="org-name"
                v-model="registerForm.organizationName"
                name="org-name"
                type="text"
                required
                class="form-input"
                placeholder="МГТУ им. Баумана"
              />
            </div>
          </div>

          <div>
            <label for="reg-email" class="block text-sm font-medium text-gray-700">
              Email администратора
            </label>
            <div class="mt-1">
              <input
                id="reg-email"
                v-model="registerForm.email"
                name="email"
                type="email"
                autocomplete="email"
                required
                class="form-input"
                placeholder="admin@university.edu"
              />
            </div>
          </div>

          <div>
            <label for="reg-password" class="block text-sm font-medium text-gray-700">
              Пароль
            </label>
            <div class="mt-1">
              <input
                id="reg-password"
                v-model="registerForm.password"
                name="password"
                type="password"
                autocomplete="new-password"
                required
                minlength="6"
                class="form-input"
                placeholder="••••••••"
              />
            </div>
            <p class="mt-1 text-sm text-gray-500">Минимум 6 символов</p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="locale" class="block text-sm font-medium text-gray-700">
                Язык
              </label>
              <div class="mt-1">
                <select id="locale" v-model="registerForm.locale" class="form-select">
                  <option value="ru">Русский</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>
            <div>
              <label for="timezone" class="block text-sm font-medium text-gray-700">
                Часовой пояс
              </label>
              <div class="mt-1">
                <select id="timezone" v-model="registerForm.tz" class="form-select">
                  <option value="Europe/Moscow">Москва (UTC+3)</option>
                  <option value="Asia/Almaty">Алматы (UTC+6)</option>
                  <option value="Europe/Minsk">Минск (UTC+3)</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              :disabled="loading"
              class="btn-primary w-full"
            >
              <span v-if="loading">Создаем организацию...</span>
              <span v-else>Создать организацию</span>
            </button>
          </div>
        </form>
      </div>

      <div class="text-center">
        <p class="text-xs text-gray-500">
          © 2025 Schedule. Система управления расписанием учебных заведений.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const activeTab = ref('login')
    const loading = ref(false)
    const error = ref('')
    
    const loginForm = ref({
      email: '',
      password: ''
    })
    
    const registerForm = ref({
      organizationName: '',
      email: '',
      password: '',
      locale: 'ru',
      tz: 'Europe/Moscow'
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
          registerForm.value.tz
        )
        router.push('/dashboard')
      } catch (err) {
        error.value = err.response?.data?.detail || err.message || 'Ошибка регистрации'
      } finally {
        loading.value = false
      }
    }

    const handleDemoLogin = async () => {
      loading.value = true
      error.value = ''

      try {
        await authStore.demoLogin()
        router.push('/dashboard')
      } catch (err) {
        error.value = err.message || 'Ошибка демо-входа'
      } finally {
        loading.value = false
      }
    }

    return {
      activeTab,
      loading,
      error,
      loginForm,
      registerForm,
      handleLogin,
      handleRegister,
      handleDemoLogin
    }
  }
}
</script>
