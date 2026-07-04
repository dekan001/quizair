import type { User } from "./api";

/** Итоги одной игровой сессии (до исчерпания лимита). */
export interface SessionStats {
  answered: number;
  correct: number;
  score: number;
}

/** Бонус к дневному лимиту за стрик: 3 дня → +2, 7 дней → +5. */
export function streakBonus(streak: number): number {
  if (streak >= 7) return 5;
  if (streak >= 3) return 2;
  return 0;
}

/** Сколько бесплатных квизов положено сегодня. */
export function dailyQuota(u: User): number {
  return u.daily_base + streakBonus(u.streak);
}

/** Всего доступно попыток: дневные (сгорают) + бонусные (за подписки, не сгорают). */
export function totalLeft(u: User): number {
  return u.daily_left + u.bonus_left;
}

/** Жёсткий дневной потолок ответов (совпадает с settings.daily_cap на бэкенде). */
export const DAILY_CAP = 50;

/** Инициалы для аватара без фото. */
export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] ?? "?").toUpperCase() + (parts[1]?.[0] ?? "").toUpperCase();
}

// ---- ТЗ v1.1: уровень сложности и бонус «каждые 10 верных → +1» ----
export const LEVEL_LABEL: Record<string, string> = {
  easy: "Новичок",
  medium: "Знаток",
  hard: "Эксперт",
};
export const LEVEL_EMOJI: Record<string, string> = {
  easy: "🌱",
  medium: "🎯",
  hard: "🔥",
};

/** Сколько верных ответов накоплено с прошлого бонусного (0..9). */
export function bonusProgress(correctTotal: number): number {
  return ((correctTotal % 10) + 10) % 10;
}

// ---- значки (ТЗ v1.1, механика 2): эмодзи и названия по ключу ----
export const BADGE_EMOJI: Record<string, string> = {
  on_fire: "🔥",
  sniper: "🎯",
  speed: "⚡",
  ai_guru: "🤖",
  crypto_master: "₿",
  psych_master: "🧠",
  football_expert: "⚽",
  science_master: "🔬",
  history_buff: "🏛️",
  movie_expert: "🎬",
  music_guru: "🎵",
  gamer: "🎮",
  geo_master: "🗺️",
  ambassador: "👥",
  legend: "💎",
  champion: "🏆",
};

export const BADGE_TITLE: Record<string, string> = {
  on_fire: "On Fire",
  sniper: "Снайпер",
  speed: "Быстрый",
  ai_guru: "AI-гуру",
  crypto_master: "Крипто-мастер",
  psych_master: "Психолог",
  football_expert: "Эксперт поля",
  science_master: "Учёный",
  history_buff: "Историк",
  movie_expert: "Киноман",
  music_guru: "Меломан",
  gamer: "Геймер",
  geo_master: "Географ",
  ambassador: "Амбассадор",
  legend: "Легенда",
  champion: "Чемпион",
};
