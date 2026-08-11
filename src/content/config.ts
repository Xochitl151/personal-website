import { defineCollection, z } from 'astro:content';

const metricSchema = z.object({
  label: z.string(),
  value: z.string(),
  hint: z.string().optional(),
});

const findingSchema = z.object({
  title: z.string(),
  detail: z.string(),
  action: z.string().optional(),
});

const chartSchema = z.object({
  src: z.string(),
  alt: z.string(),
  /** 图库导航短标题 */
  label: z.string().optional(),
  /** 这图说明什么 */
  proves: z.string(),
  /** 不说明什么 / 局限 */
  limits: z.string().optional(),
  /** 业务里下一步怎么验证 */
  next: z.string().optional(),
});

const lensSchema = z.object({
  id: z.enum(['data', 'ai']),
  label: z.string(),
  bullets: z.array(z.string()).min(1).max(4),
});

const demoSchema = z.enum([
  'funnel',
  'product-picker',
  'bidding-insights',
  'user-insights',
  'chart-gallery',
  'feature-explorer',
  'ai-workflow',
]);

const projects = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    /** 首屏结论条：一句话 + 尽量带结果导向 */
    takeaway: z.string(),
    /** 关键指标（可后补真实数字） */
    metrics: z.array(metricSchema).default([]),
    /** 我的角色一句话 */
    role: z.string(),
    date: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    kind: z.enum(['intern', 'independent', 'contest', 'side']),
    featured: z.boolean().default(false),
    order: z.number().default(0),
    /** 页脚说明，如公开数据来源 */
    disclaimer: z.string().optional(),
    /** 分析链路（静态步骤条） */
    pipeline: z.array(z.string()).default([]),
    /** 核心发现卡片 */
    findings: z.array(findingSchema).default([]),
    /** 页内交互 Demo */
    demos: z.array(demoSchema).default([]),
    /** 图库 Tab（泰迪杯等） */
    charts: z.array(chartSchema).default([]),
    /** 获奖证明图（有则图库显示第二 Tab） */
    awardImage: z.string().optional(),
    awardCaption: z.string().optional(),
    /** 阅读视角：数据分析 / 产品与交付 */
    lenses: z.array(lensSchema).default([]),
    /** 外链证据（Tableau 等） */
    externalLinks: z
      .array(z.object({ label: z.string(), href: z.string() }))
      .default([]),
  }),
});

export const collections = { projects };
