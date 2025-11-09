<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Группы</h1>
        <p class="text-gray-600 mt-1">Управление студенческими группами</p>
      </div>
      <button 
        @click="openCreateModal"
        class="btn-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Добавить группу
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
              placeholder="Поиск по названию группы..."
              class="form-input pl-10"
            />
          </div>
        </div>
        <div class="flex gap-2">
          <select v-model="filters.yearLevel" class="form-select">
            <option value="">Все курсы</option>
            <option value="1">1 курс</option>
            <option value="2">2 курс</option>
            <option value="3">3 курс</option>
            <option value="4">4 курс</option>
            <option value="5">5 курс</option>
          </select>
          <select v-model="filters.status" class="form-select">
            <option value="">Все статусы</option>
            <option value="active">Активные</option>
            <option value="inactive">Неактивные</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Groups Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка...</p>
      </div>
      
      <div v-else-if="filteredGroups.length === 0" class="p-8 text-center">
        <UsersIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ searchQuery ? 'Группы не найдены' : 'Нет групп' }}
        </h3>
        <p class="text-gray-600">
          {{ searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Создайте первую группу' }}
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
                Курс
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Размер
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Тип генерации
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
            <tr v-for="group in paginatedGroups" :key="group.group_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ group.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {{ group.year_level }} курс
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ group.size }} студентов
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getGenerationTypeColor(group.generation_type)" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ group.generation_type }} пар подряд
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="group.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ group.is_active ? 'Активна' : 'Неактивна' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(group)"
                    class="text-indigo-600 hover:text-indigo-900"
                    title="Редактировать"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button
                    @click="toggleGroupStatus(group)"
                    :class="group.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'"
                    :title="group.is_active ? 'Деактивировать' : 'Активировать'"
                  >
                    <svg v-if="group.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </button>
                  <button
                    @click="deleteGroup(group)"
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
              - <span class="font-medium">{{ Math.min(currentPage * itemsPerPage, filteredGroups.length) }}</span>
              из <span class="font-medium">{{ filteredGroups.length }}</span> групп
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
              {{ editingGroup ? 'Редактировать группу' : 'Добавить группу' }}
            </h3>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <form @submit.prevent="saveGroup" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Название группы *
              </label>
              <input
                v-model="form.name"
                type="text"
                required
                class="form-input"
                placeholder="Например: ИУ5-61Б"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Курс *
              </label>
              <select v-model="form.yearLevel" required class="form-select">
                <option value="">Выберите курс</option>
                <option value="1">1 курс</option>
                <option value="2">2 курс</option>
                <option value="3">3 курс</option>
                <option value="4">4 курс</option>
                <option value="5">5 курс</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Размер группы *
              </label>
              <input
                v-model.number="form.size"
                type="number"
                min="1"
                max="100"
                required
                class="form-input"
                placeholder="Количество студентов"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Тип генерации *
              </label>
              <select v-model.number="form.generationType" required class="form-select">
                <option value="2">2 пары подряд</option>
                <option value="3">3 пары подряд</option>
                <option value="5">5 пар подряд</option>
              </select>
              <p class="mt-1 text-xs text-gray-500">
                Количество пар, которые группа будет отучивать подряд в один день
              </p>
            </div>
            
            <div class="flex items-center">
              <input
                v-model="form.isActive"
                type="checkbox"
                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label class="ml-2 block text-sm text-gray-900">
                Активная группа
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
                <span v-else>{{ editingGroup ? 'Сохранить' : 'Создать' }}</span>
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
import { UsersIcon } from '@heroicons/vue/24/outline'
import { catalogAPI } from '@/services/api'

export default {
  name: 'Groups',
  components: {
    UsersIcon
  },
  setup() {
    // State
    const groups = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    const editingGroup = ref(null)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const itemsPerPage = 10

    // Filters
    const filters = ref({
      yearLevel: '',
      status: ''
    })

    // Form
    const form = ref({
      name: '',
      yearLevel: '',
      size: 25,
      generationType: 2,
      isActive: true
    })

    // Computed
    const filteredGroups = computed(() => {
      let filtered = groups.value

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(group => 
          group.name.toLowerCase().includes(query)
        )
      }

      // Year level filter
      if (filters.value.yearLevel) {
        filtered = filtered.filter(group => 
          group.year_level === parseInt(filters.value.yearLevel)
        )
      }

      // Status filter
      if (filters.value.status) {
        const isActive = filters.value.status === 'active'
        filtered = filtered.filter(group => group.is_active === isActive)
      }

      return filtered
    })

    const totalPages = computed(() => 
      Math.ceil(filteredGroups.value.length / itemsPerPage)
    )

    const paginatedGroups = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredGroups.value.slice(start, end)
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
    const loadGroups = async () => {
      loading.value = true
      try {
        const response = await catalogAPI.getGroups()
        groups.value = response.data || []
      } catch (error) {
        console.error('Error loading groups:', error)
        groups.value = []
      } finally {
        loading.value = false
      }
    }

    const openCreateModal = () => {
      editingGroup.value = null
      form.value = {
        name: '',
        yearLevel: '',
        size: 25,
        generationType: 2,
        isActive: true
      }
      showModal.value = true
    }

    const openEditModal = (group) => {
      editingGroup.value = group
      form.value = {
        name: group.name,
        yearLevel: group.year_level.toString(),
        size: group.size,
        generationType: group.generation_type || 2,
        isActive: group.is_active
      }
      showModal.value = true
    }

    const closeModal = () => {
      showModal.value = false
      editingGroup.value = null
      form.value = {
        name: '',
        yearLevel: '',
        size: 25,
        generationType: 2,
        isActive: true
      }
    }

    const saveGroup = async () => {
      saving.value = true
      try {
        const groupData = {
          org_id: 1, // Demo organization ID
          name: form.value.name,
          year_level: parseInt(form.value.yearLevel),
          size: form.value.size,
          generation_type: form.value.generationType,
          is_active: form.value.isActive
        }

        if (editingGroup.value) {
          // Update existing group
          const updateData = {
            name: form.value.name,
            year_level: parseInt(form.value.yearLevel),
            size: form.value.size,
            generation_type: form.value.generationType,
            is_active: form.value.isActive
          }
          await catalogAPI.updateGroup(editingGroup.value.group_id, updateData)
          const index = groups.value.findIndex(g => g.group_id === editingGroup.value.group_id)
          if (index !== -1) {
            groups.value[index] = { ...editingGroup.value, ...updateData }
          }
        } else {
          // Create new group
          const response = await catalogAPI.createGroup(groupData)
          groups.value.unshift(response.data)
        }

        closeModal()
      } catch (error) {
        console.error('Error saving group:', error)
        alert('Ошибка при сохранении группы')
      } finally {
        saving.value = false
      }
    }

    const toggleGroupStatus = async (group) => {
      try {
        const newStatus = !group.is_active
        await catalogAPI.updateGroup(group.group_id, { is_active: newStatus })
        group.is_active = newStatus
      } catch (error) {
        console.error('Error toggling group status:', error)
        alert('Ошибка при изменении статуса группы')
      }
    }

    const deleteGroup = async (group) => {
      if (!confirm(`Вы уверены, что хотите удалить группу "${group.name}"?`)) {
        return
      }

      try {
        await catalogAPI.deleteGroup(group.group_id)
        const index = groups.value.findIndex(g => g.group_id === group.group_id)
        if (index !== -1) {
          groups.value.splice(index, 1)
        }
      } catch (error) {
        console.error('Error deleting group:', error)
        alert('Ошибка при удалении группы')
      }
    }

    const getGenerationTypeColor = (type) => {
      switch (type) {
        case 2:
          return 'bg-green-100 text-green-800'
        case 3:
          return 'bg-yellow-100 text-yellow-800'
        case 5:
          return 'bg-red-100 text-red-800'
        default:
          return 'bg-gray-100 text-gray-800'
      }
    }

    // Watchers
    watch([searchQuery, filters], () => {
      currentPage.value = 1
    })

    // Lifecycle
    onMounted(() => {
      loadGroups()
    })

    return {
      // State
      groups,
      loading,
      saving,
      showModal,
      editingGroup,
      searchQuery,
      currentPage,
      itemsPerPage,
      filters,
      form,
      
      // Computed
      filteredGroups,
      totalPages,
      paginatedGroups,
      visiblePages,
      
      // Methods
      loadGroups,
      openCreateModal,
      openEditModal,
      closeModal,
      saveGroup,
      toggleGroupStatus,
      deleteGroup,
      getGenerationTypeColor
    }
  }
}
</script>
