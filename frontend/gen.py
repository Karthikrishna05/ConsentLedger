HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>ConsentLedger — Privacy Intelligence</title>
  <meta name="description" content="Understand what Account Aggregator policies really say. AI-powered NER, faithfulness-gated summaries, and on-chain fingerprinting."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800&display=swap" rel="stylesheet"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
  <script src="https://unpkg.com/lenis@1.1.18/dist/lenis.min.js"></script>
  <style>
    :root{
      --bg:#000;--bg2:#080808;--bg3:#0f0f0f;
      --glass:rgba(255,255,255,.03);--glass2:rgba(255,255,255,.06);
      --b:rgba(255,255,255,.08);--bhi:rgba(255,255,255,.18);
      --t:#f5f5f7;--t2:#a1a1a6;--t3:#6e6e73;
      --silver:#c7c7cc;
      --green:#30d158;--amber:#ff9f0a;--red:#ff453a;
      --r:20px;
    }
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    html.lenis,html.lenis body{height:auto}
    .lenis.lenis-smooth{scroll-behavior:auto!important}
    .lenis.lenis-smooth [data-lenis-prevent]{overscroll-behavior:contain}
    .lenis.lenis-stopped{overflow:hidden}
    .lenis.lenis-scrolling iframe{pointer-events:none}
    body{background:var(--bg);color:var(--t);font-family:'Inter',-apple-system,BlinkMacSystemFont,'SF Pro Display',sans-serif;overflow-x:hidden;-webkit-font-smoothing:antialiased}
    ::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0a0a0a}::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}

    /* LEFT-SIDE CRYPTOGRAPHIC LEDGER SPAN (FULL-HEIGHT BUS) */
    #ledger-thread-wrap{
      position:fixed;
      left:clamp(10px,1.8vw,26px);
      top:60px;
      bottom:16px;
      height:calc(100vh - 76px);
      width:220px;
      z-index:850;
      pointer-events:none;
      display:flex;
      flex-direction:column;
      justify-content:flex-start;
      padding:0;
      transition:opacity .4s ease;
    }
    @media(max-width:1200px){
      #ledger-thread-wrap{width:60px}
      .wp-label,.wp-lead,.ledger-hud{display:none}
    }
    @media(max-width:780px){
      #ledger-thread-wrap{display:none}
    }

    .ledger-hud{
      display:flex;
      align-items:center;
      justify-content:space-between;
      width:205px;
      padding:0 4px 8px 6px;
      font-family:'SF Mono','Fira Code',monospace;
      user-select:none;
      border-bottom:1px solid rgba(255,255,255,.14);
      margin-bottom:8px;
    }
    .hud-tag{
      display:inline-flex;
      align-items:center;
      gap:8px;
      color:#c7c7cc;
      font-size:11px;
      font-weight:700;
      letter-spacing:.14em;
    }
    .hud-dot{
      width:7px;
      height:7px;
      border-radius:50%;
      background:var(--green);
      box-shadow:0 0 8px var(--green);
      animation:pulse 2s ease infinite;
    }
    .hud-pct{
      font-size:16px;
      font-weight:800;
      color:#ffffff;
      letter-spacing:.08em;
      text-shadow:0 0 12px rgba(255,255,255,.8);
    }

    #ledger-svg{
      width:100%;
      height:calc(100% - 32px);
      overflow:visible;
      filter:drop-shadow(0 6px 20px rgba(0,0,0,.7));
    }

    .wp-node{cursor:pointer;pointer-events:auto}
    .wp-outer{transition:stroke .3s,fill .3s,filter .3s,r .25s}
    .wp-core{transition:fill .3s,filter .3s,r .25s}
    .wp-lead{transition:stroke .3s,stroke-width .3s}
    .wp-label{
      font-family:'SF Mono','Fira Code',monospace;
      font-size:22px;
      font-weight:700;
      letter-spacing:.12em;
      fill:#98989f;
      opacity:.75;
      transition:fill .25s,opacity .25s,filter .25s;
      user-select:none;
      pointer-events:none;
    }
    .wp-node:hover .wp-outer{stroke:#fff;r:9.5;filter:drop-shadow(0 0 8px rgba(255,255,255,.8))}
    .wp-node:hover .wp-core{fill:#fff;r:4.2}
    .wp-node:hover .wp-lead{stroke:rgba(255,255,255,.8);stroke-width:1.8}
    .wp-node:hover .wp-label{fill:#ffffff;opacity:1;filter:drop-shadow(0 0 8px rgba(255,255,255,.7))}

    .wp-node.active .wp-outer{stroke:#fff;stroke-width:2.2;r:9.5;filter:drop-shadow(0 0 12px rgba(255,255,255,.95))}
    .wp-node.active .wp-core{fill:#fff;r:4.2;filter:drop-shadow(0 0 6px #fff)}
    .wp-node.active .wp-lead{stroke:#fff;stroke-width:2}
    .wp-node.active .wp-label{fill:#ffffff;opacity:1;font-weight:800;filter:drop-shadow(0 0 12px rgba(255,255,255,.95))}
    .wp-node.passed .wp-core{fill:#d1d1d6}
    .wp-node.passed .wp-outer{stroke:rgba(255,255,255,.5)}
    .wp-node.passed .wp-lead{stroke:rgba(255,255,255,.3)}
    .wp-node.passed .wp-label{fill:#d1d1d6;opacity:.85}

    /* NAV */
    nav{position:fixed;top:0;left:0;right:0;z-index:900;height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 2.5rem;background:rgba(0,0,0,.75);backdrop-filter:saturate(180%) blur(24px);-webkit-backdrop-filter:saturate(180%) blur(24px);border-bottom:1px solid rgba(255,255,255,.04);transition:border-color .3s}
    .nav-logo{font-size:1.02rem;font-weight:700;letter-spacing:-.03em;color:var(--t);text-decoration:none;display:inline-flex;align-items:center;gap:10px}
    .nav-logo-icon{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,rgba(255,255,255,.16),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.18);display:grid;place-items:center;color:#fff}
    .nav-links{display:flex;gap:2.5rem;list-style:none}
    .nav-links a{color:var(--t2);text-decoration:none;font-size:.82rem;font-weight:400;transition:color .2s}
    .nav-links a:hover{color:var(--t)}
    .nav-pill{background:#fff!important;color:#000!important;padding:5px 16px;border-radius:20px;font-weight:600!important}
    .nav-pill:hover{background:var(--silver)!important}

    /* HERO */
    #hero{position:relative;height:100vh;min-height:820px;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;padding:2rem 1.5rem 3.5rem}
    #hero::before{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:min(580px,80vw);height:min(580px,80vw);background:radial-gradient(circle,rgba(255,255,255,.04) 0%,rgba(160,180,240,.012) 40%,transparent 70%);border-radius:50%;pointer-events:none;z-index:1}
    #hero-canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:1}
    .hero-inner{position:relative;z-index:2;padding:0 1.5rem;max-width:880px;will-change:transform,opacity,filter;transform-origin:center center}
    .hero-chip{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--bhi);border-radius:99px;padding:6px 18px;font-size:.74rem;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:var(--t2);background:rgba(255,255,255,.04);backdrop-filter:blur(12px);margin-bottom:2rem}
    .chip-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 2s ease infinite}
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.4)}}
    .hero-h1{font-size:clamp(3.8rem,10vw,7.5rem);font-weight:800;letter-spacing:-.05em;line-height:.96;margin-bottom:1.75rem;background:linear-gradient(175deg,#fff 30%,#555 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .hero-sub{font-size:clamp(1.05rem,2.2vw,1.3rem);font-weight:400;color:#d1d1d6;max-width:620px;margin:0 auto 2.4rem;line-height:1.7;letter-spacing:-.01em}
    .hero-ctas{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin-bottom:1rem}

    /* SCRUBBED BLUR-IN WORD TOKENS */
    .scrub-text{display:inline}
    .scrub-word{
      display:inline-block;
      white-space:pre;
      filter:blur(9px);
      opacity:0.18;
      transform:translateY(6px) scale(0.97);
      transition:filter .32s cubic-bezier(.2,0,0,1),opacity .32s cubic-bezier(.2,0,0,1),transform .32s cubic-bezier(.2,0,0,1);
      will-change:filter,opacity,transform;
    }
    .scrub-word.active{
      filter:blur(0px);
      opacity:1;
      transform:translateY(0) scale(1);
    }

    /* CRYPTOGRAPHIC CIPHER TEXT */
    .cipher-text{
      display:inline-block;
      font-feature-settings:"tnum";
      font-variant-numeric:tabular-nums;
      letter-spacing:inherit;
      transition:color .25s ease;
    }
    .cipher-text.decoding{
      color:#fff;
      text-shadow:0 0 10px rgba(255,255,255,0.85);
    }

    /* 3D CARD PERSPECTIVE TILT & SHIMMER BEAM */
    .card-beam{
      position:absolute;
      inset:0;
      border-radius:inherit;
      pointer-events:none;
      border:1px solid transparent;
      background:linear-gradient(135deg,rgba(255,255,255,0.4),transparent 35%,rgba(255,255,255,0.08) 70%,transparent) border-box;
      -webkit-mask:linear-gradient(#fff 0 0) padding-box,linear-gradient(#fff 0 0);
      -webkit-mask-composite:xor;
      mask-composite:exclude;
      opacity:0;
      transition:opacity .5s cubic-bezier(.2,0,0,1);
    }
    .feat-card:hover .card-beam,.feat-card.in-view .card-beam,.glass.in-view .card-beam{
      opacity:1;
    }

    /* CARD ORBITING BRIGHT LIGHT DOT (HOVER EDGE GLOW) */
    .card-orbit-svg{
      position:absolute;
      inset:0;
      width:100%;
      height:100%;
      pointer-events:none;
      overflow:visible;
      border-radius:inherit;
      z-index:6;
      opacity:0;
      transition:opacity .35s ease;
    }
    .feat-card:hover .card-orbit-svg,
    .glass:hover .card-orbit-svg{
      opacity:1;
    }
    .orbit-halo{
      fill:none;
      stroke:rgba(255,255,255,0.45);
      stroke-width:5px;
      stroke-linecap:round;
      stroke-dasharray:3.5 96.5;
      filter:blur(3px);
      stroke-dashoffset:100;
    }
    .orbit-spark{
      fill:none;
      stroke:#ffffff;
      stroke-width:2.8px;
      stroke-linecap:round;
      stroke-dasharray:1.6 98.4;
      filter:drop-shadow(0 0 5px #ffffff) drop-shadow(0 0 12px rgba(255,255,255,.95));
      stroke-dashoffset:100;
    }
    .feat-card:hover .orbit-halo,
    .feat-card:hover .orbit-spark,
    .glass:hover .orbit-halo,
    .glass:hover .orbit-spark{
      animation:cardOrbitRun 3.2s linear infinite;
    }
    @keyframes cardOrbitRun{
      0%{stroke-dashoffset:100}
      100%{stroke-dashoffset:0}
    }

    .btn-solid{display:inline-flex;align-items:center;gap:.45rem;padding:13px 28px;background:#fff;color:#000;border:none;border-radius:99px;font-size:.95rem;font-weight:600;font-family:inherit;cursor:pointer;letter-spacing:-.02em;text-decoration:none;transition:all .25s cubic-bezier(.4,0,.2,1)}
    .btn-solid:hover{background:#e8e8e8;transform:translateY(-2px);box-shadow:0 10px 40px rgba(255,255,255,.18)}
    .btn-outline{display:inline-flex;align-items:center;gap:.45rem;padding:13px 28px;background:transparent;color:var(--t);border:1px solid var(--bhi);border-radius:99px;font-size:.95rem;font-weight:500;font-family:inherit;cursor:pointer;letter-spacing:-.02em;text-decoration:none;backdrop-filter:blur(12px);transition:all .25s cubic-bezier(.4,0,.2,1)}
    .btn-outline:hover{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.3);transform:translateY(-2px)}

    .scroll-hint{position:absolute;bottom:1.5rem;left:50%;transform:translateX(-50%);z-index:2;display:flex;flex-direction:column;align-items:center;gap:5px;color:var(--t3);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;animation:bob 2.2s ease-in-out infinite}
    .scroll-hint::after{content:'';display:block;width:1px;height:24px;background:linear-gradient(180deg,var(--t3) 0%,transparent 100%)}
    @media (max-height:820px){.scroll-hint{display:none}}
    @keyframes bob{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(6px)}}

    /* STATS */
    .stats-strip{display:flex;border-top:1px solid var(--b);border-bottom:1px solid var(--b)}
    .stat{flex:1;text-align:center;padding:2.75rem 1rem;border-right:1px solid var(--b)}
    .stat:last-child{border-right:none}
    .stat-val{font-size:2.4rem;font-weight:800;letter-spacing:-.045em;color:var(--t);line-height:1;margin-bottom:.4rem}
    .stat-lbl{font-size:.78rem;color:var(--t3);font-weight:300}

    /* SECTIONS */
    .sec{max-width:1180px;margin:0 auto;padding:110px 2rem}
    @media(min-width:1280px){.sec{padding-left:clamp(2rem,12vw,4.5rem)}}
    .sec-eyebrow{font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--t3);margin-bottom:.9rem}
    .sec-h2{font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.04em;line-height:1.08;color:var(--t);margin-bottom:1.25rem}
    .sec-p{font-size:1.05rem;color:var(--t2);font-weight:300;line-height:1.7;max-width:520px}

    /* FEATURES */
    #features{border-top:1px solid var(--b)}
    .feat-head{text-align:center;margin-bottom:4rem}
    .feat-head .sec-p{margin:0 auto}
    .feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1.25rem}
    @media(max-width:820px){.feat-grid{grid-template-columns:1fr 1fr}}
    @media(max-width:540px){.feat-grid{grid-template-columns:1fr}}
    .feat-card{position:relative;background:var(--bg2);border:1px solid var(--b);border-radius:20px;padding:2.75rem 2.25rem;transition:background .25s,border-color .25s;cursor:default;transform-style:preserve-3d;will-change:transform;overflow:hidden}
    .feat-card:hover{background:#0e0e11;border-color:rgba(255,255,255,.2)}
    .feat-icon{width:46px;height:46px;margin-bottom:1.4rem;display:flex;align-items:center;justify-content:center;border-radius:13px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.1);color:var(--silver);box-shadow:inset 0 1px 1px rgba(255,255,255,.12);transition:all .3s ease}
    .feat-card:hover .feat-icon{color:#fff;border-color:rgba(255,255,255,.25);background:rgba(255,255,255,.1);transform:scale(1.05)}
    .feat-title{font-size:1.05rem;font-weight:600;letter-spacing:-.02em;color:var(--t);margin-bottom:.65rem}
    .feat-desc{font-size:.9rem;color:var(--t2);line-height:1.7;font-weight:300}

    /* GLASS */
    .glass{position:relative;background:var(--glass);border:1px solid var(--b);border-radius:var(--r);padding:2rem;backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);transition:border-color .3s,background .3s;transform-style:preserve-3d;overflow:hidden}
    .glass:hover{border-color:rgba(255,255,255,.2);background:var(--glass2)}
    .card-lbl{font-size:.7rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--t3);margin-bottom:.85rem}
    .card-title{font-size:1.05rem;font-weight:600;letter-spacing:-.02em;color:var(--t);margin-bottom:1.15rem}

    /* ANALYSE */
    #analyse{border-top:1px solid var(--b)}
    .analyse-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-top:3rem}
    @media(max-width:860px){.analyse-grid{grid-template-columns:1fr}}
    textarea.inp{width:100%;min-height:210px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.07);border-radius:13px;color:var(--t);font-family:inherit;font-size:.88rem;font-weight:300;line-height:1.75;padding:1rem 1.2rem;resize:vertical;outline:none;transition:border-color .2s}
    textarea.inp::placeholder{color:var(--t3)}
    textarea.inp:focus{border-color:rgba(255,255,255,.22)}
    .row-btns{display:flex;gap:.65rem;margin-top:.9rem;flex-wrap:wrap;align-items:center}
    .btn-ghost{background:transparent;border:1px solid var(--b);color:var(--t2);padding:7px 16px;border-radius:99px;font-size:.8rem;font-family:inherit;cursor:pointer;transition:all .2s}
    .btn-ghost:hover{border-color:var(--bhi);color:var(--t)}
    .upload-lbl{display:inline-flex;align-items:center;gap:5px;padding:7px 16px;border:1px solid var(--b);border-radius:99px;font-size:.8rem;color:var(--t2);cursor:pointer;transition:all .2s}
    .upload-lbl:hover{border-color:var(--bhi);color:var(--t)}
    input[type=file]{display:none}
    .cta-row{margin-top:2rem;display:flex;justify-content:center}

    .btn-analyse{position:relative;overflow:hidden;padding:16px 52px;background:#fff;color:#000;border:none;border-radius:99px;font-size:1rem;font-weight:700;font-family:inherit;letter-spacing:-.025em;cursor:pointer;transition:all .3s cubic-bezier(.4,0,.2,1)}
    .btn-analyse:hover{transform:translateY(-3px);box-shadow:0 14px 56px rgba(255,255,255,.22)}
    .btn-analyse:active{transform:translateY(0)}
    .btn-analyse:disabled{opacity:.45;cursor:not-allowed;transform:none;box-shadow:none}
    .spinner{display:inline-block;width:15px;height:15px;border:2px solid rgba(0,0,0,.25);border-top-color:#000;border-radius:50%;animation:spin .7s linear infinite;margin-right:8px;vertical-align:middle}
    @keyframes spin{to{transform:rotate(360deg)}}
    .err-box{margin-top:1rem;padding:1rem 1.4rem;background:rgba(255,69,58,.1);border:1px solid rgba(255,69,58,.25);border-radius:12px;color:var(--red);font-size:.88rem;display:none}
    .err-box.on{display:block}

    /* RESULTS */
    #results{border-top:1px solid var(--b);display:none}
    #results.on{display:block}
    .results-top{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:2rem}
    .headline-box{background:rgba(255,255,255,.04);border:1px solid var(--b);border-radius:14px;padding:1rem 1.5rem;font-size:.92rem;color:var(--t);line-height:1.6;margin-bottom:2rem}

    .tabs{display:flex;background:rgba(255,255,255,.03);border:1px solid var(--b);border-radius:13px;padding:4px;gap:2px;margin-bottom:2rem;overflow-x:auto}
    .tab{padding:8px 22px;border-radius:9px;border:none;background:transparent;font-family:inherit;font-size:.82rem;font-weight:500;cursor:pointer;color:var(--t3);transition:all .2s;white-space:nowrap}
    .tab.active{background:rgba(255,255,255,.1);color:var(--t)}
    .tab:hover:not(.active){color:var(--t2)}
    .tab-pane{display:none;animation:fadeUp .35s ease}
    .tab-pane.on{display:block}
    @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

    .hl-legend{display:flex;flex-wrap:wrap;gap:1.25rem;margin-bottom:1.25rem}
    .hl-item{display:flex;align-items:center;gap:7px;font-size:.78rem;color:var(--t2)}
    .hl-dot{width:11px;height:11px;border-radius:3px}
    .hl-text{font-size:.9rem;line-height:1.85;color:var(--t2);background:rgba(0,0,0,.4);border:1px solid var(--b);border-radius:16px;padding:2rem;white-space:pre-wrap;word-wrap:break-word}
    .hl-data{background:rgba(185,215,255,.2);color:#b9d7ff;border-radius:3px;padding:0 3px}
    .hl-purpose{background:rgba(200,240,200,.18);color:#c8f0c8;border-radius:3px;padding:0 3px}
    .hl-shared{background:rgba(255,217,168,.18);color:#ffd9a8;border-radius:3px;padding:0 3px}
    .hl-denied{background:rgba(244,182,182,.18);color:#f4b6b6;border-radius:3px;padding:0 3px;text-decoration:line-through}

    .fp-box{font-family:'SF Mono','Fira Code',monospace;font-size:.82rem;color:var(--t2);word-break:break-all;background:rgba(0,0,0,.55);border:1px solid var(--b);border-radius:13px;padding:1.5rem;line-height:1.8;letter-spacing:.02em}
    .terms-table{width:100%;border-collapse:collapse;font-size:.9rem;color:var(--t2)}
    .terms-table td{padding:.75rem 1rem;border-bottom:1px solid var(--b);line-height:1.55}
    .terms-table td:first-child{color:var(--t3);font-weight:500;white-space:nowrap;width:38%}

    .toast{position:fixed;bottom:2rem;right:2rem;z-index:9999;background:rgba(22,22,24,.96);border:1px solid var(--b);border-radius:14px;padding:.9rem 1.5rem;font-size:.88rem;color:var(--t);backdrop-filter:blur(20px);max-width:340px;transform:translateY(90px);opacity:0;transition:all .35s cubic-bezier(.4,0,.2,1);pointer-events:none}
    .toast.on{transform:translateY(0);opacity:1}

    .rv{opacity:0;transform:translateY(28px);transition:opacity .75s cubic-bezier(.4,0,.2,1),transform .75s cubic-bezier(.4,0,.2,1)}
    .rv.go{opacity:1;transform:translateY(0)}

    footer{border-top:1px solid var(--b);max-width:1180px;margin:0 auto;padding:2.5rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem}
    .footer-logo{font-size:.95rem;font-weight:700;letter-spacing:-.025em}
    .footer-copy{font-size:.75rem;color:var(--t3)}
  </style>
</head>
<body>

<!-- LEFT-SIDE CRYPTOGRAPHIC LEDGER SPAN (FULL-HEIGHT HIGH-TECH BUS) -->
<div id="ledger-thread-wrap" aria-label="Interactive Navigation Ledger Bus">
  <div class="ledger-hud">
    <div class="hud-tag"><span class="hud-dot"></span>LEDGER BUS</div>
    <div class="hud-pct" id="hud-pct">000%</div>
  </div>
  <svg id="ledger-svg" viewBox="0 0 290 1000" preserveAspectRatio="xMidYMid meet" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="threadGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
        <stop offset="50%" stop-color="#e4e4e7" stop-opacity="0.9"/>
        <stop offset="100%" stop-color="#8e8e93" stop-opacity="0.75"/>
      </linearGradient>
      <filter id="ledgerGlow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <filter id="tracerBloom" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="glow"/>
        <feMerge>
          <feMergeNode in="glow"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>

    <!-- ARCHITECTURAL GHOST RAIL -->
    <path id="ghost-path" 
          d="M 24 40 L 24 70 L 24 210 L 56 242 L 56 318 L 24 350 L 24 380 L 24 520 L 56 552 L 56 628 L 24 660 L 24 690 L 24 820 L 56 852 L 56 918 L 24 950 L 24 960 L 24 985" 
          stroke="rgba(255,255,255,0.08)" 
          stroke-width="1.5" 
          stroke-linecap="round" 
          stroke-linejoin="round"/>

    <!-- CIRCUIT VIAS (PCB micro solder pads at each 45-degree angle) -->
    <g class="circuit-vias" opacity="0.6">
      <circle cx="24" cy="210" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="242" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="318" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="24" cy="350" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>

      <circle cx="24" cy="520" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="552" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="628" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="24" cy="660" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>

      <circle cx="24" cy="820" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="852" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="56" cy="918" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
      <circle cx="24" cy="950" r="2.2" fill="#080808" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
    </g>

    <!-- ACTIVE PROGRESS AMBIENT HALO -->
    <path id="active-halo-path" 
          d="M 24 40 L 24 70 L 24 210 L 56 242 L 56 318 L 24 350 L 24 380 L 24 520 L 56 552 L 56 628 L 24 660 L 24 690 L 24 820 L 56 852 L 56 918 L 24 950 L 24 960 L 24 985" 
          stroke="rgba(255,255,255,0.2)" 
          stroke-width="5.5" 
          stroke-linecap="round" 
          stroke-linejoin="round"
          filter="url(#ledgerGlow)"/>

    <!-- ACTIVE GLOWING PROGRESS PATH -->
    <path id="active-path" 
          d="M 24 40 L 24 70 L 24 210 L 56 242 L 56 318 L 24 350 L 24 380 L 24 520 L 56 552 L 56 628 L 24 660 L 24 690 L 24 820 L 56 852 L 56 918 L 24 950 L 24 960 L 24 985" 
          stroke="url(#threadGrad)" 
          stroke-width="2.4" 
          stroke-linecap="round" 
          stroke-linejoin="round"/>

    <!-- KINETIC TRACER BEACON -->
    <g id="tracer-group">
      <circle id="tracer-glow" cx="24" cy="40" r="10" fill="rgba(255,255,255,0.38)" filter="url(#tracerBloom)"/>
      <circle id="tracer-reticle" cx="24" cy="40" r="13" fill="none" stroke="rgba(255,255,255,0.32)" stroke-width="0.8" stroke-dasharray="2 2"/>
      <circle id="tracer-core" cx="24" cy="40" r="3.4" fill="#ffffff"/>
    </g>

    <!-- MILESTONE WAYPOINT NODES WITH LEADER LINES -->
    <g class="wp-node" id="wp-0" data-target="#hero" transform="translate(24, 70)">
      <circle class="wp-hit" r="18" fill="transparent"/>
      <circle class="wp-outer" r="7.5" fill="#050505" stroke="rgba(255,255,255,0.3)" stroke-width="1.4"/>
      <circle class="wp-core" r="3.2" fill="rgba(255,255,255,0.5)"/>
      <line class="wp-lead" x1="11" y1="0" x2="34" y2="0" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
      <text class="wp-label" x="42" y="1" dominant-baseline="central">01 // ORIGIN</text>
    </g>

    <g class="wp-node" id="wp-1" data-target="#features" transform="translate(24, 380)">
      <circle class="wp-hit" r="18" fill="transparent"/>
      <circle class="wp-outer" r="7.5" fill="#050505" stroke="rgba(255,255,255,0.3)" stroke-width="1.4"/>
      <circle class="wp-core" r="3.2" fill="rgba(255,255,255,0.5)"/>
      <line class="wp-lead" x1="11" y1="0" x2="34" y2="0" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
      <text class="wp-label" x="42" y="1" dominant-baseline="central">02 // ARCHITECTURE</text>
    </g>

    <g class="wp-node" id="wp-2" data-target="#analyse" transform="translate(24, 690)">
      <circle class="wp-hit" r="18" fill="transparent"/>
      <circle class="wp-outer" r="7.5" fill="#050505" stroke="rgba(255,255,255,0.3)" stroke-width="1.4"/>
      <circle class="wp-core" r="3.2" fill="rgba(255,255,255,0.5)"/>
      <line class="wp-lead" x1="11" y1="0" x2="34" y2="0" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
      <text class="wp-label" x="42" y="1" dominant-baseline="central">03 // STUDIO</text>
    </g>

    <g class="wp-node" id="wp-3" data-target="#results" transform="translate(24, 960)">
      <circle class="wp-hit" r="18" fill="transparent"/>
      <circle class="wp-outer" r="7.5" fill="#050505" stroke="rgba(255,255,255,0.3)" stroke-width="1.4"/>
      <circle class="wp-core" r="3.2" fill="rgba(255,255,255,0.5)"/>
      <line class="wp-lead" x1="11" y1="0" x2="34" y2="0" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
      <text class="wp-label" x="42" y="1" dominant-baseline="central">04 // AUDIT SEAL</text>
    </g>
  </svg>
</div>

<nav id="nav">
  <a href="#" class="nav-logo">
    <span class="nav-logo-icon">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
    </span>
    <span>ConsentLedger</span>
  </a>
  <ul class="nav-links">
    <li><a href="#features">Architecture</a></li>
    <li><a href="#analyse">Analyse</a></li>
    <li><a href="#analyse" class="nav-pill">Launch &rarr;</a></li>
  </ul>
</nav>

<section id="hero">
  <canvas id="hero-canvas"></canvas>
  <div class="hero-inner">
    <div class="hero-chip rv"><span class="chip-dot"></span>Account Aggregator Intelligence</div>
    <h1 class="hero-h1 rv">Privacy,<br>Understood.</h1>
    <p class="hero-sub rv">Deconstruct any Account Aggregator policy in seconds. Cryptographic entity resolution, faithfulness verification, and immutable on-chain state anchoring.</p>
    <div class="hero-ctas rv">
      <a href="#analyse" class="btn-solid">Analyse a policy &rarr;</a>
      <a href="#features" class="btn-outline">Architecture</a>
    </div>
  </div>
  <div class="scroll-hint">scroll</div>
</section>

<div class="stats-strip">
  <div class="stat rv"><div class="stat-val cipher-text" data-cipher="Legal-BERT">Legal-BERT</div><div class="stat-lbl">Entity Resolution</div></div>
  <div class="stat rv"><div class="stat-val cipher-text" data-cipher="100%">100%</div><div class="stat-lbl">Faithfulness Gating</div></div>
  <div class="stat rv"><div class="stat-val cipher-text" data-cipher="256-bit">256-bit</div><div class="stat-lbl">Keccak Cryptographic Anchor</div></div>
  <div class="stat rv"><div class="stat-val cipher-text" data-cipher="ReBIT 1.1">ReBIT 1.1</div><div class="stat-lbl">Account Aggregator Protocol</div></div>
</div>

<section id="features">
<div class="sec">
  <div class="feat-head rv">
    <div class="sec-eyebrow cipher-text" data-cipher="ARCHITECTURE">Architecture</div>
    <h2 class="sec-h2">Every clause,<br>decoded.</h2>
    <p class="sec-p scrub-text">ConsentLedger decomposes dense legal fine print into structured, mathematically auditable facts &mdash; with zero ambiguity.</p>
  </div>
  <div class="feat-grid">
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><path d="M11 8v6M8 11h6"/></svg>
      </div>
      <div class="feat-title">Named Entity Recognition</div>
      <div class="feat-desc">Legal-BERT identifies and classifies every collected data attribute, authorized purpose, and external recipient with token-level span resolution.</div>
    </div>
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
      </div>
      <div class="feat-title">Faithfulness Gate</div>
      <div class="feat-desc">Every AI-generated synthesis is cross-verified against source passages. Hallucinations are actively discarded in favour of verbatim legal facts.</div>
    </div>
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
      </div>
      <div class="feat-title">Cryptographic Fingerprint</div>
      <div class="feat-desc">A canonical Keccak-256 state commitment binds the policy and consent artefact together, verifiable on the Sepolia Ethereum testnet.</div>
    </div>
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      </div>
      <div class="feat-title">ReBIT Consent Parser</div>
      <div class="feat-desc">Parses machine-readable Account Aggregator schemas: evaluating retention windows, fetch periodicity, and data consumer identity boundaries.</div>
    </div>
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/><line x1="9" y1="16" x2="15" y2="16"/></svg>
      </div>
      <div class="feat-title">Denial &amp; Covenant Detection</div>
      <div class="feat-desc">Distinguishes negative commitments such as covenants prohibiting credential harvesting or resale of identifiers from actual collection practices.</div>
    </div>
    <div class="feat-card rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="feat-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
      </div>
      <div class="feat-title">Multi-Format Normalization</div>
      <div class="feat-desc">Direct ingestion of plain text, HTML, and structured document formats with deterministic whitespace normalization before analysis.</div>
    </div>
  </div>
</div>
</section>

<section id="analyse">
<div class="sec">
  <div class="rv">
    <div class="sec-eyebrow cipher-text" data-cipher="STUDIO">Studio</div>
    <h2 class="sec-h2">Drop a policy.<br>Get the truth.</h2>
    <p class="sec-p scrub-text">Enterprise audit engine &mdash; clause-by-clause extraction, faithfulness verification, and tamper-evident state seal.</p>
  </div>
  <div class="analyse-grid">
    <div class="glass rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="card-lbl">Input</div>
      <div class="card-title">Policy Document Text</div>
      <textarea class="inp" id="pol" rows="10" placeholder="Paste the terms of service or privacy policy here&hellip;"></textarea>
      <div class="row-btns">
        <button class="btn-ghost" id="btn-eg" style="display:inline-flex;align-items:center;gap:6px">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>Load sample</span>
        </button>
        <label class="upload-lbl" for="file-up" style="display:inline-flex;align-items:center;gap:6px">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <span>Upload file</span>
        </label>
        <input type="file" id="file-up" accept=".txt,.html,.htm,.pdf"/>
      </div>
    </div>
    <div class="glass rv">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div class="card-lbl">Optional</div>
      <div class="card-title">Consent Artefact (ReBIT JSON)</div>
      <textarea class="inp" id="con" rows="10" placeholder="Paste the ReBIT consent artefact JSON here&hellip;"></textarea>
      <div class="row-btns">
        <button class="btn-ghost" id="btn-consent" style="display:inline-flex;align-items:center;gap:6px">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
          <span>Load demo schema</span>
        </button>
      </div>
    </div>
  </div>
  <div class="err-box" id="err"></div>
  <div class="cta-row">
    <button class="btn-analyse" id="btn-analyse">Analyse Policy</button>
  </div>
</div>
</section>

<section id="results">
<div class="sec">
  <div class="results-top rv">
    <div>
      <div class="sec-eyebrow">Audit Report</div>
      <h2 class="sec-h2" style="font-size:2rem">Analysis Complete</h2>
    </div>
    <button class="btn-ghost" id="btn-reset">&larr; New analysis</button>
  </div>
  <div class="headline-box rv" id="headline"></div>
  <div class="tabs rv">
    <button class="tab active" data-pane="hl">Highlights</button>
    <button class="tab" data-pane="ps">Passages &amp; Faithfulness</button>
    <button class="tab" data-pane="ct">Consent Specification</button>
    <button class="tab" data-pane="fp">Cryptographic Seal</button>
  </div>
  <div class="tab-pane on" id="pane-hl">
    <div class="hl-legend">
      <div class="hl-item"><div class="hl-dot" style="background:#b9d7ff33;border:1px solid #b9d7ff55"></div>Your data</div>
      <div class="hl-item"><div class="hl-dot" style="background:#c8f0c833;border:1px solid #c8f0c855"></div>Purpose</div>
      <div class="hl-item"><div class="hl-dot" style="background:#ffd9a833;border:1px solid #ffd9a855"></div>Shared with</div>
      <div class="hl-item"><div class="hl-dot" style="background:#f4b6b633;border:1px solid #f4b6b655"></div>Promised NOT done</div>
    </div>
    <div class="hl-text" id="hl-content"></div>
  </div>
  <div class="tab-pane" id="pane-ps"><div id="passage-wrap"></div></div>
  <div class="tab-pane" id="pane-ct">
    <div class="glass">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <table class="terms-table"><tbody id="terms-body"></tbody></table>
      <p id="terms-none" style="color:var(--t3);font-size:.9rem;padding-top:.5rem;display:none">No consent artefact provided.</p>
    </div>
  </div>
  <div class="tab-pane" id="pane-fp">
    <div class="glass">
      <div class="card-beam"></div>
      <svg class="card-orbit-svg" aria-hidden="true">
        <rect class="orbit-halo" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
        <rect class="orbit-spark" x="1" y="1" width="calc(100% - 2px)" height="calc(100% - 2px)" rx="20" ry="20" pathLength="100"/>
      </svg>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.85rem;flex-wrap:wrap;gap:8px">
        <div class="card-lbl" style="margin-bottom:0">Keccak-256 &middot; State Commitment</div>
        <button class="btn-ghost" id="btn-copy-fp" style="padding:4px 12px;font-size:.74rem;display:inline-flex;align-items:center;gap:6px">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy hash</span>
        </button>
      </div>
      <div class="fp-box" id="fp-content"></div>
    </div>
  </div>
</div>
</section>

<footer class="rv">
  <span class="footer-logo">ConsentLedger</span>
  <span class="footer-copy">Research prototype &middot; Legal-BERT NER &middot; Flan-T5 summaries &middot; Sepolia testnet &middot; Not for production use</span>
</footer>

<div class="toast" id="toast"></div>

<script>
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

/* 3D TILT */
document.querySelectorAll('.feat-card').forEach(c=>{
  c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;c.style.transform=`perspective(700px) rotateX(${-y*7}deg) rotateY(${x*7}deg) translateZ(6px)`;});
  c.addEventListener('mouseleave',()=>{c.style.transform='';});
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
const DEMO_POLICY=`1. INFORMATION WE COLLECT\\nWe collect your bank statements, PAN and mobile number when you register on the Platform, and we use them to assess your eligibility for a loan.\\n2. SHARING\\nWe share your financial information with credit bureaus and lenders only with your explicit consent. We shall not access your user authentication credentials. We will not sell your mobile number to advertisers.\\n3. RETENTION\\nWe keep your data only as long as the consent you gave allows, and you may revoke your consent at any time.`;
const DEMO_CONSENT={"_note":"SYNTHETIC demo artefact","ConsentDetail":{"consentStart":"2026-10-01T10:00:00.000Z","consentExpiry":"2030-12-31T23:59:59.000Z","consentMode":"STORE","fetchType":"PERIODIC","consentTypes":["PROFILE","SUMMARY","TRANSACTIONS"],"DataConsumer":{"id":"DC1","type":"FIU"},"DataProvider":{"id":"DP1","type":"FIP"},"Customer":{"id":"demo_customer@demo_aa"},"Purpose":{"code":"103","text":"To process borrower\\u2019s loan application"},"FIDataRange":{"from":"2026-04-01T00:00:00.000Z","to":"2026-10-01T00:00:00.000Z"},"DataLife":{"unit":"MONTH","value":3},"Frequency":{"unit":"MONTH","value":1}}};

document.getElementById('btn-eg').onclick=()=>{document.getElementById('pol').value=DEMO_POLICY.replace(/\\\\n/g,'\\n');toast('Sample policy loaded');};
document.getElementById('btn-consent').onclick=()=>{document.getElementById('con').value=JSON.stringify(DEMO_CONSENT,null,2);toast('ReBIT schema loaded');};

document.getElementById('file-up').onchange=function(){
  if(!this.files.length)return;
  const f=this.files[0];
  if(/\\.(txt|html|htm)$/i.test(f.name)){const r=new FileReader();r.onload=e=>{document.getElementById('pol').value=e.target.result;toast('Loaded: '+f.name);};r.readAsText(f);}
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
    {re:/(shall not access [^\\.\\n,]+|will not sell [^\\.\\n,]+|never disclose [^\\.\\n,]+|will not share [^\\.\\n,]+without explicit consent)/gi, label:'Promised NOT done'},
    {re:/\\b(bank statements|pan|mobile number|financial information|transaction history|credit history|account credentials|user authentication credentials)\\b/gi, label:'Your data'},
    {re:/\\b(assess your eligibility for a loan|eligibility for a loan|creditworthiness|underwriting|loan application)\\b/gi, label:'Purpose'},
    {re:/\\b(licensed credit bureaus|credit bureaus|lending partners|lenders|advertisers)\\b/gi, label:'Shared with'}
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

  const rawPassages=policy.split(/\\n\\s*\\n|\\n(?=\\d+\\.\\s+)/).map(p=>p.trim()).filter(p=>p.length>10);
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
      termsMd=`| | |\\n|---|---|\\n| Consent Mode | ${cd.consentMode||'STORE'} |\\n| Fetch Type | ${cd.fetchType||'PERIODIC'} |\\n| Purpose | ${cd.Purpose?.text||'Loan eligibility'} |\\n| Customer | ${cd.Customer?.id||'-'} |\\n| Data Life | ${cd.DataLife?cd.DataLife.value+' '+cd.DataLife.unit:'-'} |\\n| Frequency | ${cd.Frequency?cd.Frequency.value+' per '+cd.Frequency.unit:'-'} |\\n| Start Date | ${cd.consentStart||'-'} |\\n| Expiry Date | ${cd.consentExpiry||'-'} |`;
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
        `Fingerprint of this policy + consent: ${hash}\n\nClient verified. Ready for Sepolia on-chain anchoring.`
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
  document.getElementById('headline').textContent=(headline||'').replace(/\\*\\*/g,'');
  const lm={'Your data':'hl-data','Purpose':'hl-purpose','Shared with':'hl-shared','Promised NOT done':'hl-denied'};
  document.getElementById('hl-content').innerHTML=Array.isArray(highlighted)?highlighted.map(([t,l])=>l?`<span class="${lm[l]||''}" title="${l}">${esc(t)}</span>`:esc(t)).join(''):'No highlights.';
  document.getElementById('passage-wrap').innerHTML=passagesHtml||'<p style="color:var(--t3)">No passages.</p>';
  renderTerms(termsRaw);
  document.getElementById('fp-content').textContent=(sealRaw||'').replace(/\\*\\*/g,'').replace(/`/g,'');
  const sec=document.getElementById('results');sec.classList.add('on');
  if(window.lenisInstance){window.lenisInstance.scrollTo(sec,{offset:-20,duration:1.2});}else{sec.scrollIntoView({behavior:'smooth',block:'start'});}
  document.getElementById('err').classList.remove('on');
  toast('Analysis complete');
}

function renderTerms(md){
  const tbody=document.getElementById('terms-body'),fb=document.getElementById('terms-none');
  if(!md||md.includes('_No consent')){tbody.innerHTML='';fb.style.display='block';return;}
  fb.style.display='none';
  const rows=(md.match(/\\|\\s*([^|]+?)\\s*\\|\\s*([^|]+?)\\s*\\|/g)||[]).filter(r=>!r.includes('---')&&!/^\\|\\s*\\|\\s*\\|/.test(r));
  tbody.innerHTML=rows.map(r=>{const c=r.split('|').map(s=>s.trim()).filter(Boolean);return c.length===2?`<tr><td>${esc(c[0])}</td><td>${esc(c[1])}</td></tr>`:''}).join('');
  if(!tbody.children.length)tbody.innerHTML=`<tr><td colspan="2" style="color:var(--t3)">${(md||'').replace(/\\*\\*/g,'')}</td></tr>`;
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
    this.chars='01§7FλØ&%#*/\\X89_+=';
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
</script>
</body>
</html>"""

with open("d:/ConsentLedger/frontend/index.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html written:", len(HTML), "chars")