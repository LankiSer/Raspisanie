<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Аудитории</h1>
        <p class="text-gray-600 mt-1">Управление аудиториями и их вместимостью</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить аудиторию
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
              placeholder="Поиск по номеру или зданию..."
              class="form-input pl-10"
            />
          </div>
        </div>
        <div class="flex gap-2">
          <select v-model="filters.kind" class="form-select">
            <option value="">Все типы</option>
            <option value="lecture">Лекционная</option>
            <option value="practical">Практическая</option>
            <option value="lab">Лабораторная</option>
            <option value="seminar">Семинарская</option>
          </select>
          <select v-model="filters.status" class="form-select">
            <option value="">Все статусы</option>
            <option value="active">Активные</option>
            <option value="inactive">Неактивные</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Rooms Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredRooms.length === 0" class="p-8 text-center">
        <BuildingOfficeIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Аудитории не найдены' : 'Нет аудиторий' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Добавьте первую аудиторию' }}
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Аудитория
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Тип
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Вместимость
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Здание
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Статус
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Действия
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="room in paginatedRooms" :key="room.room_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ room.number }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getRoomTypeClass(room.kind)" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ getRoomTypeLabel(room.kind) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ room.capacity }} мест
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ room.building || '—' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="room.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ room.is_active ? 'Активна' : 'Неактивна' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(room)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="toggleRoomStatus(room)"
                    :class="room.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'"
                    :title="room.is_active ? 'Деактивировать' : 'Активировать'"
                  >
                    <svg v-if="room.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteRoom(room)"
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
              - <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredRooms.length) }}</span>
              из <span class="font-medium">{{ filteredRooms.length }}</span> аудиторий
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
              {{ editingRoom ? 'Редактировать аудиторию' : 'Добавить аудиторию' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <form @submit.prevent="saveRoom" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Номер аудитории *
              </label>
              <input
                v-model="form.number"
                type="text"
                required
                class="form-input"
                placeholder="Например: 101, 201А"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Тип аудитории *
              </label>
              <select v-model="form.kind" required class="form-select">
                <option value="">Выберите тип</option>
                <option value="lecture">Лекционная</option>
                <option value="practical">Практическая</option>
                <option value="lab">Лабораторная</option>
                <option value="seminar">Семинарская</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Вместимость *
              </label>
              <input
                v-model.number="form.capacity"
                type="number"
                min="1"
                max="500"
                required
                class="form-input"
                placeholder="Количество мест"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Здание
              </label>
              <input
                v-model="form.building"
                type="text"
                class="form-input"
                placeholder="Например: Главный корпус"
              />
            </div>
            
            <div class="flex items-center">
              <input
                v-model="form.isActive"
                type="checkbox"
                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label class="ml-2 block text-sm text-gray-900">
                Активная аудитория
              </label>
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
                <span v-else>{{ editingRoom ? 'Сохранить' : 'Создать' }}</span>
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
import { BuildingOfficeIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'Rooms',
  components: {
    BuildingOfficeIcon
  },
  setup() {
    // State
    const rooms = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingRoom = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      kind: '',
      status: ''
    })

    // Form
    const form = ref({
      number: '',
      kind: '',
      capacity: 30,
      building: '',
      isActive: true
    })

    // Computed
    const filteredRooms = computed(() => {
      let filtered = rooms.value

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(room => 
          room.number.toLowerCase().includes(query) ||
          (room.building && room.building.toLowerCase().includes(query))
        )
      }

      // Kind filter
      if (filters.value.kind) {
        filtered = filtered.filter(room => room.kind === filters.value.kind)
      }

      // Status filter
      if (filters.value.status) {
        const isActive = filters.value.status === 'active'
        filtered = filtered.filter(room => room.is_active === isActive)
      }

      return filtered
    })

    const totalPages = computed(() => 
      Math.ceil(filteredRooms.value.length / itemsPerPage)
    )

    const paginatedRooms = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredRooms.value.slice(start, end)
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
    const loadRooms = async () => {
      loading.value = true
      try {
        const response = await catalogAPI.getRooms()
        rooms.value = response.data || []
      } catch (error) {
        console.error('Error loading rooms:', error)
        rooms.value = []
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingRoom.value = null
      form.value = {
        number: '',
        kind: '',
        capacity: 30,
        building: '',
        isActive: true
      }
      showModal.value = true
    }

    const openEditModal = (room) => {
      editingRoom.value = room
      form.value = {
        number: room.number,
        kind: room.kind,
        capacity: room.capacity,
        building: room.building || '',
        isActive: room.is_active
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingRoom.value = null
      form.value = {
        number: '',
        kind: '',
        capacity: 30,
        building: '',
        isActive: true
      }
    }

    const saveRoom = async () => {
      saving.value = true
      try {
        const roomData = {
          org_id: 1, // Demo organization ID
          number: form.value.number,
          kind: form.value.kind,
          capacity: form.value.capacity,
          building: form.value.building || null,
          is_active: form.value.isActive
        }

        if (editingRoom.value) {
          // Update existing room
          const updateData = {
            number: form.value.number,
            kind: form.value.kind,
            capacity: form.value.capacity,
            building: form.value.building || null,
            is_active: form.value.isActive
          }
          await catalogAPI.updateRoom(editingRoom.value.room_id, updateData)
          const index = rooms.value.findIndex(r => r.room_id === editingRoom.value.room_id)
          if (index !== -1) {
            rooms.value[index] = { ...editingRoom.value, ...updateData }
          }
        } else {
          // Create new room
          const response = await catalogAPI.createRoom(roomData)
          rooms.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving room:', error)
        alert('Ошибка при сохранении аудитории')
      } finally {
        saving.value = false
      }
    }

    const toggleRoomStatus = async (room) => {
      try {
        const newStatus = !room.is_active
        await catalogAPI.updateRoom(room.room_id, { is_active: newStatus })
        room.is_active = newStatus
      } catch (error) {
        console.error('Error toggling room status:', error)
        alert('Ошибка при изменении статуса аудитории')
      }
    }

    const deleteRoom = async (room) => {
      if (!confirm(`Вы уверены, что хотите удалить аудиторию "${room.number}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteRoom(room.room_id)
        const index = rooms.value.findIndex(r => r.room_id === room.room_id)
        if (index !== -1) {
          rooms.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting room:', error)
        alert('Ошибка при удалении аудитории')
      }
    }

    const getRoomTypeLabel = (kind) => {
      const labels = {
        lecture: 'Лекционная',
        practical: 'Практическая',
        lab: 'Лабораторная',
        seminar: 'Семинарская'
      }
      return labels[kind] || kind
    }

    const getRoomTypeClass = (kind) => {
      const classes = {
        lecture: 'bg-blue-100 text-blue-800',
        practical: 'bg-green-100 text-green-800',
        lab: 'bg-purple-100 text-purple-800',
        seminar: 'bg-yellow-100 text-yellow-800'
      }
      return classes[kind] || 'bg-gray-100 text-gray-800'
    }

    // Watchers
    watch([searchQuery, filters], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadRooms()
    })

    return {
      // State
      rooms,
      loading,
      saving,
      showModal,
      editingRoom,
      searchQuery,
      currentPage,
      itemsPerPage,
      filters,
      form,
      
      // Computed
      filteredRooms,
      totalPages,
      paginatedRooms,
      visiblePages,
      
      // Methods
      loadRooms,
      openCreateModal,
      openEditModal,
      closeModal,
      saveRoom,
      toggleRoomStatus,
      deleteRoom,
      getRoomTypeLabel,
      getRoomTypeClass
    }
  }
}
</script>