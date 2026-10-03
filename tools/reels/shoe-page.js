// Reel: shoe price pages. List -> search "triumph" -> Triumph 23 page -> "Your size 10" box -> sizes table -> Watch the price
const rec=require('./rec.js');
rec('shoe-page',`(()=>{if(sessionStorage.getItem('fx'))return;sessionStorage.setItem('fx','1');
  localStorage.setItem('gf-sub',JSON.stringify({key:'00000000-0000-0000-0000-000000000000',email:'demo@thegearfox.com',active:true}));
  localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',groups:['shoes','tops','bottoms'],sizes:{shoes:{sizes:['10'],width:['Regular']},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}));
  localStorage.setItem('gf-lang','"en"');})()`,async a=>{
  const to=(sel,off,ms)=>a.pg.evaluate(([sel,off,ms])=>new Promise(r=>{const el=document.querySelector(sel);const t=document.scrollingElement,y0=t.scrollTop,y1=el.getBoundingClientRect().top+y0-off,t0=performance.now();
    (function st(n){const k=Math.min(1,(n-t0)/ms),e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;t.scrollTop=y0+(y1-y0)*e;k<1?requestAnimationFrame(st):r()})(t0)}),[sel,off,ms]);
  await a.pg.goto('https://thegearfox.com/shoes/');await a.wait(3500);          // 1. "Shoe prices by model": 380+ shoes
  await a.tap('#find',{after:300});
  for(const ch of 'triumph'){await a.pg.keyboard.type(ch);await a.wait(200)}
  await a.wait(1500);
  await a.tap(a.pg.locator('a[href="/shoes/saucony-triumph-23/"]'),{after:2500}); // 2. the Triumph 23 page
  await a.wait(1500);
  await to('#mine',90,1400);await a.wait(4500);                                   // 3. "Your size 10: $104.98 at Sporting Life"
  await a.scroll(260,1800);await a.wait(3500);                                   // 4. every size, best store for each, yours highlighted
  await to('a.watch',200,1400);await a.wait(1200);
  await a.tap('a.watch',{after:4500});                                           // 5. Watch the price -> back on the site, hearted
});
