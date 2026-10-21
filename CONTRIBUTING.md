# 贡献指南

> 适用于鑫启网安社团 **所有仓库**。单个仓库若有自己的 `CONTRIBUTING.md`，以该仓库的为准。
>
> 预计阅读 10 分钟。跟着做完，你就能独立提第一个 PR。

---

## 0. 三分钟版本

如果你只想快速上手，记住这三步：

```bash
git clone https://github.com/NingXia-XinQiCyberClub/<仓库名>.git
cd <仓库名>
git checkout -b feat/your-name-hello
# 改点东西
git add . && git commit -m "docs: 修正一个错别字"
git push -u origin feat/your-name-hello
# 然后去 GitHub 点 "Compare & pull request"
```

细节在下面。

---

## 1. 准备环境

### 1.1 安装 Git

| 系统 | 方式 |
| :-- | :-- |
| **Windows** | [下载 Git for Windows](https://git-scm.com/download/win)，一路默认安装即可 |
| **macOS** | `brew install git` 或执行 `xcode-select --install` |
| **Linux (Debian/Ubuntu)** | `sudo apt update && sudo apt install git` |

验证：

```bash
git --version
# 应输出类似 git version 2.4x.x
```

### 1.2 配置身份

**必须做**，否则提交记录会归属错误。

```bash
git config --global user.name "你的名字或昵称"
git config --global user.email "你的GitHub注册邮箱"
```

> 建议同时开启邮箱隐私保护：GitHub → Settings → Emails → 勾选 *Keep my email addresses private*，
> 然后把 `user.email` 设成页面给出的 `xxxxx@users.noreply.github.com`。

### 1.3 配置认证（二选一）

**方式 A：SSH（推荐）**

```bash
ssh-keygen -t ed25519 -C "你的邮箱"
# 一路回车，默认路径即可
```

然后把 `~/.ssh/id_ed25519.pub`（Windows 在 `C:\Users\你的用户名\.ssh\`）的内容
粘贴到 GitHub → Settings → SSH and GPG keys → New SSH key。

验证：

```bash
ssh -T git@github.com
# 成功会看到: Hi 用户名! You've successfully authenticated...
```

**方式 B：GitHub CLI**

```bash
gh auth login
```

跟着交互提示选 `GitHub.com` → `HTTPS` → 浏览器登录。

### 1.4 一个趁手的编辑器

| 编辑器 | 说明 |
| :-- | :-- |
| **VS Code** | 最通用，内置 Git 面板，推荐新手 |
| Neovim / Zed | 熟悉命令行的同学随意 |

---

## 2. Git 最小知识集

社团里你只需要掌握这些，**不用**先学 rebase、submodule、cherry-pick。

### 2.1 三个区域

```
工作区  ──git add──▶  暂存区  ──git commit──▶  本地仓库  ──git push──▶  远程仓库
(改文件)              (待提交)                (历史记录)              (GitHub)
```

### 2.2 高频命令速查

| 目的 | 命令 |
| :-- | :-- |
| 克隆仓库 | `git clone <地址>` |
| 看当前状态 | `git status` |
| 拉取最新代码 | `git pull` |
| 建并切换分支 | `git switch -c <分支名>` |
| 切换分支 | `git switch <分支名>` |
| 暂存所有改动 | `git add .` |
| 提交 | `git commit -m "说明"` |
| 推送 | `git push` |
| 看提交历史 | `git log --oneline -10` |
| 看改了什么 | `git diff` |
| 撤销未暂存的改动 | `git restore <文件>` |
| 撤销最后一次提交（保留改动） | `git reset --soft HEAD~1` |

### 2.3 常见报错怎么办

| 报错 | 原因 | 解法 |
| :-- | :-- | :-- |
| `Please tell me who you are` | 没配 user.name / user.email | 回到 1.2 |
| `Permission denied (publickey)` | SSH key 没配好 | 回到 1.3，或改用 `gh auth login` |
| `Updates were rejected` | 远程有你没有的提交 | 先 `git pull --rebase`，再 `git push` |
| `fatal: not a git repository` | 当前目录不对 | `cd` 到仓库目录 |
| `CONFLICT (content)` | 冲突 | 见 2.4 |

### 2.4 遇到冲突

打开冲突文件，会看到：

```
<<<<<<< HEAD
你的改动
=======
别人的改动
>>>>>>> main
```

**手动**删掉 `<<<<<<<`、`=======`、`>>>>>>>` 三行标记，把内容改成你想要的最终版本，然后：

```bash
git add <冲突文件>
git commit
```

> 拿不准就**直接问**，不要乱删别人的代码。

---

## 3. 分支规范

`main` 分支受保护，**禁止直接推送**。所有改动走分支 + PR。

### 3.1 命名

```
<类型>/<简短描述>
```

| 类型 | 用途 | 例子 |
| :-- | :-- | :-- |
| `feat` | 新功能 | `feat/add-flag-handler` |
| `fix` | 修 bug | `fix/login-timeout` |
| `docs` | 只改文档 | `docs/update-readme` |
| `refactor` | 重构（不改行为） | `refactor/split-utils` |
| `chore` | 杂项（配置、依赖） | `chore/bump-requests` |
| `test` | 加测试 | `test/cover-parse` |

**要求**：全小写、用连字符、不含中文和空格。

### 3.2 从哪切分支

始终从最新的 `main` 切：

```bash
git switch main
git pull
git switch -c feat/your-thing
```

---

## 4. 提交信息规范

采用 **Conventional Commits**（简化版）：

```
<类型>(<可选范围>): <一句话说明>

<可选正文：为什么这么改>
```

**示例**：

```
feat(flag_handler): 支持 UDP 接收
fix: 修复端口号校验越界
docs: 补充 Windows 安装步骤
chore: 升级 requirements 里的 requests
```

**要求**：
- 一行不超过 72 个字符
- 用**祈使句**："添加 X" 而不是 "添加了 X"
- 一次提交只做一件事
- 不要写 "update"、"修改"、"fix bug" 这种无信息量的说明

---

## 5. PR 流程

### 5.1 提交前自检

- [ ] 代码能在本地跑起来
- [ ] 没有把密码、token、flag、内网 IP 提交上去
- [ ] 没有提交无关文件（`.venv/`、`node_modules/`、`__pycache__/`、编辑器配置）
- [ ] 提交信息符合规范
- [ ] 已 `git pull --rebase origin main` 同步最新代码

### 5.2 发起 PR

推送分支后，GitHub 会提示 **Compare & pull request**，点它。或者：

```
https://github.com/NingXia-XinQiCyberClub/<仓库名>/compare
```

PR 描述会自动带上模板，把每一项填清楚。

### 5.3 Review

- 至少 **1 位** maintainer approve 才能合并
- 收到修改意见后，**在同一个分支继续提交**并推送，PR 会自动更新（不要关掉重开）
- CI 红了先看日志，多数是格式或依赖问题

### 5.4 合并

由 maintainer 操作，默认 **Squash and merge**。合并后你的分支会被删除，本地清理：

```bash
git switch main
git pull
git branch -d feat/your-thing
```

---

## 6. 代码风格

| 语言 | 工具 | 要求 |
| :-- | :-- | :-- |
| Python | `ruff` | 提交前 `ruff check . && ruff format .` |
| JavaScript / TypeScript | `prettier` | `npx prettier --write .` |
| C / C++ | `clang-format` | 跟随仓库 `.clang-format` |
| Markdown | — | 一行一句、表格对齐即可 |

通用原则：
- 变量名用英文，**不要拼音**
- 函数不超过 50 行，超了就拆
- 关键逻辑写注释说明**为什么**，不是**做什么**
- 不留 `print("debug")`、`TODO` 无主

---

## 7. 安全红线

社团仓库涉及攻防技术，**必须**遵守：

1. **不提交任何真实凭据**：密码、API Key、Cookie、私钥、数据库连接串
2. **不提交真实 flag**：比赛 flag 统一用 `flag{test}` 占位
3. **不提交内网信息**：真实 IP、域名、学号、身份证、手机号
4. **靶场代码需标注**：在 README 顶部写明「仅用于授权环境测试」
5. **不要向他人系统做任何未授权测试** —— 这是法律问题，不是纪律问题

一旦误提交了密钥：**立刻**在仓库 Discussions 或私下通知 maintainer，我们会帮你轮换并清理历史。**不要**自己 force push 掩盖。

---

## 8. 求助

| 情况 | 去哪 |
| :-- | :-- |
| 不会用 Git | 先看本文第 2 节，再看 [SUPPORT.md](./SUPPORT.md) |
| 代码跑不起来 | Discussions → Q&A，附完整报错 |
| 发现安全问题 | 按 [SECURITY.md](./SECURITY.md) 私下上报 |
| 想提议新项目 | Discussions → Ideas |
| 与人协作不愉快 | 私下联系 maintainer |

---

## 9. 新手任务去哪找

- 仓库的 **Issues → `good first issue`** 标签
- 或者直接打开 `https://github.com/NingXia-XinQiCyberClub/<仓库名>/contribute`

---

<div align="center">
<sub>本指南随社团发展持续更新。发现不合理之处，欢迎提 PR 修改。</sub>
</div>
