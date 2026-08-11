/** 站点文案：改这里即可，不必动布局代码 */
export const site = {
  name: '徐华凤',
  title: '徐华凤 · 作品集',
  description:
    '数据分析与 AI 产品应用作品集：广电用户套餐分析、招投标采集建站与泰迪杯特医案例。',
  /** 链接预览默认图（Open Graph / Twitter） */
  ogImage: '/images/og-default.png',
  tagline: '把业务数据说清楚，也能把检索站点从采集做到可演示。',
  taglineSupport: '信息与计算科学 · 2026 应届 · 数据分析 / AI 产品应用 · 广东智慧广电实习',
  contactNote: '电话、微信、邮箱见简历 PDF，本站不公开展示。',
  resumeUseNotice: '本简历仅供招聘沟通使用，请勿转载或用于非招聘目的。',
  resumeDownloadName: '徐华凤-简历.pdf',
  skillsFootnote: '另具备基础平面与剪辑能力，用于保证交付观感。',
} as const;

/** 按方向浏览作品 */
export const pitches = {
  data: {
    path: '/pitch/data',
    label: '数据分析',
    title: '数据分析方向',
    summary: '侧重指标口径、异常发现与可验证建议；同场景的产品交付可作为业务背景。',
  },
  ai: {
    path: '/pitch/ai',
    label: 'AI 产品与应用',
    title: 'AI 产品与应用方向',
    summary: '侧重需求落地、人机分工与验收交付；分析案例用于说明能把业务问题说清楚。',
  },
} as const;
