<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Временные слоты</h1>
        <p class="text-gray-600 mt-1">Управление временными интервалами занятий</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить слот
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск по названию..."
              class="form-input pl-10"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Time Slots Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredSlots.length === 0" class="p-8 text-center">
        <ClockIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Слоты не найдены' : 'Нет временных слотов' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первый временной слот' }}
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Название
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Время начала
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Время окончания
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Перемена (мин)
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Дни недели
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Действия
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="slot in paginatedSlots" :key="slot.slot_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ slot.label }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatTime(slot.start_time) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatTime(slot.end_time) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ slot.break_minutes }} мин
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {{ getWeekdaysLabel(slot.weekday_mask) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(slot)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteSlot(slot)"
                    class="text-red-600 hover:text-red-900"
                    title="Удалить"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Предыдущая
          </button>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Следующая
          </button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Показано <span class="font-medium">{{ (currentPage - 1) * itemsPerPage + 1 }}</span>
              - <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredSlots.length) }}</span>
              из <span class="font-medium">{{ filteredSlots.length }}</span> слотов
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                :class="page === currentPage ? 'bg-indigo-50 border-indigo-500 text-indigo-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'"
                class="relative inline-flex items-center px-4 py-2 border text-sm font-medium"
              >
                {{ page }}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              {{ editingSlot ? 'Редактировать слот' : 'Добавить слот' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <form @submit.prevent="saveSlot" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Название *
              </label>
              <input
                v-model="form.label"
                type="text"
                required
                class="form-input"
                placeholder="Например: 1 пара, 2 пара"
              />
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Время начала *
                </label>
                <input
                  v-model="form.startTime"
                  type="time"
                  required
                  class="form-input"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Время окончания *
                </label>
                <input
                  v-model="form.endTime"
                  type="time"
                  required
                  class="form-input"
                />
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Перемена (минуты) *
              </label>
              <input
                v-model.number="form.breakMinutes"
                type="number"
                min="0"
                max="60"
                required
                class="form-input"
                placeholder="10"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Дни недели *
              </label>
              <div class="grid grid-cols-7 gap-2 mt-2">
                <label v-for="(day, index) in weekdays" :key="index" class="flex items-center">
                  <input
                    v-model="form.weekdays"
                    :value="index + 1"
                    type="checkbox"
                    class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span class="ml-1 text-sm text-gray-700">{{ day }}</span>
                </label>
              </div>
            </div>
            
            <div class="flex justify-end gap-3 pt-4">
              <button
                type="button"
                @click="closeModal"
                class="btn-secondary"
              >
                Отмена
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="btn-primary"
              >
                <span v-if="saving">Сохранение...</span>
                <span v-else>{{ editingSlot ? 'Сохранить' : 'Создать' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { ClockIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'TimeSlots',
  components: {
    ClockIcon
  },
  setup() {
    // State
    const slots = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingSlot = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Form
    const form = ref({
      label: '',
      startTime: '',
      endTime: '',
      breakMinutes: 10,
      weekdays: [1, 2, 3, 4, 5] // Monday to Friday by default
    })

    const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    // Computed
    const filteredSlots = computed(() => {
      let filtered = slots.value

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(slot => 
          slot.label.toLowerCase().includes(query)
        )
      }

      return filtered
    })

    const totalPages = computed(() => 
      Math.ceil(filteredSlots.value.length / itemsPerPage)
    )

    const paginatedSlots = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredSlots.value.slice(start, end)
    })

    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      
      if (total <= 7) {
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) {
            pages.push(i)
          }
          pages.push('...')
          pages.push(total)
        } else if (current >= total - 3) {
          pages.push(1)
          pages.push('...')
          for (let i = total - 4; i <= total; i++) {
            pages.push(i)
          }
        } else {
          pages.push(1)
          pages.push('...')
          for (let i = current - 1; i <= current + 1; i++) {
            pages.push(i)
          }
          pages.push('...')
          pages.push(total)
        }
      }
      
      return pages
    })

    // Methods
    const loadSlots = async () => {
      loading.value = true
      try {
        const response = await catalogAPI.getTimeSlots()
        slots.value = response.data || []
      } catch (error) {
        console.error('Error loading time slots:', error)
        slots.value = []
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingSlot.value = null
      form.value = {
        label: '',
        startTime: '',
        endTime: '',
        breakMinutes: 10,
        weekdays: [1, 2, 3, 4, 5]
      }
      showModal.value = true
    }

    const openEditModal = (slot) => {
      editingSlot.value = slot
      form.value = {
        label: slot.label,
        startTime: slot.start_time,
        endTime: slot.end_time,
        breakMinutes: slot.break_minutes,
        weekdays: getWeekdaysFromMask(slot.weekday_mask)
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingSlot.value = null
      form.value = {
        label: '',
        startTime: '',
        endTime: '',
        breakMinutes: 10,
        weekdays: [1, 2, 3, 4, 5]
      }
    }

    const saveSlot = async () => {
      saving.value = true
      try {
        const weekdayMask = getWeekdayMask(form.value.weekdays)
        
        const slotData = {
          org_id: 1, // Demo organization ID
          label: form.value.label,
          start_time: form.value.startTime,
          end_time: form.value.endTime,
          break_minutes: form.value.breakMinutes,
          weekday_mask: weekdayMask
        }

        if (editingSlot.value) {
          // Update existing slot
          const updateData = {
            label: form.value.label,
            start_time: form.value.startTime,
            end_time: form.value.endTime,
            break_minutes: form.value.breakMinutes,
            weekday_mask: weekdayMask
          }
          await catalogAPI.updateTimeSlot(editingSlot.value.slot_id, updateData)
          const index = slots.value.findIndex(s => s.slot_id === editingSlot.value.slot_id)
          if (index !== -1) {
            slots.value[index] = { ...editingSlot.value, ...updateData }
          }
        } else {
          // Create new slot
          const response = await catalogAPI.createTimeSlot(slotData)
          slots.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving time slot:', error)
        alert('Ошибка при сохранении временного слота')
      } finally {
        saving.value = false
      }
    }

    const deleteSlot = async (slot) => {
      if (!confirm(`Вы уверены, что хотите удалить слот "${slot.label}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteTimeSlot(slot.slot_id)
        const index = slots.value.findIndex(s => s.slot_id === slot.slot_id)
        if (index !== -1) {
          slots.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting time slot:', error)
        alert('Ошибка при удалении временного слота')
      }
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '—'
      return timeStr.substring(0, 5) // HH:MM
    }

    const getWeekdaysLabel = (mask) => {
      const days = []
      for (let i = 0; i < 7; i++) {
        if (mask & (1 << i)) {
          days.push(weekdays[i])
        }
      }
      return days.join(', ')
    }

    const getWeekdaysFromMask = (mask) => {
      const days = []
      for (let i = 0; i < 7; i++) {
        if (mask & (1 << i)) {
          days.push(i + 1)
        }
      }
      return days
    }

    const getWeekdayMask = (weekdays) => {
      let mask = 0
      for (const day of weekdays) {
        mask |= (1 << (day - 1))
      }
      return mask
    }

    // Watchers
    watch([searchQuery], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadSlots()
    })

    return {
      // State
      slots,
      loading,
      saving,
      showModal,
      editingSlot,
      searchQuery,
      currentPage,
      itemsPerPage,
      form,
      weekdays,
      
      // Computed
      filteredSlots,
      totalPages,
      paginatedSlots,
      visiblePages,
      
      // Methods
      loadSlots,
      openCreateModal,
      openEditModal,
      closeModal,
      saveSlot,
      deleteSlot,
      formatTime,
      getWeekdaysLabel
    }
  }
}
</script>