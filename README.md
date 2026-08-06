# 期货月差 / 价差分析网站

纯前端静态网站：便捷选取品种与合约，一键查看**月差**（同品种不同月份合约）与**价差**（不同品种合约）。

**数据完全自动采集，无需手动更新 Excel：**
- **历史数据**：新浪期货日线重建（2019 年至今，全市场收盘价），一次性脚本 `collector/history_fill.py`
- **每日增量**：openctp 数据中心接口（免费、无需注册），每个交易日收盘后自动采集当日收盘价并推送
- 部署在 GitHub Pages：https://yeebooupup.github.io/futures-spread/

> 📦 部署与 Git 教程见 [`DEPLOY.md`](DEPLOY.md)

## 目录结构

```
futures-spread/
├── index.html            # 主页面（选择器 + 结果区 + 数据状态）
├── css/style.css
├── js/
│   ├── data.js           # 数据加载（index.json + 品种懒加载）+ 价差/月差计算
│   └── app.js            # 主逻辑（选择、渲染、图表、快捷键）
├── data/
│   ├── index.json        # 元数据：品种列表 / 更新时间
│   └── {品种}.json       # 各品种：dates + series{月份}.close（独立日期轴）
├── collector/
│   ├── history_fill.py   # 一次性：新浪全市场历史重建（2019+）
│   ├── daily_fetch.py    # 每日：openctp 收盘价增量（幂等）
│   ├── update_daily.bat  # 每日入口（双击运行：采集+推送）
│   ├── update_daily.ps1  # 采集+git 推送脚本
│   └── setup_task.ps1    # 注册 Windows 计划任务（每天 16:00 自动跑）
├── tools/                # 调试/验证脚本
└── README.md / DEPLOY.md
```

## 功能

- **跨品种价差** / **同品种月差**（快捷键：91/15/59 月差；豆棕/菜豆/菜棕/豆菜粕价差）
- **季节性图**（默认）：横轴一年内日期，每年一条线（最新年份红色加粗），图例点击隐藏年份
- **时序图**：完整时间线，快捷"最近1月/半年/1年"，双滑块时间轴
- **纵轴范围**手动调节
- 价格指标：**收盘价**（仅此一项）

## 数据管道（全自动）

### 一次性：重建历史

```powershell
python collector\history_fill.py
```

从 openctp 数据中心获取品种列表，用新浪日线逐个拉取历年合约（2019 至今），
按"连续月合约"规则拼接（同品种同月份历年合约无缝衔接），输出 `data/index.json` + 各品种文件。

### 每日：自动增量（Windows 计划任务）

1. 运行一次注册任务（只需一次）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File collector\setup_task.ps1
   ```
2. 之后每个交易日 **16:00 自动**：`daily_fetch.py` 拉 openctp 当日收盘价 → 增量合并 → git 提交推送
3. 也可手动双击 `collector\update_daily.bat` 立即跑一次

`daily_fetch.py` 幂等：数据已更新到当日则跳过；非交易日重复运行无副作用。

### 手动跑每日增量

```powershell
python collector\daily_fetch.py
```

## 本地预览

```powershell
python -m http.server 8000 --directory futures-spread
# 浏览器打开 http://127.0.0.1:8000
```

## 数据格式

### data/index.json

```json
{
  "updated_at": "2026-08-07 16:05",
  "source": "sina-daily + openctp",
  "products": {
    "P": { "name": "棕榈油", "contracts": ["01","02",...], "metrics": ["close"], "file": "P.json" }
  }
}
```

### data/{品种}.json

```json
{
  "dates": ["2019-01-02", "..."],
  "series": { "01": { "close": [4150.0, "..."] }, "05": { "close": ["..."] } }
}
```

每品种独立日期轴，前端按共同交易日对齐计算价差/月差。

## 常见问题

- **为什么某些品种历史只有 2019 起？** 新浪免费源历史深度约 2019 年；2019 前完整全市场历史无免费源。
- **为什么今天还没数据？** 每日 16:00 采集，收盘价 15:00 后确定；若当天休市则自动跳过。
- **计划任务没跑？** 需保持电脑开机；错过会补跑（StartWhenAvailable）。
