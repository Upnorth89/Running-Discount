// Records a phone-sized session of thegearfox.com for Instagram Reels (CDP screencast), with a finger dot on taps.
// Reels rule (Bastien, Oct 3 2026): every Reel has safe bands. Record at 360x434 (VH env, default 434), then
//   ffmpeg -f concat -safe 0 -i NAME.txt -ss 3 -vf "scale=1080:1302:flags=lanczos,pad=1080:1920:0:218:color=0x17201C,fps=30,format=yuv420p" -c:v libx264 -crf 18 OUT.mp4
// = the site in the middle, dark band 218px on top (Instagram's Reels title/camera) and 400px below (name, caption, buttons).
// Payoff first: grab the result frame as pay.png, then
//   ffmpeg -loop 1 -i pay.png -i REEL.mp4 -filter_complex "[0]crop=1080:1302:0:218,scale=2160:2604,zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih*0.55-(ih*0.55/zoom)':d=75:s=1080x1302:fps=30,trim=end_frame=75,pad=1080:1920:0:218:color=0x17201C,setsar=1,format=yuv420p[a];[1]fps=30,setsar=1,format=yuv420p[b];[a][b]concat=n=2:v=1[v]" -map "[v]" -c:v libx264 -crf 18 OUT.mp4
// Run from tools/reels: VH=434 node heart.js
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');
module.exports=async function record(name, setup, script){
  const b=await chromium.launch();
  const ctx=await b.newContext({viewport:{width:360,height:+(process.env.VH||434)},deviceScaleFactor:3,isMobile:true,hasTouch:true,
    userAgent:'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
    colorScheme:'light'});
  await ctx.route('**/*',async r=>{const u=r.request().url();
    if(u.includes('/rpc/')||u.includes('umami')||u.includes('avantlink')){try{await r.abort()}catch(_){};return}
    try{await r.fulfill({response:await r.fetch()})}catch(e){try{await r.abort()}catch(_){}}});
  if(setup)await ctx.addInitScript(setup);
  await ctx.addInitScript(()=>{addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');
    s.textContent='.fx-dot{position:fixed;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(242,106,27,.35);border:3px solid #F26A1B;pointer-events:none;z-index:99999;transition:transform .35s ease,opacity .45s ease}';
    document.head.appendChild(s)})});
  const pg=await ctx.newPage();
  const dir=`frames-${name}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir);
  const cdp=await ctx.newCDPSession(pg);const frames=[];
  cdp.on('Page.screencastFrame',async f=>{const i=frames.length;fs.writeFileSync(`${dir}/${String(i).padStart(5,'0')}.jpg`,Buffer.from(f.data,'base64'));
    frames.push(f.metadata.timestamp);try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId})}catch(e){}});
  const api={pg,
    wait:ms=>pg.waitForTimeout(ms),
    async tap(sel,opts={}){const el=typeof sel==='string'?pg.locator(sel).first():sel;await el.evaluate(e=>{const r=e.getBoundingClientRect();if(r.top<90||r.bottom>innerHeight-150)e.scrollIntoView({block:'center',behavior:'smooth'})});await pg.waitForTimeout(450);const bx=await el.boundingBox();
      const x=bx.x+bx.width*(opts.fx||.5),y=bx.y+bx.height*(opts.fy||.5);
      await pg.evaluate(([x,y])=>{const d=document.createElement('div');d.className='fx-dot';d.style.left=x+'px';d.style.top=y+'px';document.body.appendChild(d);
        setTimeout(()=>{d.style.transform='scale(1.5)';d.style.opacity='0'},350);setTimeout(()=>d.remove(),900)},[x,y]);
      await pg.waitForTimeout(250);await pg.mouse.click(x,y);await pg.waitForTimeout(opts.after||600)},
    async tapText(t,scope='body',opts){return api.tap(pg.locator(scope).getByText(t,{exact:true}).first(),opts)},
    async scroll(px,ms=1200){await pg.evaluate(([px,ms])=>new Promise(r=>{const sc=[...document.querySelectorAll('.sheet:not(.hidden) .panel, #panel')].find(e=>e.offsetParent&&e.scrollHeight>e.clientHeight+5);
      const t=sc||document.scrollingElement;const y0=t.scrollTop,t0=performance.now();
      (function st(n){const k=Math.min(1,(n-t0)/ms),e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;t.scrollTop=y0+px*e;k<1?requestAnimationFrame(st):r()})(t0)}),[px,ms]);await pg.waitForTimeout(250)}};
  await cdp.send('Page.startScreencast',{format:'jpeg',quality:92,everyNthFrame:1,maxWidth:1080,maxHeight:1920});
  await script(api);
  await cdp.send('Page.stopScreencast');await b.close();
  // frames arrive only when the screen changes: hold each one until the next, at 30 fps
  const lines=[];for(let i=0;i<frames.length;i++){const d=i+1<frames.length?frames[i+1]-frames[i]:1.0;
    lines.push(`file '${dir}/${String(i).padStart(5,'0')}.jpg'`,`duration ${Math.max(d,0.001).toFixed(4)}`)}
  lines.push(`file '${dir}/${String(frames.length-1).padStart(5,'0')}.jpg'`);
  fs.writeFileSync(`${name}.txt`,lines.join('\n'));
  console.log(name,frames.length,'frames',(frames[frames.length-1]-frames[0]).toFixed(1)+'s');
};
