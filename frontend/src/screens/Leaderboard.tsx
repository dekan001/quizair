import { useEffect, useState } from "react";
import { api, type LeaderboardEntry, type Topic } from "../lib/api";
import { useUser } from "../context/UserContext";
import { BADGE_EMOJI } from "../lib/game";

const MEDAL: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

/** Псевдо-вкладка «Общий» — суммарный рейтинг по всем темам. */
const GLOBAL = "__all__";

export function Leaderboard() {
  const { tgId } = useUser();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [active, setActive] = useState<string>(GLOBAL);
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getTopics().then(setTopics).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const req =
      active === GLOBAL
        ? api.globalLeaderboard(tgId, 100)
        : api.leaderboard(active, tgId, 100);
    req
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [active, tgId]);

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-5">
      <h1 className="animate-fade-up text-2xl font-extrabold">🏆 Лидерборд</h1>

      {/* Общий рейтинг — выделенная главная вкладка */}
      <button
        onClick={() => setActive(GLOBAL)}
        className={`mt-4 flex w-full animate-fade-up items-center gap-3 rounded-2xl border p-3 text-left transition-all duration-200 active:scale-[0.99] ${
          active === GLOBAL
            ? "border-transparent bg-gradient-to-r from-brand-500 via-violet-600 to-fuchsia-600 text-white shadow-glow-lg"
            : "border-white/10 bg-white/[0.04] text-slate-200 hover:bg-white/[0.07]"
        }`}
      >
        <span
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-2xl shadow-lg ${
            active === GLOBAL
              ? "bg-white/20"
              : "bg-gradient-to-br from-brand-400 to-fuchsia-500"
          }`}
        >
          🌍
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-bold">Общий рейтинг</span>
          <span
            className={`block text-xs ${
              active === GLOBAL ? "text-white/70" : "text-slate-400"
            }`}
          >
            Все темы · за последние 7 дней
          </span>
        </span>
        {active === GLOBAL && (
          <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-semibold">
            ТОП
          </span>
        )}
      </button>

      {/* выбор по темам */}
      <div className="mb-2 mt-5 flex items-center gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          По темам
        </span>
        <span className="h-px flex-1 bg-white/10" />
      </div>
      <div className="flex flex-wrap gap-2">
        {topics.map((t) => (
          <button
            key={t.slug}
            onClick={() => setActive(t.slug)}
            className={`chip ${
              active === t.slug
                ? "bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-glow"
                : "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
            }`}
          >
            <span>{t.emoji}</span>
            <span className="whitespace-nowrap">{t.title}</span>
          </button>
        ))}
      </div>

      {/* список */}
      <div className="mt-5 flex flex-col gap-2">
        {loading && (
          <>
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-[58px] animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
              />
            ))}
          </>
        )}
        {!loading && rows.length === 0 && (
          <div className="card mt-4 text-center">
            <div className="text-4xl">🎯</div>
            <p className="mt-2 text-sm text-slate-400">
              Пока пусто. Сыграй первым!
            </p>
          </div>
        )}
        {!loading &&
          rows.map((r, i) => {
            const rank = r.rank ?? i + 1;
            const isMe = r.tg_id === tgId;
            const acc = r.total > 0 ? Math.round((r.correct / r.total) * 100) : 0;
            return (
              <div
                key={r.tg_id}
                style={{ animationDelay: `${Math.min(i, 12) * 35}ms` }}
                className={`flex animate-fade-up items-center gap-3 rounded-2xl border px-3 py-2.5 transition ${
                  isMe
                    ? "border-brand-400/50 bg-brand-500/10 shadow-glow"
                    : "border-white/10 bg-white/[0.04]"
                }`}
              >
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-sm font-bold ${
                    rank <= 3
                      ? "bg-transparent text-lg"
                      : "bg-white/10 text-slate-300"
                  }`}
                >
                  {MEDAL[rank] ?? rank}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold">
                    {r.username ? `@${r.username}` : `id ${r.tg_id}`}
                    {r.active_badge && (
                      <span className="ml-1" title={r.active_badge}>
                        {BADGE_EMOJI[r.active_badge] ?? ""}
                      </span>
                    )}
                    {isMe && <span className="text-brand-300"> (вы)</span>}
                  </p>
                  <p className="text-xs text-slate-500">
                    {r.correct}/{r.total} верно · {acc}%
                  </p>
                </div>
                <span className="text-lg font-extrabold text-gradient">
                  {r.score}
                </span>
              </div>
            );
          })}
      </div>
    </div>
  );
}
