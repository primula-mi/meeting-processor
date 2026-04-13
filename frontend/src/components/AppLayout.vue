<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useRouter } from 'vue-router'
import { Sun, Moon, LogOut, Settings, LayoutDashboard } from 'lucide-vue-next'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <header
      v-if="auth.isAuthenticated"
      class="border-b border-border bg-card"
    >
      <div class="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div class="flex items-center gap-6">
          <router-link to="/" class="text-lg font-semibold text-foreground">
            Meeting Processor
          </router-link>
          <nav class="flex items-center gap-4">
            <router-link
              to="/"
              class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <LayoutDashboard class="h-4 w-4" />
              Совещания
            </router-link>
            <router-link
              to="/settings"
              class="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Settings class="h-4 w-4" />
              Настройки
            </router-link>
          </nav>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="auth.user" class="text-sm text-muted-foreground">
            {{ auth.user.name || auth.user.email }}
          </span>
          <button
            @click="theme.toggle()"
            class="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            :title="theme.isDark ? 'Светлая тема' : 'Тёмная тема'"
          >
            <Moon v-if="!theme.isDark" class="h-4 w-4" />
            <Sun v-else class="h-4 w-4" />
          </button>
          <button
            @click="logout"
            class="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            title="Выйти"
          >
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-6">
      <slot />
    </main>
  </div>
</template>
