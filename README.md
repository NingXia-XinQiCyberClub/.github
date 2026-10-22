# .github

本仓库为 **鑫启网安社团** 的组织级配置仓库，不含业务代码，用于统一组织主页内容与组织内各仓库的协作规范。

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
| `.github/ISSUE_TEMPLATE/onboarding.yml` | 新成员入职登记表单 |
| `.github/ISSUE_TEMPLATE/config.yml` | 工单入口配置，将提问引导至 Discussions |
| `.github/workflows/welcome.yml` | 首次交互自动应答工作流 |

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

### 5.3 入门任务

`guide` 仓库中标有 `good first issue` 的工单构成新成员入门任务集，详见该仓库 README 的「入门任务」一节。任务完成后由维护者评审合并，作为首次变更请求的实践。
