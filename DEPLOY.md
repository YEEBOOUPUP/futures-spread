# 部署到 GitHub Pages（公网访问）教程

> 目标：把网站发布到公网，**任何人打开网址就能看**（不需要登录、不需要账号）。
> GitHub Pages 提供免费静态托管，你的网站是纯前端，正好适合。

---

## 第 0 步：注册 GitHub 账号（如果没有）

1. 打开 https://github.com 点 **Sign up**
2. 按提示填邮箱、密码、用户名（用户名会出现在你的网址里，建议用拼音或英文，如 `wangyibo`）
3. 完成邮箱验证

---

## 第 1 步：安装 Git（电脑上还没装）

1. 打开 https://git-scm.com/download/win 下载 **64-bit Git for Windows Setup**
2. 双击安装，一路点 **Next** 即可（所有选项保持默认）
3. 安装完，按 `Win` 键 → 输入 `powershell` → 回车，打开 PowerShell

## 第 2 步：告诉 Git 你是谁（一次性）

在 PowerShell 里粘贴以下两行（把邮箱/名字换成你 GitHub 的）：

```powershell
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub注册邮箱"
```

---

## 第 3 步：在 GitHub 上创建空仓库

1. 打开 https://github.com/new
2. **Repository name** 填 `futures-spread`（小写字母）
3. **Public**（公开，必选，免费）
4. 其他保持默认，点 **Create repository**

创建后会看到一个页面，先别关，后面要用。

---

## 第 4 步：把网站代码推上去

在 PowerShell 里逐条粘贴执行（注意：命令里的 `你的GitHub用户名` 要替换成你的实际用户名）：

```powershell
cd C:\Users\10172\AppData\Roaming\reasonix\global-workspace\futures-spread

git init
git add .
git commit -m "首次部署期货月差价差网站"

git branch -M main
git remote add origin https://github.com/你的GitHub用户名/futures-spread.git
git push -u origin main
```

- 第一次 push 会弹出一个窗口让你**登录 GitHub**（用浏览器登录，或选 token 方式）
- 出现 `main -> main` 之类的输出就是成功了
- 如果报错 `remote origin already exists`，先执行 `git remote remove origin` 再重试

> 看不到 `git push` 弹窗的话，用这个方式登录：
> GitHub 网页 → 头像 → Settings → Developer settings → Personal access tokens →
> Tokens (classic) → Generate new token → 勾选 `repo` → 生成后复制 token，
> push 时用户名填 GitHub 用户名，密码粘贴 token。

---

## 第 5 步：开启 GitHub Pages

1. 回到你的仓库页面 https://github.com/你的GitHub用户名/futures-spread
2. 点 **Settings** → 左侧菜单选 **Pages**
3. **Branch** 选 `main`，文件夹选 `/ (root)`，点 **Save**
4. 等 1~3 分钟，页面顶部会出现网址：
   `https://你的GitHub用户名.github.io/futures-spread/`

## 第 6 步：查看效果

浏览器打开上面的网址（或发给别人）就能看到网站了。

---

## 以后每天怎么更新数据（核心流程）

每天更新 Excel 后，重新生成数据再推送，几分钟后线上更新：

```powershell
cd C:\Users\10172\AppData\Roaming\reasonix\global-workspace\futures-spread

# 1. 用最新 Excel 重新生成 data.json
python tools\excel_to_json.py --input "C:\Users\10172\OneDrive\Desktop\临时数据处理\WIND价格-wyb.xlsx" --output data\data.json

# 2. 提交并推送
git add data\data.json
git commit -m "更新数据到 2026-08-06"
git push
```

---

## 常见问题

| 问题 | 解决 |
|---|---|
| push 时提示输入用户名密码但输不对 | 用 Personal access token 当密码（见第 4 步） |
| 更新后网页没变化 | 等 1~2 分钟，或按 Ctrl+F5 强制刷新 |
| 想换网址前缀 | 把仓库改名为 `你的用户名.github.io`，网址就是 `https://你的用户名.github.io/` |
| 想删掉网站 | 仓库 Settings → 拉到最底部 Danger Zone → Delete this repository |

## 补充：想让别人"登录"？

不需要。GitHub Pages 是公开网页，**任何人打开网址直接就能看**，
和你自己访问完全一样，不用注册、不用登录。如果以后想要"必须登录才能看"（私有），
GitHub Pages 不支持，需要换别的方式（如 Cloudflare Access），到时候再说。
