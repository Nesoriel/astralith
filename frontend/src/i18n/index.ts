import { createI18n } from 'vue-i18n'

import enUS from './locales/en-US'
import zhCN from './locales/zh-CN'

export const supportedLocales = ['zh-CN', 'en-US'] as const
export type SupportedLocale = (typeof supportedLocales)[number]

const DEFAULT_LOCALE: SupportedLocale = 'zh-CN'
const STORAGE_KEY = 'astralith.locale'

export const localeLabels: Record<SupportedLocale, string> = {
  'zh-CN': '简体中文',
  'en-US': 'English',
}

export function isSupportedLocale(value: string): value is SupportedLocale {
  return supportedLocales.includes(value as SupportedLocale)
}

function resolveInitialLocale(): SupportedLocale {
  // 优先使用用户显式选择的语言，再回退到浏览器语言，避免刷新后中英文来回跳变。
  const storedLocale = localStorage.getItem(STORAGE_KEY)
  if (storedLocale !== null && isSupportedLocale(storedLocale)) {
    return storedLocale
  }

  const language = navigator.language.toLowerCase()
  return language.startsWith('en') ? 'en-US' : DEFAULT_LOCALE
}

export function persistLocale(locale: SupportedLocale): void {
  localStorage.setItem(STORAGE_KEY, locale)
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})
