/* 무게꾼 — interactive design exploration, not a production data source. */
(function(){
"use strict";
const ROOT="../../assets/lila/poster_upscaled/";
const paths={
home:"M3 10 12 3l9 7v11H3V10Zm6 11v-7h6v7",dumbbell:"M6 6l12 12M2 8l6-6m8 20 6-6M8 2l14 14M2 8l14 14M6 12l6-6",
chart:"M3 3v18h18M7 16l4-6 4 3 5-7",calendar:"M3 5h18v16H3zM7 3v4m10-4v4M3 10h18",
bell:"M18 8a6 6 0 0 0-12 0c0 7-3 8-3 9h18c0-1-3-2-3-9M10 21h4",
settings:"M12 2l2 2 3-.5.6 3 2.9 1.4-1.2 3 1.2 3-2.9 1.4-.6 3-3-.5-2 2-2-2-3 .5-.6-3-2.9-1.4 1.2-3-1.2-3L6.4 6l.6-3 3 .5zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
"chevron-right":"M9 18l6-6-6-6","chevron-left":"M15 18l-6-6 6-6","chevron-down":"M6 9l6 6 6-6",
"arrow-right":"M5 12h14m-7-7 7 7-7 7","arrow-up-right":"M7 17 17 7M8 7h9v9",
plus:"M12 5v14M5 12h14",minus:"M5 12h14",check:"M4 12l5 5L20 6",x:"M18 6 6 18M6 6l12 12",
clock:"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3 2",
timer:"M12 5a8 8 0 1 0 0 16 8 8 0 0 0 0-16M9 2h6M12 5v8l3-2",
play:"M8 5l11 7-11 7z",pause:"M6 4h4v16H6zM14 4h4v16h-4z",
"skip-forward":"M4 5l11 7-11 7zM20 5v14",
"book-open":"M12 7c-3-2-7-2-10-1v14c3-1 7-1 10 1 3-2 7-2 10-1V6c-3-1-7-1-10 1zM12 7v14",
flask:"M9 3h6M10 3v7l-6 9a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-6-9V3M8 16h8",
target:"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18m0 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10m0 4v2",
award:"M12 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12M8 14l-2 8 6-3 6 3-2-8",
user:"M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8M4 21a8 8 0 0 1 16 0",
info:"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 11v6m0-10v.01",
alert:"M12 3l10 18H2L12 3zM12 9v5m0 3v.01",
"check-circle":"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M8 12l3 3 5-6",
cloud:"M20 17a4 4 0 0 0-2-7 6 6 0 0 0-12 1 4 4 0 0 0 0 8h13",
database:"M12 2c-5 0-9 1-9 4v13c0 4 18 4 18 0V6c0-3-4-4-9-4zm-9 4c0 4 18 4 18 0M3 12c0 4 18 4 18 0",
shield:"M12 22s8-3 8-10V5l-8-3-8 3v7c0 7 8 10 8 10zM9 12l2 2 4-4",
lock:"M5 10h14v12H5zM8 10V7a4 4 0 0 1 8 0v3",
moon:"M21 13A9 9 0 0 1 11 3 9 9 0 1 0 21 13z",
sun:"M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8",
download:"M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",upload:"M12 17V5m-5 5 5-5 5 5M4 17v4h16v-4",
share:"M18 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6M6 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6m12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6M9 11l6-4m-6 7 6 4",
trash:"M4 7h16M8 7l1 14h6l1-14M9 4h6",edit:"M3 17l12-12 4 4L7 21H3zM12 20h9",
filter:"M3 5h18M7 12h10m-6 7h2",sliders:"M3 5h18M3 12h18M3 19h18M9 3v4m7 3v4m-9 3v4",
list:"M9 6h12M9 12h12M9 18h12M3 6h1m-1 6h1m-1 6h1",
"message-square":"M3 4h18v14H8l-5 4z",activity:"M2 12h4l3-8 5 16 3-8h5",
scale:"M3 7h18M12 7V3M5 7L2 15h6L5 7zm14 0l-3 8h6l-3-8M6 21h12",
heart:"M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z",
star:"M12 2l3 7 7 .4-5.5 4.7L18.3 21 12 17l-6.3 4 1.8-6.9L2 9.4 9 9z",
"rotate-ccw":"M3 9V3h6m-6 6a9 9 0 1 1-1 6",
signal:"M2 20h2v-4H2zm5 0h2v-8H7zm5 0h2V8h-2zm5 0h2V4h-2z",
wifi:"M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-10 4a5 5 0 0 1 6 0M12 20h.01",
archive:"M3 3h18v5H3zM5 8v13h14V8M10 12h4",
"file-text":"M5 2h9l5 5v15H5zM14 2v5h5M9 12h6m-6 4h6",
smartphone:"M6 2h12v20H6zM10 18h4",
logout:"M10 3H4v18h6m4-4 5-5-5-5m5 5H8",
search:"M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16m6 14 4 4",
route:"M6 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4M18 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4M8 18h6a4 4 0 0 0 0-8H8a4 4 0 0 1 0-8h8"
};
function ic(n){return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.9"><path d="'+(paths[n]||paths.info)+'"/></svg>'}
function hydrate(root){(root||document).querySelectorAll("[data-icon]").forEach(n=>n.innerHTML=ic(n.dataset.icon))}
function e(s){return String(s??"").replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[x]))}
function fmt(n){return Number(n).toLocaleString("ko-KR")}
function photo(lv,cls){return '<img class="'+(cls||"lila-small")+'" src="'+ROOT+'lila_lv0'+(lv||3)+'_4x.png" alt="릴라 Lv.'+(lv||3)+'">'}
function pill(t,c){return '<span class="pill '+(c||"")+'">'+t+'</span>'}
function heading(t,s,k){return '<span class="eyebrow-app">'+(k||"무게를 아는 사람들")+'</span><h1 class="page-title">'+t+'</h1>'+(s?'<p class="body-copy">'+s+'</p>':"")}
function section(t,to,caption){return '<div class="section-head"><h2 class="section-title">'+t+'</h2>'+(to?'<button class="section-link" data-go="'+to+'">'+(caption||"전체보기")+ic("chevron-right")+'</button>':"")+'</div>'}
function card(html,style,to){return '<div class="card '+(style||"")+(to?' tap" role="button" tabindex="0" data-go="'+to+'"':'"')+'>'+html+'</div>'}
function button(t,to,style){return '<button class="'+(style||"action-primary")+'" data-go="'+to+'">'+t+' '+ic("arrow-right")+'</button>'}
function back(t){return '<div class="page-back"><button class="back-btn" data-act="back">'+ic("chevron-left")+(t||"뒤로")+'</button></div>'}
function pane(h,cls){return '<div class="app-shell '+(cls||"")+'">'+h+'</div>'}
function demo(t){return '<div class="review-demo-note">'+ic("info")+(t||"표시된 기록·연구·지표는 디자인용 예시입니다.")+'</div>'}
function row(symbol,t,s,to,trailing){return '<button class="row-tile tap" data-go="'+to+'"><span class="row-icon">'+ic(symbol)+'</span><span class="row-main"><strong>'+t+'</strong>'+(s?'<span>'+s+'</span>':"")+'</span>'+(trailing||"")+'<span class="chev">'+ic("chevron-right")+'</span></button>'}
function notices(t,type){return '<div class="alert-soft '+(type||"")+'">'+ic(type==="status-warning"?"alert":"info")+'<span>'+t+'</span></div>'}
function fld(t,key,v,type){return '<div class="form-field"><label for="'+key+'">'+t+'</label><input class="field-input" id="'+key+'" value="'+e(v||"")+'" type="'+(type||"text")+'"></div>'}
function chips(list,selected,action){return '<div class="choice-chips">'+list.map(x=>'<button data-act="'+action+'" data-val="'+e(x)+'" class="'+(selected===x?"active":"")+'">'+e(x)+'</button>').join("")+'</div>'}
function choice(t,s,icon,action,active){return '<button class="large-choice tap '+(active?"active":"")+'" data-act="'+action+'" data-val="'+t+'"><span class="choice-illustration">'+ic(icon)+'</span><span style="flex:1"><strong>'+t+'</strong><p>'+s+'</p></span><span class="check-circle '+(active?"selected":"")+'">'+(active?ic("check"):"")+'</span></button>'}
function graph(arr){const v=arr||[91,97,104,108,120,128],low=75,high=150,x=22,w=290;const p=v.map((n,i)=>(x+i*w/(v.length-1))+","+(150-(n-low)/(high-low)*114));return '<div class="chart-wrap"><svg viewBox="0 0 335 183"><path class="axis" d="M20 36H320M20 90H320M20 150H320"/><polyline class="line" points="'+p.join(" ")+'"/>'+v.map((n,i)=>'<circle class="dot" cx="'+(x+i*w/(v.length-1))+'" cy="'+(150-(n-low)/(high-low)*114)+'" r="3.5"/>').join("")+['5월','6월','7월','8월','9월','10월'].map((m,i)=>'<text x="'+(x+i*w/5)+'" y="177" text-anchor="middle">'+m+'</text>').join("")+'</svg></div>'}
function bars(v){return '<div class="bar-chart">'+v.map((x,i)=>'<span style="height:'+x+'%" class="'+(i===v.length-1?"active":"")+'"></span>').join("")+'</div>'}
function dots(){return '<div class="month-dots">'+Array.from({length:65},(_,i)=>'<span class="'+((i*17)%13<4?"active":(i*7)%13<4?"med":"")+'"></span>').join("")+'</div>'}
const groups=[
{id:"start",name:"시작",icon:"play"},
{id:"home",name:"홈",icon:"home"},
{id:"routine",name:"루틴",icon:"dumbbell"},
{id:"session",name:"운동 진행",icon:"timer"},
{id:"records",name:"기록",icon:"calendar"},
{id:"growth",name:"성장",icon:"chart"},
{id:"settings",name:"설정",icon:"settings"}];
const definitions=[
["splash","start","첫 실행","첫 방문에서 브랜드 메시지와 명확한 시작점","브랜드에 집중 · 로그인 강요 없음","welcome","home"],
["welcome","start","서비스 소개","운동 근거와 개인 기록의 가치 전달","근거와 개인 결과를 구분 · 3문장 이내","setup-goal","splash"],
["setup-goal","start","운동 목표","초기 훈련 목적 선택","1RM·근비대·습관을 구분","setup-level","setup-lifts"],
["setup-level","start","운동 경험","개인의 훈련 숙련도 확인","평가하는 언어 금지 · 건너뛰기 허용","setup-lifts","setup-goal"],
["setup-lifts","start","관심 종목","스쿼트/벤치/데드리프트 추적 종목","여러 개 선택 가능 · 강제하지 않음","setup-baseline","setup-level"],
["setup-baseline","start","현재 중량","첫 시작 기준 중량 등록","실측 1RM·추정 e1RM 혼동 방지","setup-mode","growth-max"],
["setup-mode","start","데이터 보관","로컬 우선·선택적 동기화 안내","Apple 로그인 강제하지 않음","setup-ready","settings-account"],
["setup-ready","start","준비 완료","최초 사용을 홈/루틴으로 연결","불필요한 축하 모달 대신 바로 행동","home","routines"],
["home","home","홈 대시보드","오늘 운동과 개인 지표를 1초 만에 파악","핵심 CTA 한 개 · 릴라는 데이터 보조","routine-detail","growth"],
["notifications","home","알림 센터","오늘 확인할 알림 모으기","실제 알림 권한 확인은 개발 단계","settings-notices","home"],
["daily-insight","home","오늘의 인사이트","근거 해설과 기록 가이드 제시","논문이 검증됐다는 가짜 주장 금지","routine-evidence","growth"],
["routines","routine","루틴 탐색","훈련 목표에 맞는 루틴 비교","연구 검증 상태 표시","routine-detail","routine-custom"],
["routine-search","routine","루틴 검색","문자열·종목·난이도 필터","검색 결과 없음 상태 포함","routine-detail","routines"],
["routine-detail","routine","루틴 상세","주당 빈도·중량·진행 규칙 이해","적용 전 가정/한계 확인","routine-evidence","routine-confirm"],
["routine-evidence","routine","연구 근거","프로토콜과 자료 출처 해설","가짜 DOI·논문 제목을 만들지 않음","routine-detail","routine-confirm"],
["routine-schedule","routine","주간 일정","운동 요일 배치","휴식일 포함 · 수정 가능","routine-confirm","routine-detail"],
["routine-custom","routine","나의 루틴 편집","사용자 루틴 변수 입력","사용자 설정을 논문 추천과 혼동 금지","routine-confirm","exercise-info"],
["routine-confirm","routine","운동 시작 확인","세션 전에 운동 순서·시간 파악","현재 목표 중량을 확인 가능","session-overview","routine-detail"],
["exercise-info","routine","운동 종목 상세","SBD 운동 동작·기록 정의 이해","실제 시범 미디어는 추후 제공","session-exercise","routine-custom"],
["session-overview","session","진행 중 운동","세션 현재 상태 확인","진행 중 기록이 유지되는 흐름","session-exercise","session-end-confirm"],
["session-exercise","session","세트 입력","중량과 반복 횟수 빠른 기록","숫자를 크게 · 최소 탭","session-rest","session-edit-set"],
["session-rest","session","휴식 타이머","세트 간 휴식","연장·건너뛰기·일시정지","session-exercise","session-overview"],
["session-edit-set","session","세트 수정","잘못 저장한 세트 정정","삭제 전에 확인","session-exercise","session-overview"],
["session-swap","session","운동 변경","장비 문제 등 예외 대응","종목 변경 이력 구분","session-exercise","exercise-info"],
["session-end-confirm","session","종료 확인","운동 조기 종료 방지","운동 데이터 삭제와 분리","session-summary","session-overview"],
["session-summary","session","운동 완료","세트·볼륨 결과 요약","실제 PR 검증 전에는 PR 표시 안 함","records-detail","home"],
["records","records","기록 목록","날짜별 운동 조회","모든 수치는 예시","records-detail","records-calendar"],
["records-calendar","records","기록 캘린더","운동 빈도 회고","훈련 안 한 날에 죄책감 유도 금지","records-detail","records"],
["records-detail","records","기록 상세","종목별 세트와 볼륨","목표/실제 구분","records-edit","growth-lift"],
["records-edit","records","과거 기록 수정","이전 데이터 수정","저장 시 현재 기록만 갱신","records-detail","records"],
["record-new","records","수동 기록","운동 후 소급 입력","날짜·중량 단위 확인","records","records-detail"],
["growth","growth","성장 대시보드","실측·추정 지표 변화 요약","e1RM은 실제 1RM이 아님","growth-lift","growth-lila"],
["growth-lift","growth","종목별 추이","스쿼트·벤치·데드리프트 그래프","추정식 및 측정 방법 제공","growth-max","growth-insight"],
["growth-max","growth","실측 1RM","직접 성공한 최대 중량 기록","e1RM과 구분","growth-lift","growth"],
["growth-experiment","growth","프로토콜 리포트","프로토콜 진행과 결과 검토","원인 단정 금지","routine-detail","growth"],
["growth-lila","growth","릴라 성장","릴라와 성장 마일스톤 확인","3D 슬롯 준비 · 과도한 게임화 지양","growth","settings"],
["growth-insight","growth","분석 방법","수치 해석과 계산법 설명","e1RM은 추정치 · 개인차 표시","growth-lift","routine-evidence"],
["settings","settings","설정 홈","운동 앱 설정의 중심","개인정보·백업은 별도 구획","settings-profile","settings-data"],
["settings-profile","settings","내 프로필","목표·닉네임·관심 종목","민감 정보 기본 수집 금지","settings","setup-goal"],
["settings-theme","settings","화면 테마","밝은 화면/어두운 화면 설정","브랜드 컬러는 차콜/화이트","settings","home"],
["settings-units","settings","중량 단위","kg/lb 표기 선택","값의 내부 단위는 별도 관리","settings","session-exercise"],
["settings-notices","settings","알림 설정","운동·휴식 알림 제어","실제 권한과 UI 설정 분리","settings","notifications"],
["settings-data","settings","데이터 관리","백업·복원·동기화 선택","백업 완료 거짓 표시 금지","settings-account","settings"],
["settings-account","settings","계정·동기화","게스트와 Apple 로그인","실제 연동은 이 목업 범위 아님","settings-data","settings"],
["settings-about","settings","앱 정보","브랜드와 법적·연구 정책","제품 명칭·버전·면책","settings","routine-evidence"]
].map(([id,group,name,purpose,review,next,alt])=>({id,group,name,purpose,review,next:[next,alt].filter(Boolean)}));
const screenMap=Object.fromEntries(definitions.map(s=>[s.id,s]));
const K="mugekkun-design-review-v1";
function readNotes(){try{return JSON.parse(localStorage.getItem(K)||"{}")}catch(_){return {}}}
const state={page:"home",history:[],theme:"light",notes:readNotes(),goal:"1RM 향상",level:"중급자",lifts:["스쿼트","벤치프레스","데드리프트"],routine:"5×5 베이스",filter:"전체",recordFilter:"전체",lift:"스쿼트",lilaLevel:3,growthPeriod:"3개월",weekdays:["월","수","금"],unit:"kg",setCount:0,setLog:[],weight:"75",reps:"5",restSeconds:165,timerPaused:true,sessionActive:false,flags:{workout:true,rest:true,news:false},search:"",saved:false};
const viewport=document.getElementById("appViewport"),nav=document.getElementById("appBottomNav"),phone=document.getElementById("phoneScreen");

function appHeader(){return '<div class="app-top"><div class="brand-word">무게꾼<span style="font-size:8px;margin-left:8px;vertical-align:middle;letter-spacing:.5px;font-weight:650;color:var(--muted)">STRENGTH LAB</span></div><div class="app-top-actions"><button class="circle-control" data-go="notifications" aria-label="알림">'+ic("bell")+'</button><button class="circle-control" data-go="settings" aria-label="설정">'+ic("settings")+'</button></div></div>'}
function hero(){return '<div class="hero-home"><div class="eyebrow-app" style="color:#BCBCBD">TRAINING DAY · 03</div><h3>오늘도<br>한 세트 더.</h3><div class="hero-sub">가장 강했던 어제의 나를<br>오늘 한 번 더 만나봐요.</div><button class="cta-small" data-go="session-overview">운동 시작 '+ic("arrow-up-right")+'</button>'+photo(3,"lila-hero")+'</div>'}
function metric(t,n,unit,foot,to){return card('<div class="between"><div class="card-kicker">'+t+'</div>'+ic("arrow-up-right")+'</div><div style="margin-top:21px" class="number">'+n+' <span>'+unit+'</span></div><div class="metric-label">'+foot+'</div>',"stat-card",to)}
function onetile(t,v,sub,to){return '<button class="row-tile tap" data-go="'+to+'"><div class="row-main"><strong>'+t+'</strong><span>'+sub+'</span></div><strong style="font-size:17px">'+v+'</strong>'+ic("chevron-right")+'</button>'}
function muscles(){return '<div class="between" style="margin-top:10px"><span class="pill dark">스쿼트</span><span class="pill dark">벤치</span><span class="pill dark">데드리프트</span></div>'}
function welcomeShell(kicker,headline,copy,body,forward,backTo,btnText){
 return pane('<div class="between" style="margin-bottom:38px"><button class="back-btn" data-go="'+(backTo||"splash")+'">'+ic("chevron-left")+'이전</button><span class="eyebrow-app">시작하기 · '+kicker+'</span></div><div class="eyebrow-app">LET’S BUILD STRENGTH</div><h1 class="page-title big" style="margin-bottom:12px">'+headline+'</h1><p class="body-copy">'+copy+'</p><div class="spacer-24"></div>'+body+'<div class="spacer-24"></div>'+button(btnText||"계속",forward)+demo("입력은 목업 내부 상태만 변경하며 실제 계정에 저장되지 않습니다."),"with-fixed")
}
function startScreen(id){
 switch(id){
 case "splash":return '<div class="splash-view"><div><div class="logo-splash">'+ic("dumbbell")+'</div><h1>무게꾼</h1><p>무게를 아는 사람들.<br>논문으로 고르고, 바벨로 검증한다.</p></div>'+photo(2,"splash-lila")+'<div class="splash-cta">'+button("시작하기","welcome")+'<button class="action-plain" style="margin-top:11px;width:100%" data-go="home">일단 둘러볼게요</button></div></div>';
 case "welcome":return welcomeShell("01 / 06","훈련을 더<br>명확하게.","근거를 이해하고, 내 기록으로 확인하는 근력 훈련. 스쿼트·벤치프레스·데드리프트를 중심으로 시작해요.",
 card('<div class="between"><div><div class="card-kicker">01 · RESEARCH</div><div class="card-title" style="margin-top:6px">왜 이 방식인지 알고</div></div>'+ic("book-open")+'</div>')+
 card('<div class="between"><div><div class="card-kicker">02 · TRAIN</div><div class="card-title" style="margin-top:6px">운동을 기록하고</div></div>'+ic("dumbbell")+'</div>')+
 card('<div class="between"><div><div class="card-kicker">03 · LEARN</div><div class="card-title" style="margin-top:6px">변화를 살펴봐요</div></div>'+ic("chart")+'</div>'),"setup-goal","splash","나에게 맞게 시작");
 case "setup-goal":return welcomeShell("02 / 06","어떤 무게를<br>향해 갈까요?","목표에 맞게 기록 화면과 루틴 탐색을 구성해요.",
 choice("1RM 향상","스쿼트·벤치·데드리프트의 최대 근력", "target","goal",state.goal==="1RM 향상")+
 choice("근비대","꾸준한 근육 성장과 볼륨 관리","activity","goal",state.goal==="근비대")+
 choice("운동 습관","무리하지 않고 운동을 지속하는 루틴","calendar","goal",state.goal==="운동 습관"),"setup-level","welcome");
 case "setup-level":return welcomeShell("03 / 06","지금은 어느<br>단계인가요?","훈련 경험을 선택해 줘요. 언제든 바꿀 수 있어요.",
 choice("초급자","웨이트 트레이닝을 시작한 지 1년 미만","user","level",state.level==="초급자")+
 choice("중급자","루틴 경험이 있고, 중량 기록에 익숙함","dumbbell","level",state.level==="중급자")+
 choice("숙련자","몇 년간 계획적인 훈련 경험이 있음","award","level",state.level==="숙련자"),"setup-lifts","setup-goal");
 case "setup-lifts":return welcomeShell("04 / 06","가장 중요하게<br>보는 종목은?","복수 선택할 수 있어요. 모든 종목을 선택할 필요는 없어요.",
 ["스쿼트","벤치프레스","데드리프트"].map((t,i)=>'<button class="large-choice tap '+(state.lifts.includes(t)?"active":"")+'" data-act="toggleLift" data-val="'+t+'"><span class="choice-illustration">'+ic(["activity","dumbbell","scale"][i])+'</span><span style="flex:1"><strong>'+t+'</strong><p>'+["하체 및 전신 근력","상체 밀기 근력","후면 사슬과 전신 근력"][i]+'</p></span><span class="check-circle '+(state.lifts.includes(t)?"selected":"")+'">'+(state.lifts.includes(t)?ic("check"):"")+'</span></button>').join(""),"setup-baseline","setup-level");
 case "setup-baseline":return welcomeShell("05 / 06","출발점을<br>기록해 볼까요?","모르면 건너뛰어도 괜찮아요. 측정한 값만 정확히 기록하면 돼요.",
 card('<div class="between"><strong class="card-title">스쿼트 실측 1RM</strong>'+pill("선택 입력")+'</div>'+fld("성공한 1회 최대 중량 (kg)","baseline","", "number")+'<div class="field-caption">여러 번 반복한 세트의 추정치(e1RM)가 아니라 실제 1회 성공 기록입니다.</div>')+
 '<div class="spacer-16"></div>'+notices("최대 중량을 모르는 경우 빈칸으로 진행해도 돼요. 측정이 필요할 땐 무리하지 말고 안전한 환경에서 진행하세요."),"setup-mode","setup-lifts","다음 / 건너뛰기");
 case "setup-mode":return welcomeShell("06 / 06","기록은 어디에<br>보관할까요?","처음부터 계정을 만들 필요는 없어요.",
 card('<div class="between"><div><strong class="card-title">이 기기에 저장</strong><p class="card-copy" style="margin-top:6px">로그인 없이 즉시 시작하고, 나중에 백업할 수 있어요.</p></div>'+pill("추천")+'</div>')+
 '<div class="spacer-12"></div>'+card('<div class="between"><div><strong class="card-title">Apple 계정 연결</strong><p class="card-copy" style="margin-top:6px">나중에 설정에서 연결할 수 있어요.</p></div>'+ic("cloud")+'</div>')+
 '<div class="spacer-16"></div>'+notices("이것은 기능 설명 목업입니다. 실제 기기 백업·Apple 로그인은 여기서 실행되지 않아요."),"setup-ready","setup-baseline","기기에 저장하고 시작");
 case "setup-ready":return pane('<div class="center" style="padding:35px 10px 5px">'+photo(2,"lila-stand")+'<div class="spacer-24"></div><span class="eyebrow-app">YOU’RE ALL SET</span><h1 class="page-title">시작할 준비가<br>됐어요.</h1><p class="body-copy">하루의 기록이 쌓여<br>당신만의 근거가 됩니다.</p></div><div class="spacer-24"></div>'+card('<div class="card-kicker">나의 목표</div><h3 class="card-title" style="margin:9px 0 5px">'+e(state.goal)+'</h3><div class="card-copy">'+state.lifts.join(" · ")+'</div>')+'<div class="spacer-24"></div>'+button("홈으로 가기","home")+'<div class="spacer-8"></div>'+button("루틴 먼저 둘러보기","routines","action-secondary"));
 }
 return "";
}
function homeScreen(id){
 switch(id){
 case "home":return pane(appHeader()+'<div class="between" style="margin:8px 0 18px"><div><span class="eyebrow-app">FRIDAY, OCT 9</span><h1 class="page-title" style="margin:3px 0 0">오늘도 한 번 더.</h1></div>'+pill("DAY 03")+'</div>'+hero()+
 section("이번 주", "growth","자세히")+
 '<div class="grid-two">'+metric("운동 횟수","3","회","지난 7일 · 예시","records-calendar")+metric("누적 볼륨","3,200","kg","지난 7일 · 예시","growth")+'</div>'+
 section("오늘의 루틴","routine-detail")+
 card('<div class="between"><span class="card-kicker">STRENGTH BASE · W03</span>'+pill("예시 루틴")+'</div><div class="card-title" style="margin:14px 0 5px">스쿼트 중심 5×5</div><p class="card-copy">스쿼트 · 벤치프레스 · 보조 운동</p><div class="hr"></div><div class="between"><span class="small-text muted">'+ic("clock")+' 45~60분 · 세트간 휴식 3분</span><span class="card-arrow">'+ic("chevron-right")+'</span></div>',"", "routine-detail")+
 section("나의 변화","growth")+card('<div class="between"><span class="card-kicker">SQUAT · e1RM 추정</span><span class="small-text muted">최근 6개월</span></div><div style="margin-top:8px" class="metric-number">128 <span class="metric-unit">kg</span></div>'+graph()+'<p class="rule-label">샘플 그래프 · e1RM은 실제 1RM이 아닙니다.</p>',"","growth-lift")+
 section("릴라와 함께","growth-lila")+card('<div class="between"><div><div class="card-kicker">LILA · COMPANION</div><div class="card-title" style="margin:11px 0 5px">Lv.3 성장 릴라</div><p class="card-copy">오늘도 꾸준하게,<br>우리 페이스로.</p></div>'+photo(3,"lila-small")+'</div>',"","growth-lila")+demo(), "with-fixed");
 case "notifications":return pane(back("홈")+heading("알림","필요할 때만 알려드릴게요.","NOTIFICATIONS")+section("오늘")+row("calendar","운동 예정","오후 7시 · 스쿼트 중심 루틴","routine-detail")+row("timer","휴식 타이머","세트가 완료되면 자동으로 시작","settings-notices")+section("기타")+notices("현재 목업에서는 실제 푸시 알림을 발송하지 않습니다.")+section("알림 관리")+button("알림 설정","settings-notices","action-secondary"));
 case "daily-insight":return pane(back("홈")+heading("오늘의 인사이트","결론보다 맥락을 함께 보여줄게요.","TRAINING NOTE")+card('<div class="card-kicker">오늘의 가이드</div><h3 class="card-title" style="margin:10px 0">세트간 휴식은<br>목표에 따라 달라요.</h3><p class="card-copy">고중량 복합 운동의 휴식 길이는 총 수행량에 영향을 줄 수 있습니다. 개인의 회복 상태와 세트 목표에 따라 조정해야 합니다.</p>')+section("이 가이드를 읽는 법")+row("book-open","관련 연구 확인하기","근거 유무, 연구 설계, 적용 한계를 확인","routine-evidence")+row("chart","내 운동 기록과 비교","세트별 성공률과 휴식 기록을 함께 보기","growth")+notices("이 문구는 UX 예시입니다. 논문 DOI·검증 상태가 연결되기 전에는 '논문이 입증'했다고 주장하지 않습니다."));
 }return "";
}

function routineTile(t,short,params,to,badgeText){
 return card('<div class="between"><span class="card-kicker">ROUTINE · '+(badgeText||"예시")+'</span>'+pill("상세보기")+'</div><h3 class="card-title" style="margin:14px 0 8px">'+t+'</h3><p class="card-copy">'+short+'</p><div class="hr"></div><div class="between"><span class="small-text muted">'+params+'</span>'+ic("chevron-right")+'</div>',"tap",to)
}
function routineScreen(id){
 switch(id){
 case "routines":return pane(appHeader()+heading("근거를 이해하고<br>운동하세요.","내 운동의 기준을 정하는 공간.","TRAINING LIBRARY")+
 '<div class="spacer-16"></div>'+chips(["전체","근력","근비대","나의 루틴"],state.filter,"routineFilter")+
 '<button class="row-tile tap" style="margin-top:4px" data-go="routine-search"><span class="row-icon">'+ic("search")+'</span><span class="row-main"><strong>루틴 검색</strong><span>종목·난이도·목표로 찾기</span></span>'+ic("chevron-right")+'</button>'+
 section(state.filter==="나의 루틴"?"내가 만든 루틴":"추천 탐색")+routineTile("5×5 베이스","기본 복합 운동의 반복 가능한 훈련 구조","주 3일 · 45~60분","routine-detail","검증 연결 전")+
 (state.filter!=="나의 루틴"?routineTile("볼륨 중심 블록","중량과 세트 수를 조정해 누적 작업량 관찰","주 4일 · 55~70분","routine-detail","검증 연결 전"):"")+
 section("직접 설계")+card('<div class="between"><div><div class="card-title">나만의 루틴 만들기</div><p class="card-copy" style="margin-top:6px">중량, 반복 수, 휴식을 내 방식으로.</p></div><span class="circle-control">'+ic("plus")+'</span></div>',"tap","routine-custom")+
 section("루틴을 고르기 전에")+notices("여기에 보이는 루틴과 시간·횟수는 UI 샘플입니다. 실제 연구 데이터베이스 검증 후 근거의 강도와 적용 조건을 표시할 예정입니다.")+demo(),"with-fixed");
 case "routine-search":return pane(back("루틴 탐색")+heading("루틴 검색","내 목적에 가까운 방식부터 찾아요.","FIND A ROUTINE")+
 '<div class="form-field"><label for="searchRoutine">검색어</label><input id="searchRoutine" class="field-input" placeholder="예: 스쿼트, 5×5, 근력" value="'+e(state.search)+'" data-field="search"></div>'+chips(["전체","근력","근비대","나의 루틴"],state.filter,"routineFilter")+
 section("검색 결과")+(state.search.toLowerCase().includes("없음")?'<div class="empty-wrap"><div class="empty-illustration">'+ic("search")+'</div><h3>일치하는 루틴이 없어요.</h3><p>다른 검색어나 목적을 선택해 주세요.</p></div>':routineTile("5×5 베이스","스쿼트·벤치·데드리프트 중심","주 3일 · 기초 근력","routine-detail")+routineTile("볼륨 중심 블록","반복과 총 볼륨 추적","주 4일 · 보조 운동 포함","routine-detail"))+button("직접 루틴 만들기","routine-custom","action-secondary"));
 case "routine-detail":return pane(back("루틴 탐색")+
 '<div class="between"><div class="eyebrow-app">ROUTINE 01 · SAMPLE</div>'+pill("근력")+'</div><h1 class="page-title big">5×5<br>Strength Base</h1><p class="body-copy">반복 가능한 기본 복합운동을 통해 개인의 중량 변화를 살펴보는 훈련 구조.</p>'+
 '<div class="spacer-24"></div>'+card('<div class="grid-three">'+[['3일','주당 빈도'],['5×5','기본 세트'],['3분','목표 휴식']].map(x=>'<div class="center"><div class="card-title" style="font-size:21px">'+x[0]+'</div><span class="card-kicker">'+x[1]+'</span></div>').join("")+'</div>')+
 section("운동 구성")+row("dumbbell","스쿼트 · 5×5","목표 중량은 실제 개인 기록에서 산정","exercise-info")+row("dumbbell","벤치프레스 · 5×5","작업 중량과 휴식은 수정 가능","exercise-info")+row("dumbbell","데드리프트 · 1×5","예시 루틴 · 진행에 따라 변경","exercise-info")+
 section("이 루틴은 왜?")+card('<div class="between"><span class="card-kicker">RESEARCH CONTEXT</span>'+pill("검증 전","status-warning")+'</div><h3 class="card-title" style="margin:10px 0">훈련 원칙과 연구 근거</h3><p class="card-copy">이 루틴의 특정 구성 자체가 개별 연구로 검증되었다고 주장하지 않습니다. 실제 인용과 해석은 검증 후 제공할 예정입니다.</p><div class="spacer-16"></div><button class="inline-btn" data-go="routine-evidence">자세히 확인 '+ic("arrow-right")+'</button>',"")+
 section("운동 일정")+row("calendar","월요일 · 수요일 · 금요일","주간 일정 변경","routine-schedule")+
 '<div class="spacer-24"></div>'+button("이 루틴으로 시작","routine-confirm")+demo(),"with-fixed");
 case "routine-evidence":return pane(back("루틴 상세")+heading("왜 이 루틴일까?","연구 결과, 제품 해석, 개인 적용을 구분합니다.","EVIDENCE & LIMITATIONS")+
 card('<div class="between">'+pill("검증 전","status-warning")+pill("인용 확인 필요")+'</div><h3 class="card-title" style="margin:13px 0 8px">연구 출처를 연결하기 전</h3><p class="card-copy">임의 논문명·저자·DOI를 채우지 않습니다. 근거 자료가 준비되면 원문, 연구 대상, 연구 설계, 제한점을 함께 표시하는 공간입니다.</p>')+
 section("연구 해석 구조")+["연구에서 확인한 사실","적용할 수 있는 훈련 변수","다르게 작용할 수 있는 조건","근거의 강도와 한계"].map((t,i)=>row(["book-open","sliders","alert","flask"][i],t,["원문과 DOI 제공 자리","강도 · 빈도 · 세트 · 휴식","훈련 경력 · 회복 · 부상","작은 표본 · 비교 조건 등"][i],"routine-detail")).join("")+
 section("훈련에 적용할 때")+notices("개별 논문 결과는 모든 사람의 최적 루틴을 뜻하지 않습니다. 이 화면은 UX 디자인 단계의 근거 표시 방식을 검토하기 위한 예시입니다.")+
 '<div class="spacer-24"></div>'+button("루틴 상세로 돌아가기","routine-detail","action-secondary"));
 case "routine-schedule":return pane(back("루틴 상세")+heading("운동할 요일","회복 시간을 고려해 일정을 배치해요.","WEEKLY SCHEDULE")+
 card('<div class="card-title" style="margin-bottom:5px">주 3일 운동</div><p class="card-copy">요일을 누르면 선택이 바뀌어요. 실제 알림은 별도 설정에서 관리합니다.</p><div class="spacer-16"></div><div class="grid-three">'+["월","화","수","목","금","토","일"].map(d=>'<button class="action-secondary" style="padding:12px 0;min-height:43px;'+(state.weekdays.includes(d)?'background:var(--fg);color:var(--app-bg)':'')+'" data-act="day" data-val="'+d+'">'+d+'</button>').join("")+'</div>')+
 section("예상 흐름")+row("activity","훈련 A","월요일 · 스쿼트 중심","routine-detail")+row("activity","훈련 B","수요일 · 벤치 중심","routine-detail")+row("activity","훈련 A","금요일 · 전신","routine-detail")+
 '<div class="spacer-24"></div>'+button("일정 적용","routine-confirm")+demo("요일 선택은 목업의 임시 상태에만 반영됩니다."));
 case "routine-custom":return pane(back("루틴 탐색")+heading("나만의 루틴","정한 원칙을 직접 관리할 수 있어요.","CUSTOM ROUTINE")+
 fld("루틴 이름","customName","나만의 스쿼트 데이")+
 section("훈련 종목")+row("dumbbell","스쿼트","5세트 × 5회 · 75kg (예시)","exercise-info")+row("plus","종목 추가","운동 라이브러리에서 선택","exercise-info")+
 section("세트 구성")+card('<div class="input-double">'+fld("세트","customSet","5","number")+fld("반복","customRep","5","number")+'</div><div class="input-double">'+fld("목표 중량 (kg)","customWeight","75","number")+fld("휴식 (초)","customRest","180","number")+'</div>')+
 section("유의사항")+notices("직접 만든 루틴은 앱이 연구 결과로 추천했다고 표시하지 않습니다.")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="saveCustom">나의 루틴 저장 '+ic("check")+'</button>');
 case "routine-confirm":return pane(back("루틴 상세")+heading("오늘 운동할까요?","시작 전에 순서와 목표를 확인하세요.","BEFORE YOU START")+
 card('<div class="card-kicker">TODAY · STRENGTH BASE</div><h3 class="card-title" style="margin:12px 0 8px">스쿼트 중심 5×5</h3><p class="card-copy">예상 45~60분 · 작업 중량은 세션 중 변경할 수 있어요.</p>')+
 section("오늘의 구성")+["스쿼트","벤치프레스","데드리프트"].map((x,i)=>'<div class="choice-row"><strong>'+String(i+1).padStart(2,"0")+' · '+x+'</strong><span>'+["5 × 5","5 × 5","1 × 5"][i]+'</span></div>').join("")+
 '<div class="spacer-20"></div>'+notices("예상 중량과 횟수는 디자인 목업 예시이며 실제 처방이 아닙니다.")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="startSession">운동 시작 '+ic("play")+'</button><div class="spacer-8"></div>'+button("주간 일정 확인","routine-schedule","action-secondary"));
 case "exercise-info":return pane(back("운동 목록")+heading("스쿼트","바벨을 어깨 뒤쪽에 지지하고 앉았다가 일어나는 복합 운동.","EXERCISE LIBRARY")+
 card('<div class="center" style="padding:20px"><div style="display:grid;place-items:center;height:150px;color:var(--muted)">'+ic("dumbbell")+'<p class="card-copy">향후 동작 시범/3D 모션 슬롯</p></div></div>',"soft")+
 section("기록하는 정보")+row("scale","중량 (kg)","실제 수행한 작업 중량","session-exercise")+row("list","세트 × 반복","수행한 세트별 반복 횟수","session-exercise")+row("timer","세트간 휴식","운동 목표에 맞게 조절","session-rest")+
 section("폼 검수 원칙")+notices("움직이는 릴라 자세 시범은 아직 만들어지지 않았어요. 부정확한 관절 움직임을 운동 교본으로 표시하지 않습니다.")+
 '<div class="spacer-24"></div>'+button("운동 기록하기","session-exercise"));
 }return "";
}

function setRows(){const entries=Array.from({length:5},(_,i)=>state.setLog[i]||{n:i+1,kg:75,reps:5,done:false});return '<div class="set-grid hd"><span>세트</span><span>중량</span><span>반복</span><span>상태</span></div>'+entries.map((x,i)=>'<div class="set-grid"><span>'+(i+1).toString().padStart(2,"0")+'</span><span>'+x.kg+'kg</span><span>'+x.reps+'회</span><span class="'+(x.done?"done":"muted")+'">'+(x.done?ic("check"):"—")+'</span></div>').join("")}
function sessionProgress(){return Math.min(100,Math.floor(state.setCount/5*100))}
function sessionScreen(id){
 switch(id){
 case "session-overview":return pane(back("운동 진행")+
 '<div class="between"><span class="session-live"><span></span>WORKOUT IN PROGRESS</span>'+pill("03 / 05 SETS")+'</div>'+
 '<h1 class="page-title big" style="margin:15px 0 8px">무게는<br>정직하게.</h1><p class="body-copy">오늘의 한 세트가 다음 기록의 기준이에요.</p>'+
 '<div class="spacer-24"></div>'+card('<div class="between"><span class="card-kicker">CURRENT SESSION · SAMPLE</span>'+ic("timer")+'</div><h3 class="card-title" style="margin:12px 0 5px">스쿼트 중심 5×5</h3><p class="card-copy">시작 19:00 · 34분 진행 (예시)</p><div class="hr"></div><div class="progress-track"><span style="width:'+sessionProgress()+'%"></span></div><div class="progress-numbers"><span>세트 진행</span><span>'+Math.min(5,state.setCount)+' / 5</span></div>')+
 section("운동별 진행")+row("dumbbell","스쿼트","'+state.setCount+' / 5 세트 · 75kg (목업)","session-exercise")+row("dumbbell","벤치프레스","0 / 5 세트 · 예정","session-exercise")+row("dumbbell","데드리프트","0 / 1 세트 · 예정","session-exercise")+
 '<div class="spacer-24"></div>'+button("현재 세트 기록하기","session-exercise")+'<button style="width:100%;margin-top:9px" class="action-plain" data-go="session-end-confirm">운동 종료</button>',"with-fixed");
 case "session-exercise":return pane(back("운동 진행")+
 '<div class="between"><span class="session-live"><span></span>세트 기록 중</span><button class="back-action" data-go="session-swap">운동 변경 '+ic("chevron-down")+'</button></div>'+
 '<h1 class="page-title big" style="margin-top:18px">'+e(state.lift)+'</h1><p class="body-copy">5세트 × 5회 · 중량은 실제 수행값을 기록하세요.</p>'+
 '<div class="spacer-16"></div>'+card('<div class="between"><div><div class="card-kicker">NEXT SET</div><div class="metric-number" style="margin-top:7px">0'+Math.min(5,state.setCount+1)+' <span class="metric-unit">/ 05</span></div></div>'+pill("목표 75 kg")+'</div><div class="progress-track" style="margin-top:16px"><span style="width:'+Math.min(100,(state.setCount||2)*20)+'%"></span></div>')+
 section("이번 세트 입력")+
 '<div class="big-entry"><div style="flex:1"><label for="setWeight">중량</label><input id="setWeight" data-field="weight" inputmode="decimal" value="'+e(state.weight)+'" type="number"></div><span class="unit">kg</span><div class="sep"></div><div style="flex:1"><label for="setReps">반복 횟수</label><input id="setReps" data-field="reps" inputmode="numeric" value="'+e(state.reps)+'" type="number"></div><span class="unit">회</span></div>'+
 '<div class="choice-chips"><button data-act="weightStep" data-val="-2.5">− 2.5kg</button><button data-act="weightStep" data-val="2.5">+ 2.5kg</button><button data-act="repStep" data-val="-1">− 1회</button><button data-act="repStep" data-val="1">+ 1회</button></div>'+
 section("세트 기록","session-edit-set","수정")+
 card(setRows())+
 '<div class="spacer-24"></div><button class="action-primary" data-act="completeSet">세트 완료 '+ic("check")+'</button>'+
 '<div class="spacer-8"></div><button class="action-secondary" data-go="session-rest">휴식 타이머 열기</button>',"with-fixed");
 case "session-rest":return pane(back("세트 기록")+
 '<div class="center" style="padding-top:7px"><span class="eyebrow-app">REST BETWEEN SETS</span><h1 class="page-title">조금 쉬어도<br>괜찮아요.</h1><p class="body-copy">다음 세트를 준비하는 시간입니다.</p></div>'+
 '<div class="timer-circle"><small>남은 시간 (목업)</small><strong id="restCountdown">'+String(Math.floor(state.restSeconds/60)).padStart(2,"0")+':'+String(state.restSeconds%60).padStart(2,"0")+'</strong><small>'+((state.timerPaused)?"일시정지":"진행 중")+'</small></div>'+
 '<div class="between" style="justify-content:center;gap:10px"><button class="inline-btn" data-act="restAdjust" data-val="-30">− 30초</button><button class="inline-btn" data-act="toggleTimer">'+ic(state.timerPaused?"play":"pause")+' '+(state.timerPaused?"재개":"일시정지")+'</button><button class="inline-btn" data-act="restAdjust" data-val="30">+ 30초</button></div>'+
 section("다음 세트")+card('<div class="between"><div><div class="card-kicker">SQUAT · SET '+(state.setCount+1)+'</div><div class="card-title" style="margin-top:8px">75 kg · 5회</div></div>'+pill("예정")+'</div>')+
 '<div class="spacer-24"></div>'+button("휴식 끝내고 다음 세트","session-exercise")+
 demo("타이머는 목업 브라우저의 실제 시간으로 카운트합니다. 알림·백그라운드 실행은 지원하지 않습니다."),"with-fixed");
 case "session-edit-set":return pane(back("세트 입력")+heading("세트 수정","수정하면 이 미리보기의 기록만 변경됩니다.","EDIT SET")+
 card('<div class="between"><div class="card-kicker">SET 02 · SQUAT</div>'+pill("최근 완료")+'</div>'+
 '<div class="input-double">'+fld("중량 (kg)","editWeight",state.weight,"number")+fld("반복 (회)","editReps",state.reps,"number")+'</div>')+
 section("기록 상태")+card('<div class="between"><span class="card-title">완료한 세트</span>'+pill("완료","status-success")+'</div><div class="hr"></div><p class="card-copy">기록을 수정하더라도 운동 세션 자체는 유지됩니다.</p>')+
 '<div class="spacer-24"></div><button class="action-primary" data-act="saveSetEdit">변경 사항 저장 '+ic("check")+'</button><button class="action-plain" style="width:100%;margin-top:10px" data-act="deleteSet">이 세트 삭제 (확인)</button>');
 case "session-swap":return pane(back("세트 입력")+heading("운동 변경","기구를 사용할 수 없거나 순서를 바꿔야 할 때.","CHANGE EXERCISE")+
 '<div class="spacer-12"></div>'+["스쿼트","벤치프레스","데드리프트","바벨 로우","오버헤드 프레스"].map((name,i)=>'<button class="large-choice tap '+(state.lift===name?"active":"")+'" data-act="chooseLift" data-val="'+name+'"><span class="choice-illustration">'+ic("dumbbell")+'</span><span style="flex:1"><strong>'+name+'</strong><p>'+["현재 선택 종목","상체 밀기","전신 복합","상체 당기기","어깨·상체"][i]+'</p></span><span class="check-circle '+(state.lift===name?"selected":"")+'">'+(state.lift===name?ic("check"):"")+'</span></button>').join("")+
 '<div class="spacer-24"></div>'+notices("변경한 운동은 원본 루틴과 별도 기록으로 구분해야 합니다.")+
 '<div class="spacer-16"></div>'+button("이 종목으로 계속","session-exercise"));
 case "session-end-confirm":return pane(back("운동 진행")+
 '<div class="center" style="padding-top:30px">'+photo(3,"lila-stand")+'<h1 class="page-title">여기서<br>마칠까요?</h1><p class="body-copy">완료한 기록은 유지됩니다.<br>진행 중인 세트는 저장되지 않아요.</p></div>'+
 '<div class="spacer-16"></div>'+card('<div class="grid-two"><div><div class="card-kicker">기록한 세트</div><div class="metric-number" style="margin-top:10px">'+state.setCount+'</div></div><div><div class="card-kicker">총 운동 시간</div><div class="metric-number" style="margin-top:10px">34 <span class="metric-unit">분</span></div></div></div>')+
 '<div class="spacer-24"></div><button class="action-primary" data-act="endWorkout">운동 종료 및 저장 '+ic("check")+'</button><div class="spacer-8"></div>'+button("운동 계속하기","session-overview","action-secondary"));
 case "session-summary":return pane('<div class="center" style="padding-top:20px"><span class="eyebrow-app">WORKOUT COMPLETED</span>'+photo(4,"lila-stand")+'<h1 class="page-title" style="margin-top:7px">오늘도<br>해냈어요.</h1><p class="body-copy">무게보다 중요한 건 오늘 남긴 기록이에요.</p></div>'+
 section("오늘의 결과")+
 '<div class="grid-two">'+card('<div class="card-kicker">총 세트</div><div class="metric-number" style="margin-top:10px">'+state.setCount+' <span class="metric-unit">세트</span></div>')+
 card('<div class="card-kicker">훈련 볼륨</div><div class="metric-number" style="margin-top:10px">'+fmt(state.setLog.reduce((n,l)=>n+Number(l.kg)*Number(l.reps),0))+' <span class="metric-unit">kg</span></div>')+'</div>'+
 '<div class="spacer-12"></div>'+card('<div class="between"><div><div class="card-kicker">기록 상태</div><h3 class="card-title" style="margin:8px 0 0">운동 기록 저장 (목업)</h3></div>'+pill("샘플")+'</div>')+
 '<div class="spacer-24"></div>'+button("기록 자세히 보기","records-detail")+'<div class="spacer-8"></div>'+button("홈으로","home","action-secondary")+demo(),"with-fixed");
 }return "";
}

function recordTile(date,sub,volume,to){return '<button class="row-tile tap" data-go="'+to+'"><span class="row-icon">'+ic("calendar-check")+'</span><span class="row-main"><strong>'+date+'</strong><span>'+sub+'</span></span><span style="font-size:11px;font-weight:740">'+volume+' kg</span><span class="chev">'+ic("chevron-right")+'</span></button>'}
function recordScreen(id){
 switch(id){
 case "records":return pane(appHeader()+heading("한 세트씩<br>쌓인 시간.","지난 훈련을 빠르게 확인하세요.","YOUR WORKOUT LOG")+
 '<div class="spacer-16"></div><div class="grid-two">'+card('<div class="card-kicker">이번 달 운동</div><div class="metric-number" style="margin-top:14px">9 <span class="metric-unit">회</span></div>')+card('<div class="card-kicker">지난 7일 볼륨</div><div class="metric-number" style="margin-top:14px">3,200 <span class="metric-unit">kg</span></div>')+'</div>'+
 section("최근 운동","records-calendar","캘린더")+
 chips(["전체","스쿼트","벤치","데드리프트"],state.recordFilter,"recordFilter")+
 recordTile("10월 9일 · 금요일","스쿼트 중심 5×5 · 완료","1,520","records-detail")+
 recordTile("10월 7일 · 수요일","벤치프레스 중심 · 완료","960","records-detail")+
 recordTile("10월 5일 · 월요일","전신 기본 루틴 · 완료","720","records-detail")+
 section("기록 추가")+card('<div class="between"><div><div class="card-title">수동으로 기록</div><p class="card-copy" style="margin-top:5px">놓친 운동도 차근차근 남겨요.</p></div>'+ic("plus")+'</div>',"tap","record-new")+demo(),"with-fixed");
 case "records-calendar":return pane(back("기록")+heading("운동 캘린더","기록한 날과 회복한 날을 함께 살펴봐요.","CONSISTENCY")+
 card('<div class="between"><span class="card-title">2026년 10월</span>'+pill("샘플")+'</div>'+dots()+'<div class="between" style="margin-top:14px"><span class="card-copy">● 운동 기록 있음</span><strong style="font-size:12px">9일</strong></div>')+
 section("이번 주")+['월','화','수','목','금','토','일'].map((t,i)=>'<div class="choice-row"><span class="fw7">'+t+'요일</span><span>'+(i%2===0?'운동 기록 · 예시':'휴식/기록 없음')+'</span></div>').join("")+
 '<div class="spacer-24"></div>'+button("최근 운동 보기","records")+button("10월 9일 기록 상세","records-detail","action-secondary")+demo());
 case "records-detail":return pane(back("운동 기록")+
 '<span class="eyebrow-app">2026 · OCT 09 · SAMPLE</span><h1 class="page-title big">스쿼트 중심<br>5×5.</h1><p class="body-copy">금요일 · 19:00 ~ 19:48 · 샘플 세션</p>'+
 '<div class="spacer-24"></div><div class="grid-two">'+card('<div class="card-kicker">총 볼륨</div><div class="metric-number" style="margin-top:10px">1,520 <span class="metric-unit">kg</span></div>')+card('<div class="card-kicker">총 시간</div><div class="metric-number" style="margin-top:10px">48 <span class="metric-unit">분</span></div>')+'</div>'+
 section("세트별 내역")+card('<div class="between"><strong class="card-title">스쿼트</strong>'+pill("5세트")+'</div><div class="hr"></div>'+setRows())+
 section("세션 메모")+card('<p class="card-copy">마지막 세트가 조금 무거웠지만 자세를 유지하는 데 집중함. (예시)</p>')+
 '<div class="spacer-24"></div>'+button("기록 수정","records-edit","action-secondary")+'<div class="spacer-8"></div>'+button("성장 추이 보기","growth-lift")+demo(),"with-fixed");
 case "records-edit":return pane(back("기록 상세")+heading("기록 수정","수정 전에 날짜와 종목을 확인하세요.","EDIT HISTORY")+
 fld("운동 날짜","editDate","2026-10-09","date")+
 card('<div class="card-kicker">수정할 세트</div><div class="input-double">'+fld("중량 (kg)","historyWeight","75","number")+fld("반복 (회)","historyReps","5","number")+'</div>')+
 section("메모")+fld("운동 메모","historyNote","자세를 유지하며 완료")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="saveRecord">수정 기록 저장 '+ic("check")+'</button>'+
 '<div class="spacer-16"></div>'+notices("실제 앱에서는 수정 이력과 중량 추이를 안전하게 보존해야 합니다."));
 case "record-new":return pane(back("운동 기록")+heading("새로운 기록","이전에 수행한 운동을 수동으로 기록하세요.","MANUAL ENTRY")+
 fld("운동 날짜","newDate","2026-10-09","date")+fld("종목","newExercise","스쿼트")+
 '<div class="input-double">'+fld("중량 (kg)","newWeight","75","number")+fld("반복 (회)","newReps","5","number")+'</div>'+
 fld("세트 수","newSets","3","number")+fld("메모 (선택)","newNote","")+
 '<div class="spacer-16"></div>'+notices("샘플 기록은 이 HTML 목업에만 임시 반영됩니다. 외부 서비스에 저장되지 않아요.")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="addRecord">기록 추가 '+ic("plus")+'</button>');
 }return "";
}
function growthScreen(id){
 switch(id){
 case "growth":return pane(appHeader()+heading("숫자로 확인하는<br>나의 성장.","더 강해지는 과정은 기록에 남아요.","MY PROGRESS")+
 '<div class="spacer-16"></div><div class="grid-two">'+card('<div class="card-kicker">스쿼트 e1RM</div><div class="metric-number" style="margin-top:13px">128 <span class="metric-unit">kg</span></div><div class="metric-label">반복 세트로 추정 · 예시</div>',"tap","growth-lift")+card('<div class="card-kicker">최근 운동 세션</div><div class="metric-number" style="margin-top:13px">9 <span class="metric-unit">회</span></div><div class="metric-label">최근 30일 · 예시</div>',"tap","records")+'</div>'+
 section("근력의 흐름","growth-lift")+card('<div class="between"><span class="card-kicker">ESTIMATED 1RM · SQUAT</span>'+pill("e1RM")+'</div>'+graph()+'<div class="graph-key"><span><i></i>추정 중량</span><span><i class="alt"></i>미리보기 데이터</span></div>',"","growth-lift")+
 section("루틴 검토","growth-experiment")+row("flask","프로토콜 결과","수행률과 경과를 분리해 확인","growth-experiment")+
 section("무게꾼의 동반자","growth-lila")+card('<div class="between"><div><div class="card-kicker">LILA · LV.3</div><h3 class="card-title" style="margin:8px 0 5px">성장 릴라</h3><p class="card-copy">나의 기록을 함께 축적해요.</p></div>'+photo(3,"lila-small")+'</div>',"tap","growth-lila")+
 section("알아두기","growth-insight")+notices("e1RM은 반복 횟수와 중량으로 계산한 추정치입니다. 실제로 측정한 1RM과 같지 않을 수 있어요.")+demo(),"with-fixed");
 case "growth-lift":return pane(back("성장")+
 heading(e(state.lift)+" 성장","개인 기록의 변화는 비교하되, 인과관계를 단정하지 않아요.","LIFT ANALYTICS")+
 '<div class="spacer-16"></div>'+chips(["스쿼트","벤치프레스","데드리프트"],state.lift,"chooseLiftGrowth")+
 card('<div class="between"><span class="card-kicker">e1RM · 추정</span>'+pill("SAMPLE")+'</div><div class="metric-number" style="margin-top:12px">128 <span class="metric-unit">kg</span></div><div class="card-copy" style="margin-top:7px">반복 세트 기반 계산값</div>'+graph([88,93,102,111,121,128])+
 '<div class="graph-key"><span><i></i>e1RM (추정)</span><span><i class="alt"></i>예시 변화</span></div>')+
 section("실측 기준")+row("target","실제 1RM 직접 입력","성공한 1회 최대 중량만","growth-max")+
 section("해석 방법")+row("info","e1RM 계산과 한계","반복 수와 중량의 관계","growth-insight")+
 section("세트 볼륨")+card('<div class="card-kicker">최근 6주 · 샘플</div>'+bars([31,46,42,61,72,84])+'<div class="card-copy" style="margin-top:12px">볼륨 상승만으로 훈련 효과가 입증되지는 않습니다.</div>')+demo());
 case "growth-max":return pane(back("성장 분석")+
 heading("실측 1RM 입력","내가 실제로 성공한 1회 최대 중량을 기록해요.","VERIFIED MAX ENTRY")+
 card('<div class="card-kicker">SQUAT · TRUE 1RM</div>'+fld("성공한 최대 중량 (kg)","measuredMax","","number")+
 '<p class="card-copy">성공한 1회 수행 중량만 입력하세요. 5회 세트에서 계산한 e1RM은 넣지 않습니다.</p>')+
 section("기록 조건")+fld("측정 날짜","maxDate","2026-10-09","date")+
 '<div class="spacer-16"></div>'+notices("실측 최고 중량은 무리한 측정을 권하는 기능이 아닙니다. 부상 위험이 없는 적절한 환경에서 측정한 값만 기록해 주세요.")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="saveMax">1RM 기록 확인 '+ic("check")+'</button>'+demo());
 case "growth-experiment":return pane(back("성장")+
 heading("루틴을 돌아보는<br>시간.","목표 대비 진행 과정을 회고해요.","PROTOCOL REVIEW")+
 '<div class="spacer-16"></div>'+card('<div class="between"><span class="card-kicker">5×5 STRENGTH BASE</span>'+pill("진행 중")+'</div><div class="card-title" style="margin-top:11px">3주 차 / 6주</div><div class="progress-track" style="margin-top:17px"><span style="width:50%"></span></div><div class="progress-numbers"><span>예시 진행률</span><span>50%</span></div>')+
 section("확인할 지표")+row("check-circle","수행률","계획 9회 / 실제 7회 (샘플)","records-calendar")+row("chart","e1RM 변화","주차별 추정 변화 확인","growth-lift")+row("timer","회복과 휴식","실제 휴식 기록이 있는 경우에만 비교","growth-insight")+
 section("연구와 비교")+notices("개인의 중량 상승이나 하락만으로 루틴 자체의 효과를 입증하거나 반증할 수 없습니다.")+
 '<div class="spacer-24"></div>'+button("루틴 구성 살펴보기","routine-detail","action-secondary"));
 case "growth-lila":return pane(back("성장")+
 '<div class="center"><span class="eyebrow-app">MEET LILA</span><h1 class="page-title">함께 자라는<br>나의 동반자.</h1></div>'+
 card('<div class="center" style="padding:13px 0"><span class="card-kicker">LEVEL 0'+state.lilaLevel+' · '+['','아기','새싹','성장','단단한','숙련','무게왕'][state.lilaLevel]+' 릴라</span>'+photo(state.lilaLevel,"lila-stand")+'<div class="progress-track"><span style="width:56%"></span></div><div class="progress-numbers"><span>현재 레벨</span><span>다음 단계로 56% · 예시</span></div></div>')+
 section("성장 단계")+card('<div class="between">'+[1,2,3,4,5,6].map(i=>'<button style="border:0;background:transparent;text-align:center;padding:0;color:var(--fg)" data-act="showLila" data-val="'+i+'"><img src="'+ROOT+'lila_lv0'+i+'_4x.png" style="width:40px;height:55px;object-fit:contain"><span style="display:block;font-size:9px;font-weight:750">'+i+'</span></button>').join("")+'</div>')+
 section("릴라와 함께하는 이유")+notices("캐릭터는 훈련 기록을 동반하는 디자인 요소입니다. 현재의 레벨·진행률은 목업 샘플이며 실제 보상 규칙은 아직 확정되지 않았습니다.")+
 '<div class="spacer-16"></div>'+button("성장 분석","growth","action-secondary")+demo());
 case "growth-insight":return pane(back("종목별 성장")+
 heading("수치는 어떻게<br>계산할까요?","알고 보면 훈련 기록이 더 선명해져요.","METHODOLOGY")+
 card('<div class="card-kicker">ESTIMATED 1RM</div><h3 class="card-title" style="margin:11px 0 8px">Epley 추정식</h3><div class="card soft" style="text-align:center;margin:10px 0;font-size:13px;font-weight:730">e1RM ≈ 중량 × (1 + 반복 횟수 ÷ 30)</div><p class="card-copy">예: 100kg × 5회 → 약 116.7kg (추정). 고반복 세트에서는 오차가 커질 수 있으며 개인차가 존재합니다.</p>')+
 section("꼭 구분할 내용")+row("check-circle","실측 1RM","직접 성공한 1회 최대 중량","growth-max")+row("chart","추정 e1RM","반복 세트로 계산한 추정치","growth-lift")+row("book-open","연구 근거","출처와 대상 집단을 확인하는 과정","routine-evidence")+
 '<div class="spacer-16"></div>'+notices("두 값은 측정 의미가 다릅니다. 사용자 간 비교/등급화에는 신중해야 합니다."));
 }return "";
}

function toggleRow(key,label,description){return '<div class="choice-row"><div><strong>'+label+'</strong><div class="card-copy" style="margin-top:5px">'+description+'</div></div><button class="switch '+(state.flags[key]?"active":"")+'" role="switch" aria-checked="'+(state.flags[key]?"true":"false")+'" aria-label="'+label+'" data-act="toggleFlag" data-val="'+key+'"></button></div>'}
function settingScreen(id){
 switch(id){
 case "settings":return pane(appHeader()+heading("설정","화면·데이터·개인 설정을 관리해요.","PREFERENCES")+
 '<div class="spacer-16"></div>'+card('<div class="between"><div class="flex"><div class="avatar">무</div><div><div class="card-title">나의 운동 공간</div><p class="card-copy">게스트 · 이 기기에 저장 (예시)</p></div></div>'+ic("chevron-right")+'</div>',"tap","settings-profile")+
 section("사용 환경")+row("user","프로필·목표","경험·운동 종목 변경","settings-profile")+row("sun","화면 테마","라이트 · 다크 · 시스템","settings-theme")+row("scale","중량 단위","kg / lb","settings-units")+row("bell","운동 알림","운동·휴식 알림","settings-notices")+
 section("개인 데이터")+row("database","데이터 관리","백업 · 복원 · 동기화","settings-data")+row("cloud","계정 · 동기화","선택적 Apple 로그인","settings-account")+
 section("무게꾼")+row("info","앱 정보","브랜드 · 개발 버전 · 고지","settings-about")+demo(),"with-fixed");
 case "settings-profile":return pane(back("설정")+
 heading("내 프로필","운동 목표는 언제든 바꿀 수 있어요.","YOUR PROFILE")+
 fld("표시 이름","profileName","무게꾼")+
 section("현재 목표")+chips(["1RM 향상","근비대","운동 습관"],state.goal,"goal")+
 section("훈련 경험")+chips(["초급자","중급자","숙련자"],state.level,"level")+
 section("관심 종목")+["스쿼트","벤치프레스","데드리프트"].map(x=>'<div class="choice-row"><strong>'+x+'</strong><button class="switch '+(state.lifts.includes(x)?"active":"")+'" data-act="toggleLift" data-val="'+x+'" aria-label="'+x+' 활성화"></button></div>').join("")+
 '<div class="spacer-24"></div><button class="action-primary" data-act="saveProfile">프로필 저장 '+ic("check")+'</button>');
 case "settings-theme":return pane(back("설정")+heading("보기 좋은 화면","언제든 밝기를 바꿀 수 있어요.","APPEARANCE")+
 card('<div class="card-kicker">앱 표시 테마</div>'+
 choice("라이트 모드","밝은 배경과 차콜 텍스트","sun","theme","light"===state.theme)+
 choice("다크 모드","어두운 배경과 밝은 텍스트","moon","theme","dark"===state.theme)+
 '<p class="card-copy" style="margin:15px 0 0">시스템 테마 따라가기는 정식 앱에서 지원할 예정입니다.</p>')+
 section("미리보기")+card('<div class="between"><div><div class="card-kicker">CURRENT THEME</div><h3 class="card-title" style="margin-top:7px">무게꾼 화면</h3><p class="card-copy" style="margin-top:4px">브랜드 기본은 차콜과 화이트.</p></div>'+photo(2,"lila-small")+'</div>')+
 '<div class="spacer-24"></div>'+button("홈에서 확인","home"));
 case "settings-units":return pane(back("설정")+heading("중량 표시 단위","수치가 내게 가장 익숙한 방식으로 보이게.","WEIGHT UNITS")+
 card(choice("kg","킬로그램 · 대한민국 기본", "scale","unit",state.unit==="kg")+
 choice("lb","파운드 · 미국식 표시","scale","unit",state.unit==="lb"))+
 '<div class="spacer-16"></div>'+card('<div class="card-kicker">예시 중량 변환</div><div class="metric-number" style="margin:12px 0">'+(state.unit==="kg"?"100 kg":"220.5 lb")+'</div><p class="card-copy">내부 저장 단위와 반올림 정책은 실제 구현 단계에서 확정합니다.</p>')+
 '<div class="spacer-24"></div>'+button("설정으로 돌아가기","settings"));
 case "settings-notices":return pane(back("설정")+heading("알림 설정","꼭 필요한 순간에만 알려드릴게요.","NOTIFICATIONS")+
 card(toggleRow("workout","운동 일정","선택한 루틴 예정일")+toggleRow("rest","세트간 휴식","휴식 타이머 종료")+toggleRow("news","새 연구·업데이트","제품 관련 정보 알림"))+
 '<div class="spacer-24"></div>'+notices("이 토글은 화면 목업에서만 바뀝니다. 실제 푸시 권한·알림 예약·배경 타이머 구현은 별도 개발이 필요합니다.")+
 '<div class="spacer-16"></div>'+button("알림 센터 미리보기","notifications","action-secondary"));
 case "settings-data":return pane(back("설정")+
 heading("내 운동 기록은<br>내가 관리해요.","백업과 복원 방식은 사용자가 결정합니다.","DATA & PRIVACY")+
 card('<div class="between"><span class="card-kicker">CURRENT STORAGE</span>'+pill("로컬 우선")+'</div><h3 class="card-title" style="margin-top:12px">이 기기에 보관</h3><p class="card-copy" style="margin-top:9px">기록이 다른 서비스로 전송되기 전에는 명시적으로 동의를 받아야 합니다.</p>')+
 section("데이터 작업")+row("download","백업 파일 내보내기","실제 앱에서만 가능 · 목업은 동작하지 않음","settings-data")+row("upload","백업 복원","파일 검증·중복 기록 처리 필요","settings-data")+row("cloud","선택적 동기화","Apple 로그인 후 사용자 승인","settings-account")+
 '<div class="spacer-16"></div>'+notices("디자인 검토 화면에는 실제 운동 데이터가 없습니다. 이 버튼들로 개인 기록이 서버에 저장되거나 삭제되지 않습니다.")+
 '<div class="spacer-24"></div>'+button("계정·동기화 설정","settings-account"));
 case "settings-account":return pane(back("설정")+heading("계정과 동기화","계정 없이도 모든 기본 기록 기능을 사용할 수 있어요.","ACCOUNT")+
 card('<div class="between"><div><div class="card-kicker">ACCOUNT TYPE</div><h3 class="card-title" style="margin-top:7px">게스트 모드</h3></div>'+pill("연결 안 됨")+'</div><p class="card-copy" style="margin-top:12px">기록은 현재 사용하는 기기에서 관리해요. 다른 기기로 옮기려면 백업 또는 선택적 동기화를 이용합니다.</p>')+
 section("Apple 계정")+card('<div class="between"><span class="card-title">Apple로 계속하기</span>'+ic("lock")+'</div><p class="card-copy" style="margin-top:9px">개발자 설정과 실제 인증 흐름이 준비된 이후에만 연결 가능합니다.</p><button class="action-secondary" style="margin-top:14px" data-act="mockApple">Apple 로그인은 목업에서 실행하지 않음</button>')+
 section("알아두기")+notices("Apple 계정에 로그인하지 않았는데 ‘연결 완료’라고 표시해서는 안 됩니다. 실서비스에서는 토큰·서버 응답을 확인한 후 상태가 전환됩니다.")+
 '<div class="spacer-24"></div>'+button("로컬 데이터 관리","settings-data"));
 case "settings-about":return pane(back("설정")+
 '<div class="center" style="padding:20px 0 8px"><div class="logo-splash" style="width:75px;height:75px;border-radius:24px;margin:auto">'+ic("dumbbell")+'</div><h1 class="page-title">무게꾼</h1><p class="body-copy">무게를 아는 사람들.<br>논문으로 고르고, 바벨로 검증한다.</p></div>'+
 section("브랜드의 약속")+card('<p class="card-copy" style="font-size:12px;line-height:1.9">좋은 훈련은 단순한 유행이나 느낌이 아니라, 설명할 수 있는 근거와 스스로 쌓은 기록에서 출발한다고 믿어요.</p>')+
 section("정보")+row("file-text","개발 정보","UX 목업 · 제품 적용 전 디자인 리뷰","settings-about")+row("shield","개인정보 처리 원칙","기록 보호·최소 정보 수집","settings-data")+row("book-open","연구 출처 안내","원문·해석·제한점 구분","routine-evidence")+
 '<div class="spacer-24"></div>'+notices("현재 표시되는 앱 소개와 버전은 UX 목업 기준입니다. 정식 법적 고지·정책 문구는 출시 전에 확정해야 합니다."));
 }return "";
}

function currentRoot(id){if(id.startsWith("routine")||id==="exercise-info")return "routines";if(id.startsWith("session"))return "session-overview";if(id.startsWith("record"))return "records";if(id.startsWith("growth"))return "growth";if(id.startsWith("setting"))return "settings";return "home"}
function navMarkup(id){
 const tab=[
 ["home","홈","home"],
 ["routines","루틴","dumbbell"],
 ["records","기록","calendar"],
 ["growth","성장","chart"]
 ];
 const selected=currentRoot(id);
 return '<div class="phone-nav">'+tab.map(([name,title,icon])=>'<button data-go="'+name+'" class="'+(selected===name?"active":"")+'" aria-label="'+title+'" aria-current="'+(selected===name?"page":"false")+'">'+ic(icon)+'<span>'+title+'</span></button>').join("")+'</div>'
}
function railMarkup(searchTerm){
 const search=(searchTerm||"").trim().toLowerCase();
 return groups.map(group=>{
 const found=definitions.filter(s=>s.group===group.id&&(!search||[s.name,s.purpose,s.id].join(" ").toLowerCase().includes(search)));
 if(!found.length)return "";
 return '<div class="screen-group"><div class="group-head"><span>'+group.name+'</span><em>'+found.length.toString().padStart(2,"0")+'</em></div>'+
 found.map(s=>'<button class="screen-link '+(state.page===s.id?"active":"")+'" data-go="'+s.id+'" title="'+e(s.purpose)+'"><span class="side-icon">'+ic(group.icon)+'</span><span>'+e(s.name)+'</span><small>'+String(definitions.indexOf(s)+1).padStart(2,"0")+'</small></button>').join("")+'</div>';
 }).join("");
}
function inspectorMarkup(d){
 return '<div class="inspector-block"><div class="inspector-kicker">SCREEN '+String(definitions.indexOf(d)+1).padStart(2,"0")+' / '+definitions.length+'</div><div class="inspector-value">'+e(d.name)+'</div><p class="inspector-body">'+e(d.purpose)+'</p></div>'+
 '<div class="inspector-block"><div class="inspector-kicker">DESIGN CHECKPOINTS</div><ul class="design-points">'+d.review.split(" · ").map(r=>'<li>'+e(r)+'</li>').join("")+'</ul></div>'+
 '<div class="inspector-block"><div class="inspector-kicker">FLOW · 다음 화면</div><div class="flow-chips">'+d.next.map(id=>'<button data-go="'+id+'">'+e(screenMap[id]?.name||id)+' →</button>').join("")+'</div></div>';
}
function render(opts){
 opts=opts||{};
 const meta=screenMap[state.page]||screenMap.home;
 let markup="";
 try{
  if(meta.group==="start")markup=startScreen(meta.id);
  if(meta.group==="home")markup=homeScreen(meta.id);
  if(meta.group==="routine")markup=routineScreen(meta.id);
  if(meta.group==="session")markup=sessionScreen(meta.id);
  if(meta.group==="records")markup=recordScreen(meta.id);
  if(meta.group==="growth")markup=growthScreen(meta.id);
  if(meta.group==="settings")markup=settingScreen(meta.id);
 }catch(error){console.error("Render error in "+meta.id,error);markup='<div class="app-shell"><h2>화면을 표시할 수 없습니다.</h2><p class="body-copy">'+e(error.message)+'</p></div>'}
 if(!markup)markup='<div class="app-shell"><h2>준비 중: '+e(meta.name)+'</h2></div>';
 const previousScroll=viewport.scrollTop;
 viewport.innerHTML=markup;
 viewport.classList.toggle("full-height",meta.group==="start"||["session-rest","session-summary"].includes(meta.id));
 nav.innerHTML=meta.group==="start"||["session-rest","session-summary"].includes(meta.id)?"":navMarkup(meta.id);
 phone.dataset.theme=state.theme;
 const group=groups.find(g=>g.id===meta.group);
 document.getElementById("currentGroupLabel").textContent=group?group.name:"";
 document.getElementById("stageTitle").textContent=meta.name;
 document.getElementById("stageSubtitle").textContent=meta.purpose;
 document.getElementById("screenCounter").textContent=String(definitions.indexOf(meta)+1).padStart(2,"0")+" / "+definitions.length;
 document.getElementById("screenGroups").innerHTML=railMarkup(document.getElementById("screenSearch").value);
 document.getElementById("screenInspector").innerHTML=inspectorMarkup(meta);
 document.querySelectorAll(".theme-chip").forEach(b=>b.classList.toggle("selected",b.dataset.theme===state.theme));
 const tx=document.getElementById("feedbackText");
 tx.value=state.notes[meta.id]||"";
 document.getElementById("reviewCount").textContent=Object.values(state.notes).filter(x=>x&&x.trim()).length;
 if(opts.preserveScroll)viewport.scrollTop=previousScroll;else viewport.scrollTop=0;
 hydrate();
}
function go(id,replaceHistory){
 if(!screenMap[id]){toast("아직 연결되지 않은 화면입니다.");return}
 if(state.page!==id&&!replaceHistory)state.history.push(state.page);
 if(state.history.length>60)state.history.shift();
 state.page=id;
 // Navigation is managed locally; avoid URL hash events in file:// mode.
 render();
}
function navigateBack(){
 const previous=state.history.pop();
 if(previous&&screenMap[previous])go(previous,true);
 else go("home",true);
}
let toastTimeout;
function toast(message){
 const box=document.getElementById("phoneToast");
 box.innerHTML='<div class="toast">'+ic("info")+'<span>'+e(message)+'</span></div>';
 clearTimeout(toastTimeout);
 toastTimeout=setTimeout(()=>box.innerHTML="",2800);
}
function act(type,val){
 switch(type){
  case "back":navigateBack();break;
  case "goal":state.goal=val;render({preserveScroll:true});break;
  case "level":state.level=val;render({preserveScroll:true});break;
  case "routineFilter":state.filter=val;render({preserveScroll:true});break;
  case "recordFilter":state.recordFilter=val;render({preserveScroll:true});break;
  case "chooseLiftGrowth":state.lift=val;render({preserveScroll:true});break;
  case "chooseLift":state.lift=val;render({preserveScroll:true});break;
  case "unit":state.unit=val;render({preserveScroll:true});break;
  case "theme":state.theme=val==="라이트 모드"?"light":val==="다크 모드"?"dark":val;render({preserveScroll:true});break;
  case "day":if(state.weekdays.includes(val))state.weekdays=state.weekdays.filter(x=>x!==val);else state.weekdays.push(val);render({preserveScroll:true});break;
  case "toggleLift":if(state.lifts.includes(val))state.lifts=state.lifts.filter(x=>x!==val);else state.lifts.push(val);render({preserveScroll:true});break;
  case "toggleFlag":state.flags[val]=!state.flags[val];render({preserveScroll:true});break;
  case "startSession":state.sessionActive=true;state.setCount=0;state.setLog=[];go("session-overview");toast("운동 세션을 시작했어요 (목업).");break;
  case "weightStep":state.weight=String(Math.max(0,(parseFloat(state.weight)||0)+parseFloat(val)));render({preserveScroll:true});break;
  case "repStep":state.reps=String(Math.max(0,(parseFloat(state.reps)||0)+parseFloat(val)));render({preserveScroll:true});break;
  case "completeSet":
   if(!(Number(state.weight)>0)||!(Number(state.reps)>0)){toast("중량과 횟수를 확인해 주세요.");break;}
   state.setCount++;state.setLog.push({n:state.setCount,kg:Number(state.weight),reps:Number(state.reps),done:true});
   state.restSeconds=180;state.timerPaused=false;
   go(state.setCount>=5?"session-end-confirm":"session-rest");
   toast(state.setCount+"세트 기록 완료 (목업).");break;
  case "restAdjust":state.restSeconds=clamp(state.restSeconds+Number(val),0,3600);render({preserveScroll:true});break;
  case "toggleTimer":state.timerPaused=!state.timerPaused;render({preserveScroll:true});break;
  case "endWorkout":state.sessionActive=false;go("session-summary");break;
  case "saveSetEdit":
   state.weight=document.getElementById("editWeight")?.value||state.weight;
   state.reps=document.getElementById("editReps")?.value||state.reps;
   if(state.setLog.length){let x=state.setLog[state.setLog.length-1];x.kg=+state.weight;x.reps=+state.reps}
   go("session-exercise");toast("수정 내용을 목업에 반영했어요.");break;
  case "deleteSet":
   if(window.confirm("가장 최근 완료한 세트를 이 목업에서 삭제할까요?")){state.setLog.pop();state.setCount=Math.max(0,state.setCount-1);go("session-exercise");toast("목업 세트가 삭제됐어요.");}
   break;
  case "saveCustom":state.routine=document.getElementById("customName")?.value||"내 루틴";go("routine-confirm");toast("목업의 루틴 이름을 저장했어요.");break;
  case "saveRecord":go("records-detail");toast("목업 기록이 수정됐어요.");break;
  case "addRecord":go("records");toast("목업 기록을 추가했어요.");break;
  case "saveMax":if(!(Number(document.getElementById("measuredMax")?.value)>0)){toast("성공한 중량을 입력해 주세요.");break;}go("growth-lift");toast("목업의 실측 기준이 입력됐어요.");break;
  case "saveProfile":go("settings");toast("목업 프로필이 적용됐어요.");break;
  case "mockApple":toast("이 목업은 실제 Apple 로그인에 연결되지 않습니다.");break;
  case "showLila":state.lilaLevel=Number(val);render({preserveScroll:true});toast("Lv."+val+" 외형을 미리보고 있어요.");break;
  default:toast("아직 연결되지 않은 동작입니다.");
 }
}
function saveCurrentNote(){
 const t=document.getElementById("feedbackText").value.trim();
 if(t)state.notes[state.page]=t;else delete state.notes[state.page];
 try{localStorage.setItem(K,JSON.stringify(state.notes))}catch(e){console.warn("Review notes not saved in localStorage",e)}
 render({preserveScroll:true});
 toast(t?"이 화면의 의견을 저장했어요.":"화면 의견을 지웠어요.");
}
function exportNotes(){
 const items=definitions.filter(d=>state.notes[d.id]?.trim()).map(d=>({screen:d.name,id:d.id,group:d.group,feedback:state.notes[d.id]}));
 const lines=["# 무게꾼 — 화면별 디자인 피드백","","> 토큰은 확정하지 않은 단계의 UX 검토 의견입니다.","",...items.flatMap(x=>["## "+x.screen+" ("+x.id+")","",x.feedback,""])];
 if(!items.length){toast("먼저 마음에 들지 않는 화면을 메모해 주세요.");return}
 const blob=new Blob([lines.join("\n")],{type:"text/markdown;charset=utf-8"});
 const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="MUGEKKUN_UI_REVIEW.md";document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
 toast(items.length+"개 화면의 의견을 내보냈어요.");
}
let timerHandle=setInterval(()=>{
 if(state.page==="session-rest"&&!state.timerPaused&&state.restSeconds>0){
  state.restSeconds--;
  const target=document.getElementById("restCountdown");
  if(target)target.textContent=String(Math.floor(state.restSeconds/60)).padStart(2,"0")+":"+String(state.restSeconds%60).padStart(2,"0");
  if(!state.restSeconds){state.timerPaused=true;toast("휴식 시간이 끝났어요 (목업).")}
 }
},1000);
document.addEventListener("click",event=>{
 const button=event.target.closest("button[data-go],button[data-act],.tap[data-go]");
 if(!button)return;
 const goId=button.dataset.go;const action=button.dataset.act;
 if(goId)go(goId);else if(action)act(action,button.dataset.val);
});
document.addEventListener("keydown",event=>{
 const target=event.target.closest(".tap[data-go]");
 if(target&&(event.key==="Enter"||event.key===" ")){event.preventDefault();go(target.dataset.go)}
});
document.addEventListener("input",event=>{
 if(event.target.dataset.field){
  state[event.target.dataset.field]=event.target.value;
  if(event.target.id==="searchRoutine"){
   const caret=event.target.selectionStart;
   render({preserveScroll:true});
   const replacement=document.getElementById("searchRoutine");
   if(replacement){replacement.focus();replacement.setSelectionRange(caret,caret)}
  }
 }
});
document.getElementById("screenSearch").addEventListener("input",event=>{
 document.getElementById("screenGroups").innerHTML=railMarkup(event.target.value);
});
document.querySelectorAll(".theme-chip").forEach(b=>b.addEventListener("click",()=>{state.theme=b.dataset.theme;render({preserveScroll:true})}));
document.getElementById("jumpFirst").addEventListener("click",()=>go("splash"));
document.getElementById("saveFeedback").addEventListener("click",saveCurrentNote);
document.getElementById("clearFeedback").addEventListener("click",()=>{document.getElementById("feedbackText").value="";saveCurrentNote()});
document.getElementById("exportFeedback").addEventListener("click",exportNotes);
document.getElementById("resetDemo").addEventListener("click",()=>{
 const notes=state.notes,theme=state.theme;
 Object.assign(state,{history:[],goal:"1RM 향상",level:"중급자",lifts:["스쿼트","벤치프레스","데드리프트"],routine:"5×5 베이스",filter:"전체",recordFilter:"전체",lift:"스쿼트",lilaLevel:3,growthPeriod:"3개월",weekdays:["월","수","금"],unit:"kg",setCount:0,setLog:[],weight:"75",reps:"5",restSeconds:165,timerPaused:true,sessionActive:false,flags:{workout:true,rest:true,news:false},search:"",saved:false});
 state.notes=notes;state.theme=theme;go("home");toast("목업 상태만 초기화했어요. 피드백은 유지됩니다.");
});
const initial=location.hash.slice(1);
if(screenMap[initial])state.page=initial;
hydrate(document);
render();
window.MugekkunStudio={screens:definitions.map(d=>d.id),go,render,state,screenMap};
})();
