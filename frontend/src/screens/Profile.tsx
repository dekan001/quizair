import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Badge } from "../lib/api";
import { useUser } from "../context/UserContext";
import { bonusProgress, dailyQuota, initials, streakBonus } from "../lib/game";
import { ProgressBar } from "../components/ProgressBar";
import { RefreshIcon } from "../components/icons";

export function Profile() {
  const navigate = useNavigate();
  const { user, isDev, tgId, setDevTgId, refresh } = useUser();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [busyBadge, setBusyBadge] = useState<string | null>(null);

  const loadBadges = () => {
    api.getBadges(tgId).then(setBadges).catch(() => {});
  };
  useEffect(loadBadges, [tgId]);

  if (!user)
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-brand-400" />
      </div>
    );

  const pickBadge = async (b: Badge) => {
    if (!b.earned || busyBadge) return;
    const next = user.active_badge === b.key ? null : b.key;
    setBusyBadge(b.key);
    try {
      await api.setActiveBadge(tgId, next);
      await Promise.all([refresh(), loadBadges()]);
    } finally {
      setBusyBadge(null);
    }
  };

  const quota = dailyQuota(user);
  const used = Math.max(0, quota - user.daily_left);

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-8">
      <header className="flex animate-fade-up flex-col items-center text-center">
        <div className="rounded-full bg-gradient-to-br from-brand-400 to-fuchsia-500 p-[3px] shadow-glow">
          {user.photo_url ? (
            <img
              src={user.photo_url}
              alt=""
              className="h-24 w-24 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-24 w-24 items-center justify-center rounded-full bg-ink-900 text-3xl font-bold text-white">
              {initials(user.first_name ?? user.username)}
            </div>
          )}
        </div>
        <h1 className="mt-3 text-2xl font-extrabold">
          {user.first_name ?? user.username ?? "Игрок"}
        </h1>
        {user.username && (
          <p className="text-sm text-slate-400">@{user.username}</p>
        )}
      </header>

      {/* главный счёт */}
      <section
        className="card mt-6 animate-fade-up text-center"
        style={{ animationDelay: "60ms" }}
      >
        <div className="text-5xl font-extrabold text-gradient">
          {user.total_score}
        </div>
        <div className="mt-1 text-sm text-slate-400">всего очков</div>
      </section>

      {/* стрик и лимит */}
      <div
        className="mt-3 grid animate-fade-up grid-cols-2 gap-3"
        style={{ animationDelay: "120ms" }}
      >
        <div className="card text-center">
          <div className="text-3xl font-extrabold">🔥 {user.streak}</div>
          <div className="mt-1 text-xs text-slate-400">
            дней подряд · рекорд {user.longest_streak}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-extrabold">
            {user.daily_left}
            <span className="text-lg text-slate-500">/{quota}</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">дневных вопросов</div>
          {user.bonus_left > 0 && (
            <div className="mt-1 text-sm font-semibold text-emerald-400">
              +{user.bonus_left} бонусных
            </div>
          )}
        </div>
      </div>

      <section
        className="card mt-3 animate-fade-up"
        style={{ animationDelay: "180ms" }}
      >
        <div className="mb-2 flex items-baseline justify-between text-sm">
          <span className="text-slate-400">Дневной лимит (сгорает)</span>
          <span className="font-medium text-slate-300">
            база {user.daily_base} + стрик{" "}
            <span className="text-orange-300">+{streakBonus(user.streak)}</span>
          </span>
        </div>
        <ProgressBar value={quota === 0 ? 0 : used / quota} />
        <div className="mt-4 flex items-baseline justify-between text-sm">
          <span className="text-slate-400">Бонусные слоты (не сгорают)</span>
          <span className="font-bold text-emerald-400">{user.bonus_left}</span>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Получаешь за подписки в разделе «Задания».
        </p>
      </section>

      {/* прогресс к бонусному вопросу (каждые 10 верных → +1) */}
      <section
        className="card mt-3 animate-fade-up"
        style={{ animationDelay: "200ms" }}
      >
        <div className="mb-2 flex items-baseline justify-between text-sm">
          <span className="text-slate-400">До бонусного вопроса</span>
          <span className="font-semibold">
            {bonusProgress(user.correct_total ?? 0)} / 10
          </span>
        </div>
        <ProgressBar value={bonusProgress(user.correct_total ?? 0) / 10} />
        <p className="mt-2 text-xs text-slate-500">
          Каждые 10 верных ответов → +1 бонусный вопрос. Всего верных:{" "}
          {user.correct_total ?? 0}
        </p>
      </section>

      {/* значки */}
      <section
        className="mt-5 animate-fade-up"
        style={{ animationDelay: "220ms" }}
      >
        <div className="mb-3 flex items-baseline justify-between px-1">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
            Значки
          </h2>
          <span className="text-xs text-slate-500">
            {badges.filter((b) => b.earned).length}/{badges.length}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-4">
          {badges.map((b) => {
            const active = user.active_badge === b.key;
            return (
              <button
                key={b.key}
                disabled={!b.earned || busyBadge === b.key}
                onClick={() => void pickBadge(b)}
                title={b.desc}
                className={`flex flex-col items-center gap-1 rounded-2xl border px-2 py-3 text-center transition active:scale-95 ${
                  active
                    ? "border-brand-400/60 bg-brand-500/15"
                    : b.earned
                      ? "border-white/10 bg-white/[0.05] hover:border-white/25"
                      : "border-white/5 bg-white/[0.02] opacity-40"
                }`}
              >
                <span className="text-2xl">{b.emoji}</span>
                <span className="text-[11px] font-medium leading-tight text-slate-300">
                  {b.title}
                </span>
                {active && (
                  <span className="text-[10px] font-semibold text-brand-300">
                    активен
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <p className="mt-2 px-1 text-xs text-slate-500">
          Нажми на полученный значок, чтобы показать его в лидерборде.
        </p>
      </section>

      <button
        className="btn-ghost mt-5 w-full animate-fade-up"
        style={{ animationDelay: "260ms" }}
        onClick={() => navigate("/leaderboard")}
      >
        🏆 Открыть лидерборд
      </button>

      <button
        className="btn-primary mt-3 w-full animate-fade-up"
        style={{ animationDelay: "300ms" }}
        onClick={() => navigate("/share")}
      >
        📤 Поделиться карточкой
      </button>

      {isDev && (
        <button
          className="mt-3 w-full rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300"
          onClick={() => {
            const v = window.prompt("DEV tg_id", String(tgId));
            const n = Number(v);
            if (Number.isFinite(n) && n > 0) setDevTgId(n);
          }}
        >
          DEV · tg_id = {tgId} · нажми, чтобы сменить
        </button>
      )}

      <button
        className="mt-3 flex w-full items-center justify-center gap-1.5 text-xs text-slate-500 transition hover:text-slate-300"
        onClick={() => void refresh()}
      >
        <RefreshIcon /> Обновить профиль
      </button>
    </div>
  );
}
