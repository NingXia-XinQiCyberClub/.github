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
