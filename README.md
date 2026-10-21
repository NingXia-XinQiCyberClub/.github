# .github

这是 **鑫启网安社团** 的组织级配置仓库。

> 它本身不含业务代码，但决定了组织主页显示什么、以及所有仓库默认的协作规范。

---

## 目录说明

| 路径 | 作用 |
| :-- | :-- |
| `profile/README.md` | **组织主页** 展示的内容（`github.com/NingXia-XinQiCyberClub` 的 Overview） |
| `profile/logo.svg` | 组织图标（**占位图，需替换为官方 PNG**） |
| `CONTRIBUTING.md` | 全组织默认贡献指南 |
| `CODE_OF_CONDUCT.md` | 行为准则 |
| `SECURITY.md` | 安全漏洞上报政策 |
| `SUPPORT.md` | 求助指南 |
| `PULL_REQUEST_TEMPLATE.md` | 全组织默认 PR 模板 |
| `ISSUE_TEMPLATE/` | 全组织默认 issue 表单 |
| `ISSUE_TEMPLATE/onboarding.yml` | 新人入职清单 |
| `ISSUE_TEMPLATE/config.yml` | issue 入口引导（指向 Discussions） |
| `.github/workflows/welcome.yml` | 新人首次交互自动欢迎 |

---

## 生效规则

1. 这些文件对**组织内所有仓库**生效，**前提是该仓库自己没有同名文件**。
   仓库里自带的 `CONTRIBUTING.md` 优先级更高。
2. `profile/README.md` 只在**本仓库是 public** 时才会展示在组织公开主页。
3. 如果想让已登录成员看到额外内容（内部信息），需另建**私有**仓库 `.github-private`，
   同样放 `profile/README.md`。

---

## 怎么改

```bash
git clone https://github.com/NingXia-XinQiCyberClub/.github.git
cd .github
# 改文件
git switch -c docs/update-guide
git add .
git commit -m "docs: 更新新人入职清单"
git push -u origin docs/update-guide
```

然后去 GitHub 开 PR。

---

## 待办

- [ ] 把 `profile/logo.svg` 换成官方 logo（PNG，建议 500×500 以上）
- [ ] 建 `guide` 仓库，写系统化教程
- [ ] 开启 Discussions 并建分类：General / Q&A / Ideas / Show and tell
- [ ] 给入门任务打 `good first issue` 标签
- [ ] 设置组织基础权限为 Read
- [ ] 强制全员开启 2FA
