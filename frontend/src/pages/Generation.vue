<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Генерация расписания</h1>
        <p class="text-gray-600 mt-1">Автоматическое создание расписания с учетом ограничений</p>
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
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
          </svg>
          {{ loading ? 'Генерируем...' : 'Предварительный просмотр' }}
        </button>
        <button 
          @click="runGeneration"
          :disabled="loading || !previewData"
          class="btn-primary flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          Запустить генерацию
        </button>
      </div>
    </div>

    <!-- Generation Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Settings Panel -->
      <div class="lg:col-span-1">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Настройки генерации</h3>
          
          <form @submit.prevent="generatePreview" class="space-y-4">
            <!-- Term Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Семестр
              </label>
              <select v-model="form.term_id" class="form-select">
                <option v-for="term in terms" :key="term.term_id" :value="term.term_id">
                  {{ term.name }}
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
        <div class="bg-white shadow rounded-lg p-6 mt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Статистика</h3>
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
        <div v-if="previewData" class="bg-white shadow rounded-lg p-6 mb-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">Предварительный просмотр</h3>
            <span class="text-sm text-gray-500">
              {{ previewData.stats.total_lessons }} занятий
            </span>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div class="bg-blue-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-blue-600">{{ previewData.stats.total_lessons }}</div>
              <div class="text-sm text-blue-600">Всего занятий</div>
            </div>
            <div class="bg-indigo-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-indigo-600">{{ previewData.stats.total_blocks || 0 }}</div>
              <div class="text-sm text-indigo-600">Блоков</div>
            </div>
            <div class="bg-green-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-green-600">{{ previewData.stats.groups_count }}</div>
              <div class="text-sm text-green-600">Групп</div>
            </div>
            <div class="bg-purple-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-purple-600">{{ previewData.stats.teachers_count }}</div>
              <div class="text-sm text-purple-600">Преподавателей</div>
            </div>
            <div class="bg-orange-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-orange-600">{{ previewData.stats.rooms_count }}</div>
              <div class="text-sm text-orange-600">Аудиторий</div>
            </div>
          </div>

          <!-- Lessons Table -->
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Дата
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Время
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Группа
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Преподаватель
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Предмет
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Аудитория
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="lesson in previewData.proposals.slice(0, 20)" :key="`${lesson.date}-${lesson.slot_id}-${lesson.enrollment_id}`">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ formatDate(lesson.date) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ lesson.start_time }} - {{ lesson.end_time }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ lesson.group_name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ lesson.teacher_name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ lesson.course_name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ lesson.room_number }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="previewData.proposals.length > 20" class="mt-4 text-center">
            <span class="text-sm text-gray-500">
              Показано 20 из {{ previewData.proposals.length }} занятий
            </span>
          </div>

          <!-- Blocks Table -->
          <div v-if="previewData.blocks && previewData.blocks.length > 0" class="mt-8">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Блоки уроков</h4>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Дата
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Время
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Группа
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Преподаватель
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Предмет
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Аудитория
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Размер блока
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="block in previewData.blocks.slice(0, 10)" :key="`${block.date}-${block.start_slot_id}-${block.group_id}`" class="bg-indigo-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ formatDate(block.date) }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ block.start_time }} - {{ block.end_time }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ block.group_name }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ block.teacher_name }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ block.course_name }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {{ block.room_number }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                        {{ block.block_size }} пар
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="previewData.blocks.length > 10" class="mt-4 text-center">
              <span class="text-sm text-gray-500">
                Показано 10 из {{ previewData.blocks.length }} блоков
              </span>
            </div>
          </div>
        </div>

        <!-- Generation Results -->
        <div v-if="generationResult" class="bg-white shadow rounded-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">Результат генерации</h3>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              Успешно
            </span>
          </div>

          <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <div class="flex">
              <svg class="w-5 h-5 text-green-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <div class="ml-3">
                <p class="text-sm font-medium text-green-800">
                  {{ generationResult.message }}
                </p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-blue-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-blue-600">{{ generationResult.created_lessons }}</div>
              <div class="text-sm text-blue-600">Создано занятий</div>
            </div>
            <div class="bg-indigo-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-indigo-600">{{ generationResult.total_blocks || 0 }}</div>
              <div class="text-sm text-indigo-600">Создано блоков</div>
            </div>
            <div class="bg-green-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-green-600">{{ generationResult.total_proposals }}</div>
              <div class="text-sm text-green-600">Всего предложений</div>
            </div>
            <div class="bg-purple-50 p-3 rounded-lg">
              <div class="text-2xl font-bold text-purple-600">{{ Math.round((generationResult.created_lessons / generationResult.total_proposals) * 100) }}%</div>
              <div class="text-sm text-purple-600">Успешность</div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!previewData && !generationResult" class="bg-white shadow rounded-lg p-12 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">Нет данных</h3>
          <p class="mt-1 text-sm text-gray-500">
            Настройте параметры и нажмите "Предварительный просмотр" для генерации расписания
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { generationAPI, catalogAPI } from '@/services/api'

export default {
  name: 'Generation',
  setup() {
    // State
    const loading = ref(false)
    const previewData = ref(null)
    const generationResult = ref(null)
    const stats = ref(null)
    const terms = ref([])

    // Form
    const form = ref({
      term_id: 1,
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
        if (terms.value.length > 0) {
          form.value.term_id = terms.value[0].term_id
        }
      } catch (error) {
        console.error('Error loading terms:', error)
      }
    }

    const generatePreview = async () => {
      loading.value = true
      console.log('Starting preview generation with form:', form.value)
      try {
        const response = await generationAPI.preview(form.value)
        console.log('Preview response:', response)
        previewData.value = response.data
        generationResult.value = null
        console.log('Preview data set:', previewData.value)
      } catch (error) {
        console.error('Error generating preview:', error)
        alert('Ошибка при генерации предварительного просмотра: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const runGeneration = async () => {
      loading.value = true
      try {
        const response = await generationAPI.run(form.value)
        generationResult.value = response.data
        
        // Show success message
        alert(`Генерация завершена успешно! Создано ${response.data.created_lessons} занятий.`)
        
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 2000)
        
      } catch (error) {
        console.error('Error running generation:', error)
        alert('Ошибка при запуске генерации: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('ru-RU', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // Lifecycle
    onMounted(() => {
      loadStats()
      loadTerms()
    })

    return {
      loading,
      previewData,
      generationResult,
      stats,
      terms,
      form,
      generatePreview,
      runGeneration,
      formatDate
    }
  }
}
</script>
