/**
 * app.js — 主逻辑：依赖加载、品种/合约选择、月差/价差计算与渲染
 * 数据模型（紧凑结构）：
 *   index.products + 品种文件 {dates, series[标签].close}（每品种独立日期轴）
 */
(function () {
  'use strict';

  function $(id) { return document.getElementById(id); }

  var state = {
    dataset: null,
    source: null,          // 'local' | 'remote' | 'none'
    mode: 'spread',        // 'spread' 跨品种价差 | 'calendar' 同品种月差
    view: 'seasonal',      // 'seasonal' 季节性图（默认）| 'time' 时序图
    rangeStart: 0,         // 时序图范围（交易日索引，含）
    rangeEnd: 0,
    currentDates: null,    // 当前 A 品种的日期轴,
    seasonalStart: 0,      // 季节性图年内范围（MM-DD 索引，含）
    seasonalEnd: 0,
    yMin: null,            // 纵轴范围（null = 自动）
    yMax: null,
    hiddenYears: {},       // 季节性图用户在图例上隐藏的年份 { "2020": true }
    legA: { product: null, contract: null },
    legB: { product: null, contract: null },
    chart: null
  };

  var rafPending = false;  // 滑块拖动节流（每帧最多一次重绘）

  var CDN = {
    xlsx: 'https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js',
    chart: 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js'
  };

  // ================= 依赖加载（本地库优先，缺失回退 CDN） =================
  function ensureLibs(cb) {
    var pending = [];
    if (!window.XLSX) pending.push({ local: 'js/xlsx.full.min.js', cdn: CDN.xlsx, ok: function () { return !!window.XLSX; } });
    if (!window.Chart) pending.push({ local: 'js/chart.umd.js', cdn: CDN.chart, ok: function () { return !!window.Chart; } });
    loadNext(pending, cb);
  }
  function loadNext(list, cb) {
    if (!list.length) { cb(); return; }
    var item = list.shift();
    var srcs = [item.local, item.cdn];
    tryNext(srcs, 0, item, function () {
      if (!item.ok()) console.warn('[app] 依赖加载失败: ' + srcs.join(' / '));
      loadNext(list, cb);
    });
  }
  function tryNext(srcs, i, item, done) {
    if (i >= srcs.length) { done(); return; }
    var s = document.createElement('script');
    var finished = false;
    var timer = setTimeout(function () {   // 超时保护：加载挂起 6 秒也继续
      if (!finished) { finished = true; done(); }
    }, 6000);
    s.src = srcs[i];
    s.onload = function () { if (!finished) { finished = true; clearTimeout(timer); done(); } };
    s.onerror = function () {
      if (!finished) { finished = true; clearTimeout(timer); tryNext(srcs, i + 1, item, done); }
    };
    document.head.appendChild(s);
  }

  // ================= 初始化 =================
  window.addEventListener('DOMContentLoaded', function () {
    ensureLibs(function () {
      bindEvents();
      FuturesData.loadDataset().then(function (res) {
        state.source = res.source;
        if (res.dataset) { initSelector(); syncViewControls(); }
        renderDataStatus();
        if (res.error) {
          showStatus('err', '线上数据加载失败：' + res.error.message);
        }
      });
    });
  });

  function bindEvents() {
    document.querySelectorAll('.mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { setMode(btn.dataset.mode); });
    });
    document.querySelectorAll('.view-switch .mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { setView(btn.dataset.view); });
    });
    $('legAProduct').addEventListener('change', function () {
      state.legA.product = this.value;
      state.legA.contract = null;
      fillContracts('A');
      if (state.mode === 'calendar') syncCalendarLegB();
      refreshAsync();
    });
    $('legAContract').addEventListener('change', function () {
      state.legA.contract = this.value;
      refreshResult();
    });
    $('legBProduct').addEventListener('change', function () {
      state.legB.product = this.value;
      state.legB.contract = null;
      fillContracts('B');
      refreshAsync();
    });
    $('legBContract').addEventListener('change', function () {
      state.legB.contract = this.value;
      refreshResult();
    });
    $('swapBtn').addEventListener('click', swapLegs);
    $('rangeStart').addEventListener('input', function () { onRangeInput('start'); });
    $('rangeEnd').addEventListener('input', function () { onRangeInput('end'); });
    $('rangeResetBtn').addEventListener('click', resetRange);
    $('yMin').addEventListener('change', applyYRange);
    $('yMax').addEventListener('change', applyYRange);
    $('yAutoBtn').addEventListener('click', resetYRange);
    document.querySelectorAll('.range-q').forEach(function (btn) {
      btn.addEventListener('click', function () { applyQuickRange(parseInt(btn.dataset.months, 10)); });
    });
    $('tableLimit').addEventListener('change', renderTable);
    $('tableOrder').addEventListener('change', renderTable);
    $('showPricesChk').addEventListener('change', refreshResult);
  }

  // ================= 选择器 =================
  function initSelector() {
    var prods = FuturesData.getProducts();
    // value 用品种代码（P），显示带中文名（P · 棕榈油）
    fillSelect($('legAProduct'), prods, false, prodLabel);
    fillSelect($('legBProduct'), prods, false, prodLabel);
    if (!prods.length) { showStatus('warn', '数据中没有任何品种'); return; }

    state.legA.product = $('legAProduct').value;
    state.legB.product = $('legBProduct').value;
    fillContracts('A');
    fillContracts('B');
    pickDefaultContracts();
    setMode(state.mode);
    refreshAsync();   // 异步加载 A/B 品种数据后计算
  }

  /** 异步确保 A/B 品种数据已加载，再计算渲染 */
  function refreshAsync() {
    FuturesData.ensureProducts([state.legA.product, state.legB.product]).then(function () {
      refreshResult();
      initRange();
    }).catch(function (err) {
      showStatus('err', '数据加载失败：' + err.message);
    });
  }

  function prodLabel(code) {
    var info = FuturesData.getProductInfo(code);
    return info && info.name ? code + ' · ' + info.name : code;
  }

  /** 填充下拉；displayFn(v) 用于显示名（默认显示原值），value 始终为 v */
  function fillSelect(sel, values, keep, displayFn) {
    var prev = sel.value;
    sel.innerHTML = '';
    values.forEach(function (v) {
      var o = document.createElement('option');
      o.value = v;
      o.textContent = displayFn ? displayFn(v) : v;
      sel.appendChild(o);
    });
    if (keep && values.indexOf(prev) >= 0) sel.value = prev;
  }

  /** 填充合约下拉（标签列表：主力/最近/01...） */
  function fillContracts(which) {
    var leg = which === 'A' ? state.legA : state.legB;
    var sel = which === 'A' ? $('legAContract') : $('legBContract');
    if (!leg.product) { sel.innerHTML = '<option value="">—</option>'; return; }
    var info = FuturesData.getProductInfo(leg.product);
    var ctrs = info ? info.contracts : [];
    fillSelect(sel, ctrs, true);
    if (ctrs.length && !sel.value) sel.value = ctrs[0];
    leg.contract = sel.value || null;
  }

  function pickDefaultContracts() {
    var infoA = FuturesData.getProductInfo(state.legA.product);
    var infoB = FuturesData.getProductInfo(state.legB.product);
    var ctrsA = infoA ? infoA.contracts : [];
    var ctrsB = infoB ? infoB.contracts : [];
    if (ctrsA.length) { state.legA.contract = ctrsA[0]; $('legAContract').value = ctrsA[0]; }
    if (ctrsB.length) { state.legB.contract = ctrsB[0]; $('legBContract').value = ctrsB[0]; }
  }

  // ================= 时间轴范围（双滑块） =================
  /** 年内 MM-DD 全集（基于全部交易日，排序） */
  function seasonalAllLabels() {
    var set = {};
    (state.currentDates || []).forEach(function (d) { set[d.slice(5)] = 1; });
    return Object.keys(set).sort();
  }

  /** 按当前视图初始化滑块范围 */
  function initRange() {
    if (state.view === 'seasonal') initSeasonalRange();
    else initTimeRange();
    updateRangeUI();
  }

  function initTimeRange() {
    var n = (state.currentDates || []).length;
    state.rangeStart = 0;
    state.rangeEnd = n - 1;
    setSlider($('rangeStart'), 0, n - 1, 0);
    setSlider($('rangeEnd'), 0, n - 1, n - 1);
  }

  function initSeasonalRange() {
    var labels = seasonalAllLabels();
    var n = labels.length;
    state.seasonalStart = 0;
    state.seasonalEnd = n - 1;
    setSlider($('rangeStart'), 0, n - 1, 0);
    setSlider($('rangeEnd'), 0, n - 1, n - 1);
  }

  function setSlider(el, min, max, val) {
    el.min = min; el.max = max; el.value = val;
  }

  function onRangeInput(which) {
    var s = parseInt($('rangeStart').value, 10);
    var e = parseInt($('rangeEnd').value, 10);
    // 防交叉：start 不能超过 end
    if (s > e) {
      if (which === 'start') { e = s; $('rangeEnd').value = e; }
      else { s = e; $('rangeStart').value = s; }
    }
    if (state.view === 'seasonal') { state.seasonalStart = s; state.seasonalEnd = e; }
    else { state.rangeStart = s; state.rangeEnd = e; }
    updateRangeUI();
    // 拖动中：每帧合并一次、无动画，保证跟手不卡
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(function () {
        rafPending = false;
        refreshResult(false);
      });
    }
  }

  function resetRange() {
    initRange();
    refreshResult();
  }

  function updateRangeUI() {
    var pctS, pctE, tS, tE;
    if (state.view === 'seasonal') {
      var labels = seasonalAllLabels();
      var n = labels.length;
      if (n <= 1) return;
      pctS = (state.seasonalStart / (n - 1)) * 100;
      pctE = (state.seasonalEnd / (n - 1)) * 100;
      tS = labels[state.seasonalStart] || '—';
      tE = labels[state.seasonalEnd] || '—';
      $('rangeHint').textContent = '左右拉动手柄，调节季节性图显示的年内日期范围';
    } else {
      var dsT = state.currentDates || [];
      var m = dsT.length;
      if (m <= 1) return;
      pctS = (state.rangeStart / (m - 1)) * 100;
      pctE = (state.rangeEnd / (m - 1)) * 100;
      tS = dsT[state.rangeStart] || '—';
      tE = dsT[state.rangeEnd] || '—';
      $('rangeHint').textContent = '左右拉动两端手柄，调节显示的时间范围';
    }
    $('rangeWrap').style.setProperty('--s', pctS + '%');
    $('rangeWrap').style.setProperty('--e', pctE + '%');
    $('rangeStartText').textContent = tS;
    $('rangeEndText').textContent = tE;
  }

  /** 按当前时间轴范围过滤价差序列（仅时序图视图使用） */
  function filterByRange(joined) {
    var dsR = state.currentDates || [];
    var d0 = dsR[state.rangeStart];
    var d1 = dsR[state.rangeEnd];
    if (!d0 || !d1) return joined;
    var out = [];
    for (var i = 0; i < joined.length; i++) {
      var d = joined[i].date;
      if (d >= d0 && d <= d1) out.push(joined[i]);
    }
    return out;
  }

  /** 时间快捷键：把范围锁定到最近 N 个月（自动切到时序图） */
  function applyQuickRange(months) {
    if (state.view !== 'time') setView('time');
    var ds = state.currentDates || [];
    var last = ds.length - 1;
    var startDate = shiftDate(ds[last], -months);
    var i = 0;
    while (i < ds.length && ds[i] < startDate) i++;
    state.rangeStart = i;
    state.rangeEnd = last;
    $('rangeStart').value = i;
    $('rangeEnd').value = last;
    updateRangeUI();
    refreshResult(true);
  }

  /** 日期字符串加减月（'YYYY-MM-DD'），处理跨年与月末 */
  function shiftDate(dateStr, months) {
    var y = parseInt(dateStr.slice(0, 4), 10);
    var m = parseInt(dateStr.slice(5, 7), 10);
    var d = parseInt(dateStr.slice(8, 10), 10);
    m += months;
    while (m < 1) { m += 12; y--; }
    while (m > 12) { m -= 12; y++; }
    var dim = new Date(y, m, 0).getDate();
    d = Math.min(d, dim);
    return y + '-' + pad2(m) + '-' + pad2(d);
  }
  function pad2(n) { return n < 10 ? '0' + n : String(n); }

  // ================= 纵轴范围 =================
  function applyYRange() {
    var lo = $('yMin').value.trim();
    var hi = $('yMax').value.trim();
    state.yMin = lo === '' ? null : parseFloat(lo);
    state.yMax = hi === '' ? null : parseFloat(hi);
    if (state.yMin != null && isNaN(state.yMin)) state.yMin = null;
    if (state.yMax != null && isNaN(state.yMax)) state.yMax = null;
    if (state.yMin != null && state.yMax != null && state.yMin >= state.yMax) {
      showStatus('warn', '纵轴下限需小于上限');
      return;
    }
    refreshResult();
  }

  function resetYRange() {
    state.yMin = null;
    state.yMax = null;
    $('yMin').value = '';
    $('yMax').value = '';
    refreshResult();
  }

  /** 图表 y 轴配置（应用手动范围；null 时自动） */
  function yScale(extra) {
    var o = { grid: { color: 'rgba(0,0,0,.05)' } };
    if (state.yMin != null) o.min = state.yMin;
    if (state.yMax != null) o.max = state.yMax;
    if (extra) for (var k in extra) o[k] = extra[k];
    return o;
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.mode-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.mode === mode);
    });
    var bSel = $('legBProduct');
    if (mode === 'calendar') {
      bSel.disabled = true;
      syncCalendarLegB();
      $('legHint').textContent = '月差 = 同一品种的合约 A − 合约 B（如 P 01月 − 05月），可点 ⇄ 交换方向';
    } else {
      bSel.disabled = false;
      $('legHint').textContent = '价差 = 品种 A 合约 − 品种 B 合约（可跨品种任意组合，点 ⇄ 交换方向）';
    }
    renderShortcuts();
    refreshResult();
  }

  /** 按当前模式渲染快捷键（月差：91/15/59；价差：豆棕/菜豆/菜棕/豆菜粕） */
  function renderShortcuts() {
    var box = $('modeShortcuts');
    box.innerHTML = '';
    var items;
    if (state.mode === 'calendar') {
      items = [
        { text: '91 月差', title: '09 − 01', args: ['09', '01'] },
        { text: '15 月差', title: '01 − 05', args: ['01', '05'] },
        { text: '59 月差', title: '05 − 09', args: ['05', '09'] }
      ];
    } else {
      items = [
        { text: '豆棕', title: '豆油 Y − 棕榈油 P', args: ['Y', 'P'] },
        { text: '菜豆', title: '菜油 OI − 豆油 Y', args: ['OI', 'Y'] },
        { text: '菜棕', title: '菜油 OI − 棕榈油 P', args: ['OI', 'P'] },
        { text: '豆菜粕', title: '豆粕 M − 菜粕 RM', args: ['M', 'RM'] }
      ];
    }
    items.forEach(function (it) {
      var b = document.createElement('button');
      b.className = 'shortcut-btn';
      b.textContent = it.text;
      b.title = it.title;
      b.addEventListener('click', function () {
        if (state.mode === 'calendar') applyCalendarShortcut(it.args[0], it.args[1]);
        else applySpreadShortcut(it.args[0], it.args[1]);
      });
      box.appendChild(b);
    });
  }

  /** 月差快捷键：同品种 A 合约 − B 合约 */
  function applyCalendarShortcut(cA, cB) {
    var info = FuturesData.getProductInfo(state.legA.product);
    var ctrs = info ? info.contracts : [];
    if (ctrs.indexOf(cA) < 0 || ctrs.indexOf(cB) < 0) {
      showStatus('warn', '当前品种没有 ' + cA + ' 或 ' + cB + ' 月合约');
      return;
    }
    state.legA.contract = cA; $('legAContract').value = cA;
    state.legB.contract = cB; $('legBContract').value = cB;
    refreshResult();
  }

  /** 价差快捷键：品种 A − 品种 B（默认取主力合约） */
  function applySpreadShortcut(pA, pB) {
    if (!FuturesData.getProductInfo(pA) || !FuturesData.getProductInfo(pB)) {
      showStatus('warn', '数据中没有 ' + pA + ' 或 ' + pB + ' 品种');
      return;
    }
    state.legA.product = pA; $('legAProduct').value = pA;
    state.legB.product = pB; $('legBProduct').value = pB;
    state.legA.contract = null; state.legB.contract = null;
    fillContracts('A');
    fillContracts('B');
    refreshAsync();
  }

  /** 切换图表视图：季节性图 / 时序图 */
  function setView(view) {
    state.view = view;
    document.querySelectorAll('.view-switch .mode-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.view === view);
    });
    syncViewControls();
    initRange();      // 滑块切换到该视图的全范围
    refreshResult();
  }

  /** 季节性图只画价差线，禁用"叠加价格线"复选框；时间快捷键仅时序图可见 */
  function syncViewControls() {
    var chk = $('showPricesChk');
    chk.disabled = state.view === 'seasonal';
    $('pricesChkLabel').classList.toggle('disabled', state.view === 'seasonal');
    $('rangeQuickBtns').style.display = state.view === 'time' ? 'flex' : 'none';
  }

  function syncCalendarLegB() {
    state.legB.product = state.legA.product;
    $('legBProduct').value = state.legA.product;
    var info = FuturesData.getProductInfo(state.legA.product);
    var ctrs = info ? info.contracts : [];
    var idx = ctrs.indexOf(state.legA.contract);
    var next = idx >= 0 && idx < ctrs.length - 1 ? ctrs[idx + 1] : null;
    if (next && next !== state.legA.contract) {
      state.legB.contract = next;
    } else if (ctrs.length > 1) {
      state.legB.contract = ctrs[idx > 0 ? idx - 1 : 1];
    }
    if (state.legB.contract) $('legBContract').value = state.legB.contract;
    fillContracts('B');
  }

  function swapLegs() {
    var p = state.legA.product, c = state.legA.contract;
    state.legA.product = state.legB.product; state.legA.contract = state.legB.contract;
    state.legB.product = p; state.legB.contract = c;
    $('legAProduct').value = state.legA.product || '';
    $('legBProduct').value = state.legB.product || '';
    fillContracts('A');
    fillContracts('B');
    if (state.mode === 'calendar') syncCalendarLegB();
    refreshAsync();
  }

  // ================= 计算与渲染 =================
  /** animate=false 时图表即时更新（无动画），用于滑块拖动 */
  function refreshResult(animate) {
    var a = state.legA, b = state.legB;
    if (!a.product || !a.contract || !b.product || !b.contract) { clearResult(); return; }
    state.currentDates = FuturesData.getProductDates(a.product) || [];
    if (!state.currentDates.length) { clearResult(); return; }

    var pA = FuturesData.getPrices(a.product, a.contract);
    var pB = FuturesData.getPrices(b.product, b.contract);
    if (!pA || !pB) {
      clearResult();
      $('chartEmpty').textContent = '所选合约没有数据';
      $('chartEmpty').style.display = 'flex';
      return;
    }
    updateLegPrice('A', pA);
    updateLegPrice('B', pB);

    var joined = FuturesData.spreadSeries(state.currentDates, pA,
      FuturesData.getProductDates(b.product) || [], pB);
    if (state.view === 'time') joined = filterByRange(joined);
    if (!joined.length) {
      clearResult();
      $('chartEmpty').textContent = '两个合约在数据中没有共同交易日';
      $('chartEmpty').style.display = 'flex';
      return;
    }

    var title = state.mode === 'calendar' ? '月差走势' : '价差走势';
    var label = state.mode === 'calendar'
      ? a.product + ' ' + a.contract + '月 − ' + b.contract + '月 月差'
      : a.product + a.contract + ' − ' + b.product + b.contract + ' 价差';
    $('resultTitle').textContent = title + '：' + label;

    renderSummary(FuturesData.summarize(joined), joined);
    renderChart(joined, pA, pB, label, animate);
    renderTable(joined);
    $('chartEmpty').style.display = 'none';
  }

  function updateLegPrice(which, prices) {
    var el = which === 'A' ? $('legAPrice') : $('legBPrice');
    var last = null;
    for (var i = prices.length - 1; i >= 0; i--) { if (prices[i] != null) { last = prices[i]; break; } }
    if (last != null) {
      el.textContent = fmtNum(last);
      el.style.color = 'var(--ink)';
    } else {
      el.textContent = '—';
      el.style.color = '';
    }
  }

  function clearResult() {
    $('summaryGrid').innerHTML = '';
    $('detailBody').innerHTML = '';
    $('resultMeta').textContent = '';
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    $('chartEmpty').style.display = 'flex';
    $('chartEmpty').textContent = '请选择品种与合约';
  }

  function renderSummary(s) {
    var grid = $('summaryGrid');
    grid.innerHTML = '';
    if (!s) return;
    $('resultMeta').textContent = '共 ' + s.count + ' 个共同交易日 · ' + s.firstDate + ' ~ ' + s.lastDate;
    var items = [
      { k: '最新价差', v: fmtNum(s.latest), cls: signCls(s.latest), sub: s.change == null ? '' : '较前日 ' + (s.change >= 0 ? '+' : '') + fmtNum(s.change) },
      { k: '区间最高', v: fmtNum(s.high), cls: 'pos', sub: '' },
      { k: '区间最低', v: fmtNum(s.low), cls: 'neg', sub: '' },
      { k: '区间均值', v: fmtNum(s.avg), cls: '', sub: '' },
      { k: 'A 最新价', v: fmtNum(s.lastA), cls: '', sub: state.legA.product + ' ' + state.legA.contract + '月' },
      { k: 'B 最新价', v: fmtNum(s.lastB), cls: '', sub: state.legB.product + ' ' + state.legB.contract + '月' }
    ];
    items.forEach(function (it) {
      var div = document.createElement('div');
      div.className = 'summary-item';
      div.innerHTML = '<div class="k">' + it.k + '</div><div class="v ' + (it.cls || '') + '">' + it.v + '</div>' +
        (it.sub ? '<div class="sub">' + it.sub + '</div>' : '');
      grid.appendChild(div);
    });
  }

  function renderChart(joined, pA, pB, label, animate) {
    if (state.view === 'seasonal') { renderSeasonalChart(joined, label, animate); return; }

    var dates = joined.map(function (r) { return r.date; });
    var spreads = joined.map(function (r) { return r.spread; });
    var datasets = [{
      label: label,
      data: spreads,
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, .08)',
      fill: true,
      pointRadius: 0,
      borderWidth: 2,
      yAxisID: 'y'
    }];

    var showPrices = $('showPricesChk').checked;
    if (showPrices) {
      var byDate = function (prices) {
        var map = {};
        for (var i = 0; i < dates.length; i++) {
          // joined 的日期在 dates 中连续（同索引），直接用 joined 索引对应原始数组
          map[joined[i].date] = prices[i];
        }
        return map;
      };
      var mapA = byDate(pA), mapB = byDate(pB);
      datasets.push({
        label: 'A 价格',
        data: dates.map(function (d) { return mapA[d] == null ? null : mapA[d]; }),
        borderColor: '#2563eb', borderDash: [4, 4], pointRadius: 0, borderWidth: 1, yAxisID: 'y1'
      });
      datasets.push({
        label: 'B 价格',
        data: dates.map(function (d) { return mapB[d] == null ? null : mapB[d]; }),
        borderColor: '#f97316', borderDash: [4, 4], pointRadius: 0, borderWidth: 1, yAxisID: 'y1'
      });
    }

    updateChart({
      type: 'line',
      data: { labels: dates, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { boxWidth: 18, font: { size: 12 } } },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var d = joined[ctx.dataIndex];
                if (ctx.datasetIndex === 0) {
                  return ' 价差 = ' + fmtNum(d.spread) + '  （A ' + fmtNum(d.a) + ' − B ' + fmtNum(d.b) + '）';
                }
                return ' ' + ctx.dataset.label + ' = ' + fmtNum(ctx.parsed.y);
              }
            }
          }
        },
        scales: {
          x: { ticks: { maxTicksLimit: 12, maxRotation: 0 }, grid: { display: false } },
          y: yScale({ position: 'left' }),
          y1: { position: 'right', display: showPrices, grid: { drawOnChartArea: false } }
        }
      }
    }, animate);
  }

  /**
   * 季节性图（日度）：横轴 = 一年内的日期（MM-DD），每一年一条线，每个交易日一个点；
   * 线段连续（spanGaps 跨过节假日）；图例点击年份即可隐藏/显示
   */
  function renderSeasonalChart(joined, label, animate) {
    // 横轴：年内 MM-DD 全集，按滑块范围截取
    var allLabels = seasonalAllLabels();
    var labels = allLabels.slice(state.seasonalStart, state.seasonalEnd + 1);
    var labelSet = {};
    labels.forEach(function (l) { labelSet[l] = 1; });

    var byYear = {};
    joined.forEach(function (r) {
      var md = r.date.slice(5);
      if (!labelSet[md]) return;          // 跳过滑块范围外的日期
      var y = r.date.slice(0, 4);
      if (!byYear[y]) byYear[y] = {};
      byYear[y][md] = r.spread;           // 同一天一条记录（日频）
    });
    var years = Object.keys(byYear).sort();

    var datasets = years.map(function (y, i) {
      var isLatest = i === years.length - 1;   // 最新年份红色加粗高亮
      return {
        label: y + '年',
        data: labels.map(function (md) { return byYear[y][md] == null ? null : byYear[y][md]; }),
        borderColor: isLatest ? '#dc2626' : yearColor(i, years.length),
        backgroundColor: isLatest ? 'rgba(220, 38, 38, .05)' : 'transparent',
        pointRadius: 0,
        pointHoverRadius: 3,
        borderWidth: isLatest ? 2.8 : 1.4,
        tension: 0.1,
        spanGaps: true,                     // 跨过 null（节假日）连续绘制
        hidden: !!state.hiddenYears[y]      // 恢复用户在图例上隐藏的年份
      };
    });

    updateChart({
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            labels: { boxWidth: 16, font: { size: 11 } },
            onClick: seasonalLegendClick      // 点击年份切换显示并记录隐藏状态
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return ' ' + ctx.dataset.label + ' ' + ctx.label + ' 价差 = ' + fmtNum(ctx.parsed.y);
              }
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: '日期（年内，MM-DD）', font: { size: 11 } },
            ticks: { maxTicksLimit: 12, maxRotation: 0, autoSkip: true },
            grid: { display: false }
          },
          y: yScale({})
        }
      }
    }, animate);
  }

  /** 复用 Chart 实例更新数据（不销毁重建，避免闪烁；按 label 继承旧隐藏状态） */
  function updateChart(cfg, animate) {
    if (state.chart) {
      var old = state.chart.data.datasets || [];
      var oldHidden = {};
      old.forEach(function (ds, i) {
        try { oldHidden[ds.label] = !!state.chart.getDatasetMeta(i).hidden; } catch (e) { /* ignore */ }
      });
      (cfg.data.datasets || []).forEach(function (ds) {
        if (ds.hidden === undefined && oldHidden[ds.label]) ds.hidden = true;
      });
      state.chart.config.data = cfg.data;
      state.chart.config.options = cfg.options;
      state.chart.update(animate === false ? 'none' : undefined);
    } else {
      state.chart = new Chart($('spreadChart'), cfg);
    }
  }

  /** 季节性图图例点击：切换年份可见性并记录（重绘后恢复） */
  function seasonalLegendClick(e, legendItem, legend) {
    var index = legendItem.datasetIndex;
    var meta = legend.chart.getDatasetMeta(index);
    var year = String(legend.chart.data.datasets[index].label).replace('年', '');
    meta.hidden = !meta.hidden;
    if (meta.hidden) state.hiddenYears[year] = true;
    else delete state.hiddenYears[year];
    legend.chart.update();
  }

  /** 为年份分配均匀分布的 HSL 颜色 */
  function yearColor(i, n) {
    var hue = Math.round((i * 360) / Math.max(n, 1) + 15) % 360;
    return 'hsl(' + hue + ', 62%, 42%)';
  }

  function renderTable(joined) {
    var body = $('detailBody');
    body.innerHTML = '';
    if (!joined.length) return;
    var limit = parseInt($('tableLimit').value, 10) || 30;
    var order = $('tableOrder').value;
    var rows = joined.slice();
    if (order === 'new') rows.reverse();
    rows = rows.slice(0, limit);

    var frag = document.createDocumentFragment();
    rows.forEach(function (r, i) {
      var idx = order === 'new' ? joined.length - 1 - i : i;
      var change = idx > 0 ? joined[idx].spread - joined[idx - 1].spread : null;
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + r.date + '</td>' +
        '<td>' + fmtNum(r.a) + '</td>' +
        '<td>' + fmtNum(r.b) + '</td>' +
        '<td class="num ' + signCls(r.spread) + '">' + fmtNum(r.spread) + '</td>' +
        '<td class="num ' + (change == null ? '' : signCls(change)) + '">' +
        (change == null ? '—' : (change >= 0 ? '+' : '') + fmtNum(change)) + '</td>';
      frag.appendChild(tr);
    });
    body.appendChild(frag);
  }

  // ================= 状态显示 =================
  function renderDataStatus() {
    var list = $('statusList');
    list.innerHTML = '';
    var d = FuturesData.describe();
    var lines = [];
    lines.push(['数据源', 'OpenCTP + AkShare 自动采集']);
    lines.push(['更新时间', d && d.updated_at ? d.updated_at : '—']);
    lines.push(['交易日数量', d ? String(d.days) : '—']);
    lines.push(['品种数量', d ? String(d.products) : '—']);
    lines.push(['日期范围', d && d.firstDate ? d.firstDate + ' ~ ' + d.lastDate : '—']);

    lines.forEach(function (kv) {
      var li = document.createElement('li');
      li.innerHTML = '<span class="k">' + kv[0] + '：</span><span class="v">' + kv[1] + '</span>';
      list.appendChild(li);
    });

    var dot = $('dataDot');
    var text = $('dataStatusText');
    if (d && d.days) { dot.className = 'dot ok'; text.textContent = '自动采集 · ' + (d.lastDate || ''); }
    else { dot.className = 'dot err'; text.textContent = '无数据'; }
  }

  function showStatus(kind, msg) {
    $('dataDot').className = 'dot ' + (kind === 'err' ? 'err' : kind === 'warn' ? 'warn' : 'ok');
    $('dataStatusText').textContent = msg;
  }

  // ================= 工具 =================
  function fmtNum(n) {
    if (n == null || isNaN(n)) return '—';
    return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  }
  function signCls(n) { return n > 0 ? 'pos' : n < 0 ? 'neg' : ''; }
})();
