// Цветовые темы по разделам квиза. Классы заданы литералами целиком,
// чтобы JIT Tailwind гарантированно включил их в сборку.

export interface TopicTheme {
  /** градиент плитки-иконки */
  tile: string;
  /** мягкая подсветка фона карточки */
  surface: string;
  /** цвет тени-свечения */
  shadow: string;
  /** акцентный цвет текста/цифр */
  accent: string;
}

const THEMES: Record<string, TopicTheme> = {
  ai: {
    tile: "from-indigo-400 to-violet-600",
    surface: "from-indigo-500/15",
    shadow: "shadow-indigo-500/25",
    accent: "text-indigo-300",
  },
  crypto: {
    tile: "from-amber-400 to-orange-600",
    surface: "from-amber-500/15",
    shadow: "shadow-amber-500/25",
    accent: "text-amber-300",
  },
  psychology: {
    tile: "from-fuchsia-400 to-pink-600",
    surface: "from-fuchsia-500/15",
    shadow: "shadow-fuchsia-500/25",
    accent: "text-fuchsia-300",
  },
  football: {
    tile: "from-emerald-400 to-teal-600",
    surface: "from-emerald-500/15",
    shadow: "shadow-emerald-500/25",
    accent: "text-emerald-300",
  },
  science: {
    tile: "from-sky-400 to-cyan-600",
    surface: "from-sky-500/15",
    shadow: "shadow-sky-500/25",
    accent: "text-sky-300",
  },
  history: {
    tile: "from-yellow-400 to-amber-700",
    surface: "from-yellow-500/15",
    shadow: "shadow-yellow-500/25",
    accent: "text-yellow-300",
  },
  movies: {
    tile: "from-rose-400 to-red-600",
    surface: "from-rose-500/15",
    shadow: "shadow-rose-500/25",
    accent: "text-rose-300",
  },
  music: {
    tile: "from-purple-400 to-fuchsia-600",
    surface: "from-purple-500/15",
    shadow: "shadow-purple-500/25",
    accent: "text-purple-300",
  },
  games: {
    tile: "from-lime-400 to-green-600",
    surface: "from-lime-500/15",
    shadow: "shadow-lime-500/25",
    accent: "text-lime-300",
  },
  geography: {
    tile: "from-teal-400 to-emerald-600",
    surface: "from-teal-500/15",
    shadow: "shadow-teal-500/25",
    accent: "text-teal-300",
  },
};

const DEFAULT: TopicTheme = {
  tile: "from-brand-400 to-violet-600",
  surface: "from-brand-500/15",
  shadow: "shadow-brand-500/25",
  accent: "text-brand-300",
};

export function topicTheme(slug: string | null | undefined): TopicTheme {
  return (slug && THEMES[slug]) || DEFAULT;
}
