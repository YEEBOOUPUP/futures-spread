/**
 * data.js — 数据加载与价差/月差计算（紧凑结构：dates/series 按索引对齐）
 *
 * 数据来源优先级：
 *   1. localStorage（浏览器上传解析，本机可见）
 *   2. data/data.json（每日转换脚本生成，随站点部署，全站可见）
 *
 * 数据结构：
 *   { dates: ["2015-01-05",...],
 *     products: { "P": { name, contracts:[标签], metrics:[close,settle] } },
 *     series: { "P": { "主力": { close:[5006,...] }, "01": { close:[...], settle:[...] } } } }
 *
 * 计算：
 *   getPrices(dataset, product, label, metric) → number[]（与 dates 对齐，缺失为 null）
 *   spreadSeries(dates, a, b)                 → [{date,a,b,spread}] 按共同有效交易日
 */
(function (global) {
  'use strict';

  var STORAGE_KEY = 'futures_spread_dataset_v1';

  function loadDataset() {
    return new Promise(function (resolve) {
      var local = loadLocal();
      if (local) {
        resolve({ dataset: local, source: 'local' });
        return;
      }
      fetch('data/data.json', { cache: 'no-cache' })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (json) {
          if (!json || !json.dates || !json.series) throw new Error('data.json 结构无效');
          resolve({ dataset: json, source: 'remote' });
        })
        .catch(function (err) {
          resolve({ dataset: null, source: 'none', error: err });
        });
    });
  }

  function saveLocal(dataset) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(dataset)); return true; }
    catch (e) { return false; }
  }
  function loadLocal() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var ds = JSON.parse(raw);
      if (!ds || !ds.dates || !ds.series) return null;
      return ds;
    } catch (e) { return null; }
  }
  function clearLocal() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
  }

  function getProducts(dataset) {
    if (!dataset || !dataset.products) return [];
    return Object.keys(dataset.products).sort();
  }

  function getProductInfo(dataset, product) {
    return (dataset && dataset.products && dataset.products[product]) || null;
  }

  /** 价格数组（与 dates 对齐；无该指标或该合约 → null） */
  function getPrices(dataset, product, label, metric) {
    if (!dataset || !dataset.series || !dataset.series[product]) return null;
    var m = dataset.series[product][label];
    if (!m) return null;
    return (m[metric || 'close'] != null) ? m[metric || 'close'] : null;
  }

  /** 两条价格数组 → 按日期对齐的价差序列（跳过任一侧缺失的日子） */
  function spreadSeries(dates, pricesA, pricesB) {
    var n = Math.min(dates.length, pricesA ? pricesA.length : 0, pricesB ? pricesB.length : 0);
    var out = [];
    for (var i = 0; i < n; i++) {
      var a = pricesA[i], b = pricesB[i];
      if (a == null || b == null) continue;
      out.push({ date: dates[i], a: a, b: b, spread: round2(a - b) });
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

  /** 数据状态报告 */
  function describe(dataset) {
    if (!dataset || !dataset.dates) return null;
    return {
      days: dataset.dates.length,
      products: dataset.products ? Object.keys(dataset.products).length : 0,
      firstDate: dataset.dates[0] || null,
      lastDate: dataset.dates[dataset.dates.length - 1] || null,
      updated_at: dataset.updated_at || null,
      source: dataset.source || null
    };
  }

  function round2(n) { return Math.round(n * 100) / 100; }

  global.FuturesData = {
    loadDataset: loadDataset,
    saveLocal: saveLocal,
    clearLocal: clearLocal,
    getProducts: getProducts,
    getProductInfo: getProductInfo,
    getPrices: getPrices,
    spreadSeries: spreadSeries,
    summarize: summarize,
    describe: describe
  };
})(window);
