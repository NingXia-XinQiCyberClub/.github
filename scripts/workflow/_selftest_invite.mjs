#!/usr/bin/env node
// invite-member.yml 的离线回归测试：不联网、不需要凭据。
//
// 覆盖 2026-10-27 漏发事故的关键分支：
//   - 成员状态 active / pending / 不存在
//   - 邀请成功后的复核
//   - 422「User must have a valid role」不得被当成「已有邀请」
//
// 用法（仓库根目录）：node scripts/workflow/_selftest_invite.mjs

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const workflowPath = path.resolve(here, '../../.github/workflows/invite-member.yml');
const source = fs.readFileSync(workflowPath, 'utf8');

// 从 YAML 中取出 github-script 的 script 块（按缩进判断块边界，不引入 YAML 依赖）
function extractScript(yaml) {
  const lines = yaml.split(/\r?\n/);
  const start = lines.findIndex((l) => /^\s*script:\s*\|\s*$/.test(l));
  if (start < 0) throw new Error('未找到 script: | 块');
  const indent = lines[start].match(/^\s*/)[0].length;
  const body = [];
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === '') {
      body.push('');
      continue;
    }
    if (line.match(/^\s*/)[0].length <= indent) break;
    body.push(line.slice(indent + 2)); // script 内容比 script: 多缩进两格
  }
  return body.join('\n');
}

process.env.ORG_INVITE_TOKEN = 'selftest-token';

const script = extractScript(source);

const body = [
  '### 中文姓名', '', '张三', '',
  '### 英文名', '', 'Zhang San', '',
  '### 学号', '', '12024242193', '',
  '### 年级', '', '大二', '',
  '### 学院与专业', '', '信息工程学院 网络工程', '',
  '### 研究兴趣', '', 'Web 安全', '',
  '### 流程清单', '',
  '- [x] 步骤 1：安装并配置 Git',
  '- [x] 步骤 2：配置认证方式',
  '- [x] 步骤 3：阅读贡献指南',
  '- [x] 步骤 4：克隆仓库',
  '- [x] 步骤 5：完成首次变更请求',
  '- [x] 步骤 6：在 Discussions 自我介绍',
  '- [ ] 步骤 7：加入飞书群组',
  '',
  '### 承诺', '',
  '- [x] 同意行为准则',
  '- [x] 仅对授权环境测试',
  '- [x] 信息真实有效',
].join('\n');

const ok = (data, status = 200) => ({
  status,
  ok: status < 300,
  text: async () => JSON.stringify(data),
});

// membershipSeq：每次查询成员状态依次返回的 state（不足则重复最后一项）
function run({ membershipSeq, put }) {
  const log = { comments: [], labels: [], closed: false, failed: null, status: null, puts: [] };
  let calls = 0;

  globalThis.fetch = async (url, init = {}) => {
    const p = new URL(url).pathname;
    const method = (init.method || 'GET').toUpperCase();

    if (method === 'PUT' && p.includes('/memberships/')) {
      log.puts.push(JSON.parse(init.body));
      return ok(put.body || { message: put.message }, put.status);
    }
    if (p.endsWith('/memberships/tester')) {
      const step = membershipSeq[Math.min(calls++, membershipSeq.length - 1)];
      if (step === 'active') return ok({ state: 'active', role: 'member' });
      if (step === 'pending') return ok({ state: 'pending', role: 'member' });
      return ok({ message: 'Not Found' }, 404);
    }
    if (/^\/orgs\/[^/]+$/.test(p)) return ok({ login: 'ORG' });
    return ok({ message: `unexpected ${p}` }, 500);
  };

  globalThis.context = {
    repo: { owner: 'ORG', repo: 'repo' },
    payload: { issue: { number: 1, body, user: { login: 'tester', type: 'User' } } },
  };

  globalThis.core = {
    info: () => {},
    warning: () => {},
    setOutput: (k, v) => { if (k === 'status') log.status = v; },
    setFailed: (m) => { log.failed = m; },
  };

  globalThis.github = {
    paginate: async (fn, args) => (await fn(args)).data ?? [],
    rest: {
      issues: {
        listComments: async () => ({ data: [] }),
        createComment: async ({ body: b }) => { log.comments.push(b); },
        updateComment: async ({ body: b }) => { log.comments.push(b); },
        addLabels: async ({ labels }) => { log.labels.push(...labels); },
        update: async ({ state }) => { if (state === 'closed') log.closed = true; },
      },
    },
  };

  vm.runInThisContext(`(async () => {${script}\n})()`);
  return new Promise((resolve) => setTimeout(() => resolve(log), 150));
}

const cases = [
  {
    name: '已是成员（active）只说明，不关单',
    opts: { membershipSeq: ['active'], put: { status: 500 } },
    check: (l) => l.status === 'already_member' && /已是组织成员/.test(l.comments[0]) && !l.closed,
  },
  {
    name: '已有待接受邀请（pending）按「邀请已存在」处理',
    opts: { membershipSeq: ['pending'], put: { status: 500 } },
    check: (l) => l.status === 'pending' && /邀请已存在/.test(l.comments[0]) && l.closed,
  },
  {
    name: '正常邀请：role 传 member，成功后复核并关单',
    opts: { membershipSeq: ['none', 'pending'], put: { status: 201, body: { state: 'pending' } } },
    check: (l) => l.status === 'invited'
      && /已发出组织邀请/.test(l.comments[0])
      && l.closed
      && JSON.stringify(l.puts[0]) === '{"role":"member"}',
  },
  {
    name: '422「User must have a valid role」按失败上报，不得说成已有邀请',
    opts: {
      membershipSeq: ['none', 'none'],
      put: { status: 422, body: { message: 'User must have a valid role.' } },
    },
    check: (l) => !l.comments.some((c) => /邀请已存在/.test(c))
      && /自动邀请失败/.test(l.comments[0])
      && /User must have a valid role/.test(l.comments[0])
      && l.failed
      && !l.closed,
  },
  {
    name: '接口报错但状态确为 pending 时仍按已有邀请处理',
    opts: { membershipSeq: ['none', 'pending'], put: { status: 422, body: { message: 'x' } } },
    check: (l) => /邀请已存在/.test(l.comments[0]) && l.closed && !l.failed,
  },
  {
    name: '接口成功但复核无状态：报失败，不关单',
    opts: { membershipSeq: ['none', 'none'], put: { status: 201, body: { state: 'pending' } } },
    check: (l) => /邀请复核未通过/.test(l.comments[0]) && l.failed && !l.closed,
  },
];

let failed = 0;
for (const c of cases) {
  const log = await run(c.opts);
  const pass = c.check(log);
  if (!pass) failed++;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${c.name}`);
  if (!pass) console.log(JSON.stringify(log, null, 2));
}

console.log(failed === 0 ? '\n全部通过。' : `\n${failed} 项未通过。`);
process.exit(failed === 0 ? 0 : 1);
