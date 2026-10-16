# -*- coding: utf-8 -*-
"""龙虎榜前端逻辑：日期下拉 + 净多/净空榜单"""
import esprima

p = 'js/app.js'
js = open(p, encoding='utf-8').read()

# 1) 用新版 loadRank 替换（含日期下拉、5 榜、新旧结构兼容）
old = js[js.find('  function loadRank(product) {'):js.find('  function renderRankCol(tbody, rows) {')]
assert 'function loadRank' in old, 'loadRank 未找到'
new = '''  function loadRank(product, date) {
    if (!product) { state.rankAvailable = false; syncViewControls(); return; }
    fetch('data/rank/' + product + '.json', { cache: 'no-cache' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (d) {
        if (!d) { state.rankAvailable = false; syncViewControls(); return; }
        // 兼容旧单日结构
        var dates = d.dates || (d.date ? [d.date] : []);
        var dataMap = d.data || (d.date ? (function () { var m = {}; m[d.date] = d; return m; })() : {});
        if (!dates.length) { state.rankAvailable = false; syncViewControls(); return; }
        var sel = $('rankDateSel');
        if (sel.dataset.product !== product) {          // 换品种时重建日期下拉
          sel.innerHTML = '';
          dates.forEach(function (dt) {
            var o = document.createElement('option');
            o.value = dt;
            o.textContent = dt.slice(0, 4) + '-' + dt.slice(4, 6) + '-' + dt.slice(6, 8);
            sel.appendChild(o);
          });
          sel.dataset.product = product;
          date = dates[0];
        }
        var cur = date || sel.value || dates[0];
        if (dates.indexOf(cur) < 0) cur = dates[0];
        sel.value = cur;
        var day = dataMap[cur];
        if (!day) { state.rankAvailable = false; syncViewControls(); return; }
        $('rankMeta').textContent = (day.contract || product) + ' · ' +
          cur.slice(0, 4) + '-' + cur.slice(4, 6) + '-' + cur.slice(6, 8);
        renderRankCol($('rankVolBody'), day.vol);
        renderRankCol($('rankLongBody'), day.long);
        renderRankCol($('rankShortBody'), day.short);
        renderNetCol($('rankNetLongBody'), day.netLong);
        renderNetCol($('rankNetShortBody'), day.netShort);
        state.rankAvailable = true;
        syncViewControls();
      })
      .catch(function () { state.rankAvailable = false; syncViewControls(); });
  }

'''
js = js.replace(old, new, 1)

# 2) 加 renderNetCol（在 fmtInt 前）
old2 = '  function fmtInt(n) {'
new2 = '''  /** 净持仓榜单（名次/会员/多单/空单/净） */
  function renderNetCol(tbody, rows) {
    tbody.innerHTML = '';
    (rows || []).slice(0, 20).forEach(function (r) {
      var tr = document.createElement('tr');
      var cls = r.net > 0 ? 'pos' : 'neg';
      tr.innerHTML = '<td>' + r.rank + '</td><td class="rank-name">' + r.name + '</td><td>' +
        fmtInt(r.long) + '</td><td>' + fmtInt(r.short) + '</td><td class="' + cls + '">' + fmtInt(r.net) + '</td>';
      tbody.appendChild(tr);
    });
  }

  function fmtInt(n) {'''
assert old2 in js
js = js.replace(old2, new2, 1)

# 3) 绑定日期下拉
old3 = "    $('palmMonthSel').addEventListener('change', function () {"
new3 = """    $('rankDateSel').addEventListener('change', function () {
      loadRank(state.legA.product, this.value);
    });
    $('palmMonthSel').addEventListener('change', function () {"""
assert old3 in js
js = js.replace(old3, new3, 1)

open(p, 'w', encoding='utf-8').write(js)
esprima.parseScript(js)
print('app.js 龙虎榜逻辑已更新，语法 OK')
