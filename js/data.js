/**
 * data.js — 数据加载与价差/月差计算（v2：按品种拆分 + 懒加载）
 *
 * 数据结构：
 *   data/index.json（元数据 + 全局日期轴）：
 *     { updated_at, source, dates: [...], products: { "P": { name, contracts, metrics, file } } }
 *   data/{品种}.json（单品种，series 与全局 dates 按索引对齐）：
 *     { series: { "01": { close: [...], settle: [...] } } }
 *
 * 前端按需加载品种文件（懒加载 + 内存缓存），避免全市场数据一次性拉取。
 */
(function (global) {
  'use strict';

  var indexData = null;   // index.json 内容
  var cache = {};         // 品种代码 -> { series: {...} }
  var loading = {};       // 加载中的 Promise 去重

  function loadDataset() {
    return new Promise(function (resolve) {
      fetch('data/index.json', { cache: 'no-cache' })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (json) {
          if (!json || !json.products) throw new Error('index.json 结构无效');
          indexData = json;
          cache = {};
          resolve({ dataset: json, source: 'remote' });
        })
        .catch(function (err) {
          resolve({ dataset: null, source: 'none', error: err });
        });
    });
  }

  /** 确保指定品种数据已加载（懒加载 + 缓存） */
  function ensureProducts(codes) {
    var pending = [];
    (codes || []).forEach(function (code) {
      if (!code || cache[code]) return;
      if (!loading[code]) {
        var info = indexData.products[code];
        var file = info && info.file ? info.file : code + '.json';
        loading[code] = fetch('data/' + file, { cache: 'no-cache' })
          .then(function (res) {
            if (!res.ok) throw new Error('加载 ' + code + ' 失败: HTTP ' + res.status);
            return res.json();
          })
          .then(function (js) {
            cache[code] = js;
            return js;
          })
          .finally(function () { delete loading[code]; });
      }
      pending.push(loading[code]);
    });
    return Promise.all(pending);
  }

  function isLoaded(code) { return !!cache[code]; }

  function getProducts() {
    return indexData ? Object.keys(indexData.products).sort() : [];
  }

  function getProductInfo(code) {
    return (indexData && indexData.products[code]) || null;
  }

  function getDates() { return []; }   // 已废弃：每品种独立日期轴（用 getProductDates）

  /** 某品种的日期轴（独立 dates） */
  function getProductDates(code) {
    var p = cache[code];
    return (p && p.dates) ? p.dates : null;
  }

  /** 价格数组（与品种自己的 dates 对齐；无该合约/指标 → null） */
  function getPrices(product, label, metric) {
    var p = cache[product];
    if (!p || !p.series) return null;
    var m = p.series[label];
    if (!m) return null;
    return (m[metric || 'close'] != null) ? m[metric || 'close'] : null;
  }

  /** 两条序列（各自日期轴）按共同交易日对齐 → [{date,a,b,spread}] */
  function spreadSeries(datesA, pricesA, datesB, pricesB) {
    if (!datesA || !datesB || !pricesA || !pricesB) return [];
    var i = 0, j = 0, out = [];
    while (i < datesA.length && j < datesB.length) {
      if (datesA[i] < datesB[j]) { i++; }
      else if (datesA[i] > datesB[j]) { j++; }
      else {
        var a = pricesA[i], b = pricesB[j];
        if (a != null && b != null) {
          out.push({ date: datesA[i], a: a, b: b, spread: round2(a - b) });
        }
        i++; j++;
      }
    }
    return out;
  }

  function summarize(joined) {
    if (!joined || !joined.length) return null;
    var vals = joined.map(function (r) { return r.spread; });
    var min = Math.min.apply(null, vals);
    var max = Math.max.apply(null, vals);
    var sum = vals.reduce(function (x, y) { return x + y; }, 0);
    var last = joined[joined.length - 1];
    var prev = joined.length > 1 ? joined[joined.length - 2].spread : null;
    return {
      latest: round2(last.spread),
      prev: prev == null ? null : round2(prev),
      change: prev == null ? null : round2(last.spread - prev),
      high: round2(max),
      low: round2(min),
      avg: round2(sum / vals.length),
      count: vals.length,
      firstDate: joined[0].date,
      lastDate: joined[joined.length - 1].date,
      lastA: last.a,
      lastB: last.b
    };
  }

  function describe() {
    if (!indexData) return null;
    return {
      products: indexData.products ? Object.keys(indexData.products).length : 0,
      updated_at: indexData.updated_at || null,
      source: indexData.source || null
    };
  }

  function round2(n) { return Math.round(n * 100) / 100; }

  global.FuturesData = {
    loadDataset: loadDataset,
    ensureProducts: ensureProducts,
    isLoaded: isLoaded,
    getProducts: getProducts,
    getProductInfo: getProductInfo,
    getDates: getDates,
    getProductDates: getProductDates,
    getPrices: getPrices,
    spreadSeries: spreadSeries,
    summarize: summarize,
    describe: describe
  };
})(window);
