// Reel: the heart pulses when a watched shoe drops, then the watchlist explains it (slow, with pauses to talk over)
const rec=require('./rec.js');const fs=require('fs');
const W=fs.readFileSync('watch.json','utf8');
rec('heart',`(()=>{if(sessionStorage.getItem('fx'))return;sessionStorage.setItem('fx','1');
  localStorage.setItem('gf-sub',JSON.stringify({key:'00000000-0000-0000-0000-000000000000',email:'demo@thegearfox.com',active:true}));
  localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',groups:['shoes','tops','bottoms','socks','packs','gear'],sizes:{shoes:{sizes:['10'],width:['Regular']},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}));
  localStorage.setItem('gf-watch',${JSON.stringify(W)});
  localStorage.setItem('gf-lang','"en"');})()`,async a=>{
  await a.pg.goto('https://thegearfox.com/');await a.wait(3200);
  await a.wait(7500);                                   // 1. the heart pulses (3 times) with its "2"
  await a.wait(3000);                                   // 2. the "Watchlist: 2 price drops" strip
  await a.tap('#openWatch',{after:3500});               // 3. the watchlist opens
  await a.wait(1500);await a.scroll(175,1500);await a.wait(4500); // 4. "Dropped $X since you saved it" + "Lowest since you started watching"
  await a.scroll(300,2200);await a.wait(4500);          // 5. the second shoe
  await a.wait(1500);
});
