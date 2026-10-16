# -*- coding: utf-8 -*-
"""龙虎榜独立视图：syncViewControls/refreshView/loadRank/state 改造"""
import esprima

p = 'js/app.js'
js = open(p, encoding='utf-8').read()

# 1) state 加 rankAvailable
old = "    forexMap: null,        // 棕榈油内外套汇率 {date: rate}"
new = "    forexMap: null,        // 棕榈油内外套汇率 {date: rate}\n    rankAvailable: false,  // 当前品种是否有龙虎榜数据"
assert old in js
js = js.replace(old, new, 1)

# 2) syncViewControls 加 rank 分支
old2 = """  function syncViewControls() {
    var chk = $('showPricesChk');
    chk.disabled = state.view === 'seasonal';
    $('pricesChkLabel').classList.toggle('disabled', state.view === 'seasonal');
    $('rangeQuickBtns').style.display = state.view === 'time' ? 'flex' : 'none';
    $('yearRangeControl').style.display = state.view === 'seasonal' ? '' : 'none';
  }"""
new2 = """  function syncViewControls() {
    var isRank = state.view === 'rank';
    var chk = $('showPricesChk');
    chk.disabled = state.view === 'seasonal';
    $('pricesChkLabel').classList.toggle('disabled', state.view === 'seasonal');
    $('rangeQuickBtns').style.display = state.view === 'time' ? 'flex' : 'none';
    $('yearRangeControl').style.display = state.view === 'seasonal' ? '' : 'none';
    // 龙虎榜视图：隐藏图表相关区块，只留龙虎榜
    var chartWrap = document.querySelector('.chart-wrap');
    if (chartWrap) chartWrap.style.display = isRank ? 'none' : '';
    $('summaryGrid').style.display = isRank ? 'none' : '';
    $('pricesChkLabel').style.display = isRank ? 'none' : '';
    var rangeControl = $('rangeControl');
    if (rangeControl) rangeControl.style.display = isRank ? 'none' : '';
    var tableWrap = document.querySelector('.table-wrap');
    if (tableWrap) tableWrap.style.display = isRank ? 'none' : '';
    $('rankCard').style.display = (isRank && state.rankAvailable) ? '' : 'none';
    $('rankEmpty').style.display = (isRank && !state.rankAvailable) ? '' : 'none';
  }"""
assert old2 in js
js = js.replace(old2, new2, 1)

# 3) refreshView 加 rank 分支
old3 = """  function refreshView(animate) {
    if (state.mode === 'flow') { renderProfitFlow(); return; }
    if (state.mode === 'palm') { renderPalm(); return; }
    refreshResult(animate);
  }"""
new3 = """  function refreshView(animate) {
    if (state.view === 'rank') { loadRank(state.legA.product); return; }   // 龙虎榜视图
    if (state.mode === 'flow') { renderProfitFlow(); return; }
    if (state.mode === 'palm') { renderPalm(); return; }
    refreshResult(animate);
  }"""
assert old3 in js
js = js.replace(old3, new3, 1)

# 4) loadRank：设置 rankAvailable 并交给 syncViewControls 控制显隐
old4 = """      .then(function (d) {
        if (!d || !d.vol) { card.style.display = 'none'; return; }
        var dt = String(d.date);
        $('rankMeta').textContent = (d.contract || product) + ' · ' +
          dt.slice(0, 4) + '-' + dt.slice(4, 6) + '-' + dt.slice(6, 8);
        renderRankCol($('rankVolBody'), d.vol);
        renderRankCol($('rankLongBody'), d.long);
        renderRankCol($('rankShortBody'), d.short);
        card.style.display = '';
      })
      .catch(function () { card.style.display = 'none'; });"""
new4 = """      .then(function (d) {
        if (!d || !d.vol) { state.rankAvailable = false; syncViewControls(); return; }
        var dt = String(d.date);
        $('rankMeta').textContent = (d.contract || product) + ' · ' +
          dt.slice(0, 4) + '-' + dt.slice(4, 6) + '-' + dt.slice(6, 8);
        renderRankCol($('rankVolBody'), d.vol);
        renderRankCol($('rankLongBody'), d.long);
        renderRankCol($('rankShortBody'), d.short);
        state.rankAvailable = true;
        syncViewControls();
      })
      .catch(function () { state.rankAvailable = false; syncViewControls(); });"""
assert old4 in js
js = js.replace(old4, new4, 1)

# 5) loadRank 开头：非 rank 视图时不改显隐（交给 syncViewControls）
old5 = """  function loadRank(product) {
    var card = $('rankCard');
    if (!product) { card.style.display = 'none'; return; }"""
new5 = """  function loadRank(product) {
    if (!product) { state.rankAvailable = false; syncViewControls(); return; }"""
assert old5 in js
js = js.replace(old5, new5, 1)

open(p, 'w', encoding='utf-8').write(js)
esprima.parseScript(js)
print('app.js 龙虎榜视图改造完成，语法 OK')
