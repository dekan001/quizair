import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type ReferralInfo } from "../lib/api";
import { useUser } from "../context/UserContext";
import { getWebApp } from "../lib/telegram";
import { ChevronLeftIcon, ShareIcon } from "../components/icons";

export function Share() {
  const navigate = useNavigate();
  const { user, tgId } = useUser();
  const [ref, setRef] = useState<ReferralInfo | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getReferral(tgId).then(setRef).catch(() => {});
  }, [tgId]);

  if (!user)
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/15 border-t-brand-400" />
      </div>
    );

  const refLink = ref?.ref_link ?? `https://t.me/QuizAIr_bot?startapp=ref_${tgId}`;

  const share = () => {
    const text =
      "Играю в QuizAIr 🧠 — квизы по ИИ, крипте, футболу и не только. Обгонишь меня?";
    const url = `https://t.me/share/url?url=${encodeURIComponent(
      refLink,
    )}&text=${encodeURIComponent(text)}`;
    const wa = getWebApp();
    if (wa?.openTelegramLink) wa.openTelegramLink(url);
    else window.open(url, "_blank");
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(refLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard может быть недоступен */
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-5">
      <header className="flex items-center gap-3">
        <button
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/10 active:scale-95"
          onClick={() => navigate(-1)}
          aria-label="Назад"
        >
          <ChevronLeftIcon />
        </button>
        <span className="text-lg font-bold">Пригласить друзей</span>
      </header>

      {/* герой */}
      <section className="card relative mt-6 animate-pop overflow-hidden text-center">
        <div className="pointer-events-none absolute inset-x-0 -top-10 mx-auto h-40 w-40 rounded-full bg-gradient-to-br from-brand-500/30 to-fuchsia-500/20 blur-3xl" />
        <div className="relative">
          <div className="mx-auto flex h-20 w-20 animate-float items-center justify-center rounded-3xl bg-gradient-to-br from-brand-400 to-fuchsia-500 text-4xl shadow-glow-lg">
            🎁
          </div>
          <h1 className="mt-4 text-2xl font-extrabold">Зови друзей</h1>
          <p className="mt-1 text-sm text-slate-400">
            За каждого друга, который сыграет 5 вопросов, —{" "}
            <span className="font-semibold text-emerald-400">+3 вопроса</span>{" "}
            тебе.
          </p>
        </div>
      </section>

      {/* реферальная ссылка */}
      <div className="card mt-4 animate-fade-up" style={{ animationDelay: "80ms" }}>
        <p className="mb-2 text-xs font-medium text-slate-500">
          Твоя реферальная ссылка
        </p>
        <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2.5">
          <span className="flex-1 truncate text-sm text-slate-200">
            {refLink}
          </span>
          <button
            onClick={() => void copy()}
            className="shrink-0 rounded-lg bg-white/10 px-3 py-1.5 text-xs font-semibold text-slate-100 transition hover:bg-white/15 active:scale-95"
          >
            {copied ? "✓ Готово" : "Копировать"}
          </button>
        </div>
      </div>

      <button
        className="btn-primary mt-4 w-full animate-fade-up"
        style={{ animationDelay: "120ms" }}
        onClick={share}
      >
        <ShareIcon /> Поделиться в Telegram
      </button>

      {ref && (
        <div
          className="card mt-4 flex animate-fade-up items-center justify-around text-center"
          style={{ animationDelay: "160ms" }}
        >
          <div>
            <div className="text-2xl font-extrabold text-gradient">
              {ref.referrals_active}
            </div>
            <div className="text-xs text-slate-400">активных</div>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div>
            <div className="text-2xl font-extrabold">{ref.referrals_total}</div>
            <div className="text-xs text-slate-400">всего друзей</div>
          </div>
        </div>
      )}
    </div>
  );
}
