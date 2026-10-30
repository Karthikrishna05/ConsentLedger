/* HERO: three.js crystal, cage and ring */
(function(){
  const canvas=document.getElementById('hero-canvas');
  if(!canvas||typeof THREE==='undefined')return;   // offline (no CDN): no 3D background, the page still works

  const heroSection=document.getElementById('hero');
  let isVisible=true;

  // Pixel ratio capped to save GPU fill rate
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 1.25));
  renderer.setClearColor(0x000000,0);

  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(40,1,0.1,50);
  camera.position.z=4.6;

  function resize(){
    if(!canvas.parentElement)return;
    const w=canvas.parentElement.offsetWidth,h=canvas.parentElement.offsetHeight;
    renderer.setSize(w,h,false);
    camera.aspect=w/h;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener('resize',resize,{passive:true});

  const group=new THREE.Group();
  scene.add(group);

  const crystalGeo=new THREE.IcosahedronGeometry(1.22,0);
  const crystalMat=new THREE.MeshPhongMaterial({
    color:0x08080a,
    emissive:0x020203,
    specular:0xd5d5db,
    shininess:110,
    flatShading:true
  });
  const crystal=new THREE.Mesh(crystalGeo,crystalMat);
  group.add(crystal);

  const cageGeo=new THREE.IcosahedronGeometry(1.48,0);
  const cageMat=new THREE.MeshBasicMaterial({
    color:0xffffff,
    wireframe:true,
    transparent:true,
    opacity:0.075
  });
  const cage=new THREE.Mesh(cageGeo,cageMat);
  group.add(cage);

  const ringGeo=new THREE.TorusGeometry(1.82,0.003,4,48);
  const ringMat=new THREE.MeshBasicMaterial({
    color:0xffffff,
    transparent:true,
    opacity:0.12
  });
  const ring=new THREE.Mesh(ringGeo,ringMat);
  ring.rotation.x=Math.PI/2.4;
  ring.rotation.y=0.25;
  group.add(ring);

  scene.add(new THREE.AmbientLight(0xffffff,0.12));
  const L1=new THREE.PointLight(0xffffff,2.5,14);
  L1.position.set(3.2,3,3.5);
  scene.add(L1);
  const L2=new THREE.PointLight(0x8e92bc,0.7,10);
  L2.position.set(-3,-2.5,-3);
  scene.add(L2);

  // Mouse tilt
  let mx=0,my=0;
  let tx=0,ty=0;
  window.addEventListener('mousemove',e=>{
    mx=(e.clientX/window.innerWidth-.5)*2;
    my=(e.clientY/window.innerHeight-.5)*2;
  },{passive:true});

  // No rendering while the hero is off-screen
  if('IntersectionObserver' in window && heroSection){
    const obs=new IntersectionObserver(([e])=>{isVisible=e.isIntersecting;},{threshold:0.04});
    obs.observe(heroSection);
  }

  let t=0;
  function frame(){
    requestAnimationFrame(frame);
    if(!isVisible)return;

    t+=0.005;
    tx+=(mx-tx)*0.05;
    ty+=(my-ty)*0.05;

    crystal.rotation.y=t*0.35+tx*0.25;
    crystal.rotation.x=t*0.18+ty*0.2;

    cage.rotation.y=-t*0.22+tx*0.2;
    cage.rotation.z=t*0.1;

    ring.rotation.z=t*0.2;

    renderer.render(scene,camera);
  }
  frame();
})();

/* REVEAL */
const rObs=new IntersectionObserver(entries=>entries.forEach((e,i)=>{if(e.isIntersecting)setTimeout(()=>e.target.classList.add('go'),i*55);}),{threshold:.08});
document.querySelectorAll('.rv').forEach(el=>rObs.observe(el));

/* 3D TILT & CARD HOVER */
document.querySelectorAll('.feat-card, .glass').forEach(c=>{
  c.addEventListener('mouseenter',()=>{c.classList.add('hovered');});
  c.addEventListener('mouseleave',()=>{c.classList.remove('hovered');c.style.transform='';});
  c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;c.style.transform=`perspective(700px) rotateX(${-y*7}deg) rotateY(${x*7}deg) translateZ(6px)`;});
});

/* TOAST */
function toast(msg,ms=3000){const el=document.getElementById('toast');el.textContent=msg;el.classList.add('on');setTimeout(()=>el.classList.remove('on'),ms);}

/* TABS */
document.querySelectorAll('.tab').forEach(tab=>{
  tab.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('on'));
    tab.classList.add('active');
    document.getElementById('pane-'+tab.dataset.pane).classList.add('on');
  });
});

/* BACKEND: same origin normally; the absolute URL covers file:// and other local dev servers.
   Every fact, verdict and fingerprint shown comes from the backend's report, never from the browser. */
const API=(location.protocol==='file:'||(location.port&&location.port!=='7860'))?'http://127.0.0.1:7860':'';
const $=id=>document.getElementById(id);
let lastReport=null,uploadFile=null,canWrite=false;

function esc(t){return String(t??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

async function api(path,opts={}){
  let res;
  try{res=await fetch(API+path,opts);}
  catch(e){throw new Error('Cannot reach the ConsentLedger backend. Start it with "python app.py" and reload this page.');}
  let body=null;
  try{body=await res.json();}catch(e){}
  if(!res.ok){
    const d=body&&body.detail;
    throw new Error(Array.isArray(d)?d.map(x=>x.msg).join('; '):(d||`The server answered ${res.status}.`));
  }
  return body;
}

async function refreshStatus(){
  const st=$('api-status'),wrap=$('rec-wrap'),rec=$('rec');
  try{
    const s=await api('/api/status');
    canWrite=!!s.chain_write;
    st.textContent=(s.models_loaded?'Backend connected · models ready':'Backend connected · models load on the first analysis')
      +(s.chain_read?' · Sepolia reachable':' · Sepolia not configured');
    st.className='api-status ok';
  }catch(e){
    canWrite=false;
    st.textContent='Backend not running: start "python app.py"';
    st.className='api-status bad';
  }
  rec.disabled=!canWrite;
  wrap.classList.toggle('off',!canWrite);
  wrap.title=canWrite?'Records the fingerprint with the server\'s test wallet (needs the consent artefact)'
                     :'Recording needs a test wallet in the server\'s .env';
  if(!canWrite)rec.checked=false;
}
refreshStatus();

/* INPUTS */
const POL_PLACEHOLDER=$('pol').placeholder;
function clearUpload(){uploadFile=null;$('file-up').value='';$('pol').placeholder=POL_PLACEHOLDER;}
// The sample comes from the backend, so it is identical to the Gradio page's example (same fingerprint).
async function loadDemo(which){
  try{
    const d=await api('/api/demo');
    if(which==='policy'){$('pol').value=d.policy;clearUpload();toast('Sample policy loaded');}
    else{$('con').value=d.consent;toast('Demo consent artefact loaded (synthetic, made-up ids)');}
  }catch(e){toast(e.message,5000);}
}
$('btn-eg').onclick=()=>loadDemo('policy');
$('btn-consent').onclick=()=>loadDemo('consent');
$('pol').addEventListener('input',()=>{if(uploadFile&&$('pol').value.trim())clearUpload();});
$('file-up').onchange=function(){
  if(!this.files.length)return;
  const f=this.files[0];
  if(/\.txt$/i.test(f.name)){
    const r=new FileReader();
    r.onload=e=>{$('pol').value=e.target.result;uploadFile=null;toast('Loaded: '+f.name);};
    r.readAsText(f);
  }else if(/\.(html?|pdf)$/i.test(f.name)){
    uploadFile=f;$('pol').value='';
    $('pol').placeholder=`${f.name} selected: the server will read it when you analyse. Type here to paste text instead.`;
    toast('Selected: '+f.name);
  }else toast('Upload a .txt, .html or .pdf file');
};

/* ANALYSE */
$('btn-analyse').addEventListener('click',async()=>{
  const policy=$('pol').value.trim(),consent=$('con').value.trim(),record=$('rec').checked,err=$('err');
  err.classList.remove('on');
  if(!policy&&!uploadFile){err.textContent='Paste a policy, click "Load sample", or upload a file first.';err.classList.add('on');return;}
  if(record&&!consent){err.textContent='Recording on Sepolia needs the consent artefact: its expiry is what the chain enforces.';err.classList.add('on');return;}
  const btn=$('btn-analyse');
  btn.innerHTML=`<span class="spinner"></span>${record?'Analysing and recording on Sepolia&hellip;':'Analysing&hellip;'}`;
  btn.disabled=true;
  try{
    let res;
    if(uploadFile&&!policy){
      const fd=new FormData();
      fd.append('file',uploadFile);fd.append('consent',consent);fd.append('record',record?'true':'false');
      res=await api('/api/analyse-file',{method:'POST',body:fd});
    }else{
      res=await api('/api/analyse',{method:'POST',headers:{'Content-Type':'application/json'},
                                    body:JSON.stringify({text:policy,consent,record})});
    }
    lastReport=res.report;
    renderResults(res);
    refreshStatus();
  }catch(e){
    err.textContent=e.message;err.classList.add('on');
  }finally{
    btn.innerHTML='Analyse Policy';btn.disabled=false;
  }
});

/* RENDER */
const LABEL={DATA_TYPE:['Your data','hl-data'],PURPOSE:['Purpose','hl-purpose'],THIRD_PARTY:['Shared with','hl-shared']};
const DENIED=['Promised NOT done','hl-denied'];
const VERDICT={show:'Summary checked',add:'Summary checked · missing facts added',reject:'Summary withheld · facts shown instead'};
const WHY={reversed:'it reversed a meaning',swapped:'it named the wrong party',invented:'it named something the passage does not'};

function highlightHtml(text,facts){
  let out='',pos=0;
  for(const f of [...facts].sort((a,b)=>a.start-b.start)){
    if(f.start<pos)continue;
    const [name,cls]=f.denied?DENIED:LABEL[f.label];
    out+=esc(text.slice(pos,f.start))+`<span class="${cls}" title="${name}">${esc(text.slice(f.start,f.end))}</span>`;
    pos=f.end;
  }
  return out+esc(text.slice(pos));
}

function factList(facts){
  if(!facts||!facts.length)return '';
  return '<ul>'+facts.map(f=>`<li><b>${esc(f.text)}</b> · ${LABEL[f.label][0].toLowerCase()}`
    +(f.denied?' · <span class="no">the policy says this is NOT done</span>':'')+'</li>').join('')+'</ul>';
}

function passagesHtml(text,passages){
  return passages.map((p,i)=>{
    let body;
    if(p.verdict==='reject'){
      const why=Object.keys(p.why_rejected||{}).map(k=>WHY[k]).filter(Boolean).join(', ');
      body=`<p><i>The automatic summary was withheld${why?' ('+why+')':''}.</i> What this passage says:</p>`
        +(factList(p.facts)||'<p>No facts were found here. Please read the passage itself.</p>');
    }else{
      body=`<div class="pcard-sum">${esc(p.summary)}</div>`
        +(p.missing&&p.missing.length?'<p>The summary leaves out:</p>'+factList(p.missing):'');
    }
    return `<div class="pcard"><div class="pcard-top"><span>Passage ${i+1}</span><span class="verdict ${p.verdict}">${VERDICT[p.verdict]}</span></div>`
      +`${body}<details><summary>Read the passage</summary><p>${esc(text.slice(p.start,p.end))}</p></details></div>`;
  }).join('')||'<p style="color:var(--t3)">No passages.</p>';
}

function termRows(c){
  if(!c)return [];
  const day=s=>(s||'?').slice(0,10),low=s=>String(s||'').toLowerCase();
  return [
    ['Who receives your data',c.RECIPIENT&&`${c.RECIPIENT.id} (${c.RECIPIENT.type}, a coded id)`],
    ['Why',c.purpose&&`${c.purpose.text} (code ${c.purpose.code})`],
    ['Consent valid',c.DURATION&&`${day(c.DURATION.start)} to ${day(c.DURATION.expiry)}`],
    ['How often data may be fetched',c.FREQUENCY&&`up to ${c.FREQUENCY.value} time(s) per ${low(c.FREQUENCY.unit)}`],
    ['Which period of your data',c.DATA_RANGE&&`${day(c.DATA_RANGE.from)} to ${day(c.DATA_RANGE.to)}`],
    ['How long they may keep it',c.DATA_LIFE&&`${c.DATA_LIFE.value} ${low(c.DATA_LIFE.unit)}(s)`],
    ['One-time or repeated',c.fetch_type],
  ];
}

function renderResults(res){
  const r=res.report;
  $('headline').textContent=(res.headline||'').replace(/\*\*/g,'');
  $('hl-content').innerHTML=highlightHtml(res.text,r.facts||[]);
  $('passage-wrap').innerHTML=passagesHtml(res.text,r.passages||[]);
  const rows=termRows(r.consent);
  $('terms-body').innerHTML=rows.map(([k,v])=>`<tr><td>${esc(k)}</td><td>${esc(v||'-')}</td></tr>`).join('');
  $('terms-none').style.display=rows.length?'none':'block';
  $('fp-content').textContent=r.record_hash;
  const ci=$('chain-info'),chk=$('btn-check-this');
  if(r.chain){
    const link=r.chain.audit_link;
    ci.innerHTML=`Recorded on Sepolia. Consent id <code>${esc(r.chain.consent_id)}</code>`
      +(link?` · <a href="${esc(link)}" target="_blank" rel="noopener">view the transaction on Etherscan</a>`:' (local test chain)');
    chk.style.display='';
  }else{
    ci.textContent='Not recorded on-chain. Tick "Record the fingerprint on the Sepolia test network" before analysing to record it.';
    chk.style.display='none';
  }
  $('btn-download').href=API+'/api/report/'+res.report_id;
  $('v-last').style.display='';
  const sec=$('results');
  sec.classList.add('on');
  sec.querySelectorAll('.rv').forEach(el=>el.classList.add('go'));
  if(window.lenisInstance){window.lenisInstance.scrollTo(sec,{offset:-20,duration:1.2});}else{sec.scrollIntoView({behavior:'smooth',block:'start'});}
  toast('Analysis complete');
}

/* VERIFY A RECORDED CONSENT */
let verifyReport=null;
function setVerifyReport(rep,label){verifyReport=rep;$('v-file-name').textContent=label;}
$('v-file').onchange=function(){
  if(!this.files.length)return;
  const f=this.files[0],rd=new FileReader();
  rd.onload=e=>{try{setVerifyReport(JSON.parse(e.target.result),f.name);}catch(x){setVerifyReport(null,'That file is not valid JSON');}};
  rd.readAsText(f);
};
$('v-last').onclick=()=>{
  if(!lastReport)return;
  setVerifyReport(lastReport,'The report from this session');
  if(lastReport.chain)$('v-cid').value=lastReport.chain.consent_id;
};
$('btn-check-this').onclick=()=>{
  $('v-last').click();
  const v=$('verify');
  if(window.lenisInstance){window.lenisInstance.scrollTo(v,{offset:-20,duration:1.2});}else{v.scrollIntoView({behavior:'smooth'});}
};
$('btn-verify').addEventListener('click',async()=>{
  const err=$('v-err'),out=$('v-result'),cid=$('v-cid').value.trim();
  err.classList.remove('on');out.classList.remove('on');
  if(!/^0x[0-9a-fA-F]{64}$/.test(cid)){err.textContent='The consent id is 0x followed by 64 hexadecimal characters.';err.classList.add('on');return;}
  if(!verifyReport){err.textContent='Choose the report file the consent came from, or use the report from this session.';err.classList.add('on');return;}
  const btn=$('btn-verify');
  btn.innerHTML='<span class="spinner"></span>Checking on Sepolia&hellip;';btn.disabled=true;
  try{
    const c=await api('/api/check',{method:'POST',headers:{'Content-Type':'application/json'},
                                    body:JSON.stringify({consent_id:cid,report:verifyReport})});
    const v=$('v-verdict');
    v.textContent=c.valid?'VALID':'NOT VALID';
    v.className='v-verdict '+(c.valid?'ok':'bad');
    const rows=[
      ['Status on-chain',c.status],
      ['This record matches the one registered',c.hash_matches?'yes':'NO: the record was changed'],
      ['Expired',c.expired?'yes':'no'],
      ['Owner',c.owner],
      ['Network',c.chain_id===11155111?'Sepolia (11155111)':c.chain_id],
    ];
    $('v-body').innerHTML=rows.map(([k,x])=>`<tr><td>${esc(k)}</td><td>${esc(x)}</td></tr>`).join('');
    out.classList.add('on');
  }catch(e){
    err.textContent=e.message;err.classList.add('on');
  }finally{
    btn.innerHTML='Check on Sepolia';btn.disabled=false;
  }
});

const copyFpBtn=document.getElementById('btn-copy-fp');
if(copyFpBtn){
  copyFpBtn.onclick=()=>{
    const t=document.getElementById('fp-content').textContent;
    const m=t.match(/0x[a-fA-F0-9]{64}/);
    navigator.clipboard.writeText(m?m[0]:t);
    toast('Fingerprint copied to clipboard');
  };
}

document.getElementById('btn-reset').onclick=()=>{
  document.getElementById('results').classList.remove('on');
  const ana=document.getElementById('analyse');
  if(window.lenisInstance){window.lenisInstance.scrollTo(ana,{offset:-20,duration:1.2});}else{ana.scrollIntoView({behavior:'smooth'});}
};

/* SMOOTH SCROLL (Lenis) AND LEDGER BUS */
let lenis=null;
try{
  if(typeof Lenis!=='undefined'){
    lenis=new Lenis({
      duration:1.2,
      easing:(t)=>Math.min(1,1.001-Math.pow(2,-10*t)),
      orientation:'vertical',
      gestureOrientation:'vertical',
      smoothWheel:true,
      wheelMultiplier:0.92,
      touchMultiplier:1.6,
      infinite:false
    });
    window.lenisInstance=lenis;
    function lenisRaf(time){lenis.raf(time);requestAnimationFrame(lenisRaf);}
    requestAnimationFrame(lenisRaf);
  }
}catch(e){console.warn('Lenis init:',e);}

document.querySelectorAll('a[href^="#"]').forEach(anchor=>{
  anchor.addEventListener('click',function(e){
    const targetId=this.getAttribute('href');
    if(!targetId||targetId==='#')return;
    const targetEl=document.querySelector(targetId);
    if(targetEl){
      e.preventDefault();
      if(lenis){lenis.scrollTo(targetEl,{offset:-25,duration:1.25});}else{targetEl.scrollIntoView({behavior:'smooth'});}
    }
  });
});

[
  {id:'wp-0',sel:'#hero'},
  {id:'wp-1',sel:'#features'},
  {id:'wp-2',sel:'#analyse'},
  {id:'wp-3',sel:'#results'}
].forEach(wp=>{
  const el=document.getElementById(wp.id);
  if(!el)return;
  el.addEventListener('click',()=>{
    let target=document.querySelector(wp.sel);
    if(wp.sel==='#results'&&(!target||!target.classList.contains('on'))){
      target=document.querySelector('#analyse');
    }
    if(target){
      if(lenis){lenis.scrollTo(target,{offset:-20,duration:1.25});}else{target.scrollIntoView({behavior:'smooth'});}
    }
  });
});

(function initLedgerThread(){
  const activePath=document.getElementById('active-path');
  const activeHaloPath=document.getElementById('active-halo-path');
  const tracerGlow=document.getElementById('tracer-glow');
  const tracerReticle=document.getElementById('tracer-reticle');
  const tracerCore=document.getElementById('tracer-core');
  if(!activePath||!tracerGlow||!tracerCore)return;

  const totalLength=activePath.getTotalLength();
  activePath.style.strokeDasharray=`${totalLength} ${totalLength}`;
  activePath.style.strokeDashoffset=`${totalLength}`;
  if(activeHaloPath){
    activeHaloPath.style.strokeDasharray=`${totalLength} ${totalLength}`;
    activeHaloPath.style.strokeDashoffset=`${totalLength}`;
  }

  const waypoints=[
    {el:document.getElementById('wp-0'),target:document.getElementById('hero')},
    {el:document.getElementById('wp-1'),target:document.getElementById('features')},
    {el:document.getElementById('wp-2'),target:document.getElementById('analyse')},
    {el:document.getElementById('wp-3'),target:document.getElementById('results')}
  ];

  function updateThread(){
    const scrollY=window.scrollY||window.pageYOffset||0;
    const maxScroll=Math.max(1,document.documentElement.scrollHeight-window.innerHeight);
    const progress=Math.max(0,Math.min(1,scrollY/maxScroll));

    const pctEl=document.getElementById('hud-pct');
    if(pctEl){
      const pct=Math.round(progress*100);
      pctEl.textContent=(pct<10?'00':pct<100?'0':'')+pct+'%';
    }

    const curOffset=totalLength*(1-progress);
    activePath.style.strokeDashoffset=curOffset;
    if(activeHaloPath)activeHaloPath.style.strokeDashoffset=curOffset;

    const pt=activePath.getPointAtLength(totalLength*progress);
    if(pt){
      tracerGlow.setAttribute('cx',pt.x);
      tracerGlow.setAttribute('cy',pt.y);
      tracerCore.setAttribute('cx',pt.x);
      tracerCore.setAttribute('cy',pt.y);
      if(tracerReticle){
        tracerReticle.setAttribute('cx',pt.x);
        tracerReticle.setAttribute('cy',pt.y);
      }
    }

    const vh=window.innerHeight;
    const viewCenter=scrollY+vh*0.45;

    let activeIdx=0;
    waypoints.forEach((wp,idx)=>{
      if(!wp.target)return;
      const top=wp.target.offsetTop;
      const height=wp.target.offsetHeight||400;
      const isResults=wp.target.id==='results';
      const isResultsOn=isResults&&wp.target.classList.contains('on');

      if(isResults&&!isResultsOn){
        if(progress>0.92)activeIdx=3;
      }else if(viewCenter>=top&&viewCenter<top+height){
        activeIdx=idx;
      }else if(idx===3&&progress>0.94){
        activeIdx=3;
      }
    });

    waypoints.forEach((wp,idx)=>{
      if(!wp.el)return;
      wp.el.classList.toggle('active',idx===activeIdx);
      wp.el.classList.toggle('passed',idx<activeIdx);
    });
  }

  if(lenis){lenis.on('scroll',updateThread);}
  window.addEventListener('scroll',updateThread,{passive:true});
  window.addEventListener('resize',updateThread);
  setTimeout(updateThread,150);
})();

/* SCROLL EFFECTS */
if('scrollRestoration' in history){history.scrollRestoration='manual';}
const heroInner=document.querySelector('.hero-inner');
const heroCanvas=document.getElementById('hero-canvas');
function applySpatialHeroDepth(scrollY){
  if(!heroInner)return;
  if(scrollY<=380){
    heroInner.style.transform='';
    heroInner.style.filter='';
    heroInner.style.opacity='1';
    if(heroCanvas){
      heroCanvas.style.opacity='1';
      heroCanvas.style.transform='';
    }
    return;
  }
  const p=Math.min(1,Math.max(0,(scrollY-380)/470));
  const easeP=p*p;
  const blur=easeP*8;
  const scale=1-(easeP*0.06);
  const y=easeP*50;
  const op=Math.max(0,1-easeP);
  const rot=easeP*2.5;
  heroInner.style.transform=`perspective(1000px) translateY(${y.toFixed(1)}px) scale(${scale.toFixed(3)}) rotateX(${rot.toFixed(2)}deg)`;
  heroInner.style.filter=blur>0.2?`blur(${blur.toFixed(1)}px)`:'';
  heroInner.style.opacity=op.toFixed(3);
  if(heroCanvas){
    heroCanvas.style.opacity=Math.max(0,1-easeP*0.8).toFixed(3);
    heroCanvas.style.transform=`scale(${(1-easeP*0.06).toFixed(3)})`;
  }
}

class CipherScramble{
  constructor(el){
    this.el=el;
    this.finalText=el.getAttribute('data-cipher')||el.innerText.trim();
    this.chars='01§7FλØ&%#*/\X89_+=';
    this.done=false;
  }
  scramble(){
    if(this.done)return;
    this.done=true;
    this.el.classList.add('decoding');
    let iter=0;
    const total=this.finalText.length;
    const timer=setInterval(()=>{
      this.el.innerText=this.finalText.split('').map((ch,idx)=>{
        if(idx<iter)return this.finalText[idx];
        if(ch===' ')return ' ';
        return this.chars[Math.floor(Math.random()*this.chars.length)];
      }).join('');
      if(iter>=total){
        clearInterval(timer);
        this.el.innerText=this.finalText;
        this.el.classList.remove('decoding');
      }
      iter+=1/3;
    },32);
  }
}

const cipherObserver=new IntersectionObserver((entries,obs)=>{
  entries.forEach(entry=>{
    if(entry.isIntersecting){
      new CipherScramble(entry.target).scramble();
      obs.unobserve(entry.target);
    }
  });
},{threshold:0.25});
document.querySelectorAll('.cipher-text').forEach(el=>cipherObserver.observe(el));

const scrubElements=[];
document.querySelectorAll('.scrub-text').forEach(p=>{
  const words=p.innerText.trim().split(/\s+/);
  p.innerHTML=words.map(w=>`<span class="scrub-word">${w} </span>`).join('');
  const spans=Array.from(p.querySelectorAll('.scrub-word'));
  scrubElements.push({el:p,spans});
});

function updateScrubbedWords(){
  const vh=window.innerHeight;
  scrubElements.forEach(({el,spans})=>{
    const rect=el.getBoundingClientRect();
    const start=vh*0.88;
    const end=vh*0.28;
    const progress=Math.min(1,Math.max(0,(start-rect.top)/(start-end)));
    const activeCount=Math.floor(progress*spans.length);
    spans.forEach((span,idx)=>{
      span.classList.toggle('active',idx<=activeCount);
    });
  });
}

const interactiveCards=Array.from(document.querySelectorAll('.feat-card,.glass'));
function updateCardTilt(){
  const vh=window.innerHeight;
  const viewCenter=vh*0.5;
  interactiveCards.forEach(card=>{
    const rect=card.getBoundingClientRect();
    const cardCenter=rect.top+rect.height*0.5;
    const distFromCenter=cardCenter-viewCenter;
    if(rect.top<vh&&rect.bottom>0){
      card.classList.add('in-view');
      const tiltX=Math.max(-4.5,Math.min(4.5,(distFromCenter/vh)*7));
      card.style.transform=`perspective(1000px) rotateX(${-tiltX.toFixed(2)}deg)`;
    }else{
      card.classList.remove('in-view');
    }
  });
}

const sectionsToSkew=document.querySelectorAll('.sec,.stats-strip');
let currentSkew=0;
function applyInertiaSkew(velocity){
  const targetSkew=Math.max(-1.2,Math.min(1.2,(velocity||0)*0.03));
  currentSkew+=(targetSkew-currentSkew)*0.18;
  if(Math.abs(currentSkew)>0.01){
    sectionsToSkew.forEach(sec=>{
      sec.style.transform=`skewY(${currentSkew.toFixed(3)}deg)`;
    });
  }else{
    sectionsToSkew.forEach(sec=>{
      sec.style.transform='';
    });
  }
}

function onScrollFrame(e){
  const sy=window.scrollY||window.pageYOffset||0;
  applySpatialHeroDepth(sy);
  updateScrubbedWords();
  updateCardTilt();
  if(e&&typeof e.velocity==='number'){
    applyInertiaSkew(e.velocity);
  }
}

if(lenis){lenis.on('scroll',onScrollFrame);}
window.addEventListener('scroll',()=>onScrollFrame({velocity:0}),{passive:true});
setTimeout(()=>onScrollFrame({velocity:0}),100);

window.addEventListener('scroll',()=>{document.getElementById('nav').style.borderBottomColor=scrollY>60?'rgba(255,255,255,.1)':'rgba(255,255,255,.04)';});
setTimeout(()=>document.querySelectorAll('#hero .rv').forEach((el,i)=>setTimeout(()=>el.classList.add('go'),200+i*130)),100);

/* LEDGER BUS LABELS: shown only while scrolling (see style.css) */
(function(){
  const wrap=document.getElementById('ledger-thread-wrap');
  if(!wrap)return;
  let idle;
  window.addEventListener('scroll',()=>{
    wrap.classList.add('scrolling');
    clearTimeout(idle);
    idle=setTimeout(()=>wrap.classList.remove('scrolling'),900);
  },{passive:true});
})();
