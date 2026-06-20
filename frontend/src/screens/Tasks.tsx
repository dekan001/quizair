import { useCallback, useEffect, useState } from "react";
import { api, type Task } from "../lib/api";
import { useUser } from "../context/UserContext";
import { haptic } from "../lib/telegram";
import { topicTheme } from "../lib/theme";

const TOPIC_TITLE: Record<string, string> = {
  ai: "ИИ",
  crypto: "Крипто",
  psychology: "Психология",
  football: "Футбол",
  science: "Наука",
};

export function Tasks() {
  const { user, tgId, refresh } = useUser();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setTasks(await api.getTasks(tgId));
    } catch {
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, [tgId]);

  useEffect(() => {
    void load();
  }, [load]);

  const claim = async (t: Task) => {
    setBusyId(t.id);
    haptic("light");
    try {
      await api.claimTask(t.id, tgId);
      haptic("success");
      await Promise.all([load(), refresh()]);
    } catch {
      haptic("error");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-5">
      <header className="animate-fade-up">
        <h1 className="text-2xl font-extrabold">🎁 Задания</h1>
        <p className="mt-1 text-sm text-slate-400">
          Подпишись на канал и получи бонусные слоты. Они{" "}
          <span className="font-medium text-emerald-400">не сгорают</span> в конце
          дня.
        </p>
      </header>

      {/* баланс бонусов */}
      {user && (
        <div
          className="card mt-4 flex animate-fade-up items-center gap-3"
          style={{ animationDelay: "60ms" }}
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 text-xl shadow-lg">
            ⚡
          </div>
          <div>
            <p className="text-xs text-slate-400">Бонусных слотов</p>
            <p className="text-xl font-bold text-emerald-300">
              {user.bonus_left}
            </p>
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-col gap-3">
        {loading && <SkeletonList />}
        {!loading && tasks.length === 0 && (
          <p className="mt-6 text-center text-sm text-slate-500">
            Заданий пока нет.
          </p>
        )}
        {[...tasks]
          .sort((a, b) => Number(a.claimed) - Number(b.claimed))
          .map((t, i) => {
          const th = topicTheme(t.topic);
          return (
            <div
              key={t.id}
              style={{ animationDelay: `${i * 50}ms` }}
              className="card flex animate-fade-up items-center gap-3"
            >
              <div
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${th.tile} text-lg shadow-lg`}
              >
                📢
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-bold">{t.channel_username}</p>
                <p className="text-xs text-slate-400">
                  {t.topic ? TOPIC_TITLE[t.topic] ?? t.topic : "любая тема"} ·{" "}
                  <span className="text-emerald-400">+{t.reward_quizzes} слотов</span>
                </p>
              </div>
              {t.claimed ? (
                <span className="flex items-center gap-1 rounded-xl bg-emerald-500/15 px-3 py-2 text-sm font-semibold text-emerald-400">
                  ✓ Получено
                </span>
              ) : (
                <div className="flex shrink-0 flex-col gap-1.5">
                  <a
                    href={`https://t.me/${t.channel_username.replace("@", "")}`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-center text-xs font-medium text-slate-200 transition hover:bg-white/10"
                  >
                    Открыть
                  </a>
                  <button
                    disabled={busyId === t.id}
                    onClick={() => void claim(t)}
                    className="btn-primary !rounded-xl !px-3 !py-1.5 text-xs"
                  >
                    {busyId === t.id ? "…" : `+${t.reward_quizzes}`}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="mt-5 text-center text-xs text-slate-600">
        Проверка реальной подписки появится с aiogram-ботом (Этап 4). Сейчас слоты
        начисляются сразу после нажатия.
      </p>
    </div>
  );
}

function SkeletonList() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <div key={i} className="card flex items-center gap-3">
          <div className="h-11 w-11 shrink-0 animate-pulse rounded-2xl bg-white/10" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-2/3 animate-pulse rounded bg-white/10" />
            <div className="h-2.5 w-1/3 animate-pulse rounded bg-white/10" />
          </div>
        </div>
      ))}
    </>
  );
}
