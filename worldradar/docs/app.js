"use strict";
const PAGES=[["overview","總覽"],["top10","十大新聞"],["map","世界地圖"],["watch","局勢追蹤"],["economy","經濟"],["tech","科技與 AI"],["learning","每日學習"],["archive","歷史資料庫"],["settings","設定"]];
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl=u=>/^https?:\/\//i.test(u)?esc(u):"#";
let D=null,IDX=[],CUR=null;
const REGIONS=["北美洲","南美洲","歐洲","東亞","東南亞","南亞","中東","非洲","大洋洲","全球性事件"];
const pref=()=>{try{return JSON.parse(localStorage.getItem("radar-pref")||"{}")}catch(e){return{}}};
const setPref=o=>{try{localStorage.setItem("radar-pref",JSON.stringify({...pref(),...o}))}catch(e){}};

async function j(u){const r=await fetch(u,{cache:"no-cache"});if(!r.ok)throw new Error(u+" "+r.status);return r.json();}
function nav(p){$("#nav").innerHTML=PAGES.map(([k,n])=>`<a href="#${k}" ${k===p?'aria-current="page"':""}>${n}</a>`).join("");}

function card(s){
  const a=s.ai||{};
  return `<button class="card" data-id="${esc(s.id)}"><div class="meta"><span class="rank">#${s.rank}</span><span class="score ${s.score>=8?"hi":""}">${s.score}/10</span><span class="tag">${esc(s.country)}</span><span class="tag">${esc(s.category)}</span></div>
  <h3>${esc(s.title_zh||s.title)}</h3><p>${esc(a.short||(s.summary_en?"（原文，未翻譯）"+s.summary_en.slice(0,120):""))}</p>
  <div class="meta" style="margin-top:8px"><span class="${s.source_count>=2?"good":"warn"}">${esc(s.verification)}</span></div></button>`;
}
function bindCards(root,list){root.querySelectorAll(".card[data-id]").forEach(b=>b.onclick=()=>openStory(list.find(s=>s.id===b.dataset.id)));}
function sec(t,v){return v?`<div class="sec"><b>${t}</b>${esc(v)}</div>`:"";}
function openStory(s){
  if(!s)return;const a=s.ai||{};
  const cert=(a.certainty||[]).map(c=>`<div>・${esc(c.claim)}　<span class="tag">${esc(c.level)}</span></div>`).join("");
  $("#dlgBody").innerHTML=`<button class="x" onclick="document.getElementById('dlg').close()">關閉</button>
  <div class="meta"><span class="score">${s.score}/10</span><span class="tag">${esc(s.country)}</span><span class="tag">${esc(s.region)}</span><span class="tag">${esc(s.category)}</span></div>
  <h2 style="margin-top:10px;color:var(--text)">${esc(s.title_zh||s.title)}</h2><div class="meta">${esc(s.title)}</div>
  ${a.what?"":`<div class="empty" style="margin-top:12px">這則新聞尚未經過 AI 分析（未設定 AI_API_KEY 或 AI 呼叫失敗）。以下為來源原文。<p>${esc(s.summary_en)}</p></div>`}
  ${sec("重要性評分說明",a.score_reason)}${sec("發生了什麼事？",a.what)}${sec("事件背景",a.background)}${sec("為什麼重要？",a.why)}${sec("國際影響",a.international)}${sec("對台灣的影響",a.taiwan)}
  ${(a.watch||[]).length?`<div class="sec"><b>接下來觀察什麼？</b>${a.watch.map(w=>"・"+esc(w)).join("<br>")}</div>`:""}
  ${cert?`<div class="sec"><b>資訊等級</b>${cert}</div>`:""}
  ${(a.unverified_numbers||[]).length?`<div class="sec warn">⚠️ AI 摘要中的數字 ${esc(a.unverified_numbers.join("、"))} 未出現在來源摘要，請以原文為準。</div>`:""}
  <div class="sec"><b>消息來源（${esc(s.verification)}）</b>${s.sources.map(x=>`<div><a href="${safeUrl(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.name)}</a> ${esc(x.title)} ${x.url_ok===false?'<span class="bad">（連結檢查失敗）</span>':""}</div>`).join("")}</div>`;
  $("#dlg").showModal();
}
const empty=()=>`<div class="empty"><b>目前還沒有任何資料。</b><br>這個網站只顯示真實抓取的新聞。請先執行一次每日流程：在電腦終端機執行 <code>python -m worldradar.run</code>，或到 GitHub 的 Actions 頁面按「Run workflow」。</div>`;
const list=(arr)=>`<div class="list">${arr.map(x=>`<a href="${safeUrl(x.url)}" target="_blank" rel="noopener noreferrer"><span class="meta"><span class="score">${x.score}</span><span class="tag">${esc(x.country)}</span><span class="tag">${esc(x.category)}</span><span>${esc(x.source)}</span></span><br>${esc(x.title)}</a>`).join("")}</div>`;


const COORDS={"美國":[38.9,-77],"加拿大":[45.4,-75.7],"墨西哥":[19.4,-99.1],"巴西":[-15.8,-47.9],"阿根廷":[-34.6,-58.4],"委內瑞拉":[10.5,-66.9],"哥倫比亞":[4.7,-74.1],"智利":[-33.4,-70.7],"英國":[51.5,-0.1],"法國":[48.9,2.35],"德國":[52.5,13.4],"義大利":[41.9,12.5],"西班牙":[40.4,-3.7],"波蘭":[52.2,21],"歐盟":[50.85,4.35],"俄羅斯":[55.75,37.6],"烏克蘭":[50.45,30.5],"台灣":[25,121.5],"中國":[39.9,116.4],"日本":[35.7,139.7],"北韓":[39,125.75],"南韓":[37.55,127],"印尼":[-6.2,106.8],"菲律賓":[14.6,121],"越南":[21,105.85],"泰國":[13.75,100.5],"緬甸":[19.75,96.1],"新加坡":[1.35,103.8],"馬來西亞":[3.1,101.7],"印度":[28.6,77.2],"巴基斯坦":[33.7,73.05],"阿富汗":[34.5,69.2],"孟加拉":[23.8,90.4],"以色列／加薩":[31.8,35.2],"伊朗":[35.7,51.4],"沙烏地阿拉伯":[24.7,46.7],"土耳其":[39.9,32.85],"敘利亞":[33.5,36.3],"黎巴嫩":[33.9,35.5],"葉門":[15.4,44.2],"伊拉克":[33.3,44.4],"埃及":[30.05,31.25],"奈及利亞":[9.1,7.4],"衣索比亞":[9,38.75],"蘇丹":[15.6,32.5],"南非":[-25.7,28.2],"肯亞":[-1.3,36.8],"剛果":[-4.3,15.3],"澳洲":[-35.3,149.1],"紐西蘭":[-41.3,174.8]};
const CATCOL={"戰爭與軍事安全":"#ff4d4f","國際政治與外交":"#5ec2d6","全球經濟與金融":"#f5a524","國際貿易與產業":"#e8d24a","科技與人工智慧":"#9b8cff","能源與氣候":"#ff8a3d","自然災害與公共安全":"#ff6fae","醫療與公共衛生":"#3ddc84","社會與文化":"#8da2b8","科學與重大發現":"#4aa3ff"};
const off=new Set();let MAP=null;
const jit=t=>{let h=0;for(const ch of t)h=(h*31+ch.charCodeAt(0))|0;return[((h&255)/255-.5)*4,(((h>>8)&255)/255-.5)*6];};
function pts(){
  const a=D.stories.filter(s=>s.lat||s.lon).map(s=>({t:"s",s,lat:s.lat,lon:s.lon,cat:s.category,score:s.score,title:s.title_zh||s.title,country:s.country}));
  (D.extra||[]).forEach(e=>{const c=COORDS[e.country];if(c){const j=jit(e.title);a.push({t:"e",e,lat:c[0]+j[0],lon:c[1]+j[1],cat:e.category,score:e.score,title:e.title,country:e.country});}});
  return a;
}
function mapPanel(h){
  const all=pts(),cnt={};all.forEach(p=>cnt[p.cat]=(cnt[p.cat]||0)+1);
  const lay=Object.keys(CATCOL).map(c=>`<label class="lay"><input type="checkbox" value="${esc(c)}" ${off.has(c)?"":"checked"}><i style="background:${CATCOL[c]}"></i>${esc(c)}<em>${cnt[c]||0}</em></label>`).join("");
  return `<section class="panel s12"><div class="ph"><b>GLOBAL SITUATION　全球情勢地圖</b><span class="mut">大圓＝今日十大、小圓＝其他報導（位置為該國首都）。可滾輪縮放、拖曳；點圓點看內容</span></div>
  <div class="mapbox" style="--mh:${h}"><div id="map"></div><div class="layers"><b>LAYERS 圖層</b>${lay}</div><div id="tip" class="tip" hidden></div></div></section>`;
}
function loadScript(u){return new Promise((ok,no)=>{const s=document.createElement("script");s.src=u;s.onload=ok;s.onerror=no;document.head.appendChild(s);});}
async function loadLibs(){if(window.d3&&window.topojson)return;
  await loadScript("https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js");
  await loadScript("https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js");}
function sizeDots(){document.querySelectorAll("#dots circle").forEach(c=>c.setAttribute("r",c.dataset.r/MAP.k));}
function drawDots(){
  const g=$("#dots");if(!g||!MAP)return;
  const list=MAP.pts.map((p,i)=>({p,i})).filter(({p})=>!off.has(p.cat)).sort((a,b)=>(a.p.t==="s")-(b.p.t==="s"));
  g.innerHTML=list.map(({p,i})=>{const xy=MAP.proj([p.lon,p.lat]);if(!xy)return"";
    const big=p.t==="s",r=big?3+p.score*.7:2.6,c=CATCOL[p.cat]||"#8da2b8";
    return `<circle data-i="${i}" data-r="${r}" cx="${xy[0].toFixed(1)}" cy="${xy[1].toFixed(1)}" r="${(r/MAP.k).toFixed(2)}" fill="${c}" fill-opacity="${big?.55:.8}" stroke="${c}" ${big?'class="pulse"':""}/>`;}).join("");
}
function paint(){
  const host=$("#map");if(!host||!MAP)return;
  let grid="";
  if(!MAP.land){const W=MAP.W,H=MAP.H;for(let lo=-180;lo<=180;lo+=30){const x=(lo+180)/360*W;grid+=`<line x1="${x}" y1="0" x2="${x}" y2="${H}"/>`;}
    for(let la=-60;la<=60;la+=30){const y=(90-la)/180*H;grid+=`<line x1="0" y1="${y}" x2="${W}" y2="${y}"/>`;}grid=`<g class="gl">${grid}</g>`;}
  host.innerHTML=`<svg id="msvg" viewBox="0 0 ${MAP.W} ${MAP.H}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="世界新聞地圖"><g id="mg">${grid}${MAP.land}<g id="dots"></g></g></svg>`;
  drawDots();
  const svg=$("#msvg"),box=$(".mapbox");
  svg.addEventListener("mousemove",ev=>{const c=ev.target.closest("circle[data-i]"),tip=$("#tip");if(!c){tip.hidden=true;return;}
    const p=MAP.pts[+c.dataset.i],r=box.getBoundingClientRect();tip.hidden=false;
    tip.innerHTML=`<b>${esc(p.country)}</b>・${esc(p.cat)}<br>${esc(p.title)}`;
    tip.style.left=Math.max(4,Math.min(ev.clientX-r.left+12,r.width-262))+"px";tip.style.top=Math.max(4,ev.clientY-r.top+12)+"px";});
  svg.addEventListener("mouseleave",()=>{$("#tip").hidden=true;});
  svg.addEventListener("click",ev=>{const c=ev.target.closest("circle[data-i]");if(!c)return;const p=MAP.pts[+c.dataset.i];
    if(p.t==="s")openStory(p.s);else window.open(p.e.url,"_blank","noopener");});
  if(MAP.d3&&window.d3){d3.select(svg).call(d3.zoom().scaleExtent([1,10]).on("zoom",e=>{$("#mg").setAttribute("transform",e.transform.toString());MAP.k=e.transform.k;sizeDots();}));}
}
async function drawMap(){
  const host=$("#map");if(!host)return;
  const W=1000,H=500;
  MAP={k:1,pts:pts(),W,H,proj:([lo,la])=>[(lo+180)/360*W,(90-la)/180*H],land:"",d3:false};
  document.querySelectorAll(".lay input").forEach(i=>i.onchange=()=>{i.checked?off.delete(i.value):off.add(i.value);drawDots();});
  paint();
  try{
    await loadLibs();
    const topo=await (await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json")).json();
    if($("#map")!==host||!MAP)return;
    const p=d3.geoNaturalEarth1().fitSize([W,H],{type:"Sphere"}),g=d3.geoPath(p);
    MAP.proj=p;
    MAP.land=`<path class="sph" d="${g({type:"Sphere"})}"/><path class="land" d="${g(topojson.feature(topo,topo.objects.land))}"/><path class="bord" d="${g(topojson.mesh(topo,topo.objects.countries,(a,b)=>a!==b))}"/>`;
    MAP.d3=true;paint();
  }catch(e){/* 無法載入國界資料時，保留格線版地圖 */}
}
function heat(){const h={};[...D.stories.map(s=>[s.country,s.score]),...(D.extra||[]).map(e=>[e.country,e.score])].forEach(([c,v])=>{if(c&&c!=="全球")h[c]=(h[c]||0)+v;});return Object.entries(h).sort((a,b)=>b[1]-a[1]).slice(0,8);}
function dashboard(){
  const s=D.stories,ex=D.extra||[],reg={};[...s,...ex].forEach(x=>reg[x.region]=(reg[x.region]||0)+1);
  const rmax=Math.max(1,...Object.values(reg)),hs=heat(),hmax=Math.max(1,...hs.map(x=>x[1]));
  const news=s.map(x=>`<button class="row" data-id="${esc(x.id)}"><span class="score ${x.score>=8?"hi":""}">${x.score}</span><span class="tag">${esc(x.country)}</span>${esc(x.title_zh||x.title)}</button>`).join("")
   +ex.map(x=>`<a class="row" href="${safeUrl(x.url)}" target="_blank" rel="noopener noreferrer"><span class="score lo">${x.score}</span><span class="tag">${esc(x.country)}</span>${esc(x.title)} <span class="mut">${esc(x.source)}</span></a>`).join("");
  const dg=D.digest;
  const ai=dg?`<div class="brief"><p>${esc(dg.overview)}</p></div>${(dg.trends||[]).map(t=>`<div class="trend">${esc(t)}</div>`).join("")}`:`<p class="mut">今日沒有 AI 分析（未設定 AI_API_KEY，或 AI 呼叫失敗）。左側新聞流仍是真實抓取的新聞。</p>`;
  const watch=D.watch.map(w=>`<div class="wrow"><b>${esc(w.name)}</b><span class="st ${w.status.includes("有新")?"on":"off"}">${esc(w.status)}</span><br>${w.latest?`<a href="${safeUrl(w.latest.url)}" target="_blank" rel="noopener noreferrer">${esc(w.latest.title)}</a> <span class="mut">${esc(w.latest.date)}</span>`:'<span class="mut">尚無紀錄</span>'}</div>`).join("");
  const srcs=Object.entries(D.source_status).map(([k,v])=>`<span class="src ${v.ok?"ok":"bad"}">${v.ok?"●":"○"} ${esc(k)}${v.ok?" "+v.count:""}</span>`).join("");
  const k=dg&&(dg.knowledge||[])[0];
  return `<div class="strip"><span class="chip"><b>${esc(D.date)}</b></span><span class="chip">事件 <b>${D.stats.events}</b></span><span class="chip">文章 <b>${D.stats.articles}</b></span>
   <span class="chip ${D.stats.sources_ok===D.stats.sources_total?"ok":"bad"}">來源 <b>${D.stats.sources_ok}/${D.stats.sources_total}</b></span><span class="chip ${D.ai_enabled?"ok":"bad"}">AI <b>${D.ai_enabled?"ON":"OFF"}</b></span>
   ${D.shortfall_note?`<span class="chip warn">${esc(D.shortfall_note)}</span>`:""}</div>
  <div class="dash">${mapPanel("56vh")}
   <section class="panel s4"><div class="ph"><b>LIVE NEWS　新聞流</b><span class="mut">前 ${s.length} 則＝十大（可點開完整分析）</span></div><div class="pb" style="max-height:440px;padding:4px 12px">${news}</div></section>
   <section class="panel s4"><div class="ph"><b>AI INSIGHTS　AI 局勢總覽</b></div><div class="pb" style="max-height:440px">${ai}</div></section>
   <section class="panel s4"><div class="ph"><b>STRATEGIC WATCH　局勢追蹤</b><a href="#watch">全部 →</a></div><div class="pb" style="max-height:440px">${watch}</div></section>
   <section class="panel s4"><div class="ph"><b>TOP 10　今日十大</b><a href="#top10">詳細 →</a></div><div class="pb">${s.map(x=>`<button class="row" data-id="${esc(x.id)}"><span class="rank">#${x.rank}</span> <span class="score ${x.score>=8?"hi":""}">${x.score}/10</span> ${esc(x.title_zh||x.title)}<br><span class="mut">${esc(x.country)}・${esc(x.category)}・${esc(x.verification)}</span></button>`).join("")}</div></section>
   <section class="panel s4"><div class="ph"><b>COUNTRY HEAT　國家新聞熱度</b></div><div class="pb"><p class="mut" style="margin:0 0 6px">＝該國今日報導的重要性總和，不是政局不穩定指數</p>${hs.map(([c,v])=>`<div class="hrow"><span>${esc(c)}</span><span><i class="bar a" style="width:${v/hmax*100}%"></i></span><b>${v}</b></div>`).join("")}</div></section>
   <section class="panel s4"><div class="ph"><b>REGIONS 地區分布</b><span class="mut">今日報導數</span></div><div class="pb">${REGIONS.map(r=>`<div class="hrow"><span>${r}</span><span><i class="bar" style="width:${(reg[r]||0)/rmax*100}%"></i></span><b>${reg[r]||0}</b></div>`).join("")}</div></section>
   <section class="panel s6"><div class="ph"><b>DAILY LEARNING　今日知識</b><a href="#learning">更多 →</a></div><div class="pb">${k?`<b style="color:var(--amber)">${esc(k.term)}</b><p style="margin:.3em 0">${esc(k.explain)}</p>${dg.think?`<p class="mut">今日思考：${esc(dg.think)}</p>`:""}`:'<span class="mut">今日沒有 AI 產生的學習內容。</span>'}</div></section>
   <section class="panel s6"><div class="ph"><b>SOURCES　資料來源狀態</b><span class="mut">更新：${esc(D.generated_at.slice(0,16).replace("T"," "))}（台灣時間）</span></div><div class="pb">${srcs}</div></section>
  </div>`;
}

const views={
overview(){return dashboard();},
top10(){const f=pref().region||"";const s=D.stories.filter(x=>!f||x.region===f);
  return `<h1>每日十大國際新聞</h1><div class="date">${esc(D.date)}　點擊卡片閱讀完整分析</div>
  <label>地區篩選：<select id="rf"><option value="">全部</option>${REGIONS.map(r=>`<option ${r===f?"selected":""}>${r}</option>`).join("")}</select></label>
  <div class="grid" style="margin-top:12px">${s.map(card).join("")||"<p>沒有符合的新聞。</p>"}</div>`;},
map(){return `<div class="strip"><span class="chip"><b>${esc(D.date)}</b></span></div><div class="dash">${mapPanel("72vh")}</div><h2>依地區</h2>${REGIONS.map(r=>{const a=D.stories.filter(s=>s.region===r);return a.length?`<h3>${r}（${a.length}）</h3><div class="grid">${a.map(card).join("")}</div>`:""}).join("")}`;},
watch(){return `<h1>GLOBAL WATCH 國際局勢追蹤</h1><div class="date">每天更新；時間軸累積自每日資料庫，系統上線越久越完整。</div>
  ${D.watch.map(w=>`<div class="card" style="cursor:default;margin-bottom:12px"><h3>${esc(w.name)}　<span class="tag ${w.status.includes("有新")?"good":""}">${esc(w.status)}</span></h3>
  <div class="meta">首次記錄：${esc(w.first_seen||"尚無")}${w.countries.length?"｜相關國家："+esc(w.countries.join("、")):""}${w.people.length?"｜今日報導中的人物／組織："+esc(w.people.join("、")):""}</div>
  ${w.latest?`<p style="color:var(--text);margin-top:8px"><b>最新發展：</b><a href="${safeUrl(w.latest.url)}" target="_blank" rel="noopener noreferrer">${esc(w.latest.title)}</a>（${esc(w.latest.date)}）</p>`:"<p>尚無相關報導紀錄。</p>"}
  <div class="timeline">${w.timeline.map(t=>`<div>${esc(t.date)}　<a href="${safeUrl(t.url)}" target="_blank" rel="noopener noreferrer">${esc(t.title)}</a></div>`).join("")}</div></div>`).join("")}`;},
economy(){return catPage("全球經濟與金融","經濟",["全球經濟與金融","國際貿易與產業","能源與氣候"]);},
tech(){return catPage("科技與 AI","科技",["科技與人工智慧"]);},
learning(){const d=D.digest;if(!d)return `<h1>每日國際知識</h1><div class="empty">今天沒有 AI 產生的學習內容（未設定 AI_API_KEY，或 AI 呼叫失敗）。</div>`;
  const kv=(a,k,v)=>(a||[]).map(x=>`<div class="sec"><b>${esc(x[k])}</b>${esc(x[v])}</div>`).join("");
  return `<h1>DAILY LEARNING 每日國際知識</h1><div class="date">${esc(D.date)}</div><h2>三個國際知識</h2>${kv(d.knowledge,"term","explain")}<h2>三個重要人物或組織</h2>${kv(d.people_orgs,"name","explain")}<h2>三個專業詞彙</h2>${kv(d.terms,"term","explain")}
  <h2>值得思考的議題</h2><div class="lead">${esc(d.think)}</div><h2>時事測驗</h2><ol class="quiz">${(d.quiz||[]).map((q,i)=>`<li>${esc(q.q)}<br>${q.options.map((o,k)=>`<button data-q="${i}" data-k="${k}">${esc(o)}</button>`).join("")}<div class="ex" id="ex${i}"></div></li>`).join("")}</ol>`;},
archive(){return `<h1>歷史新聞資料庫</h1><div class="date">每天的十大新聞都會永久保存。點選日期載入當天內容。</div>${IDX.length?`<div class="list">${IDX.map(x=>`<a href="#archive/${x.date}"><b>${x.date}</b><br><span class="meta">${x.headlines.map(esc).join("｜")}</span></a>`).join("")}</div>`:empty()}`;},
settings(){const p=pref();return `<h1>設定</h1>
  <div class="sec"><b>預設地區篩選（十大新聞頁）</b><select id="sr"><option value="">全部</option>${REGIONS.map(r=>`<option ${r===p.region?"selected":""}>${r}</option>`).join("")}</select></div>
  <div class="sec"><b>資料更新時間</b>${esc(D?D.generated_at:"尚無資料")}</div>
  <div class="sec"><b>來源狀態</b>${D?Object.entries(D.source_status).map(([k,v])=>`<div>${v.ok?"✅":"❌"} ${esc(k)} ${v.ok?v.count+" 篇":esc(v.error||"")}</div>`).join(""):""}</div>
  <div class="sec"><b>安裝到手機主畫面</b>iPhone：用 Safari 開啟本頁 → 點下方「分享」→「加入主畫面」。Android：用 Chrome 開啟 → 右上角選單 → 「安裝應用程式」或「加到主畫面」。</div>
  ${D&&D.links.actions?`<div class="sec"><b>立即更新</b><a href="${safeUrl(D.links.actions)}" target="_blank" rel="noopener noreferrer">開啟 GitHub Actions，按「Run workflow」</a></div>`:""}`;}
};
function catPage(title,short,cats){
  const s=D.stories.filter(x=>cats.includes(x.category)),e=D.extra.filter(x=>cats.includes(x.category));
  return `<h1>${title}</h1><div class="date">${esc(D.date)}</div><h2>今日十大中的相關新聞</h2>${s.length?`<div class="grid">${s.map(card).join("")}</div>`:`<p>今日十大新聞中沒有${short}類事件。</p>`}<h2>其他${short}相關報導（僅標題，未經 AI 分析）</h2>${e.length?list(e):"<p>沒有更多相關報導。</p>"}`;
}
async function render(){
  const h=(location.hash||"#overview").slice(1),[p,arg]=h.split("/");
  const page=views[p]?p:"overview";nav(page);
  const m=$("#view");
  if(page==="archive"&&arg){
    try{const d=await j(`data/${encodeURIComponent(arg)}.json`);CUR=d;m.innerHTML=`<h1>${esc(d.date)} 十大新聞</h1><p><a href="#archive">← 回到歷史資料庫</a></p><div class="grid">${d.stories.map(card).join("")}</div>`;bindCards(m,d.stories);}catch(e){m.innerHTML=`<div class="empty">找不到 ${esc(arg)} 的資料。</div>`;}return;}
  if(!D&&page!=="settings"&&page!=="archive"){m.innerHTML=empty();return;}
  m.innerHTML=views[page]();
  m.className=(page==="overview"||page==="map")?"wide":"";
  if(D)bindCards(m,D.stories);
  m.querySelectorAll(".row[data-id]").forEach(b=>b.onclick=()=>openStory(D.stories.find(x=>x.id===b.dataset.id)));
  if(D&&(page==="overview"||page==="map"))drawMap();
  m.querySelectorAll(".dot").forEach(d=>d.onclick=()=>openStory(D.stories.find(s=>s.id===d.dataset.id)));
  const rf=$("#rf");if(rf)rf.onchange=()=>{setPref({region:rf.value});render();};
  const sr=$("#sr");if(sr)sr.onchange=()=>setPref({region:sr.value});
  m.querySelectorAll(".quiz button").forEach(b=>b.onclick=()=>{const q=D.digest.quiz[+b.dataset.q],k=+b.dataset.k,ok=k===q.answer;
    b.classList.add(ok?"right":"wrong");$("#ex"+b.dataset.q).innerHTML=`<p class="${ok?"good":"bad"}">${ok?"答對了！":"答錯了。正確答案："+esc(q.options[q.answer])}　${esc(q.explain)}</p>`;});
  m.focus();window.scrollTo(0,0);
}
setInterval(()=>{const c=document.getElementById("clock");if(c){const n=new Date();c.innerHTML=n.toISOString().slice(0,10)+" "+n.toISOString().slice(11,19)+" UTC<br>"+n.toLocaleTimeString("zh-TW",{timeZone:"Asia/Taipei",hour12:false})+" 台北";}},1000);
(async()=>{
  try{D=await j("data/latest.json");}catch(e){D=null;}
  try{IDX=await j("data/index.json");}catch(e){IDX=[];}
  window.addEventListener("hashchange",render);render();
  if("serviceWorker"in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});
})();
