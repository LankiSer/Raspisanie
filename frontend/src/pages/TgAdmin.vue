<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>Диалоги Telegram</h1>
        <p class="text-gray-500 text-sm mt-0.5">Вопросы пользователей из бота — отвечайте прямо здесь</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="loadChats" class="btn-secondary">Обновить</button>
        <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
          <input v-model="showResolved" type="checkbox" class="rounded" @change="loadChats" />
          Показать закрытые
        </label>
      </div>
    </div>

    <div v-if="error" class="alert-error mb-4">{{ error }}</div>

    <div class="flex gap-4 h-[calc(100vh-11rem)]">
      <!-- ── Chat list ────────────────────────────────────────────── -->
      <div class="w-72 shrink-0 card flex flex-col overflow-hidden">
        <div class="card-header py-3">
          <span class="text-sm font-semibold text-gray-700">Чаты</span>
          <span v-if="unreadTotal" class="badge-red">{{ unreadTotal }}</span>
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
          Загрузка…
        </div>

        <div v-else-if="!chats.length" class="flex-1 flex items-center justify-center text-gray-400 text-sm p-4 text-center">
          Нет диалогов
        </div>

        <div v-else class="flex-1 overflow-y-auto divide-y divide-gray-100">
          <button
            v-for="chat in chats"
            :key="chat.id"
            @click="selectChat(chat)"
            :class="[
              'w-full text-left px-3 py-2.5 hover:bg-gov-50 transition-colors',
              selectedChat?.id === chat.id ? 'bg-gov-50 border-l-2 border-gov-600' : '',
              chat.is_resolved ? 'opacity-60' : '',
            ]"
          >
            <div class="flex items-center justify-between gap-1">
              <span class="text-sm font-medium text-gray-800 truncate">
                {{ chat.full_name || chat.tg_username || `User #${chat.tg_user_id}` }}
              </span>
              <span v-if="chat.unread" class="badge-red shrink-0">{{ chat.unread }}</span>
              <span v-else-if="chat.is_resolved" class="badge-gray shrink-0 text-xs">✓</span>
            </div>
            <p class="text-xs text-gray-500 truncate mt-0.5">{{ chat.last_text || '…' }}</p>
          </button>
        </div>
      </div>

      <!-- ── Conversation ───────────────────────────────────────────── -->
      <div class="flex-1 card flex flex-col overflow-hidden">
        <!-- No chat selected -->
        <div v-if="!selectedChat" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
          Выберите диалог слева
        </div>

        <template v-else>
          <!-- Header -->
          <div class="card-header py-3">
            <div>
              <div class="font-semibold text-gray-800">
                {{ selectedChat.full_name || selectedChat.tg_username || `User #${selectedChat.tg_user_id}` }}
              </div>
              <div class="text-xs text-gray-400">
                @{{ selectedChat.tg_username || '—' }} · ID {{ selectedChat.tg_user_id }}
              </div>
            </div>
            <button
              v-if="!selectedChat.is_resolved"
              @click="resolveChat"
              class="btn-secondary text-xs py-1"
            >
              Закрыть диалог
            </button>
            <span v-else class="badge-gray">Закрыт</span>
          </div>

          <!-- Messages -->
          <div ref="msgContainer" class="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-50">
            <div v-if="messagesLoading" class="text-center text-gray-400 text-sm py-8">Загрузка…</div>
            <template v-else>
              <div
                v-for="msg in messages"
                :key="msg.id"
                :class="msg.direction === 'out' ? 'flex justify-end' : 'flex justify-start'"
              >
                <div
                  :class="[
                    'max-w-[75%] px-3 py-2 rounded-lg text-sm leading-relaxed shadow-sm',
                    msg.direction === 'out'
                      ? 'bg-gov-600 text-white rounded-br-none'
                      : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none',
                  ]"
                >
                  {{ msg.text }}
                  <div class="text-xs mt-1 opacity-60 text-right">
                    {{ fmtTime(msg.created_at) }}
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Reply input -->
          <div class="border-t border-gray-200 p-3 flex gap-2 bg-white">
            <textarea
              v-model="replyText"
              @keydown.enter.exact.prevent="sendReply"
              placeholder="Введите ответ… (Enter — отправить)"
              rows="2"
              :disabled="selectedChat.is_resolved || sending"
              class="flex-1 form-input resize-none text-sm py-1.5"
            ></textarea>
            <button
              @click="sendReply"
              :disabled="!replyText.trim() || selectedChat.is_resolved || sending"
              class="btn-primary self-end"
            >
              <span v-if="sending">…</span>
              <span v-else>Отправить</span>
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onUnmounted, computed } from 'vue'
import api from '@/services/api'

export default {
  name: 'TgAdmin',
  setup() {
    const chats        = ref([])
    const selectedChat = ref(null)
    const messages     = ref([])
    const replyText    = ref('')
    const showResolved = ref(false)
    const loading      = ref(false)
    const messagesLoading = ref(false)
    const sending      = ref(false)
    const error        = ref('')
    const msgContainer = ref(null)

    const unreadTotal = computed(() => chats.value.reduce((s, c) => s + (c.unread || 0), 0))

    const loadChats = async () => {
      loading.value = true
      error.value   = ''
      try {
        const params = showResolved.value ? {} : { resolved: false }
        const res = await api.get('/tg/chats', { params })
        chats.value = res.data
      } catch (e) {
        error.value = e.response?.data?.detail || e.message
      } finally {
        loading.value = false
      }
    }

    const selectChat = async (chat) => {
      selectedChat.value = chat
      messagesLoading.value = true
      messages.value = []
      try {
        const res = await api.get(`/tg/chats/${chat.id}/messages`)
        messages.value = res.data
        // Mark unread = 0 locally
        chat.unread = 0
        await nextTick()
        if (msgContainer.value) {
          msgContainer.value.scrollTop = msgContainer.value.scrollHeight
        }
      } catch (e) {
        error.value = e.response?.data?.detail || e.message
      } finally {
        messagesLoading.value = false
      }
    }

    const sendReply = async () => {
      if (!replyText.value.trim() || !selectedChat.value) return
      sending.value = true
      try {
        await api.post(`/tg/chats/${selectedChat.value.id}/reply`, { text: replyText.value })
        messages.value.push({
          id: Date.now(),
          direction: 'out',
          text: replyText.value,
          is_read: true,
          created_at: new Date().toISOString(),
        })
        replyText.value = ''
        await nextTick()
        if (msgContainer.value) {
          msgContainer.value.scrollTop = msgContainer.value.scrollHeight
        }
      } catch (e) {
        error.value = 'Ошибка отправки: ' + (e.response?.data?.detail || e.message)
      } finally {
        sending.value = false
      }
    }

    const resolveChat = async () => {
      if (!selectedChat.value) return
      try {
        await api.patch(`/tg/chats/${selectedChat.value.id}/resolve`)
        selectedChat.value.is_resolved = true
        const found = chats.value.find(c => c.id === selectedChat.value.id)
        if (found) found.is_resolved = true
      } catch (e) {
        error.value = e.response?.data?.detail || e.message
      }
    }

    const fmtTime = (iso) => {
      try {
        return new Date(iso).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
      } catch {
        return iso
      }
    }

    // Poll for new messages every 15 s
    let pollInterval = null
    const pollMessages = async () => {
      if (!selectedChat.value) return
      try {
        const res = await api.get(`/tg/chats/${selectedChat.value.id}/messages`)
        const prev = messages.value.length
        messages.value = res.data
        selectedChat.value.unread = 0
        const found = chats.value.find(c => c.id === selectedChat.value.id)
        if (found) found.unread = 0
        if (res.data.length > prev) {
          await nextTick()
          if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
        }
      } catch {}
    }

    onMounted(async () => {
      await loadChats()
      pollInterval = setInterval(async () => {
        await loadChats()
        await pollMessages()
      }, 15000)
    })

    onUnmounted(() => {
      if (pollInterval) clearInterval(pollInterval)
    })

    return {
      chats, selectedChat, messages, replyText,
      showResolved, loading, messagesLoading, sending, error,
      unreadTotal, msgContainer,
      loadChats, selectChat, sendReply, resolveChat, fmtTime,
    }
  },
}
</script>
