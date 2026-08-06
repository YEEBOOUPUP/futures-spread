# 期货月差 / 价差分析网站

纯前端静态网站：便捷选取品种与合约，一键查看**月差**（同品种不同月份合约）与**价差**（不同品种合约），
数据源为 WIND 导出的期货价格 Excel（宽表格式），每日更新。

> 📦 **部署到公网请看 [`DEPLOY.md`](DEPLOY.md)**（手把手：注册 → 装 Git → 上传 → 开启 Pages）

内置 5 个品种（来自 `WIND价格-wyb.xlsx` 前两个工作表）：

| 品种 | 名称 | 合约 | 指标 |
|---|---|---|---|
| P | 棕榈油 | 主力 / 最近 / 01~12月（14 个） | 收盘价、结算价 |
| Y | 豆油 | 主力 / 最近 / 01、03、05、07、08、09、11、12月（10 个） | 收盘价 |
| OI | 菜油 | 主力 / 最近 / 01、03、05、07、09、11月（8 个） | 收盘价、结算价 |
| M | 豆粕 | 主力 / 01、03、05、07、08、09、11、12月（9 个） | 收盘价 |
| RM | 菜粕 | 主力 / 01、03、05、07、08、09、11月（8 个） | 收盘价、结算价 |

数据覆盖 2015-01-05 ~ 最新交易日（2817+ 个交易日），`data/data.json` 已用真实文件生成（约 1.6MB）。

## 目录结构

```
futures-spread/
├── index.html            # 主页面（选择器 + 结果区 + 数据管理）
├── css/style.css         # 样式
├── js/
│   ├── parser.js         # 浏览器端解析 WIND 宽表（上传模式）
│   ├── data.js           # 数据加载 + 价差/月差计算
│   └── app.js            # 主逻辑（选择、渲染、图表）
├── data/data.json        # 由转换脚本生成的最新数据（自动读取模式）
├── tools/
│   ├── excel_to_json.py  # 每日转换脚本：WIND Excel → data.json
│   └── explore_winprice.py  # 结构探查调试工具（可选）
├── samples/              # 样例：WIND迷你示例.csv + 格式说明
└── README.md
```

## 功能说明

- **跨品种价差**：任意两个品种各选一个合约（如 P01月 − Y01月），逐日对齐计算 A−B 价差。
- **同品种月差**：一键切换到月差模式，B 自动跟随 A 品种（如 P 01月 − 05月），可 ⇄ 交换方向。
- **价格指标**：收盘价 / 结算价可切换（有结算价数据的品种才有 settle，如 P/OI/RM）。
- **展示**：最新价差、区间最高/最低/均值、日变化、价差走势图（可叠加 A/B 价格线）、明细表。
- **两种数据更新**：
  1. 手动上传：网页直接上传 Excel，浏览器本地解析（localStorage），仅本机可见；
  2. 自动读取：每日用转换脚本生成 `data/data.json`，随站点部署，全站可见（推荐）。

## 快速开始（本地预览）

纯静态页面通过 `fetch` 读取 `data/data.json`，直接双击 `index.html` 会被浏览器拦截跨域请求。
推荐用任意静态服务器：

```powershell
python -m http.server 8000 --directory futures-spread
# 或：npx serve futures-spread
```

浏览器打开 `http://localhost:8000`。

> 本地双击打开时，"自动读取"模式不可用（fetch 被拦截），但可用"手动上传"模式
> （上传 `samples/WIND迷你示例.csv` 或你的真实 Excel 体验）。

## 每日更新流程（线上模式）

1. 把最新 Excel 放到任意路径（如 `C:\...\WIND价格-wyb.xlsx`）。
2. 运行转换脚本：

   ```powershell
   python tools/excel_to_json.py --input "C:\...\WIND价格-wyb.xlsx" --output data/data.json
   ```

   脚本自动处理前两个工作表（油脂 + 油料期货），识别块结构（close/settle）、
   证券代码（主力/最近/01-12月）与日期轴，输出紧凑 JSON。可用 `--sheets 1,2` 指定工作表、
   `--name-map "P:棕榈油"` 覆盖品种中文名。
3. 把 `data/data.json` 随网站一起部署（git push），几分钟后线上数据即更新。

## 部署到公网

### GitHub Pages（推荐，免费）

1. 把本目录推送到 GitHub 仓库。
2. 仓库 Settings → Pages → Source 选 `main` 分支根目录。
3. 访问 `https://<用户名>.github.io/<仓库名>/`。
4. 每日更新：跑转换脚本 → 提交 `data/data.json` → push。

### Cloudflare Pages / Vercel

连接仓库后构建输出目录选根目录即可，同样每次 push 自动更新。

## 数据格式

### WIND 宽表 Excel（输入）

```
行1-2  开始日期 / 截止日期（每块重复）
行3    证券代码：P.DCE=主力  P00.DCE=最近合约  P01M.DCE=01月合约
行4    证券简称（中文名）
行5    指标中文（日期/收盘价）
行6    指标英文：Date/close 或 Date/settle（决定块类型）
行7起  数据：块标签列 = 该块日期列，其余列 = 合约价格
```

### data.json（输出，紧凑结构）

```json
{
  "updated_at": "2026-08-07 10:00",
  "source": "WIND价格-wyb.xlsx",
  "dates": ["2015-01-05", "...", "2026-08-06"],
  "products": {
    "P": { "name": "棕榈油", "contracts": ["主力", "最近", "01", "05"], "metrics": ["close", "settle"] }
  },
  "series": {
    "P": { "主力": { "close": [5006, 5038, "..."], "settle": ["..."] }, "01": { "close": ["..."] } }
  }
}
```

`series` 中每个价格数组与 `dates` 按索引对齐（缺失为 null），前端按共同有效日计算价差/月差。

## 常见问题

- **为什么双击 index.html 显示"无数据"？** 本地 fetch 被浏览器拦截，请用静态服务器或上传模式。
- **为什么某品种切结算价没反应？** 只有 P/OI/RM 有结算价块（Y/M 无），属正常。
- **Excel 换了品种/合约怎么办？** 转换脚本自动按第 3 行代码解析，新增品种只要在文件里就会出现。
