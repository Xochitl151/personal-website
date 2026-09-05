import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();

export type BiddingKeyword = {
  keyword: string;
  search: number;
  clicks: number;
  ctr: number;
};

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
