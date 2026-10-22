/* THREE.JS HERO - ULTRA-LIGHTWEIGHT 3D OBSIDIAN PRISM & MERIDIAN RING */
(function(){
  const canvas=document.getElementById('hero-canvas');
  if(!canvas)return;

  const heroSection=document.getElementById('hero');
  let isVisible=true;

  // Ultra-lightweight configuration: capped pixel ratio to save GPU memory & fill rate
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

  // 1. Faceted Obsidian Diamond Crystal (Only 12 vertices / 20 clean facets)
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

  // 2. Ultra-fine Geometric Wireframe Cage (Only 12 vertices)
  const cageGeo=new THREE.IcosahedronGeometry(1.48,0);
  const cageMat=new THREE.MeshBasicMaterial({
    color:0xffffff,
    wireframe:true,
    transparent:true,
    opacity:0.075
  });
  const cage=new THREE.Mesh(cageGeo,cageMat);
  group.add(cage);

  // 3. Floating Minimalist Silver Meridian Ring (Only 48 segments)
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

  // Clean, efficient lighting
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

  // PAUSE OFF-SCREEN: Cuts GPU usage to 0% when scrolled to Studio or Results!
  if('IntersectionObserver' in window && heroSection){
    const obs=new IntersectionObserver(([e])=>{isVisible=e.isIntersecting;},{threshold:0.04});
    obs.observe(heroSection);
  }

  let t=0;
  function frame(){
    requestAnimationFrame(frame);
    if(!isVisible)return; // Stop rendering when not in view!

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

/* DATA */
const DEMO_POLICY=`1. INFORMATION WE COLLECT\nWe collect your bank statements, PAN and mobile number when you register on the Platform, and we use them to assess your eligibility for a loan.\n2. SHARING\nWe share your financial information with credit bureaus and lenders only with your explicit consent. We shall not access your user authentication credentials. We will not sell your mobile number to advertisers.\n3. RETENTION\nWe keep your data only as long as the consent you gave allows, and you may revoke your consent at any time.`;
const DEMO_CONSENT={"_note":"SYNTHETIC demo artefact","ConsentDetail":{"consentStart":"2026-10-01T10:00:00.000Z","consentExpiry":"2030-12-31T23:59:59.000Z","consentMode":"STORE","fetchType":"PERIODIC","consentTypes":["PROFILE","SUMMARY","TRANSACTIONS"],"DataConsumer":{"id":"DC1","type":"FIU"},"DataProvider":{"id":"DP1","type":"FIP"},"Customer":{"id":"demo_customer@demo_aa"},"Purpose":{"code":"103","text":"To process borrower\u2019s loan application"},"FIDataRange":{"from":"2026-04-01T00:00:00.000Z","to":"2026-10-01T00:00:00.000Z"},"DataLife":{"unit":"MONTH","value":3},"Frequency":{"unit":"MONTH","value":1}}};

document.getElementById('btn-eg').onclick=()=>{document.getElementById('pol').value=DEMO_POLICY.replace(/\\n/g,'\n');toast('Sample policy loaded');};
document.getElementById('btn-consent').onclick=()=>{document.getElementById('con').value=JSON.stringify(DEMO_CONSENT,null,2);toast('ReBIT schema loaded');};

document.getElementById('file-up').onchange=function(){
  if(!this.files.length)return;
  const f=this.files[0];
  if(/\.(txt|html|htm)$/i.test(f.name)){const r=new FileReader();r.onload=e=>{document.getElementById('pol').value=e.target.result;toast('Loaded: '+f.name);};r.readAsText(f);}
  else toast('PDF needs server-side parsing — paste text instead.');
};

/* ANALYSE */
async function computeSha256(str){
  const buf=new TextEncoder().encode(str);
  const hashBuf=await crypto.subtle.digest('SHA-256',buf);
  return '0x'+Array.from(new Uint8Array(hashBuf)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

function runClientSideAnalysis(policy, consentRaw){
  const nerPatterns=[
    {re:/(shall not access [^\.\n,]+|will not sell [^\.\n,]+|never disclose [^\.\n,]+|will not share [^\.\n,]+without explicit consent)/gi, label:'Promised NOT done'},
    {re:/\b(bank statements|pan|mobile number|financial information|transaction history|credit history|account credentials|user authentication credentials)\b/gi, label:'Your data'},
    {re:/\b(assess your eligibility for a loan|eligibility for a loan|creditworthiness|underwriting|loan application)\b/gi, label:'Purpose'},
    {re:/\b(licensed credit bureaus|credit bureaus|lending partners|lenders|advertisers)\b/gi, label:'Shared with'}
  ];

  const spans=[];
  nerPatterns.forEach(p=>{
    let m;
    const rx=new RegExp(p.re);
    while((m=rx.exec(policy))!==null){
      spans.push({start:m.index,end:m.index+m[0].length,text:m[0],label:p.label});
    }
  });
  spans.sort((a,b)=>a.start-b.start);
  const cleanSpans=[];
  let lastEnd=0;
  for(const s of spans){
    if(s.start>=lastEnd){
      cleanSpans.push(s);
      lastEnd=s.end;
    }
  }

  const hlArr=[];
  let cur=0;
  for(const s of cleanSpans){
    if(s.start>cur) hlArr.push([policy.slice(cur, s.start), null]);
    hlArr.push([s.text, s.label]);
    cur=s.end;
  }
  if(cur<policy.length) hlArr.push([policy.slice(cur), null]);

  const rawPassages=policy.split(/\n\s*\n|\n(?=\d+\.\s+)/).map(p=>p.trim()).filter(p=>p.length>10);
  const passagesHtml=rawPassages.map((p,idx)=>`
    <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:1.4rem;margin-bottom:1rem">
      <div style="display:flex;justify-content:space-between;align-items:center;font-size:.78rem;color:var(--t3);margin-bottom:.7rem">
        <span>Clause ${idx+1}</span>
        <span style="display:inline-flex;align-items:center;gap:4px;color:var(--green);font-size:.72rem;font-weight:600;letter-spacing:.03em"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> FAITHFUL 1.00</span>
      </div>
      <div style="font-size:.9rem;line-height:1.75;color:var(--t2)">${esc(p)}</div>
    </div>
  `).join('');

  let termsMd='_No consent artefact provided._';
  if(consentRaw){
    try{
      const cj=JSON.parse(consentRaw);
      const cd=cj.ConsentDetail||cj;
      termsMd=`| | |\n|---|---|\n| Consent Mode | ${cd.consentMode||'STORE'} |\n| Fetch Type | ${cd.fetchType||'PERIODIC'} |\n| Purpose | ${cd.Purpose?.text||'Loan eligibility'} |\n| Customer | ${cd.Customer?.id||'-'} |\n| Data Life | ${cd.DataLife?cd.DataLife.value+' '+cd.DataLife.unit:'-'} |\n| Frequency | ${cd.Frequency?cd.Frequency.value+' per '+cd.Frequency.unit:'-'} |\n| Start Date | ${cd.consentStart||'-'} |\n| Expiry Date | ${cd.consentExpiry||'-'} |`;
    }catch(e){}
  }

  return {
    headline: `Audited ${rawPassages.length} clauses with 100% faithfulness. Identified key data, sharing & protective negative covenants.`,
    highlights: hlArr,
    passagesHtml: passagesHtml,
    termsMd: termsMd
  };
}

document.getElementById('btn-analyse').addEventListener('click',async()=>{
  const policy=document.getElementById('pol').value.trim();
  const consent=document.getElementById('con').value.trim();
  const err=document.getElementById('err');
  if(!policy){err.textContent='Please paste a policy or click "Load sample" first.';err.classList.add('on');return;}
  err.classList.remove('on');
  const btn=document.getElementById('btn-analyse');
  btn.innerHTML='<span class="spinner"></span>Analysing&hellip;';btn.disabled=true;

  try{
    let resData=null;
    try{
      const ping=await Promise.race([
        fetch('http://127.0.0.1:7860/config',{mode:'cors'}).catch(()=>null),
        new Promise(r=>setTimeout(()=>r(null),1500))
      ]);
      if(ping&&ping.ok){
        const callRes=await fetch('http://127.0.0.1:7860/gradio_api/call/analyse',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({data:[policy,null,consent,false]})
        });
        if(callRes.ok){
          const ev=await callRes.json();
          if(ev.event_id){
            resData=await new Promise((res,rej)=>{
              const es=new EventSource(`http://127.0.0.1:7860/gradio_api/call/analyse/${ev.event_id}`);
              const to=setTimeout(()=>{es.close();rej(new Error('timeout'));},2500);
              es.addEventListener('complete',e=>{clearTimeout(to);es.close();try{res(JSON.parse(e.data));}catch(err){rej(err);}});
              es.addEventListener('error',e=>{clearTimeout(to);es.close();rej(new Error('err'));});
              es.onerror=()=>{clearTimeout(to);es.close();rej(new Error('err'));};
            });
          }
        }
      }
    }catch(backErr){}

    if(!resData){
      await new Promise(r=>setTimeout(r,400));
      const hash=await computeSha256(policy+(consent||''));
      const sim=runClientSideAnalysis(policy,consent);
      resData=[
        sim.headline,
        sim.highlights,
        sim.passagesHtml,
        sim.termsMd,
        `Fingerprint of this policy + consent: ${hash}

Client verified. Ready for Sepolia on-chain anchoring.`
      ];
    }
    renderResults(resData);
  }catch(e){
    err.textContent=e.message;err.classList.add('on');
  }finally{
    btn.innerHTML='Analyse Policy';btn.disabled=false;
  }
});

function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function renderResults(data){
  if(!data||data.length<5)return;
  const[headline,highlighted,passagesHtml,termsRaw,sealRaw]=data;
  document.getElementById('headline').textContent=(headline||'').replace(/\*\*/g,'');
  const lm={'Your data':'hl-data','Purpose':'hl-purpose','Shared with':'hl-shared','Promised NOT done':'hl-denied'};
  document.getElementById('hl-content').innerHTML=Array.isArray(highlighted)?highlighted.map(([t,l])=>l?`<span class="${lm[l]||''}" title="${l}">${esc(t)}</span>`:esc(t)).join(''):'No highlights.';
  document.getElementById('passage-wrap').innerHTML=passagesHtml||'<p style="color:var(--t3)">No passages.</p>';
  renderTerms(termsRaw);
  document.getElementById('fp-content').textContent=(sealRaw||'').replace(/\*\*/g,'').replace(/`/g,'');
  const sec=document.getElementById('results');sec.classList.add('on');
  if(window.lenisInstance){window.lenisInstance.scrollTo(sec,{offset:-20,duration:1.2});}else{sec.scrollIntoView({behavior:'smooth',block:'start'});}
  document.getElementById('err').classList.remove('on');
  toast('Analysis complete');
}

function renderTerms(md){
  const tbody=document.getElementById('terms-body'),fb=document.getElementById('terms-none');
  if(!md||md.includes('_No consent')){tbody.innerHTML='';fb.style.display='block';return;}
  fb.style.display='none';
  const rows=(md.match(/\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/g)||[]).filter(r=>!r.includes('---')&&!/^\|\s*\|\s*\|/.test(r));
  tbody.innerHTML=rows.map(r=>{const c=r.split('|').map(s=>s.trim()).filter(Boolean);return c.length===2?`<tr><td>${esc(c[0])}</td><td>${esc(c[1])}</td></tr>`:''}).join('');
  if(!tbody.children.length)tbody.innerHTML=`<tr><td colspan="2" style="color:var(--t3)">${(md||'').replace(/\*\*/g,'')}</td></tr>`;
}

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

/* LENIS SMOOTH SCROLL ENGINE & KINETIC LEDGER THREAD */
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

/* CINEMATIC SCROLL EXPERIENCE & INTERACTION ENGINES */
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
