-- The Gear Fox (Nov 4, 2026): the 11:17 UTC morning timer didn't start refresh.yml today (the 08:23 night timer and the
-- 23:17 afternoon timer did, so the GitHub key in Vault works). Two parts. Paste into Supabase > SQL Editor.

-- PART 1 (read only): why didn't it fire? Copy the results back to Claude.
select j.jobname, j.schedule, j.active, d.status, d.return_message, d.start_time
from cron.job j left join cron.job_run_details d on d.jobid = j.jobid and d.start_time > now() - interval '2 days'
where j.jobname like 'gear-fox-%' or j.jobname like 'gf-%'
order by d.start_time desc nulls first limit 30;
-- GitHub's answers to the starts (Supabase keeps these ~6 hours, so this may come back empty):
select id, status_code, left(content::text, 200) as answer, created from net._http_response
where created > now() - interval '24 hours' and (status_code is null or status_code >= 300) order by created desc limit 20;

-- PART 2: a backup start at 12:47 UTC (4:47am Vancouver in winter), same function as the 11:17 one. If the morning read already
-- happened, the workflow's first step sees today's morning report and stops, so nobody gets a second health email.
select cron.unschedule(jobid) from cron.job where jobname = 'gear-fox-morning-backup';
select cron.schedule('gear-fox-morning-backup', '47 12 * * *', 'select public._gf_start_refresh()');
