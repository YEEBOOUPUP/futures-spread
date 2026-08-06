/**
 * parser.js — 浏览器端解析 WIND 期货宽表 Excel（与 tools/excel_to_json.py 逻辑一致）
 * 依赖：SheetJS (window.XLSX)
 *
 * WIND 宽表格式：
 *   行1-2  : 开始/截止日期（每块重复）
 *   行3    : 证券代码（每块以"证券代码/代码"标签开始；P.DCE=主力 P00.DCE=最近 P01M.DCE=01月）
 *   行4    : 证券简称（中文名）
 *   行5    : 指标中文（日期/收盘价）
 *   行6    : 指标英文（Date/close/settle）—— 块的指标类型
 *   行7 起 : 数据（块标签列 = 该块日期列，其余列 = 价格）
 *
 * 输出（与 data.json 同构）：
 *   { dates: ["2015-01-05",...],
 *     products: { "P": { name:"棕榈油", contracts:["主力","最近","01",...], metrics:["close","settle"] } },
 *     series: { "P": { "主力": { close:[5006,...], settle:[...] } } } }
 */
(function (global) {
  'use strict';

  var BLOCK_LABELS = { '证券代码': 1, '代码': 1 };
  var CODE_RE = /^([A-Za-z]+)(\d{2})?(M)?\.(DCE|CZC|SHFE|INE|CZCE|GFEX)$/;

  var PRODUCT_NAMES = {
    'P': '棕榈油', 'Y': '豆油', 'OI': '菜油', 'M': '豆粕', 'RM': '菜粕',
    'A': '豆一', 'B': '豆二', 'C': '玉米', 'CS': '淀粉', 'L': '塑料',
    'PP': '聚丙烯', 'V': 'PVC', 'EG': '乙二醇', 'EB': '苯乙烯', 'PG': '液化气',
    'RB': '螺纹钢', 'HC': '热卷', 'I': '铁矿石', 'J': '焦炭', 'JM': '焦煤',
    'CU': '铜', 'AL': '铝', 'ZN': '锌', 'AU': '黄金', 'AG': '白银',
    'SC': '原油', 'FU': '燃料油', 'TA': 'PTA', 'MA': '甲醇', 'SA': '纯碱',
    'FG': '玻璃', 'UR': '尿素', 'CF': '棉花', 'SR': '白糖', 'AP': '苹果'
  };

  /** 解析 File → Promise<Dataset> */
  function parseFile(file) {
    return new Promise(function (resolve, reject) {
      if (!global.XLSX) { reject(new Error('SheetJS 未加载，无法解析 Excel')); return; }
      var reader = new FileReader();
      reader.onerror = function () { reject(new Error('读取文件失败')); };
      reader.onload = function (e) {
        try {
          var wb = XLSX.read(e.target.result, { type: 'array' });
          var datasets = [];
          // 处理前两个工作表（与转换脚本默认一致），其余忽略
          var sheets = wb.SheetNames.slice(0, 2);
          for (var i = 0; i < sheets.length; i++) {
            var ws = wb.Sheets[sheets[i]];
            var rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: null, raw: true });
            var ds = build(rows, file.name + '::' + sheets[i]);
            datasets.push(ds);
          }
          var merged = mergeDatasets(datasets);
          merged.fileName = file.name;
          resolve(merged);
        } catch (err) {
          reject(err);
        }
      };
      reader.readAsArrayBuffer(file);
    });
  }

  /** 'P.DCE'→('P','主力')  'P00.DCE'→('P','最近')  'P01M.DCE'→('P','01') */
  function parseCode(code) {
    var m = CODE_RE.exec(String(code).trim().toUpperCase());
    if (!m) return null;
    var product = m[1], num = m[2], isM = m[3];
    if (!num) return [product, '主力'];
    if (num === '00' && !isM) return [product, '最近'];
    if (isM) return [product, num];
    return [product, num];
  }

  /** Excel serial / Date / 'YYYY-MM-DD' → 'YYYY-MM-DD' 或 null */
  function fmtDate(v) {
    if (v == null || v === '') return null;
    if (v instanceof Date && !isNaN(v.getTime())) return toYmd(v);
    if (typeof v === 'number' && isFinite(v) && v > 20000 && v < 80000) {
      var ms = Math.round((v - 25569) * 86400 * 1000);
      return toYmd(new Date(ms));
    }
    var s = String(v).trim();
    var m = s.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})/);
    if (m) return m[1] + '-' + pad2(m[2]) + '-' + pad2(m[3]);
    return null;
  }
  function toYmd(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  function pad2(n) { return n < 10 ? '0' + n : String(n); }

  function toNum(v) {
    if (v == null) return null;
    if (typeof v === 'number' && isFinite(v)) return v;
    var s = String(v).trim();
    if (!s || /^#/.test(s)) return null;
    var n = parseFloat(s.replace(/[,，\s]/g, ''));
    return isFinite(n) ? n : null;
  }

  /** 识别块结构：返回 [{startCol, metric, columns:[{col,code,product,label}]}] */
  function extractBlocks(rows) {
    var header3 = rows[2] || [];
    var header6 = rows[5] || [];
    var blocks = [];
    var cur = null;
    for (var c = 0; c < header3.length; c++) {
      var v = header3[c];
      if (v != null && BLOCK_LABELS[String(v).trim()]) {
        var metricRaw = header6[c + 1];
        var metric = metricRaw != null ? String(metricRaw).trim().toLowerCase() : 'close';
        if (metric !== 'close' && metric !== 'settle') metric = 'close';
        cur = { startCol: c, metric: metric, columns: [] };
        blocks.push(cur);
        continue;
      }
      if (cur && v != null) {
        var parsed = parseCode(String(v));
        if (parsed) {
          cur.columns.push({ col: c, code: String(v).trim().toUpperCase(), product: parsed[0], label: parsed[1] });
        }
      }
    }
    return blocks;
  }

  /** rows（含表头）→ 紧凑数据集 */
  function build(rows, source) {
    var blocks = extractBlocks(rows);
    if (!blocks.length) throw new Error('未识别到 WIND 宽表块结构（第 3 行需含"证券代码/代码"）');

    // 主日期轴 = 第一块日期列（第 7 行起）
    var dates = [];
    for (var r = 6; r < rows.length; r++) {
      var d = fmtDate(rows[r] ? rows[r][blocks[0].startCol] : null);
      if (d) dates.push(d);
    }
    if (!dates.length) throw new Error('日期列无有效数据');

    var series = {};
    var products = {};
    var i, j, b, colInfo, prod, label;
    for (i = 0; i < blocks.length; i++) {
      b = blocks[i];
      var dateCol = b.startCol;
      var rowByDate = {};
      for (r = 6; r < rows.length; r++) {
        var dd = fmtDate(rows[r] ? rows[r][dateCol] : null);
        if (dd) rowByDate[dd] = r;
      }
      for (j = 0; j < b.columns.length; j++) {
        colInfo = b.columns[j];
        prod = colInfo.product; label = colInfo.label;
        var prices = [];
        for (var k = 0; k < dates.length; k++) {
          var ri = rowByDate[dates[k]];
          var v = (ri != null && rows[ri] != null) ? rows[ri][colInfo.col] : null;
          prices.push(toNum(v));
        }
        if (!series[prod]) series[prod] = {};
        if (!series[prod][label]) series[prod][label] = {};
        series[prod][label][b.metric] = prices;
        if (!products[prod]) products[prod] = { name: PRODUCT_NAMES[prod] || '', contracts: [], metrics: [] };
        if (products[prod].contracts.indexOf(label) < 0) products[prod].contracts.push(label);
        if (products[prod].metrics.indexOf(b.metric) < 0) products[prod].metrics.push(b.metric);
      }
    }

    sortProducts(products);
    return { updated_at: nowStr(), source: source, dates: dates, products: products, series: series };
  }

  /** 合并多个工作表的数据集（不同品种分区） */
  function mergeDatasets(list) {
    if (!list.length) throw new Error('没有可解析的工作表');
    var out = { updated_at: nowStr(), source: list[0].source, dates: list[0].dates, products: {}, series: {} };
    list.forEach(function (ds) {
      Object.keys(ds.products).forEach(function (p) {
        if (!out.products[p]) out.products[p] = { name: ds.products[p].name, contracts: [], metrics: [] };
        ds.products[p].contracts.forEach(function (c) { if (out.products[p].contracts.indexOf(c) < 0) out.products[p].contracts.push(c); });
        ds.products[p].metrics.forEach(function (m) { if (out.products[p].metrics.indexOf(m) < 0) out.products[p].metrics.push(m); });
        if (!out.series[p]) out.series[p] = {};
        Object.keys(ds.series[p]).forEach(function (lbl) {
          out.series[p][lbl] = ds.series[p][lbl];
        });
      });
    });
    sortProducts(out.products);
    return out;
  }

  function sortProducts(products) {
    var code;
    for (code in products) {
      if (products.hasOwnProperty(code)) {
        products[code].contracts.sort(compareLabels);
        products[code].metrics.sort();
      }
    }
  }

  /** 合约标签排序：主力 < 最近 < 01 < 02 < ... */
  function compareLabels(a, b) {
    var ka = labelKey(a), kb = labelKey(b);
    return ka[0] !== kb[0] ? ka[0] - kb[0] : ka[1] - kb[1];
  }
  function labelKey(lb) {
    if (lb === '主力') return [0, 0];
    if (lb === '最近') return [0, 1];
    return [1, parseInt(lb, 10) || 0];
  }

  function nowStr() {
    var d = new Date();
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + ' ' +
      pad2(d.getHours()) + ':' + pad2(d.getMinutes());
  }

  global.FuturesParser = {
    parseFile: parseFile,
    build: build,
    parseCode: parseCode,
    fmtDate: fmtDate,
    PRODUCT_NAMES: PRODUCT_NAMES
  };
})(window);
