-- ============================================================================
-- 0001_init.sql — полная схема БД квиз-приложения
-- ----------------------------------------------------------------------------
-- Все таблицы в схеме public. RLS включён, политик НЕТ => прямой доступ через
-- anon-ключ закрыт; бэкенд работает с service_role (обходит RLS).
-- ============================================================================

create extension if not exists "pgcrypto";

-- ============================ topics ========================================
-- Справочник тем квизов. slug — ключ, используется в questions/answers.
create table if not exists public.topics (
  slug       text primary key,                 -- 'ai','crypto','psychology','football','science'
  title      text not null,                    -- отображаемое название ('ИИ')
  emoji      text,                             -- '🤖'
  cpa_low    numeric(10,2),                    -- ориентир CPA (нижняя граница, $/sub)
  cpa_high   numeric(10,2),                    -- ориентир CPA (верхняя граница)
  position   int not null default 0,           -- порядок вывода на главном экране
  active     boolean not null default true,
  created_at timestamptz not null default now()
);

-- ============================ users =========================================
-- Профиль пользователя. Ключ — Telegram id (стабильный bigint).
-- Авторизация TG проверяется бэкендом (initData), поэтому своя таблица, а не auth.users.
create table if not exists public.users (
  tg_id              bigint primary key,
  username           text,
  first_name         text,
  photo_url          text,
  -- streak
  streak             int not null default 0,
  longest_streak     int not null default 0,
  streak_anchor_date date,                     -- дата последнего «дня активности» для расчёта streak
  -- дневной лимит квизов
  daily_base         int not null default 10,  -- базовых бесплатных в день (10)
  daily_left         int not null default 10,  -- остаток ВОЗОБНОВЛЯЕМЫХ попыток (сгорают на след. день)
  bonus_left         int not null default 0,   -- купленные/бонусные слоты (за подписки, рефералку) — НЕ сгорают
  quizzes_reset_date date,                     -- когда последний раз сбрасывали дневной лимит
  -- очки
  total_score        int not null default 0,
  -- реферальная программа
  referred_by        bigint references public.users(tg_id),
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);
create index if not exists users_referred_by_idx    on public.users(referred_by);
create index if not exists users_total_score_idx    on public.users(total_score desc);
create index if not exists users_username_idx       on public.users(username);

-- ============================ questions =====================================
-- Банк вопросов (250 шт., предгенерированы). explanation_cached уже заполнен.
create table if not exists public.questions (
  id                 bigint generated always as identity primary key,
  topic              text not null references public.topics(slug),
  text               text not null,
  option_a           text not null,
  option_b           text not null,
  option_c           text not null,
  option_d           text not null,
  correct_answer     char(1) not null check (correct_answer in ('a','b','c','d')),
  explanation_cached text,                     -- кэш объяснения (Claude не вызывается повторно)
  difficulty         smallint not null default 2,  -- 1=лёгкий, 2=средний, 3=сложный
  active             boolean not null default true,
  created_at         timestamptz not null default now()
);
create index if not exists questions_topic_active_idx on public.questions(topic) where active;
-- уникальность (тема + текст) — для идемпотентного upsert при повторной загрузке вопросов
create unique index if not exists questions_topic_text_uidx on public.questions(topic, text);

-- ============================ answers =======================================
-- История ответов. topic денормализован — для быстрых выборок и leaderboard-запросов.
create table if not exists public.answers (
  id           bigint generated always as identity primary key,
  user_tg_id   bigint not null references public.users(tg_id) on delete cascade,
  question_id  bigint not null references public.questions(id) on delete cascade,
  topic        text not null references public.topics(slug),
  is_correct   boolean not null,
  answered_at  timestamptz not null default now()
);
create index if not exists answers_user_time_idx        on public.answers(user_tg_id, answered_at desc);
create index if not exists answers_user_question_idx     on public.answers(user_tg_id, question_id);
create index if not exists answers_topic_time_idx        on public.answers(topic, answered_at desc);

-- ============================ user_topic_stats ==============================
-- Агрегаты по (пользователь, тема) — основа leaderboard'ов. Обновляется триггером.
create table if not exists public.user_topic_stats (
  user_tg_id bigint not null references public.users(tg_id) on delete cascade,
  topic      text not null references public.topics(slug),
  score      int not null default 0,          -- +10 за каждый верный ответ
  correct    int not null default 0,
  total      int not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_tg_id, topic)
);
create index if not exists uts_topic_score_idx on public.user_topic_stats(topic, score desc);

-- ============================ partners ======================================
-- Партнёрские каналы для CPA-монетизации.
create table if not exists public.partners (
  id               bigint generated always as identity primary key,
  channel_username text not null,             -- '@partner_channel'
  channel_id       bigint,                    -- telegram id канала (для getChatMember)
  topic            text references public.topics(slug),  -- под какую тему офферим
  reward_quizzes   int not null default 5,    -- сколько квизов даём за подписку
  cpa_rate         numeric(10,2) not null default 0,  -- сколько платит партнёр за подписчика
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);
create index if not exists partners_topic_active_idx on public.partners(topic) where active;

-- ============================ conversions ===================================
-- Биллинг партнёров: кто из юзеров подписался на какого партнёра.
create table if not exists public.conversions (
  id           bigint generated always as identity primary key,
  user_tg_id   bigint not null references public.users(tg_id) on delete cascade,
  partner_id   bigint not null references public.partners(id) on delete restrict,
  reward_given int not null default 0,        -- сколько квизов начислили за эту конверсию
  converted_at timestamptz not null default now(),
  -- один партнёр = одна конверсия на юзера (защита от «фарма» подписок)
  unique (user_tg_id, partner_id)
);
create index if not exists conversions_partner_idx on public.conversions(partner_id);

-- ============================ referrals =====================================
-- Реферальная программа («пригласи друга → оба +3 квиза»).
create table if not exists public.referrals (
  id             bigint generated always as identity primary key,
  referrer_tg_id bigint not null references public.users(tg_id) on delete cascade,
  referred_tg_id bigint not null unique references public.users(tg_id) on delete cascade,
  reward_quizzes int not null default 3,
  rewarded       boolean not null default false,   -- выданы ли награды обеим сторонам
  created_at     timestamptz not null default now()
);
create index if not exists referrals_referrer_idx on public.referrals(referrer_tg_id);

-- ============================ streak_log ====================================
-- История стрика для экрана профиля. Одна строка = один «день удержания».
create table if not exists public.streak_log (
  user_tg_id bigint not null references public.users(tg_id) on delete cascade,
  day_date   date not null,
  kept       boolean not null default true,
  primary key (user_tg_id, day_date)
);

-- ============================================================================
-- Триггеры
-- ============================================================================

-- автообновление updated_at на users
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists users_touch_updated_at on public.users;
create trigger users_touch_updated_at
  before update on public.users
  for each row execute function public.touch_updated_at();

-- Примечание: агрегаты лидербордов (user_topic_stats, users.total_score)
-- обновляются в Python-сервисе бэкенда — единый источник правды для SQLite и Postgres.
-- БД-триггер намеренно не используется, чтобы избежать двойного счёта при switch dev→prod.

-- ============================================================================
-- Row Level Security
-- ----------------------------------------------------------------------------
-- Политик нет => через anon-ключ доступ закрыт. Чтение/запись идёт только через
-- бэкенд (FastAPI) с service_role key, который RLS обходит.
-- ============================================================================
alter table public.topics          enable row level security;
alter table public.users           enable row level security;
alter table public.questions       enable row level security;
alter table public.answers         enable row level security;
alter table public.user_topic_stats enable row level security;
alter table public.partners        enable row level security;
alter table public.conversions     enable row level security;
alter table public.referrals       enable row level security;
alter table public.streak_log      enable row level security;
