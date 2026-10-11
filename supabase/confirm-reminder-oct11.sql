-- Oct 11, 2026: one reminder to confirm the email (scraper/confirm_reminder.py, morning refresh). In 21 days 90 people signed up
-- and only 47 confirmed. This column records the one reminder so nobody gets two. Paste in Supabase > SQL Editor > Run.
alter table public.subscribers add column if not exists confirm_reminded_at timestamptz;
