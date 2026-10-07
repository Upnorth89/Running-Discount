-- Oct 8, 2026: four kinds of events the site sends were silently dropped because they weren't on this list:
-- the come-back store bar (store-offer, store-view), the Canadian brands filter (canadian) and the Canada/USA switch (country).
-- Paste this whole file in Supabase > SQL Editor > Run. Safe to run twice.
create or replace function public.ana_kinds() returns text[] language sql immutable as $$
  select array['visit','leave','scroll','welcome-view','signup-step','sizes-saved','peek-view','signup','signup-confirmed',
               'signin','resend','deal-click','watch-add','watch-remove','watchlist-open','watch-from-page','search',
               'search-none','category','type','filter','sort','menu','language','currency','share','shoe-page-link',
               'shoe-page-view','shoe-page-size','more','ref-visit','error',
               'store-offer','store-view','canadian','country']
$$;
