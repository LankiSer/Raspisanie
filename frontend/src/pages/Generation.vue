<template>
  <div class="page-container">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Генерация расписания</h1>
        <p class="text-gray-500 text-sm mt-0.5">Автоматическое создание расписания с учётом ограничений</p>
      </div>
      <div class="flex gap-3">
        <button 
          @click="generatePreview"
          :disabled="loading"
          class="btn-secondary flex items-center gap-2"
        >
          <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          <span v-if="loading && loadingPhase === 'preview'">Генерируем… {{ elapsedSec }}с</span>
          <span v-else>Предварительный просмотр</span>
        </button>
        <button 
          @click="runGeneration"
          :disabled="loading || !previewData"
          class="btn-primary flex items-center gap-2"
        >
          <svg class="w-5 h-5" :class="{ 'animate-spin': loading && loadingPhase === 'run' }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          <span v-if="loading && loadingPhase === 'run'">Сохраняем… {{ elapsedSec }}с</span>
          <span v-else>Запустить генерацию</span>
        </button>
      </div>
    </div>

    <!-- Generation Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Settings Panel -->
      <div class="lg:col-span-1">
        <div class="card card-body">
          <h2 class="mb-4">Настройки генерации</h2>
          
          <form @submit.prevent="generatePreview" class="space-y-4">
            <!-- Term Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Семестр <span class="text-gray-400 text-xs">(необязательно - будет создан автоматически)</span>
              </label>
              <select v-model="form.term_id" class="form-select">
                <option :value="null">Автоматически (создать новый)</option>
                <option v-for="term in terms" :key="term.term_id" :value="term.term_id">
                  {{ term.name }} ({{ term.start_date }} - {{ term.end_date }})
                </option>
              </select>
            </div>

            <!-- Date Range -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  С
                </label>
                <input
                  v-model="form.from_date"
                  type="date"
                  class="form-input"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  По
                </label>
                <input
                  v-model="form.to_date"
                  type="date"
                  class="form-input"
                  required
                />
              </div>
            </div>
            <button
              type="button"
              @click="setMonthRange"
              class="btn-outline w-full mt-2"
            >
              На весь месяц
            </button>

            <!-- Rules -->
            <div class="space-y-3">
              <h4 class="text-sm font-medium text-gray-700">Ограничения</h4>
              
              <div class="flex items-center">
                <input
                  v-model="form.ruleset.respect_availability"
                  type="checkbox"
                  class="form-checkbox"
                />
                <label class="ml-2 text-sm text-gray-700">
                  Учитывать доступность преподавателей
                </label>
              </div>

              <div class="flex items-center">
                <input
                  v-model="form.ruleset.enable_block_scheduling"
                  type="checkbox"
                  class="form-checkbox"
                />
                <label class="ml-2 text-sm text-gray-700">
                  Блочное расписание (пары подряд)
                </label>
              </div>

              <div v-if="form.ruleset.enable_block_scheduling">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Максимум блоков в день
                </label>
                <input
                  v-model.number="form.ruleset.max_blocks_per_day"
                  type="number"
                  min="1"
                  max="3"
                  class="form-input"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Максимум пар в день для группы
                </label>
                <input
                  v-model.number="form.ruleset.max_lessons_per_day_group"
                  type="number"
                  min="1"
                  max="10"
                  class="form-input"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Максимум пар в день для преподавателя
                </label>
                <input
                  v-model.number="form.ruleset.max_lessons_per_day_teacher"
                  type="number"
                  min="1"
                  max="12"
                  class="form-input"
                />
              </div>

              <div class="flex items-center">
                <input
                  v-model="form.ruleset.room_capacity_check"
                  type="checkbox"
                  class="form-checkbox"
                />
                <label class="ml-2 text-sm text-gray-700">
                  Проверять вместимость аудиторий
                </label>
              </div>
            </div>
          </form>
        </div>

        <!-- Statistics -->
        <div class="card card-body mt-4">
          <h2 class="mb-4">Статистика базы данных</h2>
          <div v-if="stats" class="space-y-2">
            <div class="flex justify-between">
              <span class="text-sm text-gray-600">Группы:</span>
              <span class="text-sm font-medium">{{ stats.available_groups }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-600">Преподаватели:</span>
              <span class="text-sm font-medium">{{ stats.available_teachers }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-600">Аудитории:</span>
              <span class="text-sm font-medium">{{ stats.available_rooms }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-600">Временные слоты:</span>
              <span class="text-sm font-medium">{{ stats.available_time_slots }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-600">Записи:</span>
              <span class="text-sm font-medium">{{ stats.total_enrollments }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Panel -->
      <div class="lg:col-span-2">
        <!-- Preview Results -->
        <div v-if="previewData" class="card mb-4">
          <div class="card-header">
            <h2>Предварительный просмотр</h2>
            <span class="badge-blue">{{ previewData.stats.total_lessons }} занятий</span>
          </div>
          <div class="card-body">

          <!-- Stats row -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5">
            <div class="bg-gov-50 border border-gov-200 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-gov-700">{{ previewData.stats.total_lessons }}</div>
              <div class="text-xs text-gov-600 mt-0.5">Занятий</div>
            </div>
            <div class="bg-indigo-50 border border-indigo-200 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-indigo-700">{{ previewData.stats.total_blocks || 0 }}</div>
              <div class="text-xs text-indigo-600 mt-0.5">Блоков</div>
            </div>
            <div class="bg-green-50 border border-green-200 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-green-700">{{ previewData.stats.groups_count }}</div>
              <div class="text-xs text-green-600 mt-0.5">Групп</div>
            </div>
            <div class="bg-purple-50 border border-purple-200 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-purple-700">{{ previewData.stats.teachers_count }}</div>
              <div class="text-xs text-purple-600 mt-0.5">Преподавателей</div>
            </div>
            <div class="bg-amber-50 border border-amber-200 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-amber-700">{{ previewData.stats.rooms_count }}</div>
              <div class="text-xs text-amber-600 mt-0.5">Аудиторий</div>
            </div>
          </div>

          <!-- Lessons Table -->
          <div class="table-wrapper">
            <table class="gov-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Время</th>
                  <th>Группа</th>
                  <th>Преподаватель</th>
                  <th>Предмет</th>
                  <th>Аудитория</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lesson in previewData.proposals.slice(0, 20)" :key="`${lesson.date}-${lesson.slot_id}-${lesson.enrollment_id}`">
                  <td>{{ formatDate(lesson.date) }}</td>
                  <td class="text-gray-500">{{ String(lesson.start_time).slice(0,5) }}–{{ String(lesson.end_time).slice(0,5) }}</td>
                  <td class="font-medium">{{ lesson.group_name }}</td>
                  <td>{{ lesson.teacher_name }}</td>
                  <td>{{ lesson.course_name }}</td>
                  <td class="badge-gray">{{ lesson.room_number }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="previewData.proposals.length > 20" class="mt-3 text-xs text-gray-400 text-center">
            Показано 20 из {{ previewData.proposals.length }} занятий
          </p>

          <!-- Blocks Table -->
          <div v-if="previewData.blocks && previewData.blocks.length > 0" class="mt-6">
            <h3 class="text-sm font-semibold text-gray-700 mb-2">Блоки уроков</h3>
            <div class="table-wrapper">
              <table class="gov-table">
                <thead>
                  <tr>
                    <th>Дата</th><th>Время</th><th>Группа</th>
                    <th>Преподаватель</th><th>Предмет</th><th>Аудитория</th><th>Блок</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="block in previewData.blocks.slice(0, 10)" :key="`${block.date}-${block.start_slot_id}-${block.group_id}`">
                    <td>{{ formatDate(block.date) }}</td>
                    <td class="text-gray-500">{{ String(block.start_time).slice(0,5) }}–{{ String(block.end_time).slice(0,5) }}</td>
                    <td class="font-medium">{{ block.group_name }}</td>
                    <td>{{ block.teacher_name }}</td>
                    <td>{{ block.course_name }}</td>
                    <td>{{ block.room_number }}</td>
                    <td><span class="badge-blue">{{ block.block_size }} п.</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-if="previewData.blocks.length > 10" class="mt-2 text-xs text-gray-400 text-center">
              Показано 10 из {{ previewData.blocks.length }} блоков
            </p>
          </div>
          </div><!-- /card-body -->
        </div><!-- /card preview -->

        <!-- Generation Results -->
        <div v-if="generationResult" class="card">
          <div class="card-header">
            <h2>Результат генерации</h2>
            <span class="badge-green">Успешно</span>
          </div>
          <div class="card-body">
            <div class="alert-success mb-4">{{ generationResult.message }}</div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div class="bg-gov-50 border border-gov-200 p-3 rounded-lg text-center">
                <div class="text-2xl font-bold text-gov-700">{{ generationResult.created_lessons }}</div>
                <div class="text-xs text-gov-600">Создано занятий</div>
              </div>
              <div class="bg-indigo-50 border border-indigo-200 p-3 rounded-lg text-center">
                <div class="text-2xl font-bold text-indigo-700">{{ generationResult.total_blocks || 0 }}</div>
                <div class="text-xs text-indigo-600">Блоков</div>
              </div>
              <div class="bg-green-50 border border-green-200 p-3 rounded-lg text-center">
                <div class="text-2xl font-bold text-green-700">{{ generationResult.total_proposals }}</div>
                <div class="text-xs text-green-600">Предложений</div>
              </div>
              <div class="bg-purple-50 border border-purple-200 p-3 rounded-lg text-center">
                <div class="text-2xl font-bold text-purple-700">
                  {{ generationResult.total_proposals ? Math.round((generationResult.created_lessons / generationResult.total_proposals) * 100) : 0 }}%
                </div>
                <div class="text-xs text-purple-600">Успешность</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading overlay -->
        <div v-if="loading" class="card p-12 text-center">
          <svg class="mx-auto h-12 w-12 text-gov-500 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <p class="font-semibold text-gray-700 text-lg">
            {{ loadingPhase === 'run' ? 'Сохраняем расписание…' : 'Генерируем расписание…' }}
          </p>
          <p class="text-gray-500 text-sm mt-1">Прошло: {{ elapsedSec }} сек. Подождите, OR-Tools подбирает оптимальный вариант.</p>
          <div class="mt-4 bg-gray-200 rounded-full h-2 max-w-xs mx-auto overflow-hidden">
            <div
              class="bg-gov-500 h-2 rounded-full transition-all duration-1000"
              :style="{ width: Math.min(elapsedSec / 270 * 100, 98) + '%' }"
            ></div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Максимум 270 секунд</p>
        </div>

        <!-- Empty State -->
        <div v-if="!loading && !previewData && !generationResult" class="card p-12 text-center text-gray-400">
          <svg class="mx-auto h-12 w-12 opacity-40 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <p class="font-medium text-gray-600">Нет данных для предпросмотра</p>
          <p class="text-sm mt-1">Настройте параметры и нажмите «Предварительный просмотр»</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { generationAPI, catalogAPI } from '@/services/api'

export default {
  name: 'Generation',
  setup() {
    const router = useRouter()

    // State
    const loading       = ref(false)
    const loadingPhase  = ref('')   // 'preview' | 'run'
    const elapsedSec    = ref(0)
    let _timerHandle    = null

    const startTimer = (phase) => {
      loading.value      = true
      loadingPhase.value = phase
      elapsedSec.value   = 0
      _timerHandle = setInterval(() => { elapsedSec.value++ }, 1000)
    }
    const stopTimer = () => {
      loading.value = false
      clearInterval(_timerHandle)
      _timerHandle = null
    }

    const previewData = ref(null)
    const generationResult = ref(null)
    const stats = ref(null)
    const terms = ref([])

    // Form
    const form = ref({
      term_id: null,  // Don't use default, require user to select
      from_date: new Date().toISOString().split('T')[0],
      to_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      ruleset: {
        respect_availability: true,
        max_lessons_per_day_group: 6,
        max_lessons_per_day_teacher: 8,
        room_capacity_check: true,
        enable_block_scheduling: true,
        max_blocks_per_day: 2,
        min_gap_between_blocks: 1
      }
    })

    // Methods
    const loadStats = async () => {
      try {
        const response = await generationAPI.getStats()
        stats.value = response.data
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    }

    const loadTerms = async () => {
      try {
        const response = await catalogAPI.getTerms()
        terms.value = response.data || []
        // Don't auto-select term - let user choose
        // This prevents issues with invalid term_id
      } catch (error) {
        console.error('Error loading terms:', error)
      }
    }

    const generatePreview = async () => {
      // Validate dates (term_id is now optional)
      if (!form.value.from_date || !form.value.to_date) {
        alert('Пожалуйста, укажите диапазон дат.')
        return
      }
      
      const fromDate = new Date(form.value.from_date)
      const toDate = new Date(form.value.to_date)
      if (toDate < fromDate) {
        alert('Дата окончания должна быть позже даты начала.')
        return
      }
      
      startTimer('preview')
      try {
        // 1. Start background job (returns immediately)
        const startRes = await generationAPI.preview(form.value)
        const jobId = startRes.data?.job_id
        if (!jobId) throw new Error('Сервер не вернул job_id')

        // 2. Poll until done (every 3 s, max 300 s)
        let waited = 0
        while (waited < 300) {
          await new Promise(r => setTimeout(r, 3000))
          waited += 3
          const statusRes = await generationAPI.previewStatus(jobId)
          const job = statusRes.data
          if (job.status === 'done') {
            previewData.value      = job.result
            generationResult.value = null
            return
          }
          if (job.status === 'error') {
            throw new Error(job.error || 'Неизвестная ошибка генерации')
          }
          // still 'running' → keep polling
        }
        throw new Error('Генерация заняла слишком долго. Сократите период или количество групп.')
      } catch (error) {
        const msg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Неизвестная ошибка'
        alert('Ошибка при генерации: ' + msg)
      } finally {
        stopTimer()
      }
    }

    const runGeneration = async () => {
      startTimer('run')
      try {
        // 1. Start background job (returns immediately)
        const startRes = await generationAPI.run(form.value)
        const jobId = startRes.data?.job_id
        if (!jobId) throw new Error('Сервер не вернул job_id')

        // 2. Poll until done (every 3 s, max 300 s)
        let waited = 0
        while (waited < 300) {
          await new Promise(r => setTimeout(r, 3000))
          waited += 3
          const statusRes = await generationAPI.runStatus(jobId)
          const job = statusRes.data
          if (job.status === 'done') {
            const res = job.result
            generationResult.value = res
            alert(`Генерация завершена! Создано ${res.created_lessons} занятий за ${elapsedSec.value} сек.`)
            setTimeout(() => { router.push('/dashboard') }, 2000)
            return
          }
          if (job.status === 'error') {
            throw new Error(job.error || 'Неизвестная ошибка генерации')
          }
          // still 'running' → keep polling
        }
        throw new Error('Сохранение заняло слишком долго. Попробуйте сократить период.')
      } catch (error) {
        const msg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Неизвестная ошибка'
        alert('Ошибка при запуске генерации: ' + msg)
      } finally {
        stopTimer()
      }
    }

    const formatDate = (dateString) => {
      // Parse ISO date string manually to avoid UTC→local timezone shift (off-by-1 day bug).
      // "2026-03-17" → [2026, 3, 17] → local midnight
      const [y, m, d] = String(dateString).split('-').map(Number)
      const date = new Date(y, m - 1, d)
      return date.toLocaleDateString('ru-RU', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    }

    const parseISOToLocalDate = (iso) => {
      if (!iso) return null
      const [y, m, d] = String(iso).split('-').map(Number)
      if (!y || !m || !d) return null
      return new Date(y, m - 1, d)
    }

    const toISODate = (d) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    }

    const setMonthRange = () => {
      const from = parseISOToLocalDate(form.value.from_date)
      if (!from) return
      const y = from.getFullYear()
      const m = from.getMonth()

      const start = new Date(y, m, 1)
      const end = new Date(y, m + 1, 0) // last day of month

      form.value.from_date = toISODate(start)
      form.value.to_date = toISODate(end)
    }

    // Lifecycle
    onMounted(() => {
      loadStats()
      loadTerms()
    })

    return {
      loading, loadingPhase, elapsedSec,
      previewData,
      generationResult,
      stats,
      terms,
      form,
      generatePreview,
      runGeneration,
      formatDate,
      setMonthRange,
    }
  }
}
</script>
