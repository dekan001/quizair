// Обёртка над Telegram Web App SDK с dev-фолбэком.

export function getWebApp() {
  return window.Telegram?.WebApp;
}

/** Инициализация: готовность, раскрытие, тёмный фон. */
export function initTelegram(): void {
  const wa = getWebApp();
  if (!wa) return;
  try {
    wa.ready();
    wa.expand();
    wa.setHeaderColor?.("#020617");
    wa.setBackgroundColor?.("#020617");
  } catch {
    /* SDK может быть не готов — игнорируем */
  }
}

export interface TgUserLite {
  id: number;
  username?: string;
  first_name?: string;
  photo_url?: string;
}

/** Реальный пользователь из Telegram или null (вне TG — dev-режим). */
export function getTgUser(): TgUserLite | null {
  const u = getWebApp()?.initDataUnsafe?.user;
  if (!u) return null;
  return {
    id: u.id,
    username: u.username,
    first_name: u.first_name,
    photo_url: u.photo_url,
  };
}

export function inTelegram(): boolean {
  return !!getWebApp()?.initDataUnsafe?.user;
}

export type Haptic =
  | "light"
  | "medium"
  | "heavy"
  | "soft"
  | "rigid"
  | "success"
  | "error"
  | "warning"
  | "select";

export function haptic(type: Haptic): void {
  const hf = getWebApp()?.HapticFeedback;
  if (!hf) return;
  if (type === "select") hf.selectionChanged();
  else if (type === "success" || type === "error" || type === "warning")
    hf.notificationOccurred(type);
  else hf.impactOccurred(type);
}

/** Поделиться результатом через нативный шаринг Telegram. */
export function shareResult(score: number, topicTitle: string): void {
  const botUrl = "https://t.me/agent_era_ai/app";
  const text = `Я набрал ${score} очков в квизе «${topicTitle}» 🔥 А ты сколько выжмешь?`;
  const url = `https://t.me/share/url?url=${encodeURIComponent(
    botUrl,
  )}&text=${encodeURIComponent(text)}`;
  const wa = getWebApp();
  if (wa?.openTelegramLink) wa.openTelegramLink(url);
  else window.open(url, "_blank");
}
