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

const views={
overview(){
  const s=D.stories,reg={};s.forEach(x=>reg[x.region]=(reg[x.region]||0)+1);
  const max=Math.max(1,...Object.values(reg));
  const alerts=s.filter(x=>x.score>=8);
  return `<h1>全球情報總覽</h1><div class="date">${esc(D.date)}｜蒐集 ${D.stats.articles} 篇、合併為 ${D.stats.events} 個事件｜來源正常 ${D.stats.sources_ok}/${D.stats.sources_total}${D.ai_enabled?"":"｜<span class='warn'>未啟用 AI 分析</span>"}</div>
  <div class="lead">${esc(D.digest?D.digest.overview:"今日未啟用 AI，無法產生局勢總覽。下方為程式篩選出的十大新聞。")}</div>
  ${D.shortfall_note?`<p class="warn">${esc(D.shortfall_note)}</p>`:""}
  ${alerts.length?`<h2>全球重大事件提醒（重要性 8 分以上）</h2><div class="grid" id="g1">${alerts.map(card).join("")}</div>`:""}
  <h2>今日十大新聞</h2><div class="grid" id="g2">${s.map(card).join("")}</div>
  <h2>各地區新聞分布</h2><div class="bars">${REGIONS.map(r=>`<div><span>${r}</span><span><i class="bar" style="display:block;width:${(reg[r]||0)/max*100}%"></i></span><b>${reg[r]||0}</b></div>`).join("")}</div>
  ${D.digest&&D.digest.trends?`<h2>今日三個國際趨勢</h2>${D.digest.trends.map((t,i)=>`<p>${i+1}. ${esc(t)}</p>`).join("")}`:""}`;
},
top10(){const f=pref().region||"";const s=D.stories.filter(x=>!f||x.region===f);
  return `<h1>每日十大國際新聞</h1><div class="date">${esc(D.date)}　點擊卡片閱讀完整分析</div>
  <label>地區篩選：<select id="rf"><option value="">全部</option>${REGIONS.map(r=>`<option ${r===f?"selected":""}>${r}</option>`).join("")}</select></label>
  <div class="grid" style="margin-top:12px">${s.map(card).join("")||"<p>沒有符合的新聞。</p>"}</div>`;},
map(){
  const pts=D.stories.filter(s=>s.lat||s.lon);const X=l=>(l+180)/360*720,Y=l=>(90-l)/180*360;
  let g="";for(let lo=-180;lo<=180;lo+=30)g+=`<line x1="${X(lo)}" y1="0" x2="${X(lo)}" y2="360" stroke="#26394f"/>`;
  for(let la=-60;la<=60;la+=30)g+=`<line x1="0" y1="${Y(la)}" x2="720" y2="${Y(la)}" stroke="#26394f"/>`;
  const dots=pts.map(s=>`<g class="dot" data-id="${esc(s.id)}" style="cursor:pointer"><circle cx="${X(s.lon)}" cy="${Y(s.lat)}" r="${4+s.score}" fill="${s.score>=8?"#ef6f5e":"#f2b24b"}" fill-opacity=".55" stroke="#f2b24b"/><title>${esc(s.country)}：${esc(s.title_zh||s.title)}</title></g>`).join("");
  return `<h1>世界新聞地圖</h1><div class="date">圓點位置為新聞主要國家的首都座標，大小代表重要性；點擊可閱讀分析。未能判定國家的全球性事件不會顯示在地圖上，請見下方清單。</div>
  <svg class="map" viewBox="0 0 720 360" role="img" aria-label="世界新聞分布">${g}${dots}</svg>
  <h2>依地區</h2>${REGIONS.map(r=>{const a=D.stories.filter(s=>s.region===r);return a.length?`<h3>${r}（${a.length}）</h3><div class="grid">${a.map(card).join("")}</div>`:""}).join("")}`;},
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
  if(D)bindCards(m,D.stories);
  m.querySelectorAll(".dot").forEach(d=>d.onclick=()=>openStory(D.stories.find(s=>s.id===d.dataset.id)));
  const rf=$("#rf");if(rf)rf.onchange=()=>{setPref({region:rf.value});render();};
  const sr=$("#sr");if(sr)sr.onchange=()=>setPref({region:sr.value});
  m.querySelectorAll(".quiz button").forEach(b=>b.onclick=()=>{const q=D.digest.quiz[+b.dataset.q],k=+b.dataset.k,ok=k===q.answer;
    b.classList.add(ok?"right":"wrong");$("#ex"+b.dataset.q).innerHTML=`<p class="${ok?"good":"bad"}">${ok?"答對了！":"答錯了。正確答案："+esc(q.options[q.answer])}　${esc(q.explain)}</p>`;});
  m.focus();window.scrollTo(0,0);
}
(async()=>{
  try{D=await j("data/latest.json");}catch(e){D=null;}
  try{IDX=await j("data/index.json");}catch(e){IDX=[];}
  window.addEventListener("hashchange",render);render();
  if("serviceWorker"in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});
})();
