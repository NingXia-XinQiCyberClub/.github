# 贡献指南

本文件规定宁夏大学鑫启网安俱乐部各仓库的协作流程与技术约定，适用于组织内全部仓库。

若单个仓库提供独立的 `CONTRIBUTING.md`，以该仓库文件为准。

---

## 1. 适用范围

本指南适用于以下参与者：

- 组织成员对任意仓库提交变更
- 外部协作者在获得授权后提交变更
- 维护者执行评审与合并操作

---

## 2. 环境准备

### 2.1 Git 安装

| 操作系统 | 安装方式 |
| :-- | :-- |
| Windows | 下载并安装 [Git for Windows](https://git-scm.com/download/win)，采用默认配置 |
| macOS | `brew install git`，或执行 `xcode-select --install` |
| Debian / Ubuntu | `sudo apt update && sudo apt install git` |

安装后验证：

```bash
git --version
```

### 2.2 身份配置

提交身份必须配置，否则提交记录无法正确归属。

```bash
git config --global user.name "<姓名或固定昵称>"
git config --global user.email "<GitHub 注册邮箱>"
```

建议启用邮箱隐私保护：GitHub → Settings → Emails → 勾选 *Keep my email addresses private*，随后将 `user.email` 设置为页面提供的 `*.users.noreply.github.com` 地址。

### 2.3 认证配置

以下两种方式择一。

**方式 A：SSH（推荐）**

```bash
ssh-keygen -t ed25519 -C "<邮箱>"
```

将公钥 `~/.ssh/id_ed25519.pub`（Windows 位于 `%USERPROFILE%\.ssh\`）的内容添加至 GitHub → Settings → SSH and GPG keys。

验证：

```bash
ssh -T git@github.com
```

**方式 B：GitHub CLI**

```bash
gh auth login
```

按提示依次选择 `GitHub.com`、`HTTPS` 与浏览器授权。

### 2.4 编辑器

推荐使用 Visual Studio Code，其内置 Git 面板可覆盖本指南涉及的全部操作。

---

## 3. Git 基本操作

### 3.1 工作区模型

```
工作区 ──git add──▶ 暂存区 ──git commit──▶ 本地仓库 ──git push──▶ 远程仓库
```

### 3.2 常用命令

| 操作目的 | 命令 |
| :-- | :-- |
| 克隆仓库 | `git clone <地址>` |
| 查看工作区状态 | `git status` |
| 同步远程更新 | `git pull` |
| 创建并切换分支 | `git switch -c <分支名>` |
| 切换分支 | `git switch <分支名>` |
| 暂存全部改动 | `git add .` |
| 提交 | `git commit -m "<提交信息>"` |
| 推送 | `git push` |
| 查看提交历史 | `git log --oneline -10` |
| 查看未暂存差异 | `git diff` |
| 撤销未暂存改动 | `git restore <文件>` |
| 撤销最近一次提交并保留改动 | `git reset --soft HEAD~1` |

### 3.3 常见错误处理

| 报错信息 | 成因 | 处理方式 |
| :-- | :-- | :-- |
| `Please tell me who you are` | 未配置提交身份 | 参见 2.2 |
| `Permission denied (publickey)` | SSH 密钥未配置或未加载 | 参见 2.3，或改用 GitHub CLI 认证 |
| `Updates were rejected` | 远程分支存在本地缺失的提交 | 先执行 `git pull --rebase`，再推送 |
| `fatal: not a git repository` | 工作目录错误 | 切换至仓库根目录 |
| `CONFLICT (content)` | 合并冲突 | 参见 3.4 |

### 3.4 冲突处理

冲突文件包含如下标记：

```
<<<<<<< HEAD
本地改动
=======
远程改动
>>>>>>> main
```

处理步骤：

1. 删除 `<<<<<<<`、`=======`、`>>>>>>>` 三行标记
2. 将内容整合为最终版本
3. 执行 `git add <冲突文件>`
4. 执行 `git commit`

无法判断取舍时，应向该文件的最近提交者或维护者确认，不得随意删除他人改动。

---

## 4. 分支规范

`main` 分支受保护，禁止直接推送。全部变更须经分支与变更请求（Pull Request）流程合入。

### 4.1 命名规则

```
<类型>/<简要描述>
```

| 类型 | 用途 | 示例 |
| :-- | :-- | :-- |
| `feat` | 新增功能 | `feat/add-flag-handler` |
| `fix` | 缺陷修复 | `fix/login-timeout` |
| `docs` | 文档变更 | `docs/update-readme` |
| `refactor` | 重构，不改变外部行为 | `refactor/split-utils` |
| `chore` | 构建、依赖与配置调整 | `chore/bump-requests` |
| `test` | 测试相关 | `test/cover-parse` |

命名要求：全小写，使用连字符分隔，不得包含中文、空格或下划线。

### 4.2 分支来源

分支应始终基于最新的 `main` 创建：

```bash
git switch main
git pull
git switch -c <分支名>
```

---

## 5. 提交信息规范

采用 Conventional Commits 的简化形式：

```
<类型>(<可选范围>): <变更摘要>

<可选正文：变更动因与影响>
```

示例：

```
feat(flag_handler): 支持 UDP 数据接收
fix: 修正端口号校验的越界判断
docs: 补充 Windows 环境安装步骤
chore: 升级 requests 依赖版本
```

要求：

- 摘要行不超过 72 个字符
- 使用祈使语气，描述变更而非已完成状态
- 单次提交仅对应一项逻辑变更
- 禁止使用 `update`、`修改`、`fix bug` 等无信息量的摘要

---

## 6. 变更请求流程

### 6.1 提交前检查

- 本地可正常构建与运行
- 未包含密码、令牌、私钥、真实 flag 或内网地址
- 未包含无关文件（`.venv/`、`node_modules/`、`__pycache__/`、编辑器配置）
- 提交信息符合第 5 节要求
- 已执行 `git pull --rebase origin main` 同步最新代码

### 6.2 发起变更请求

推送分支后，于 GitHub 点击 **Compare & pull request**，或访问：

```
https://github.com/NingXia-XinQiCyberClub/<仓库名>/compare
```

变更请求描述由模板生成，须逐项填写。

### 6.3 评审

- 合入前须至少获得 1 名维护者批准
- 评审意见的处理方式为在原分支追加提交并推送，变更请求将自动更新；不得关闭后重新发起
- 持续集成失败时，应先查阅构建日志，多数情形由格式或依赖问题导致

### 6.4 合并

由维护者执行，默认采用 **Squash and merge**。合并后源分支自动删除，本地同步方式：

```bash
git switch main
git pull
git branch -d <分支名>
```

---

## 7. 代码风格

| 语言 | 工具 | 要求 |
| :-- | :-- | :-- |
| Python | ruff | 提交前执行 `ruff check . && ruff format .` |
| JavaScript / TypeScript | prettier | 执行 `npx prettier --write .` |
| C / C++ | clang-format | 遵循仓库内 `.clang-format` |
| Markdown | — | 单行单句，表格对齐 |

通用约定：

- 标识符使用英文，不使用拼音
- 单个函数不超过 50 行，超出应予拆分
- 注释说明设计动因与约束条件，不描述代码字面行为
- 不得保留调试输出、无主 `TODO` 或注释掉的废弃代码

---

## 8. 安全合规要求

本组织涉及攻防技术研究，全部仓库须遵守以下条款。

1. 不得提交任何真实凭据，包括密码、API 密钥、Cookie、私钥与数据库连接串。
2. 不得提交真实 flag。示例与测试数据统一使用 `flag{test}` 占位。
3. 不得提交内网信息，包括真实 IP、域名、学号、身份证号与手机号。
4. 靶场与演练代码须在 `README` 顶部注明适用环境为授权测试环境。
5. 不得对任何未获书面授权的系统实施安全测试。

若误提交凭据，应立即通知维护者并轮换该凭据。清理提交历史不能替代凭据轮换，因为公开仓库的内容应视为已泄露。

---

## 9. 支持渠道

| 事项 | 渠道 |
| :-- | :-- |
| Git 与 GitHub 使用问题 | 本文件第 3 节，及 [SUPPORT.md](./SUPPORT.md) |
| 运行错误 | Discussions → Q&A，须附完整错误输出 |
| 安全缺陷 | [SECURITY.md](./SECURITY.md)，私下上报 |
| 新项目提议 | Discussions → Ideas |
| 协作纠纷 | 私下联系维护者 |

---

## 10. 入门任务

入门任务的获取渠道：

- 各仓库 Issues 中标记为 `good first issue` 的条目
- 仓库 `/contribute` 页面，该页面自动聚合 `good first issue` 与 `help wanted` 标签

---

<div align="center">
<sub>

本指南随组织发展持续修订。修订建议通过变更请求提出。

</sub>
</div>
