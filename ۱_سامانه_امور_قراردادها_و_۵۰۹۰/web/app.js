// سامانه جامع امور قراردادها و مهندسی ادعا — خط ۱۰ متروی تهران
// قرارگاه سازندگی خاتم‌الانبیاء (ص) — موسسه مهندسی رهاب

let projectData = null;
let cashflowChart = null;
let delaysChart = null;
let allKnowledge = null;
let allContractGuide = null;

// فرمت‌دهی مبالغ به صورت سه رقم سه رقم
function formatNumber(num) {
  if (num === null || num === undefined) return "۰";
  return Number(num).toLocaleString('fa-IR');
}

// تبدیل ارقام لاتین به فارسی
function toPersianDigits(n) {
  if (n === null || n === undefined) return "";
  const f = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return String(n).replace(/[0-9]/g, w => f[+w]);
}

// سوئیچ تم تاریک و روشن
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.classList.toggle('dark');
  if (!isDark) {
    html.classList.add('light');
    localStorage.setItem('contract_theme', 'light');
  } else {
    html.classList.remove('light');
    localStorage.setItem('contract_theme', 'dark');
  }
  try { renderCharts(); } catch(e) {}
}

// بارگذاری تم ذخیره شده
function initTheme() {
  const saved = localStorage.getItem('contract_theme');
  if (saved === 'light') {
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.add('light');
  } else {
    document.documentElement.classList.add('dark');
    document.documentElement.classList.remove('light');
  }
}

// عناوین تب‌ها
const viewTitles = {
  'dashboard': { title: 'داشبورد جامع امور قراردادها و مهندسی ادعا', desc: 'پروژه احداث خط ۱۰ متروی تهران — قرارگاه خاتم‌الانبیاء (مهندسی رهاب)' },
  'certificates': { title: 'پایش صورت‌وضعیت‌ها و پیش‌پرداخت‌ها (ماده ۳۷)', desc: 'کنترل مواعد ۱۰ روزه رسیدگی و تادیه و محاسبه روزشمار تاخیرات ۵۰۹۰' },
  'events': { title: 'جبهه‌های کاری و معارضات خط ۱۰ (ماده ۲۸)', desc: 'ثبت و رصد موانع ملکی، تأسیساتی، ترافیکی و توقفات کارگاه‌های غربی' },
  'delay-claim': { title: 'موتور محاسبات لایحه تاخیرات ۵۰۹۰ و همپوشانی', desc: 'پالایش ریاضی ایام تداخل مالی و موانع فیزیکی جهت استخراج تمدید قطعی' },
  'knowledge-base': { title: 'دانشنامه قوانین و مقررات نظام فنی و اجرایی', desc: 'استنادات نشریه ۴۳۱۱، بخشنامه ۵۰۹۰، تعلیق و دستورالعمل مدیریت ادعای خاتم' },
  'contract-guide': { title: 'اطلس ۵۱ بند کلیدی و راهنمای قرارداد خط ۱۰', desc: 'فهرست موضوعی مواد، موافقتنامه و شرایط خصوصی با شماره صفحات دقیق پیمان' },
  'documents': { title: 'استودیوی تولید و دانلود اسناد و مکاتبات رسمی', desc: 'تولید فوری لوایح تاخیرات، نامه‌های ادعایی، صورت‌جلسات و دفترچه فرموله‌شده اکسل' }
};

// تغییر تب
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('sidebar-link-active'));
  
  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.remove('hidden');
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const btn = document.querySelector(`.sidebar-link[data-tab="${tabId}"]`);
  if (btn) btn.classList.add('sidebar-link-active');

  const meta = viewTitles[tabId] || viewTitles['dashboard'];
  const titleEl = document.getElementById('current-view-title');
  if (titleEl) {
    titleEl.textContent = meta.title;
    if (titleEl.nextElementSibling) titleEl.nextElementSibling.textContent = meta.desc;
  }

  if (tabId === 'documents') loadGeneratedDocuments();
  if (tabId === 'contract-guide' && !allContractGuide) loadContractGuide();
  if (tabId === 'knowledge-base' && !allKnowledge) loadKnowledgeBase();
}

// نمایش پیام اعلان شناور
function showToast(message, type = 'success') {
  const existing = document.getElementById('app-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'app-toast';
  const bg = type === 'success' ? 'bg-amber-500 text-slate-950 font-black' : 'bg-rose-600 text-white font-bold';
  toast.className = `fixed bottom-6 left-6 z-50 ${bg} text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 transition-all duration-300 transform translate-y-3 opacity-0`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}" class="w-4 h-4"></i>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  if (typeof lucide !== 'undefined') lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-3', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('translate-y-3', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// دریافت داده‌های پروژه
async function fetchProjectData() {
  try {
    const res = await fetch('/api/project');
    if (!res.ok) throw new Error('خطا در برقراری ارتباط با سرور');
    projectData = await res.json();
    renderDashboard();
    renderCertificates();
    renderEvents();
    renderDelayClaimBreakdown();
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch (err) {
    console.error(err);
    showToast('خطا در بارگذاری داده‌ها از سرور', 'error');
  }
}

// رندر داشبورد اصلی
function renderDashboard() {
  if (!projectData) return;
  const c = projectData.contract || {};
  const a = projectData.analysis || {};
  const f = projectData.financial_summary || {};

  // شماره پیمان در سایدبار
  const sbContract = document.getElementById('sidebar-contract-no');
  if (sbContract) sbContract.textContent = c.contract_number || '۰۱/۱۰/۷۲/م';

  // تمدید در هدر
  const topDelay = document.getElementById('topbar-delay-days');
  if (topDelay) topDelay.textContent = `+${toPersianDigits(a.net_justified_delay_days || 379)} روز تمدید مصوب`;

  // مبلغ اولیه بخش یک
  const initAmount = c.initial_amount || 397070750000000;
  const initBillion = Math.round(initAmount / 1e9);
  const initHemmat = (initAmount / 1e13).toFixed(1);
  const elInit = document.getElementById('kpi-initial-amount');
  if (elInit) elInit.textContent = `${formatNumber(initBillion)} م ریال (${toPersianDigits(initHemmat)} همت)`;

  // سقف ۲۵٪
  const ceilingBillion = Math.round(initAmount * 0.25 / 1e9);
  const elCeiling = document.getElementById('kpi-ceiling-25');
  if (elCeiling) elCeiling.textContent = `${formatNumber(ceilingBillion)} م ریال`;

  // کارکرد مصوب
  const totalApproved = f.total_approved || 244600000000000;
  const approvedBillion = Math.round(totalApproved / 1e9);
  const elAppr = document.getElementById('kpi-total-approved');
  if (elAppr) elAppr.textContent = `${formatNumber(approvedBillion)} م ریال`;

  // درصد پیشرفت مالی
  const elProg = document.getElementById('kpi-financial-progress');
  if (elProg) elProg.textContent = `${toPersianDigits(f.ceiling_usage_percent || 61.6)}٪`;

  // روزهای تمدید مجاز
  const elNet = document.getElementById('kpi-net-delay-days');
  if (elNet) elNet.textContent = `${toPersianDigits(a.net_justified_delay_days || 379)} روز تقویمی`;

  const elMonths = document.getElementById('kpi-delay-months');
  if (elMonths) elMonths.textContent = `${toPersianDigits(a.extension_months || 12.4)} ماه تمدید قطعی`;

  // مواعد زمانی
  const elNewFinish = document.getElementById('kpi-new-finish-date');
  if (elNewFinish) elNewFinish.textContent = a.new_finish_date || '۱۴۰۹/۰۳/۱۵';

  const elInitFinish = document.getElementById('kpi-initial-finish');
  if (elInitFinish) elInitFinish.textContent = a.initial_finish_date || '۱۴۰۸/۰۳/۰۲';

  // رندر تضامین
  const guarTbody = document.getElementById('tbl-guarantees-dashboard');
  if (guarTbody) {
    guarTbody.innerHTML = '';
    (projectData.guarantees || []).forEach(g => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="font-bold text-white">${g.guarantee_type}</td>
        <td class="text-slate-400">${g.bank_name}</td>
        <td class="num-font font-bold text-amber-400">${formatNumber(g.amount)}</td>
        <td class="font-mono text-slate-300 text-xs">${g.expiry_date}</td>
        <td class="text-center">
          <span class="badge-status badge-emerald">${g.status}</span>
        </td>
      `;
      guarTbody.appendChild(tr);
    });
  }

  // رندر خلاصه معارضین در داشبورد
  const evList = document.getElementById('dashboard-events-list');
  if (evList) {
    evList.innerHTML = '';
    (projectData.events || []).slice(0, 3).forEach(e => {
      const item = document.createElement('div');
      item.className = 'p-3.5 rounded-xl border border-slate-750 bg-slate-800/50 flex items-start justify-between gap-3 text-xs';
      item.innerHTML = `
        <div>
          <div class="font-bold text-white flex items-center gap-2">
            <span class="w-2 h-2 rounded-full ${e.status === 'رفع معارض' ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}"></span>
            <span>${e.station_or_shaft}</span>
          </div>
          <div class="text-slate-300 mt-1 leading-relaxed text-[11px]">${e.description}</div>
          <div class="text-slate-400 mt-1.5 font-mono text-[10px]">بازه: ${e.start_date} لغایت ${e.end_date || 'جاری'}</div>
        </div>
        <span class="badge-status ${e.status === 'رفع معارض' ? 'badge-emerald' : 'badge-amber'} shrink-0">
          ${toPersianDigits(e.delay_days)} روز توقف
        </span>
      `;
      evList.appendChild(item);
    });
  }

  // رندر نمودارها به صورت ایمن
  try {
    renderCharts();
  } catch (e) {
    console.error('Chart error:', e);
  }
}

// رندر نمودارها
function renderCharts() {
  if (!projectData || typeof Chart === 'undefined') return;

  const isDark = document.documentElement.classList.contains('dark');
  const textColor = isDark ? '#94A3B8' : '#475569';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';

  // ۱. نمودار جریان نقدینگی
  const canvasCash = document.getElementById('chart-cashflow');
  if (canvasCash) {
    try {
      const certs = (projectData.certificates || []).filter(c => c.cert_type !== 'advance');
      const labels = certs.map(c => (c.cert_number || '').replace('صورت‌وضعیت کارکرد موقت شماره ', 'ص.و '));
      const approvedVals = certs.map(c => Math.round((c.approved_amount || 0) / 1e9));
      const paidVals = certs.map(c => Math.round((c.paid_amount || 0) / 1e9));

      const ctxCash = canvasCash.getContext('2d');
      if (cashflowChart) cashflowChart.destroy();
      cashflowChart = new Chart(ctxCash, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'کارکرد مصوب مشاور',
              data: approvedVals,
              backgroundColor: '#f59e0b',
              borderRadius: 6,
              borderSkipped: false
            },
            {
              label: 'واریزی / حواله کارفرما',
              data: paidVals,
              backgroundColor: '#10b981',
              borderRadius: 6,
              borderSkipped: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              align: 'end',
              labels: { font: { family: 'Vazirmatn', size: 10, weight: 'bold' }, color: textColor, usePointStyle: true, boxWidth: 6 }
            },
            tooltip: {
              titleFont: { family: 'Vazirmatn', size: 11 },
              bodyFont: { family: 'Vazirmatn', size: 11 },
              callbacks: { label: ctx => ` ${ctx.dataset.label}: ${formatNumber(ctx.raw)} میلیارد ریال` }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: gridColor },
              ticks: { font: { family: 'Vazirmatn', size: 9 }, color: textColor, callback: v => formatNumber(v) }
            },
            x: {
              grid: { display: false },
              ticks: { font: { family: 'Vazirmatn', size: 9, weight: 'bold' }, color: textColor }
            }
          }
        }
      });
    } catch(err) {
      console.error('Cashflow chart error:', err);
    }
  }

  // ۲. نمودار دونات تفکیک تاخیرات
  const canvasDelays = document.getElementById('chart-delays');
  if (canvasDelays) {
    try {
      const a = projectData.analysis || {};
      const ctxDelays = canvasDelays.getContext('2d');
      if (delaysChart) delaysChart.destroy();
      delaysChart = new Chart(ctxDelays, {
        type: 'doughnut',
        data: {
          labels: ['تاخیرات ۵۰۹۰ مالی', 'موانع فیزیکی کارگاه', 'همپوشانی ایام مشترک'],
          datasets: [{
            data: [
              Math.max(0, Math.round((a.financial_calendar_days || 153) - (a.overlap_days_count || 0))),
              Math.max(0, Math.round((a.technical_calendar_days || 226) - (a.overlap_days_count || 0))),
              Math.round(a.overlap_days_count || 51.5)
            ],
            backgroundColor: ['#f59e0b', '#38bdf8', '#a855f7'],
            borderColor: isDark ? '#151e32' : '#ffffff',
            borderWidth: 3,
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '70%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: { font: { family: 'Vazirmatn', size: 10, weight: 'bold' }, color: textColor, usePointStyle: true, boxWidth: 6 }
            }
          }
        }
      });
    } catch(err) {
      console.error('Delays chart error:', err);
    }
  }
}

// رندر جدول صورت‌وضعیت‌ها
function renderCertificates() {
  if (!projectData) return;
  const tbody = document.getElementById('tbl-certificates');
  if (!tbody) return;
  tbody.innerHTML = '';
  (projectData.certificates || []).forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-bold text-white">${c.cert_number}</td>
      <td class="font-mono text-slate-400 text-xs">${c.submission_date}</td>
      <td class="font-mono text-slate-400 text-xs">${c.consultant_approval_date || '-'}</td>
      <td class="font-mono ${c.client_payment_date ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'} text-xs">${c.client_payment_date || 'در حال رسیدگی'}</td>
      <td class="num-font text-slate-300">${formatNumber(c.approved_amount)}</td>
      <td class="num-font font-bold text-emerald-400">${formatNumber(c.paid_amount)}</td>
      <td><span class="badge-status badge-blue">${c.payment_method}</span></td>
      <td class="text-center font-bold text-slate-200 num-font">${toPersianDigits(c.total_delay_days)}</td>
      <td class="text-center font-bold text-amber-400 num-font font-mono">${toPersianDigits((c.justified_delay_days || 0).toFixed(2))}</td>
    `;
    tbody.appendChild(tr);
  });
}

// رندر جدول معارضین
function renderEvents() {
  if (!projectData) return;
  const tbody = document.getElementById('tbl-events');
  if (!tbody) return;
  tbody.innerHTML = '';
  (projectData.events || []).forEach(e => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-bold text-white">${e.station_or_shaft}</td>
      <td class="text-slate-300 leading-relaxed">${e.description}</td>
      <td class="text-center">${e.impact_on_critical_path ? '<span class="badge-status badge-amber">بله (بحرانی)</span>' : '<span class="badge-status badge-blue">خیر</span>'}</td>
      <td class="font-mono text-slate-400 text-xs">${e.start_date}</td>
      <td class="font-mono text-slate-400 text-xs">${e.end_date || 'جاری'}</td>
      <td class="text-center font-bold text-amber-400 num-font">${toPersianDigits(e.delay_days)} روز</td>
      <td class="font-mono text-slate-400 text-xs">${e.official_letter_ref || '-'}</td>
      <td class="text-center"><span class="badge-status ${e.status === 'رفع معارض' ? 'badge-emerald' : 'badge-amber'}">${e.status}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// رندر جدول محاسبات همپوشانی
function renderDelayClaimBreakdown() {
  if (!projectData) return;
  const tbody = document.getElementById('tbl-overlap-breakdown');
  if (!tbody) return;
  tbody.innerHTML = '';

  const certs = projectData.certificates || [];
  const events = projectData.events || [];

  certs.forEach(c => {
    if (c.justified_delay_days > 0) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="font-bold text-white">${c.cert_number}</td>
        <td class="font-mono text-slate-400 text-xs">${c.delay_start_date || c.submission_date} تا ${c.delay_end_date || c.client_payment_date || 'جاری'}</td>
        <td class="text-center num-font text-slate-400">${toPersianDigits(c.total_delay_days)} روز</td>
        <td><span class="badge-status badge-blue">ماده ۳۷ (۵۰۹۰)</span></td>
        <td><span class="text-slate-400 text-xs">پالایش شده در تقویم</span></td>
        <td class="text-center font-bold text-amber-400 font-mono num-font">+${toPersianDigits((c.justified_delay_days || 0).toFixed(1))} روز T</td>
      `;
      tbody.appendChild(tr);
    }
  });

  events.forEach(e => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-bold text-white">${e.station_or_shaft}</td>
      <td class="font-mono text-slate-400 text-xs">${e.start_date} تا ${e.end_date || 'جاری'}</td>
      <td class="text-center num-font text-slate-400">${toPersianDigits(e.delay_days)} روز</td>
      <td><span class="badge-status badge-amber">مانع کارگاهی (ماده ۲۸)</span></td>
      <td><span class="text-slate-400 text-xs">${e.impact_on_critical_path ? 'مسیر بحرانی' : 'غیربحرانی'}</span></td>
      <td class="text-center font-bold text-white font-mono num-font">${toPersianDigits(e.delay_days)} روز</td>
    `;
    tbody.appendChild(tr);
  });
}

// بارگذاری دانشنامه حقوقی
async function loadKnowledgeBase() {
  try {
    const res = await fetch('/api/knowledge_base');
    allKnowledge = await res.json();
    renderKnowledgeBase(allKnowledge);
  } catch (err) {
    console.error(err);
  }
}

// رندر کارت‌های دانشنامه
function renderKnowledgeBase(kbData) {
  const container = document.getElementById('knowledge-cards-container');
  if (!container) return;
  container.innerHTML = '';

  (kbData.articles_4311 || []).forEach(art => {
    const card = document.createElement('div');
    card.className = 'exec-card p-6 flex flex-col justify-between';
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between text-xs mb-3">
          <span class="badge-status badge-blue">نشریه ۴۳۱۱ • ماده ${toPersianDigits(art.article_number)}</span>
          <span class="text-slate-400 font-medium">شرایط عمومی پیمان</span>
        </div>
        <h4 class="text-sm font-bold text-white mb-2">${art.title}</h4>
        <p class="text-xs text-slate-300 leading-relaxed">${art.text}</p>
      </div>
      <div class="mt-4 pt-3 border-t border-slate-800 bg-amber-500/5 p-3.5 rounded-xl border border-amber-500/20">
        <span class="text-xs font-bold text-amber-400 block mb-1">استناد در مهندسی ادعا:</span>
        <p class="text-slate-300 leading-relaxed text-xs">${art.claim_basis}</p>
      </div>
    `;
    container.appendChild(card);
  });

  (kbData.circulars || []).forEach(circ => {
    const card = document.createElement('div');
    card.className = 'exec-card p-6 flex flex-col justify-between border-amber-500/30';
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between text-xs mb-3">
          <span class="badge-status badge-amber">${circ.category}</span>
          <span class="font-mono text-slate-400 text-xs">${circ.number}</span>
        </div>
        <h4 class="text-sm font-bold text-white mb-2">${circ.title}</h4>
        <p class="text-xs text-slate-300 leading-relaxed">${circ.summary}</p>
        ${circ.formula ? `<div class="mt-3 p-2.5 bg-slate-900 border border-slate-700 text-amber-400 font-mono text-xs font-bold text-center rounded-lg dir-ltr">${circ.formula}</div>` : ''}
      </div>
      <div class="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
        ${(circ.key_clauses || []).map(c => `<div>• ${c}</div>`).join('')}
      </div>
    `;
    container.appendChild(card);
  });
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

// جستجو در دانشنامه
function searchKnowledge() {
  const input = document.getElementById('knowledge-search-input');
  if (!input || !allKnowledge) return;
  const q = input.value.trim().toLowerCase();
  if (!q) {
    renderKnowledgeBase(allKnowledge);
    return;
  }
  const filteredArticles = (allKnowledge.articles_4311 || []).filter(a =>
    `ماده ${a.article_number} ${a.title} ${a.text} ${a.claim_basis}`.toLowerCase().includes(q)
  );
  const filteredCircs = (allKnowledge.circulars || []).filter(c =>
    `${c.title} ${c.summary} ${c.number} ${c.category} ${(c.key_clauses || []).join(' ')}`.toLowerCase().includes(q)
  );
  renderKnowledgeBase({
    articles_4311: filteredArticles,
    circulars: filteredCircs
  });
}

// بارگذاری اطلس ۵۱ بند
async function loadContractGuide() {
  try {
    const res = await fetch('/api/contract_guide');
    allContractGuide = await res.json();
    renderContractGuide(allContractGuide);
  } catch (err) {
    console.error(err);
  }
}

// رندر اطلس
function renderContractGuide(items) {
  const tbody = document.getElementById('tbl-contract-guide');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center p-6 text-slate-500">موردی یافت نشد.</td></tr>';
    return;
  }
  items.forEach(it => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-mono text-slate-400 text-center font-bold">${toPersianDigits(it.row_num)}</td>
      <td class="font-bold text-white">${it.subject}</td>
      <td class="text-amber-400 font-mono text-xs">${it.clause_ref}</td>
      <td class="text-center font-mono font-bold text-emerald-400 bg-emerald-500/5">ص ${toPersianDigits(it.page_number)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// جستجو در اطلس
function searchContractGuide() {
  const input = document.getElementById('guide-search-input');
  if (!input || !allContractGuide) return;
  const q = input.value.trim().toLowerCase();
  if (!q) {
    renderContractGuide(allContractGuide);
    return;
  }
  const filtered = allContractGuide.filter(it =>
    (it.subject || '').toLowerCase().includes(q) ||
    (it.clause_ref || '').toLowerCase().includes(q)
  );
  renderContractGuide(filtered);
}

// تولید و دانلود یک سند
async function generateDoc(docType) {
  try {
    showToast('در حال تولید و فرمت‌بندی سند رسمی...', 'success');
    const res = await fetch('/api/generate_doc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_type: docType })
    });
    const result = await res.json();
    if (result.status === 'success') {
      showToast(`سند آماده شد: ${result.filename}`, 'success');
      const a = document.createElement('a');
      a.href = result.download_url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      loadGeneratedDocuments();
    } else {
      showToast(`خطا: ${result.message}`, 'error');
    }
  } catch (err) {
    showToast('خطا در برقراری ارتباط با سرور', 'error');
    console.error(err);
  }
}

// تولید یکپارچه کلیه اسناد
async function generateAllDocs() {
  const types = [
    { type: 'delay_claim', label: 'لایحه جامع تاخیرات ۵۰۹۰ (Word)' },
    { type: 'excel_full', label: 'دفترچه محاسبات جامع اکسل' },
    { type: 'payment_letter', label: 'نامه تاخیر در پرداخت (Word)' },
    { type: 'obstacle_letter', label: 'نامه معارض تاسیساتی (Word)' },
    { type: 'ceiling_letter', label: 'نامه هشدار سقف ۲۵٪ (Word)' },
    { type: 'site_minutes', label: 'صورت‌جلسه کارگاهی (Word)' }
  ];

  showToast('در حال تولید یکجای کلیه اسناد و دفترچه‌ها...', 'success');
  let count = 0;
  for (const item of types) {
    try {
      const res = await fetch('/api/generate_doc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_type: item.type })
      });
      const data = await res.json();
      if (data.status === 'success') count++;
    } catch (e) {
      console.error(e);
    }
  }
  showToast(`${toPersianDigits(count)} سند رسمی با موفقیت تولید و در مخزن ذخیره شد.`, 'success');
  loadGeneratedDocuments();
}

// بارگذاری فایل‌های تولید شده در مخزن
async function loadGeneratedDocuments() {
  try {
    const res = await fetch('/api/documents');
    const docs = await res.json();
    const tbody = document.getElementById('tbl-generated-docs');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!docs || docs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3" class="text-center p-6 text-slate-500">تاکنون سندی تولید نشده است.</td></tr>';
      return;
    }
    docs.forEach(doc => {
      const tr = document.createElement('tr');
      const isWord = doc.filename.endsWith('.docx');
      const badgeClass = isWord ? 'badge-blue' : 'badge-emerald';
      const tag = isWord ? 'DOCX' : 'XLSX';

      tr.innerHTML = `
        <td class="font-bold text-white flex items-center gap-2.5">
          <span class="badge-status ${badgeClass}">${tag}</span>
          <span>${doc.filename}</span>
        </td>
        <td class="font-mono text-slate-400 text-xs">${toPersianDigits(doc.size_kb)} KB</td>
        <td class="text-center">
          <a href="${doc.download_url}" download class="btn-ghost py-1 px-3 text-xs">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            <span>دانلود</span>
          </a>
        </td>
      `;
      tbody.appendChild(tr);
    });
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch (err) {
    console.error(err);
  }
}

// مودال‌ها
function openNewCertModal() {
  document.getElementById('modal-new-cert').classList.remove('hidden');
  if (typeof lucide !== 'undefined') lucide.createIcons();
}
function closeNewCertModal() {
  document.getElementById('modal-new-cert').classList.add('hidden');
}

function openNewEventModal() {
  document.getElementById('modal-new-event').classList.remove('hidden');
  if (typeof lucide !== 'undefined') lucide.createIcons();
}
function closeNewEventModal() {
  document.getElementById('modal-new-event').classList.add('hidden');
}

// ثبت صورت‌وضعیت جدید
async function submitNewCert(e) {
  e.preventDefault();
  const payload = {
    cert_number: document.getElementById('cert-input-number').value,
    cert_type: document.getElementById('cert-input-type').value,
    payment_method: document.getElementById('cert-input-method').value,
    submission_date: document.getElementById('cert-input-submission').value,
    consultant_approval_date: document.getElementById('cert-input-approval').value || null,
    client_payment_date: document.getElementById('cert-input-payment').value || null,
    claimed_amount: parseFloat(document.getElementById('cert-input-approved').value) || 0,
    approved_amount: parseFloat(document.getElementById('cert-input-approved').value) || 0,
    paid_amount: parseFloat(document.getElementById('cert-input-paid').value) || 0,
    notes: document.getElementById('cert-input-notes').value || ''
  };

  try {
    const res = await fetch('/api/certificates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const ans = await res.json();
    showToast(ans.message, 'success');
    closeNewCertModal();
    fetchProjectData();
  } catch (err) {
    showToast('خطا در ذخیره اطلاعات', 'error');
  }
}

// ثبت معارض جدید
async function submitNewEvent(e) {
  e.preventDefault();
  const payload = {
    station_or_shaft: document.getElementById('ev-input-station').value,
    event_type: document.getElementById('ev-input-type').value,
    impact_on_critical_path: document.getElementById('ev-input-critical').value === 'true',
    start_date: document.getElementById('ev-input-start').value,
    end_date: document.getElementById('ev-input-end').value || null,
    description: document.getElementById('ev-input-desc').value,
    official_letter_ref: document.getElementById('ev-input-letter').value || null,
    status: document.getElementById('ev-input-end').value ? 'رفع معارض' : 'در حال پیگیری'
  };

  try {
    const res = await fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const ans = await res.json();
    showToast(ans.message, 'success');
    closeNewEventModal();
    fetchProjectData();
  } catch (err) {
    showToast('خطا در ذخیره اطلاعات', 'error');
  }
}

// ساعت و تقویم در هدر
function updateJalaliHeaderClock() {
  const el = document.getElementById('topbar-jalali-date');
  if (!el) return;
  const now = new Date();
  const days = ['یک‌شنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه'];
  const dayName = days[now.getDay()];
  el.textContent = `${dayName} • تقویم کاری خط ۱۰`;
}

// شروع به کار اولیه
window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  fetchProjectData();
  updateJalaliHeaderClock();
  if (typeof lucide !== 'undefined') lucide.createIcons();
});
