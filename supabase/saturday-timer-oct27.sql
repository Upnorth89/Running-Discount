-- Oct 27, test 'emailday' (Bastien OK'd): half the subscribers get the weekly email Saturday 7am instead of Friday, Oct 31 - Nov 21.
-- Same timer as friday-timer.sql, on Saturdays (GitHub's own Saturday schedule is the backup). Saturday runs only send to group B;
-- outside the test dates nobody is due on a Saturday, so leaving this on costs nothing. Paste in Supabase > SQL Editor > Run.
select cron.unschedule(jobid) from cron.job where jobname = 'gear-fox-saturday-email';
select cron.schedule('gear-fox-saturday-email', '7 9-18 * * 6', 'select public._gf_start_weekly()');
