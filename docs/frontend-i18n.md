# Frontend i18n

Astralith frontend supports Simplified Chinese and English UI text through `vue-i18n`.

## Locale Files

```text
frontend/src/i18n/
├── index.ts
└── locales/
    ├── zh-CN.ts
    └── en-US.ts
```

## Rules

- User-facing text in Vue pages should use `t('message.key')` instead of hardcoded strings.
- The first version supports `zh-CN` and `en-US`.
- The language selector stores the user's choice in `localStorage` under `astralith.locale`.
- If no saved language exists, the frontend falls back to the browser language and then `zh-CN`.
- Code comments remain Chinese, even in TypeScript/Vue files.
- Backend API error i18n can be added later after the core task workflow is implemented.

## Current Scope

The current scaffold internationalizes navigation labels, dashboard labels, page placeholder text, and built-in operation module metadata returned by the backend. Other business data returned by the backend remains unchanged.
