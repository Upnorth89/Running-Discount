// Reel (French, other gear): real drops from the price history (Oct 2 -> 3): Vaporfly Next 4 -$136 at Le Coureur Nordique, Salomon S/Lab Sense 6 vest -$112. Pick new items from the history branch each time.
const rec=require('./rec.js');const fs=require('fs');
const W=fs.readFileSync('watch-fr.json','utf8');
rec('heart-fr',`(()=>{if(sessionStorage.getItem('fx'))return;sessionStorage.setItem('fx','1');
  localStorage.setItem('gf-sub',JSON.stringify({key:'00000000-0000-0000-0000-000000000000',email:'demo@thegearfox.com',active:true}));
  localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',groups:['shoes','tops','bottoms','socks','packs','gear'],sizes:{shoes:{sizes:['11'],width:['Regular']},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'fr'}));
  localStorage.setItem('gf-watch',${JSON.stringify(W)});
  localStorage.setItem('gf-lang','"fr"');})()`,async a=>{
  await a.pg.goto('https://thegearfox.com/');await a.wait(3200);
  await a.wait(7500);                                   // 1. the heart pulses (3 times) with its "2"
  await a.wait(3000);                                   // 2. the "Watchlist: 2 price drops" strip
  await a.tap('#openWatch',{after:3500});               // 3. the watchlist opens
  await a.wait(1500);await a.scroll(175,1500);await a.wait(4500); // 4. "Dropped $X since you saved it" + "Lowest since you started watching"
  const px=await a.pg.evaluate(()=>{const t=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&/S\/Lab Sense 6/.test(e.textContent))[0];let c=t;while(c&&c.parentElement&&c.getBoundingClientRect().height<200)c=c.parentElement;return Math.round(c.getBoundingClientRect().top-80)});await a.scroll(px,2400);await a.wait(4500);          // 5. the second shoe
  await a.wait(1500);
});
