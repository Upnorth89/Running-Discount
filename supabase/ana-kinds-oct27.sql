-- Oct 27: the funnel report has had NO page-load times since Oct 8. Two files set the list of events the database keeps
-- (ana-kinds-oct8.sql without 'load', ana-load-oct8.sql with it); pasted in that order, 'load' was dropped. This is the full,
-- current list from analytics.sql (tools/check.py checks the site against it). Paste in Supabase > SQL Editor > Run.
create or replace function public.ana_kinds() returns text[] language sql immutable as $$
  select array['visit','leave','scroll','welcome-view','signup-step','sizes-saved','peek-view','signup','signup-confirmed',
               'signin','resend','deal-click','watch-add','watch-remove','watchlist-open','watch-from-page','search',
               'search-none','category','type','filter','sort','menu','language','currency','share','shoe-page-link',
               'shoe-page-view','shoe-page-size','more','ref-visit','error',
               'store-offer','store-view','canadian','country',   -- Oct 8: these four were sent but dropped
               'load']   -- Oct 8: ms until the deals are on screen (detail: file|connection|page=ms|kb=size)
$$;
