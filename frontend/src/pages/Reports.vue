<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Отчеты</h1>
    
    <div class="bg-white shadow rounded-lg p-6">
      <div class="text-center py-12">
        <DocumentTextIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          Система отчетов
        </h3>
        <p class="text-gray-600">
          Здесь будут доступны отчеты по нагрузке преподавателей, групп, конфликтам в расписании и экспорт в iCal.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

export default {
  name: 'Reports',
  components: {
    DocumentTextIcon
  }
}
</script>
