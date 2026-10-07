-- Oct 8, 2026: one more event kind, 'load' (how long the deals take to show on screen). Paste in Supabase > SQL Editor > Run.
create or replace function public.ana_kinds() returns text[] language sql immutable as $$
  select array['visit','leave','scroll','welcome-view','signup-step','sizes-saved','peek-view','signup','signup-confirmed',
               'signin','resend','deal-click','watch-add','watch-remove','watchlist-open','watch-from-page','search',
               'search-none','category','type','filter','sort','menu','language','currency','share','shoe-page-link',
               'shoe-page-view','shoe-page-size','more','ref-visit','error',
               'store-offer','store-view','canadian','country','load']
$$;
