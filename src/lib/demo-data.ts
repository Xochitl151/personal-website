import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();

export type FunnelRow = {
  channel: string;
  step: string;
  sessions: number;
  pct: number;
};

export type BiddingKeyword = {
  keyword: string;
  search: number;
  clicks: number;
  ctr: number;
};

const FUNNEL_STEPS = ['总会话', '浏览商品页', '深度浏览', '有购买意向信号', '成交'] as const;

/** UCI 渠道编号 → 业务可读名（练习数据口径） */
const CHANNEL_LABELS: Record<string, string> = {
  渠道类型1: 'Referral 引荐',
  渠道类型2: 'Direct 直接访问',
  渠道类型3: 'Social 社交',
  渠道类型4: 'Email 邮件',
  渠道类型13: 'Paid 付费推广',
  渠道类型20: 'Other 其他',
};

export function getFunnelChannels(): { id: string; label: string }[] {
  const raw = fs.readFileSync(path.join(root, 'data/02-电商漏斗/01-漏斗汇总_按渠道.csv'), 'utf8');
  const channels = [...new Set(raw.trim().split('\n').slice(1).map((line) => line.split(',')[0]))];
  const preferred = ['渠道类型2', '渠道类型13', '渠道类型1', '渠道类型3', '渠道类型4', '渠道类型20'];
  const ordered = [
    ...preferred.filter((c) => channels.includes(c)),
    ...channels.filter((c) => !preferred.includes(c)),
  ].slice(0, 6);

  return ordered.map((id) => ({
    id,
    label: CHANNEL_LABELS[id] ?? id,
  }));
}

export function getFunnelByChannel(channelId: string): FunnelRow[] {
  const raw = fs.readFileSync(path.join(root, 'data/02-电商漏斗/01-漏斗汇总_按渠道.csv'), 'utf8');
  const rows = raw
    .trim()
    .split('\n')
    .slice(1)
    .map((line) => {
      const [channel, step, sessions, pct] = line.split(',');
      return {
        channel,
        step,
        sessions: Number(sessions),
        pct: Number(pct),
      };
    })
    .filter((row) => row.channel === channelId && FUNNEL_STEPS.includes(row.step as (typeof FUNNEL_STEPS)[number]));

  return FUNNEL_STEPS.map((step) => rows.find((r) => r.step === step)).filter(Boolean) as FunnelRow[];
}

export function getBiddingChannels(): string[] {
  const raw = fs.readFileSync(path.join(root, 'data/01-招投标搜索/02-实习级练习.csv'), 'utf8');
  return [...new Set(raw.trim().split('\n').slice(1).map((line) => line.split(',')[2]))].sort();
}

export function getBiddingKeywords(channel?: string): BiddingKeyword[] {
  const raw = fs.readFileSync(path.join(root, 'data/01-招投标搜索/02-实习级练习.csv'), 'utf8');
  const agg = new Map<string, { search: number; clicks: number }>();

  raw
    .trim()
    .split('\n')
    .slice(1)
    .forEach((line) => {
      const parts = line.split(',');
      const rowChannel = parts[2];
      if (channel && channel !== '全部' && rowChannel !== channel) return;

      const keyword = parts[1];
      const search = Number(parts[6]);
      const clicks = Number(parts[7]);
      const prev = agg.get(keyword) ?? { search: 0, clicks: 0 };
      agg.set(keyword, {
        search: prev.search + search,
        clicks: prev.clicks + clicks,
      });
    });

  return [...agg.entries()]
    .map(([keyword, { search, clicks }]) => ({
      keyword,
      search,
      clicks,
      ctr: search ? Math.round((clicks / search) * 1000) / 10 : 0,
    }))
    .sort((a, b) => b.search - a.search)
    .slice(0, 10);
}

export type UserPackageRow = {
  packageType: string;
  opened: number;
  pending: number;
  stopped: number;
  total: number;
  openRate: number;
};

export type UserServiceRow = {
  serviceType: string;
  users: number;
  active: number;
  activeRate: number;
};

function readCsvLines(relPath: string): string[] {
  const raw = fs.readFileSync(path.join(root, relPath), 'utf8').replace(/^\uFEFF/, '');
  return raw.trim().split(/\r?\n/).slice(1);
}

export function getUserPackageSummary(): UserPackageRow[] {
  const map = new Map<string, { opened: number; pending: number; stopped: number }>();

  readCsvLines('data/04-用户套餐分析/02-套餐开通汇总.csv').forEach((line) => {
    const [packageType, status, usersRaw] = line.split(',');
    const users = Number(usersRaw);
    const prev = map.get(packageType) ?? { opened: 0, pending: 0, stopped: 0 };
    // Telco 公开集：在网 / 已流失（映射到 opened / stopped；pending 不用）
    if (status === '在网' || status === '已开通') prev.opened = users;
    else if (status === '待开通') prev.pending = users;
    else if (status === '已流失' || status === '已停用') prev.stopped = users;
    map.set(packageType, prev);
  });

  return [...map.entries()]
    .map(([packageType, s]) => {
      const total = s.opened + s.pending + s.stopped;
      return {
        packageType,
        ...s,
        total,
        openRate: total ? Math.round((s.opened / total) * 1000) / 10 : 0,
      };
    })
    .sort((a, b) => b.total - a.total);
}

export function getUserServiceSummary(): UserServiceRow[] {
  return readCsvLines('data/04-用户套餐分析/03-业务类型分布汇总.csv')
    .map((line) => {
      const [serviceType, usersRaw, activeRaw] = line.split(',');
      const users = Number(usersRaw);
      const active = Number(activeRaw);
      return {
        serviceType,
        users,
        active,
        activeRate: users ? Math.round((active / users) * 1000) / 10 : 0,
      };
    })
    .sort((a, b) => b.users - a.users);
}

/** @deprecated 使用 getUserServiceSummary */
export function getUserRegionSummary() {
  return getUserServiceSummary();
}

export function getFunnelInsight(channelId: string): string {
  const rows = getFunnelByChannel(channelId);
  if (rows.length < 2) return '选择渠道后可查看各步转化率。';

  const rates = rows.slice(1).map((row, i) => ({
    from: rows[i].step,
    to: row.step,
    rate: rows[i].sessions ? Math.round((row.sessions / rows[i].sessions) * 1000) / 10 : 0,
  }));

  const weakest = rates.reduce((min, r) => (r.rate < min.rate ? r : min), rates[0]);
  return `「${weakest.from} → ${weakest.to}」转化率最低（${weakest.rate}%），优先排查该环节体验或意图匹配。`;
}
