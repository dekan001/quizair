import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  api,
  LimitError,
  type AnswerResult,
  type Question,
  type Topic,
} from "../lib/api";
import { useUser } from "../context/UserContext";
import { dailyQuota, LEVEL_LABEL, BADGE_EMOJI, BADGE_TITLE, type SessionStats } from "../lib/game";
import { haptic } from "../lib/telegram";
import { topicTheme } from "../lib/theme";
import { ProgressBar } from "../components/ProgressBar";
import { ChevronLeftIcon } from "../components/icons";

type Phase = "loading" | "answering" | "result";
type Letter = "a" | "b" | "c" | "d";

const OPTIONS: Letter[] = ["a", "b", "c", "d"];

export function Quiz() {
  const { topic = "" } = useParams<{ topic: string }>();
  const navigate = useNavigate();
  const { user, tgId, refresh } = useUser();
  const th = topicTheme(topic);

  const [topicMeta, setTopicMeta] = useState<Topic | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [selected, setSelected] = useState<Letter | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [session, setSession] = useState<SessionStats>({
    answered: 0,
    correct: 0,
    score: 0,
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getTopics()
      .then((ts) => setTopicMeta(ts.find((t) => t.slug === topic) ?? null))
      .catch(() => {});
  }, [topic]);

  const goToLimit = useCallback(() => {
    navigate("/limit", { state: { topic, title: topicMeta?.title, session } });
  }, [navigate, topic, topicMeta?.title, session]);

  const loadQuestion = useCallback(async () => {
    setPhase("loading");
    setSelected(null);
    setResult(null);
    setError(null);
    try {
      const q = await api.getQuestion(topic, tgId);
      setQuestion(q);
      setPhase("answering");
    } catch (e) {
      if (e instanceof LimitError) goToLimit();
      else setError(e instanceof Error ? e.message : "Не удалось загрузить вопрос");
    }
  }, [topic, tgId, goToLimit]);

  useEffect(() => {
    void loadQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic]);

  const choose = async (letter: Letter) => {
    if (phase !== "answering" || !question) return;
    setSelected(letter);
    haptic("light");
    setPhase("result");
    try {
      const r = await api.answer({
        tg_id: tgId,
        question_id: question.id,
        answer: letter,
      });
      setResult(r);
      haptic(r.correct ? "success" : "error");
      setSession((s) => ({
        answered: s.answered + 1,
        correct: s.correct + (r.correct ? 1 : 0),
        score: s.score + r.score_awarded,
      }));
      void refresh();
    } catch (e) {
      if (e instanceof LimitError) {
        goToLimit();
        return;
      }
      setError(e instanceof Error ? e.message : "Ошибка проверки ответа");
    }
  };

  const next = () => {
    if (result?.limit_reached) {
      goToLimit();
      return;
    }
    void loadQuestion();
  };

  if (!user)
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-brand-400" />
      </div>
    );

  const dailyLeft = result?.daily_left ?? user.daily_left;
  const bonusLeft = result?.bonus_left ?? user.bonus_left;
  const left = dailyLeft + bonusLeft;
  const quota = dailyQuota(user);
  const used = Math.max(0, quota - dailyLeft);

  const optionText = (l: Letter): string => {
    switch (l) {
      case "a": return question?.option_a ?? "";
      case "b": return question?.option_b ?? "";
      case "c": return question?.option_c ?? "";
      case "d": return question?.option_d ?? "";
    }
  };

  const optionClass = (l: Letter): string => {
    if (phase !== "result" || !result) {
      return "border-white/10 bg-white/[0.05] hover:border-white/25 hover:bg-white/[0.08]";
    }
    if (l === result.correct_answer)
      return "border-emerald-400/50 bg-emerald-500/15 shadow-[0_0_24px_-6px_rgba(16,185,129,0.6)]";
    if (l === selected) return "border-rose-400/50 bg-rose-500/15";
    return "border-white/5 bg-white/[0.03] opacity-50";
  };

  const badgeClass = (l: Letter): string => {
    if (phase !== "result" || !result) return "bg-white/10 text-slate-200";
    if (l === result.correct_answer) return "bg-emerald-500 text-white";
    if (l === selected) return "bg-rose-500 text-white";
    return "bg-white/10 text-slate-400";
  };

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-5">
      {/* шапка */}
      <header className="flex items-center gap-3">
        <button
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/10 active:scale-95"
          onClick={() => navigate("/")}
          aria-label="Назад"
        >
          <ChevronLeftIcon />
        </button>
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br ${th.tile} text-xl shadow-lg`}
        >
          {topicMeta?.emoji ?? "🎯"}
        </div>
        <span className="font-bold">{topicMeta?.title ?? topic}</span>
        <span className="ml-auto flex items-center gap-1.5 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1.5 text-orange-300">
          🔥 <span className="font-bold">{user.streak}</span>
        </span>
      </header>

      {/* прогресс */}
      <div className="mt-5">
        <div className="mb-2 flex items-baseline justify-between text-sm">
          <span className="font-medium text-slate-300">
            Вопрос #{session.answered + 1}
          </span>
          <span className="text-slate-400">
            осталось <span className="font-semibold text-slate-200">{left}</span>
            {bonusLeft > 0 && (
              <span className="ml-1 text-emerald-400">(+{bonusLeft})</span>
            )}
          </span>
        </div>
        <ProgressBar value={quota === 0 ? 0 : used / quota} />
        {error && <p className="mt-2 text-sm text-rose-300">{error}</p>}
      </div>

      {/* вопрос */}
      {question && (
        <section key={question.id} className="card mt-5 animate-fade-up">
          <p className="text-lg font-semibold leading-snug">{question.text}</p>
        </section>
      )}

      {/* варианты — скрываются, как только пришёл результат */}
      {question && !result && (
        <div className="mt-3 flex flex-col gap-2.5">
          {OPTIONS.map((l, i) => (
            <button
              key={l}
              disabled={phase === "result" || phase === "loading"}
              onClick={() => void choose(l)}
              style={{ animationDelay: `${i * 50}ms` }}
              className={`flex animate-fade-up items-center gap-3 rounded-2xl border px-4 py-3.5 text-left transition-all duration-200 active:scale-[0.99] disabled:active:scale-100 ${optionClass(l)}`}
            >
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-sm font-bold uppercase transition-colors ${badgeClass(l)}`}
              >
                {l}
              </span>
              <span className="font-medium">{optionText(l)}</span>
            </button>
          ))}
        </div>
      )}

      {/* результат */}
      {phase === "result" && result && (
        <section className="card mt-4 animate-pop">
          {result.level_up && (
            <div className="mb-3 rounded-xl border border-brand-400/40 bg-brand-500/15 px-3 py-2 text-sm text-brand-200">
              🎯 Ты вырос до уровня {LEVEL_LABEL[result.skill_level ?? "easy"] ?? result.skill_level}!
            </div>
          )}
          {(result.milestone_bonus ?? 0) > 0 && (
            <div className="mb-3 rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
              +1 бонусный вопрос за 10 верных ответов!
            </div>
          )}
          {(result.new_badges ?? []).length > 0 && (
            <div className="mb-3 flex flex-col gap-1.5">
              {(result.new_badges ?? []).map((k) => (
                <div
                  key={k}
                  className="flex items-center gap-2 rounded-xl border border-amber-400/40 bg-amber-500/15 px-3 py-2 text-sm text-amber-200"
                >
                  <span className="text-xl">{BADGE_EMOJI[k] ?? "🏅"}</span>
                  <span>Новый значок: <b>{BADGE_TITLE[k] ?? k}</b></span>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-2xl">{result.correct ? "🎉" : "💭"}</span>
            <span className="text-lg font-bold">
              {result.correct ? "Верно!" : "Не угадал"}
            </span>
            {result.score_awarded > 0 && (
              <span className="ml-auto rounded-full bg-emerald-500/15 px-3 py-1 font-bold text-emerald-300">
                +{result.score_awarded}
              </span>
            )}
          </div>
          {!result.correct && (
            <div className="mt-3 rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-3 py-2.5">
              <p className="text-xs font-medium text-emerald-300/70">
                Правильный ответ
              </p>
              <p className="mt-0.5 font-medium text-emerald-100">
                {optionText(result.correct_answer as Letter)}
              </p>
            </div>
          )}
          {result.explanation && (
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              {result.correct ? "💡 " : ""}
              {result.explanation}
            </p>
          )}
          <button className="btn-primary mt-4 w-full" onClick={next}>
            {result.limit_reached ? "Итоги сессии →" : "Следующий вопрос →"}
          </button>
        </section>
      )}
    </div>
  );
}
