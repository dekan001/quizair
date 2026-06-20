// API-клиент для бэкенда FastAPI.

const API_URL = (
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

// ------------------------ типы (зеркало Pydantic-схем бэкенда) -----------------
export interface Topic {
  slug: string;
  title: string;
  emoji: string | null;
  position: number;
}

export interface User {
  tg_id: number;
  username: string | null;
  first_name: string | null;
  photo_url: string | null;
  streak: number;
  longest_streak: number;
  daily_left: number;
  bonus_left: number;
  daily_base: number;
  total_score: number;
  skill_level: "easy" | "medium" | "hard";
  correct_total: number;
  active_badge: string | null;
}

export interface Question {
  id: number;
  topic: string;
  text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

export interface AnswerResult {
  correct: boolean;
  correct_answer: string;
  explanation: string | null;
  score_awarded: number;
  daily_left: number;
  bonus_left: number;
  streak: number;
  skill_level: "easy" | "medium" | "hard";
  level_up: boolean;
  new_badges: string[];
  active_badge: string | null;
  milestone_bonus: number;
  correct_total: number;
  limit_reached: boolean;
}

export interface LeaderboardEntry {
  tg_id: number;
  username: string | null;
  score: number;
  correct: number;
  total: number;
  active_badge: string | null;
  rank: number | null;
}

export interface LimitDetail {
  limit_reached: boolean;
  daily_left: number;
  bonus_left: number;
  message: string;
}

export interface Task {
  id: number;
  channel_username: string;
  topic: string | null;
  reward_quizzes: number;
  cpa_rate: number;
  claimed: boolean;
}

export interface ClaimResult {
  daily_left: number;
  bonus_left: number;
  reward_given: number;
}

export interface Badge {
  key: string;
  emoji: string;
  title: string;
  desc: string;
  earned: boolean;
}

export interface ReferralInfo {
  ref_link: string;
  bot_username: string;
  referrals_total: number;
  referrals_active: number;
}

// ------------------------ ошибки ----------------------------------------------
export class LimitError extends Error {
  detail: LimitDetail;
  constructor(detail: LimitDetail) {
    super("limit_reached");
    this.name = "LimitError";
    this.detail = detail;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// ------------------------ низкоуровневый запрос -------------------------------
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Не удалось связаться с сервером");
  }

  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : null;

  if (!res.ok) {
    if (res.status === 402) {
      const detail = (data && (data as { detail?: unknown }).detail) ?? data;
      throw new LimitError(detail as LimitDetail);
    }
    let msg = res.statusText;
    if (data && typeof data === "object" && "detail" in (data as object)) {
      const d = (data as { detail: unknown }).detail;
      msg = typeof d === "string" ? d : JSON.stringify(d);
    }
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

// ------------------------ публичный API ---------------------------------------
export interface CreateUserPayload {
  tg_id: number;
  username?: string | null;
  first_name?: string | null;
  photo_url?: string | null;
  referred_by?: number | null;
}

export interface AnswerPayload {
  tg_id: number;
  question_id: number;
  answer: "a" | "b" | "c" | "d";
}

export const api = {
  createUser: (p: CreateUserPayload) =>
    request<User>("/users", { method: "POST", body: JSON.stringify(p) }),
  getUser: (tgId: number) => request<User>(`/users/${tgId}`),
  getTopics: () => request<Topic[]>("/topics"),
  getQuestion: (topic: string, tgId: number) =>
    request<Question>(
      `/question?topic=${encodeURIComponent(topic)}&tg_id=${tgId}`,
    ),
  answer: (p: AnswerPayload) =>
    request<AnswerResult>("/answer", { method: "POST", body: JSON.stringify(p) }),
  leaderboard: (topic: string, tgId: number, limit = 100) =>
    request<LeaderboardEntry[]>(
      `/leaderboard?topic=${encodeURIComponent(topic)}&tg_id=${tgId}&limit=${limit}`,
    ),
  globalLeaderboard: (tgId: number, limit = 100) =>
    request<LeaderboardEntry[]>(`/leaderboard/global?tg_id=${tgId}&limit=${limit}`),
  getTasks: (tgId: number) =>
    request<Task[]>(`/tasks?tg_id=${tgId}`),
  claimTask: (partnerId: number, tgId: number) =>
    request<ClaimResult>(
      `/tasks/${partnerId}/claim?tg_id=${tgId}`,
      { method: "POST" },
    ),
  getBadges: (tgId: number) =>
    request<Badge[]>(`/badges?tg_id=${tgId}`),
  setActiveBadge: (tgId: number, badgeKey: string | null) =>
    request<User>(`/users/${tgId}/active-badge`, {
      method: "POST",
      body: JSON.stringify({ badge_key: badgeKey }),
    }),
  getReferral: (tgId: number) =>
    request<ReferralInfo>(`/users/${tgId}/referral`),
};
