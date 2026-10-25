# .github

本仓库为 **宁夏大学鑫启网安俱乐部** 的组织级配置仓库，不含业务代码，用于统一组织主页内容与组织内各仓库的协作规范。

---

## 一、目录结构

| 路径 | 作用 |
| :-- | :-- |
| `profile/README.md` | 组织主页 Overview 页面的展示内容 |
| `profile/logo.png` | 组织标识（512×512，32 位 ARGB） |
| `CONTRIBUTING.md` | 组织级默认贡献指南 |
| `CODE_OF_CONDUCT.md` | 行为准则 |
| `SECURITY.md` | 安全缺陷上报政策 |
| `SUPPORT.md` | 技术支持与提问规范 |
| `PULL_REQUEST_TEMPLATE.md` | 组织级默认变更请求模板 |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | 缺陷报告表单 |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | 功能建议表单 |
| `.github/ISSUE_TEMPLATE/join.yml` | 加入社团申请表单（含流程清单与信息登记） |
| `.github/ISSUE_TEMPLATE/config.yml` | 工单入口配置，将提问引导至 Discussions |
| `.github/workflows/welcome.yml` | 首次交互自动应答工作流 |
| `.github/workflows/validate-join.yml` | 加入申请学号格式校验工作流 |
| `.github/workflows/invite-member.yml` | 加入申请校验通过后自动发出组织邀请工作流 |
| `.github/workflows/feishu-broadcast.yml` | 飞书播报的可复用工作流，供各仓库调用 |
| `.github/workflows/feishu-events.yml` | 本仓库的播报触发入口 |
| `.github/workflows/weekly-summary.yml` | 每周一汇总组织动态并播报 |
| `.github/workflows/welcome-reminder.yml` | 发现飞书群新成员并提醒填写加入工单 |
| `scripts/feishu/notify.py` | 事件卡片渲染与飞书发送 |
| `scripts/feishu/summary.py` | 周报统计与卡片生成 |
| `scripts/feishu/welcome.py` | 群成员对比与新成员提醒 |
| `scripts/feishu/_selftest.py` | 播报渲染的本地测试，不联网 |
| `scripts/feishu/_selftest_summary.py` | 周报渲染的本地测试，不联网 |
| `scripts/feishu/_selftest_send.py` | 签名与地址校验的本地测试，不联网 |
| `scripts/feishu/_selftest_welcome.py` | 新成员提醒的本地测试，不联网 |
| `workflow-templates/feishu-events.yml` | 各仓库一键添加播报的模板文件 |

---

## 二、生效机制

1. 上述文件对组织内所有仓库生效，前提是目标仓库未提供同名文件。仓库内自带文件的优先级高于组织级默认文件。
2. `profile/README.md` 仅在**本仓库可见性为 public** 时展示于组织公开主页。本仓库当前已设为 public。
3. 若需向已登录成员展示额外内容，应另行创建**私有**仓库 `.github-private`，并在其 `profile/README.md` 中维护。

---

## 三、修订流程

```bash
git clone https://github.com/NingXia-XinQiCyberClub/.github.git
cd .github
git switch -c docs/<变更说明>
# 修改文件
git add .
git commit -m "docs: <变更说明>"
git push -u origin docs/<变更说明>
```

推送后在 GitHub 发起变更请求。`main` 分支已启用保护规则，要求至少 1 名评审人通过。

---

## 四、待办事项

- [x] 补充 `profile/logo.png` 并在 `profile/README.md` 中引用
- [x] 建立 `guide` 仓库，编写体系化教程
- [x] 核验 Discussions 分类配置（Announcements / General / Ideas / Polls / Q&A / Show and tell）
- [x] 为入门任务添加 `good first issue` 标签，并在 `guide` 仓库建立 4 项入门工单
- [x] 配置组织默认仓库权限为 read
- [x] 上传组织头像
- [x] 组织治理决策：全体成员均授予所有者权限（见下节说明）
- [x] 组织治理决策：不启用组织级两步验证强制策略

---

## 五、治理决策记录

本节记录与组织治理相关的既定决策，避免后续重复讨论。

### 5.1 所有者权限

组织现有 8 名成员，全部授予所有者（Owner）权限。

决策依据：组织当前处于初创阶段，成员均为核心管理人员，需共同承担仓库创建、成员邀请、权限配置等管理工作。扁平结构可减少审批环节，提升协作效率。

约束条件：

1. 所有者可执行仓库删除、成员移除、计费设置修改等不可逆操作，操作前应知会其他所有者。
2. 组织须始终保持至少两名所有者，防止因单一账号失联导致组织无法管理。
3. 成员规模扩大至 15 人以上时，应重新评估该结构，将非管理职能成员调整为 Member，并按仓库授权。

### 5.2 两步验证

组织不启用两步验证强制策略。

说明：该策略一旦启用，未完成配置的成员将立即失去组织访问权限，需在成员自行完成配置后方可启用。组织当前依赖成员个人账号的安全设置，建议成员主动启用，但不作强制要求。

加入社团申请工单不设两步验证条目，流程清单不含该步骤。

### 5.3 入门任务

`guide` 仓库中标有 `good first issue` 的工单构成新成员入门任务集，详见该仓库 README 的「入门任务」一节。任务完成后由维护者评审合并，作为首次变更请求的实践。

### 5.4 成员邀请

加入申请工单通过校验后，由 `invite-member.yml` 自动发出组织邀请，角色固定为 **Member**（`direct_member`），不授予 Owner。

决策依据：自动化只承担可机械判定的部分（学号格式、流程清单、承诺事项），减少维护者的重复操作；角色不随自动化放开，避免权限扩张。

约束条件：

1. 工作流不修改现有成员的角色。申请账号若已是成员，仅回复说明并跳过，**不降级、不提权**。
2. 邀请由申请人在 7 天内自行接受，逾期需重新发出；工作流只能投递邀请，不能代为接受。
3. 邀请依赖仓库密钥 `ORG_INVITE_TOKEN`，须具备 `admin:org` 范围或 GitHub App 的 Members 读写权限。默认 `GITHUB_TOKEN` 无组织管理权限，不可替代。
4. 新增成员默认只读公开仓库。私有仓库仍须按 5.1 的约束单独授权。
5. 校验通过仅代表**格式合规**，不代表身份核实。学号与姓名为申请人自填，工单正文公开可见，存在冒填可能；如需收紧，应在 5.1 的规模评估中一并调整。
6. 邀请发出后向招新群公告新成员，公告口径与隐私处理见 7.2 节。公告失败不回滚邀请，也不阻塞工单关闭。

开关：仓库变量 `AUTO_INVITE`。**默认开启**，仅当显式设为 `off` 时整条工作流跳过，不打标签、不发评论、不报错。

```bash
gh variable set AUTO_INVITE --body off --repo NingXia-XinQiCyberClub/.github   # 关闭
gh variable set AUTO_INVITE --body on  --repo NingXia-XinQiCyberClub/.github   # 开启
```

关闭后工单保持原样，由维护者按人工流程处理。已发出的邀请不受影响，仍须在组织 People 页面的 pending 列表中撤销。

---

## 六、新建仓库检查清单

新建仓库后，须按以下清单逐项配置。本节记录已出现过的配置错误，避免重复发生。

### 6.1 模板目录位置

工单模板与配置必须位于**仓库内的 `.github/ISSUE_TEMPLATE/` 目录**，不得放在仓库根目录的 `ISSUE_TEMPLATE/`。

```
<仓库>/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   └── ...
│   └── workflows/
└── README.md
```

位置错误的表现：访问 `?template=<名称>.yml` 时回落到空白工单编辑器，`config.yml` 中的 `blank_issues_enabled: false` 不生效。

注意本仓库名为 `.github`，其模板路径为 `.github/.github/ISSUE_TEMPLATE/`，并非根目录 `ISSUE_TEMPLATE/`。

### 6.2 标签创建

模板 `labels` 字段声明的标签，必须在**当前仓库**中存在，否则提交后标签不会自动附加。

GitHub 默认提供的标签：

```
accessibility  bug  documentation  duplicate  enhancement
good first issue  help wanted  invalid  question  wontfix
```

组织内模板额外依赖以下**非默认**标签，每个新建仓库均须手动创建：

| 标签 | 建议颜色 | 用途 |
| :-- | :-- | :-- |
| `triage` | `fbca04` | 待分类，等待维护者评估优先级与归属 |
| `membership` | `0e8a16` | 加入社团申请与成员登记 |
| `needs-info` | `d93f0b` | 信息不完整或格式不符，需补充 |
| `invited` | `8250df` | 已发出组织邀请或已是成员 |

创建命令：

```bash
for repo in <仓库1> <仓库2>; do
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" \
    -f name="triage" -f color="fbca04" \
    -f description="待分类，等待维护者评估优先级与归属"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" \
    -f name="membership" -f color="0e8a16" \
    -f description="加入社团申请与成员登记"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" \
    -f name="needs-info" -f color="d93f0b" \
    -f description="信息不完整或格式不符，需补充"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" \
    -f name="invited" -f color="8250df" \
    -f description="已发出组织邀请或已是成员"
done
```

PowerShell 等价写法：

```powershell
foreach ($repo in @('<仓库1>','<仓库2>')) {
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" -f name="triage" -f color="fbca04" -f description="待分类，等待维护者评估优先级与归属"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" -f name="membership" -f color="0e8a16" -f description="加入社团申请与成员登记"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" -f name="needs-info" -f color="d93f0b" -f description="信息不完整或格式不符，需补充"
  gh api -X POST "repos/NingXia-XinQiCyberClub/$repo/labels" -f name="invited" -f color="8250df" -f description="已发出组织邀请或已是成员"
}
```

### 6.3 合并策略

组织内仓库统一采用 Squash 合并，保持 `main` 线性历史：

```bash
gh api -X PATCH "repos/NingXia-XinQiCyberClub/<仓库>" \
  -F allow_squash_merge=true \
  -F allow_merge_commit=false \
  -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true
```

### 6.4 分支保护

`main` 分支须启用保护，要求至少 1 名评审人通过：

```bash
gh api -X PUT "repos/NingXia-XinQiCyberClub/<仓库>/branches/main/protection" \
  -F "required_status_checks=null" \
  -F "enforce_admins=false" \
  -F "required_pull_request_reviews[required_approving_review_count]=1" \
  -F "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  -F "restrictions=null" \
  -F "allow_force_pushes=false" \
  -F "allow_deletions=false"
```

### 6.5 检查项汇总

- [ ] `.github/ISSUE_TEMPLATE/` 目录存在，且包含 `config.yml`
- [ ] `triage`、`membership`、`needs-info`、`invited` 标签已创建
- [ ] 合并方式仅保留 Squash，且合并后自动删除分支
- [ ] `main` 分支保护已启用
- [ ] Discussions 是否需开启（教程与配置类仓库建议开启）
- [ ] Wiki 是否需开启（默认关闭，文档统一用 Markdown 维护）
- [ ] 仓库描述与 Topics 已填写
- [ ] 若启用自动邀请，`.github` 仓库已配置 `ORG_INVITE_TOKEN` 与变量 `AUTO_INVITE`
- [ ] 若启用飞书播报，已复制 `workflow-templates/feishu-events.yml` 至该仓库 `.github/workflows/`
- [ ] 若启用新成员提醒，`.github` 仓库已配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_CHAT_ID_RECRUIT`

### 6.6 验证接口的局限

判断模板是否生效时，以下接口**不可靠**：

| 接口 | 局限 |
| :-- | :-- |
| `GET /repos/{owner}/{repo}/community/profile` | `issue_template` 字段仅反映旧版单文件模板，YAML 表单返回 `null` |
| GraphQL `repository.issueTemplates` | 仅返回旧版 `.md` 模板，YAML 表单不出现 |

可靠验证方式为直接访问：

```
https://github.com/NingXia-XinQiCyberClub/<仓库>/issues/new/choose
```

页面应列出各表单选项。若模板刚提交，GitHub 存在短暂缓存，可等待约 1 分钟后重试。

---

## 七、飞书播报

组织内的提交、变更请求与工单可播报到飞书群，每周一另发一份周报。播报只做通知，不参与任何审批或权限判定；播报失败不影响仓库的正常协作。

### 7.1 工作原理

```
仓库事件 ──▶ .github/workflows/feishu-events.yml（各仓库内的触发入口）
                    │ uses
                    ▼
             .github/workflows/feishu-broadcast.yml（本仓库的可复用工作流）
                    │ 下载并执行
                    ▼
             scripts/feishu/notify.py ──▶ 飞书群自定义机器人
```

三个仓库各自只需一份约 30 行的触发文件，文案与格式改动只需修改 `scripts/feishu/notify.py`，不必逐仓库同步。

### 7.2 播报范围

| 事件 | 触发时机 | 卡片标题 | 目标群 |
| :-- | :-- | :-- | :-- |
| `push` | 推送至任意分支，或推送 `v*` 标签 | 提交 · 仓库名 / 标签 · 仓库名 | 主群 |
| `pull_request` | 新开、重开、转为待评审、转为草稿、关闭（含合入） | 变更请求已合入 · 仓库名 等 | 主群 |
| `issues` | 新开、重开、关闭（入会工单除外） | 新开工单 · 仓库名 | 主群 |
| 新成员加入 | `invite-member.yml` 校验通过并发出组织邀请 | 新成员加入 | 招新群 |

入会工单的播报口径与其他工单不同：**申请提交时不播报，只在审核通过、组织邀请正式发出后公告一次**。理由是新成员信息（姓名、年级、学号）在未批准前属于待审材料，不宜在群里扩散；同时避免「申请一条、退回一条、再申请一条」造成刷屏。

公告卡片包含姓名、GitHub 账号、年级、脱敏学号（形如 `1202＊＊＊＊193`）、学院专业与研究兴趣，末尾注明邀请已发至注册邮箱、7 天内有效、需本人接受。以下情形不公告：

- 邀请接口返回 422，即组织内已有该账号的待接受邀请（属重试，非新成员）
- 申请账号已是组织成员，工作流未修改其角色
- 邀请失败，此时由工单评论与 Actions 失败状态提示维护者

刻意不播报的其他情形：

1. 变更请求的 `synchronize`（每次追加提交）不播报，否则评审期间会反复刷屏
2. 仅含 `Merge pull request #N`、`Merge branch ...` 或 `...(#N)` 的推送不播报。采用 Squash 合并时，合入动作已由 `pull_request closed` 播报一次，这类推送属重复
3. `github-actions[bot]` 自身操作触发的推送不播报
4. 来自分叉仓库的变更请求拿不到密钥，播报自动失效
5. 删除分支的推送不播报

### 7.3 配置步骤

#### 第一步：建群并添加自定义机器人

群机器人挂在群上，必须先有群。建议建两个群：一个主群收代码动态，一个招新群只收新成员公告。

**1. 建群**

飞书客户端（桌面端或手机端均可）左上角「＋」→「创建群组」→ 拉人 → 建好。建完点群名进入群设置，可以改名，例如「鑫启网安 · 开发播报」「鑫启网安 · 招新」。

**2. 添加机器人**

进入群聊 → 右上角「···」或群名 →「设置」→「群机器人」→「添加机器人」→ 在列表里找到「自定义机器人」（有的版本叫「Webhook 机器人」）→「添加」。

> 只有群主或管理员能添加。若看不到该选项，说明你在这个群里不是管理员。

找不到「自定义机器人」时，按以下顺序排查：

1. **必须用飞书客户端**。网页版没有「添加机器人」入口，这是飞书自身的限制，不是权限问题。Windows / macOS 桌面端或手机 App 都可以。
2. **外部群只能用桌面端**。群里只要有一名非本校成员（例如已毕业的学长用的是另一个租户），该群即为外部群。外部群照旧支持自定义机器人，但只允许在桌面端添加，手机端看不到入口。
3. 群设置里只有「添加机器人」而没有分类列表时，点进去往下滚，自定义机器人通常排在应用机器人之后。
4. 企业管理员可能在管理后台关闭了群自定义机器人。此时群设置里只会剩下应用机器人，无法绕过——改用 7.3B 的自建应用方案。

如果四条都试过仍没有，直接用方案 B，不必在这一点上继续耗时间。

**3. 设置安全校验**

添加时会弹出配置页，填三项：

| 项 | 怎么填 |
| :-- | :-- |
| 机器人名称 | 例如「鑫启播报」，群里显示的就是这个名字 |
| 描述 | 可留空 |
| 安全设置 | 勾选「签名校验」，页面会给出一个密钥（一长串字母数字） |

密钥只显示这一次，先复制到记事本再继续。若误关页面，回到机器人设置里可以「重置密钥」，重置后旧密钥立即失效，需要同步更新 GitHub Secrets。

「自定义关键词」和「IP 白名单」不要勾。关键词会要求每条消息都包含指定词，而播报内容是脚本生成的，加关键词容易漏发；GitHub Actions 的出口 IP 不固定，白名单也没法用。

**4. 复制 Webhook 地址**

点「完成」后，页面显示 Webhook 地址，形如：

```
https://open.feishu.cn/open-apis/bot/v2/hook/8f3a1c2e-4b5d-6e7f-8a9b-0c1d2e3f4a5b
```

这一段是「投递地址」，等于群的收件箱，谁拿到都能往里发消息，因此同样按密钥对待，不要贴到公开页面。

**5. 到招新群重复一次**

同样的步骤在招新群再加一个机器人，得到第二个 Webhook 与第二个密钥。

#### 第二步：写入 GitHub Secrets

回到 GitHub 网页，进入 `NingXia-XinQiCyberClub/.github` 仓库：

Settings → 左侧「Secrets and variables」→「Actions」→「Secrets」标签页 → 右上「New repository secret」。

每条密钥建完都要点一次「Add repository」并选择可访问的仓库，关键是：

**把 `Repository access` 选成「All repositories」，否则 `guide` 和站点仓库里的播报工作流取不到值。**

| Name 填这个 | Secret 填这个 | 来源 |
| :-- | :-- | :-- |
| `FEISHU_WEBHOOK` | 主群 Webhook 地址 | 第一步第 4 项 |
| `FEISHU_WEBHOOK_SECRET` | 主群机器人密钥 | 第一步第 3 项 |
| `FEISHU_WEBHOOK_RECRUIT` | 招新群 Webhook 地址 | 第一步第 5 项 |
| `ORG_STATS_TOKEN` | GitHub 令牌，见下方说明 | GitHub 个人设置 |

找不到「自定义机器人」时，跳过本步，改用 7.3B 的方案 B（企业自建应用）。

名称必须一字不差，大小写敏感。填完后列表里只显示名称与更新时间，值无法再查看，填错只能删除重建。

**只想先试主群**：只配前两条即可。`FEISHU_WEBHOOK_RECRUIT` 不配时，新成员公告会并入主群，不会丢。

`ORG_STATS_TOKEN` 只影响周报，不影响提交与变更请求播报，可以稍后再补。它需要覆盖整个组织的读取范围，不能用 Actions 自带的 `GITHUB_TOKEN`（该令牌只对当前仓库有效）。两种做法：

1. 经典令牌：GitHub 右上头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾选 `repo` 与 `read:org`
2. 细粒度令牌：Personal access tokens → Fine-grained tokens，`Repository access` 选「All repositories」，权限给 `Metadata`（必选，自动附带）、`Contents` 只读、`Issues` 只读、`Pull requests` 只读

令牌到期后周报会停止发送并在卡片上标注 403，不会静默失败。建议设置一年有效期并在日历上留一条续期提醒。

#### 第三步：验证

1. 进入 `NingXia-XinQiCyberClub/.github` 仓库的 Actions 页面
2. 左侧选「飞书播报」→ 右侧「Run workflow」→ 分支选 `main` → 运行
3. 约 30 秒后主群应收到一张青色卡片，标题「播报测试」

收到即说明 Webhook、签名与 Secrets 全部正确。

若 Actions 显示成功但群里没消息，八成是 Secret 的 `Repository access` 没选全部仓库，或 webhook 复制时带了空格。若 Actions 报 `发送被拒绝`，说明签名密钥不匹配，回飞书重置密钥后更新 Secret。

之后随便推一个提交、开一个变更请求，主群就会自然收到播报。

**第四步：在需要播报的仓库放置触发文件**

从本仓库 `workflow-templates/feishu-events.yml` 复制到目标仓库的 `.github/workflows/` 目录，或在该仓库 Actions 页面的「New workflow」中直接选用「飞书播报」模板。

`guide` 与站点仓库已放置该文件。

#### 7.3B 方案 B：企业自建应用机器人

群设置里确实找不到「自定义机器人」时用这条。区别在于：方案 A 是「群上的 webhook」，方案 B 是「企业自建应用」，后者需要在飞书开放平台建应用、加机器人能力、发版，由企业管理员审批，但审批一次之后可以给多个群发消息，也不必每个群单独配。

**1. 建自建应用**

浏览器打开 <https://open.feishu.cn/app> → 「创建企业自建应用」→ 填名称（如「鑫启播报」）与描述 → 创建。

**2. 加机器人能力**

进入应用 → 左侧「添加应用能力」→ 找到「机器人」→ 添加。

**3. 申请权限**

左侧「权限管理」→ 搜索并开通：

| 权限 | 用途 |
| :-- | :-- |
| `im:message:send_as_bot`（以应用的身份发消息） | 向群发消息，用这一个即可 |
| `im:chat:readonly`（获取群组信息） | 可选，用于查 chat_id 核对 |

**4. 记下凭证**

左侧「凭证与基础信息」→ 复制 `App ID`（形如 `cli_a1b2c3d4...`）与 `App Secret`。

**5. 发布应用**

左侧「版本管理与发布」→ 「创建版本」→ 填版本号与说明 → 「保存」→ 「申请发布」。企业自建应用的审核通常由你们的飞书管理员点一下通过；发布后机器人才能被加进群。

**6. 把机器人加进群**

回到飞书客户端，进入目标群 →「设置」→「群机器人」→「添加机器人」→ 这次列表中会出现你刚建的「鑫启播报」，添加即可。

**7. 取群 chat_id**

自建应用发消息要指定 `chat_id`（形如 `oc_xxxxxxxx`），不是群名。取法二选一：

- 群设置 → 群机器人 → 点你添加的机器人 → 页面里通常显示所在群的 chat_id
- 或用 API 查：拿到 `tenant_access_token` 后调 `GET /open-apis/im/v1/chats`，返回里 `chat_id` 对应 `name`

**8. 写入 Secrets**

与方案 A 同一个位置，把名称换成下面这些：

| Name | Secret |
| :-- | :-- |
| `FEISHU_APP_ID` | 第 4 步的 App ID |
| `FEISHU_APP_SECRET` | 第 4 步的 App Secret |
| `FEISHU_CHAT_ID` | 第 7 步的主群 chat_id |
| `FEISHU_CHAT_ID_RECRUIT` | 招新群 chat_id，可后补 |

脚本的投递顺序是：**配了 `FEISHU_WEBHOOK` 就用 webhook，否则看 `FEISHU_APP_ID` + `FEISHU_APP_SECRET` + `FEISHU_CHAT_ID`**。两套都配时以 webhook 为准，因此将来群设置里出现了自定义机器人，随时可以切回去，不用改代码。

> 注意：方案 B 无法「托管」在任何第三方服务器上。应用凭证属于你们的企业，App Secret 等同于机器人的钥匙，只能存放于 GitHub Secrets。任何声称能替你托管并代持密钥的做法，都等于把发消息的权限交给了外部。

在配置以下任一项之前，先做一件零成本的事：**把入会指引写成群公告并置顶**。新人进群第一眼就能看到，不需要任何机器人、任何凭据。公告文案见 7.3C。

### 7.3C 新成员引导：默认用群公告

新同学进飞书群后，往往不知道还要去 GitHub 填工单，结果一直看不到仓库。最省事的做法是在招新群写一条群公告，勾上「在群组置顶显示」——公告会一直挂在群顶部，后续入群的成员也能看到。

**操作**：招新群 → 右上角「···」→「设置」→「群管理」→「群公告」→ 编辑以下文案 → 勾选「在群组置顶显示」→ 发布。

```
欢迎加入宁夏大学鑫启网安俱乐部。

进群后请完成三件事，才能查看组织仓库与参与赛事报名：

一、填写加入工单
https://github.com/NingXia-XinQiCyberClub/.github/issues/new?template=join.yml
需填写真实姓名、11 位学号，并勾选流程清单与承诺事项。

二、接受组织邀请
工单审核通过后，GitHub 会向你的注册邮箱发送组织邀请，请在 7 天内点击接受。

三、完成入门任务
按教程第 0 章操作：https://github.com/NingXia-XinQiCyberClub/guide

群昵称统一改为「姓名-年级」，格式如「张三-大二」。
技术问题请提到 GitHub Discussions，不要在群里直接问，讨论结论同样归档到 Discussions。
```

公告的局限也很明确：它是**静态**的，不会 @ 到具体某个人，也不会因为谁没看完而提醒。但它有三个好处——不依赖任何凭证、不会漏、不会因为权限或接口变更而失效。

**如果确实需要自动点名提醒**，`welcome-reminder.yml` 提供了可选实现，默认关闭。启用前提是走 7.3B 的企业自建应用，并额外开通 `im:chat.members:read`（获取群成员信息）权限；加完权限必须重新创建版本并发布，否则调用返回 403。

**工作原理**：

```
每 10 分钟 ──▶ 拉取招新群成员名单
                    │
                    ▼
        与 feishu-state 分支上的快照对比
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   有新增成员                 无变动
        │                       │
        ▼                       ▼
 @ 他们填工单              更新快照后退出
        │
        ▼
   更新快照（发送失败则不更新，下次重试）
```

快照存在 `feishu-state` 分支的 `feishu-members.json`，不写 main，也不影响页面发布。分支由工作流首次运行时自动创建。

**几个刻意设计**：

1. **首次运行不发提醒**。只把现有成员记下来，避免上线瞬间 @ 全群
2. **一次最多 @ 20 人**。超过就判定为异常（例如权限变更导致看到别的群），只更新快照不发提醒，并让工作流标红
3. **发送失败不更新快照**。宁可下次重复检查，也不漏掉一个新人
4. **退出的人静默移除**，不发任何消息
5. **只在招新群提醒**。优先用 `FEISHU_CHAT_ID_RECRUIT`，未配置时用 `FEISHU_CHAT_ID`
6. **默认关闭**。仅在仓库变量 `WELCOME_REMINDER` 显式设为 `on` 时才运行，未设置时整个工作流不触发，不产生任何 Actions 用量

**开关**：

```bash
gh variable set WELCOME_REMINDER --body on  --repo NingXia-XinQiCyberClub/.github   # 启用（默认关闭）
gh variable set WELCOME_REMINDER --body off --repo NingXia-XinQiCyberClub/.github   # 停用
```

未配置应用凭证时，工作流会打印「未配置…跳过新成员提醒」并正常退出，不影响其他播报。

**成本**：每 10 分钟一次，一天 144 次运行。GitHub 公开仓库的 Actions 免费额度不设上限，但如果组织开始按分钟计费，建议改成 `*/30 * * * *` 或每小时一次——新人等半小时才收到提醒，实际并不算慢。

**结论**：先用群公告。群公告能覆盖八成场景，且不引入任何凭据；只有当公告确实被忽略、需要点名时，再开这条工作流。


### 7.4 周报

`weekly-summary.yml` 每周一 08:00（北京时间）运行，统计最近 7 天的提交、变更请求与工单，并列出待评审请求与未分类工单。

| 统计项 | 口径 |
| :-- | :-- |
| 提交 | 组织内公开仓库默认分支的提交数，按作者归类 |
| 变更请求 | 新开 / 合入 / 关闭未合入 / 当前待处理 |
| 工单 | 新开 / 关闭 / 当前待处理 |
| 待评审 | 已开启、非草稿、无他人批准 |
| 未分类 | 已开启且无标签 |

开关与参数：

```bash
gh variable set WEEKLY_SUMMARY --body off --repo NingXia-XinQiCyberClub/.github   # 停发周报
gh variable set WEEKLY_DAYS --body 14 --repo NingXia-XinQiCyberClub/.github      # 改为双周
```

一周内确实没有任何动静时只发一张灰色短卡片；若因令牌失效导致统计失败，不会误报为「无活动」，而是在卡片上注明统计提示。

注意：GitHub 在公开仓库连续 60 天无提交时会自动停用 `schedule` 触发。若周报忽然中断，先到 Actions 页面确认「每周汇总」是否被标记为 disabled 并重新启用。

### 7.5 本地验证

四个测试脚本均不联网，也不读取真实凭据：

```bash
cd scripts/feishu
python _selftest.py           # 事件卡片渲染、转义、合入痕迹过滤、新成员公告
python _selftest_summary.py   # 周报渲染、空活动与统计失败的区分
python _selftest_send.py      # 签名算法、地址白名单、错误码处理
python _selftest_welcome.py   # 新成员对比、首次运行、上限保护、快照分支
```

渲染真实事件后如仍需确认，可设置 `DRY_RUN=1` 让脚本只打印 JSON 而不发送。

### 7.6 安全约束

1. Webhook 地址与签名密钥只存于 Actions Secrets，不写入仓库文件、站点页面与教程
2. `notify.py` 仅向 `open.feishu.cn` 与 `open.larksuite.com` 的 `/open-apis/bot/v2/hook/` 发送，误配地址会直接拒绝而非把消息发往他处
3. 提交标题、工单标题等外部输入在写入 `lark_md` 前统一转义，链接只能由脚本自身生成，防止标题中的 Markdown 语法伪造按钮或外链
4. 新成员公告中的学号做掩码处理，只保留前 4 位与后 3 位；姓名、年级、专业取自申请人自填的工单正文，未经核实
5. 播报内容不含代码正文、凭据与赛事信息，仅含标题、作者、分支与链接
6. 新成员提醒只读群成员名单（`im:chat.members:read`），不读取聊天内容；快照仅存 open_id 与昵称，存于 `feishu-state` 分支

