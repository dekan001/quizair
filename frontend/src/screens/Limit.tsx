import { useLocation, useNavigate } from "react-router-dom";
import type { SessionStats } from "../lib/game";
import { ShareIcon } from "../components/icons";

interface LimitState {
  topic?: string;
  title?: string;
  session?: SessionStats;
}

export function Limit() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const s = (state ?? {}) as LimitState;
  const session = s.session ?? { answered: 0, correct: 0, score: 0 };
  const title = s.title ?? s.topic ?? "квиз";
  const accuracy =
    session.answered > 0
      ? Math.round((session.correct / session.answered) * 100)
      : 0;

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-8">
      {/* трофей-герой */}
      <div className="card animate-pop relative overflow-hidden text-center">
        <div className="pointer-events-none absolute inset-x-0 -top-10 mx-auto h-40 w-40 rounded-full bg-gradient-to-br from-brand-500/30 to-fuchsia-500/20 blur-3xl" />
        <div className="relative">
          <div className="mx-auto flex h-20 w-20 animate-float items-center justify-center rounded-3xl bg-gradient-to-br from-brand-400 to-fuchsia-500 text-4xl shadow-glow-lg">
            🏆
          </div>
          <h1 className="mt-4 text-2xl font-extrabold">Сессия завершена</h1>
          <p className="mt-1 text-sm text-slate-400">
            Вопросы закончились. Забери ещё за подписки!
          </p>
        </div>
      </div>

      {/* итоги сессии */}
      <section
        className="card mt-4 animate-fade-up"
        style={{ animationDelay: "80ms" }}
      >
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Твоя сессия · {title}
        </h2>
        <div className="grid grid-cols-3 gap-3 text-center">
          <Stat label="Очки" value={session.score} accent="text-gradient" />
          <Stat
            label="Верно"
            value={`${session.correct}/${session.answered}`}
          />
          <Stat label="Точность" value={`${accuracy}%`} />
        </div>
      </section>

      <button
        className="btn-primary mt-5 w-full animate-fade-up"
        style={{ animationDelay: "140ms" }}
        onClick={() => navigate("/tasks")}
      >
        🎁 Получить слоты за подписки
      </button>

      <div className="mt-3 flex gap-2">
        <button
          className="btn-ghost flex-1"
          onClick={() => navigate("/share")}
        >
          <ShareIcon /> Пригласить
        </button>
        <button className="btn-ghost flex-1" onClick={() => navigate("/")}>
          На главную
        </button>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] py-3.5">
      <div className={`text-xl font-extrabold ${accent ?? ""}`}>{value}</div>
      <div className="mt-0.5 text-xs text-slate-400">{label}</div>
    </div>
  );
}
