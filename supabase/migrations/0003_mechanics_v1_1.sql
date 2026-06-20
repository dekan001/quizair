-- ============================================================================
-- 0003_mechanics_v1_1.sql — три механики вовлечённости (ТЗ v1.1)
-- ----------------------------------------------------------------------------
-- 1) AI-персонализация сложности: questions.difficulty -> text, users.skill_level
-- 2) Значки и статус: таблица badges, users.active_badge, поля для пушей
-- 3) Бонус «каждые 10 верных → +1»: users.correct_total
-- Идемпотентно: повторный запуск безопасен.
-- ============================================================================

-- ---- 1) difficulty: smallint(1/2/3) -> text(easy/medium/hard) --------------
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'questions'
      and column_name = 'difficulty' and data_type <> 'text'
  ) then
    alter table public.questions alter column difficulty drop default;
    alter table public.questions
      alter column difficulty type text
      using (case difficulty::text when '1' then 'easy' when '3' then 'hard' else 'medium' end);
    alter table public.questions alter column difficulty set default 'medium';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'questions_difficulty_check'
  ) then
    alter table public.questions
      add constraint questions_difficulty_check check (difficulty in ('easy','medium','hard'));
  end if;
end $$;

create index if not exists questions_topic_diff_idx
  on public.questions(topic, difficulty) where active;

-- ---- 2/3) новые поля users -------------------------------------------------
alter table public.users add column if not exists skill_level          text not null default 'easy';
alter table public.users add column if not exists answers_since_recalc int  not null default 0;
alter table public.users add column if not exists correct_total        int  not null default 0;
alter table public.users add column if not exists active_badge         text;
alter table public.users add column if not exists last_rank            int;
alter table public.users add column if not exists last_push_at         date;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'users_skill_level_check') then
    alter table public.users
      add constraint users_skill_level_check check (skill_level in ('easy','medium','hard'));
  end if;
end $$;

-- ---- значки (механика 2) ---------------------------------------------------
create table if not exists public.badges (
  user_tg_id bigint not null references public.users(tg_id) on delete cascade,
  badge_key  text   not null,
  earned_at  timestamptz not null default now(),
  primary key (user_tg_id, badge_key)
);
create index if not exists badges_user_idx on public.badges(user_tg_id);
alter table public.badges enable row level security;

-- индекс для недельного скользящего окна лидерборда/пушей
create index if not exists answers_answered_at_idx on public.answers(answered_at desc);
