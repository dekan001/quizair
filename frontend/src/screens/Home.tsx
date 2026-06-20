import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Topic } from "../lib/api";
import { useUser } from "../context/UserContext";
import {
  initials,
  LEVEL_EMOJI,
  LEVEL_LABEL,
  bonusProgress,
  DAILY_CAP,
} from "../lib/game";
import { topicTheme } from "../lib/theme";
import { RingProgress } from "../components/RingProgress";

export function Home() {
  const navigate = useNavigate();
  const { user, loading, error, isDev, tgId, setDevTgId, refresh } = useUser();
  const [topics, setTopics] = useState<Topic[]>([]);

  useEffect(() => {
    api.getTopics().then(setTopics).catch(() => {});
  }, []);

  if (loading && !user)
    return <CenterLoader />;
  if (error && !user)
    return (
      <div className="mx-auto max-w-md px-4 pt-24">
        <div className="card text-center">
          <p className="text-rose-300">{error}</p>
          <button className="btn-primary mt-4" onClick={() => void refresh()}>
            Повторить
          </button>
        </div>
      </div>
    );
  if (!user) return null;

  const left = user.daily_left;
  const total = user.daily_left + user.bonus_left; // общая доступная цифра
  const ringValue = Math.min(1, total / DAILY_CAP);
  const canPlay = total > 0;

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-5">
      {/* профиль */}
      <header className="flex animate-fade-up items-center gap-3">
        <div className="rounded-full bg-gradient-to-br from-brand-400 to-fuchsia-500 p-[2px]">
          {user.photo_url ? (
            <img
              src={user.photo_url}
              alt=""
              className="h-12 w-12 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-ink-900 font-bold text-white">
              {initials(user.first_name ?? user.username)}
            </div>
          )}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-slate-400">С возвращением</p>
          <p className="truncate text-lg font-bold leading-tight">
            {user.first_name ?? user.username ?? "Игрок"}
          </p>
          <p className="mt-0.5 text-xs text-slate-400">
            Уровень: {LEVEL_LABEL[user.skill_level ?? "easy"] ?? user.skill_level}{" "}
            {LEVEL_EMOJI[user.skill_level ?? "easy"] ?? ""}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-1.5 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1.5 text-orange-300">
          <span className="text-base">🔥</span>
          <span className="font-bold">{user.streak}</span>
        </div>
      </header>

      {isDev && (
        <button
          className="mt-3 w-full rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300"
          onClick={() => {
            const v = window.prompt("DEV tg_id", String(tgId));
            const n = Number(v);
            if (Number.isFinite(n) && n > 0) setDevTgId(n);
          }}
        >
          DEV-режим (вне Telegram) · tg_id = {tgId}
        </button>
      )}

      {/* дневной лимит — герой-карточка */}
      <section
        className="card mt-5 animate-fade-up overflow-hidden"
        style={{ animationDelay: "60ms" }}
      >
        <div className="flex items-center gap-4">
          <RingProgress value={ringValue}>
            <span className="text-2xl font-extrabold leading-none">{total}</span>
            <span className="text-[10px] text-slate-400">из {DAILY_CAP}</span>
          </RingProgress>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-slate-400">Доступно вопросов</p>
            <p className="text-xl font-bold leading-tight">
              {canPlay ? "Готов играть" : "На сегодня всё"}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              <span className="font-semibold text-slate-200">
                {user.daily_left}
              </span>{" "}
              дневных
              {user.bonus_left > 0 && (
                <>
                  {" + "}
                  <span className="font-semibold text-emerald-300">
                    {user.bonus_left}
                  </span>{" "}
                  бонусных
                </>
              )}
            </p>
            {left === 0 && user.bonus_left > 0 && (
              <p className="mt-1.5 text-xs text-slate-500">
                Дневной лимит исчерпан — играешь на бонусных
              </p>
            )}
            {left === 0 && user.bonus_left === 0 && (
              <p className="mt-1.5 text-xs text-slate-500">
                Новые вопросы завтра 🌙
              </p>
            )}
          </div>
        </div>
      </section>

      {/* тонкая полоска прогресса к бонусному вопросу (подробности — в профиле) */}
      <div
        className="mt-3 flex animate-fade-up items-center gap-2 px-1"
        style={{ animationDelay: "100ms" }}
      >
        <span className="shrink-0 text-xs text-slate-500">🎁 До бонуса</span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all duration-500"
            style={{ width: `${bonusProgress(user.correct_total ?? 0) * 10}%` }}
          />
        </div>
        <span className="shrink-0 text-xs font-medium text-slate-400">
          {bonusProgress(user.correct_total ?? 0)}/10
        </span>
      </div>

      {/* темы */}
      <h2 className="mb-3 mt-7 px-1 text-sm font-semibold uppercase tracking-wider text-slate-500">
        Выбери тему
      </h2>
      <div className="flex flex-col gap-2.5">
        {topics.map((t, i) => {
          const th = topicTheme(t.slug);
          return (
            <button
              key={t.slug}
              onClick={() => navigate(`/quiz/${t.slug}`)}
              style={{ animationDelay: `${100 + i * 50}ms` }}
              className={`group relative flex w-full animate-fade-up items-center gap-3 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-r ${th.surface} to-white/[0.02] p-3 text-left transition-all duration-200 hover:border-white/20 active:scale-[0.99] ${th.shadow} hover:shadow-lg`}
            >
              <div
                className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${th.tile} text-2xl shadow-lg`}
              >
                {t.emoji ?? "🎯"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-bold leading-tight">{t.title}</p>
                <p className="mt-0.5 text-xs text-slate-400">Играть</p>
              </div>
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-slate-200 transition-all duration-200 group-hover:bg-white/20 group-hover:text-white">
                <span className="transition-transform duration-200 group-hover:translate-x-0.5">
                  →
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CenterLoader() {
  return (
    <div className="flex h-[70vh] items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-brand-400" />
    </div>
  );
}
