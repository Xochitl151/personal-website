export const projectKinds = {
  intern: { label: '实习交付', tagClass: 'tag--intern' },
  independent: { label: '个人练习', tagClass: 'tag--independent' },
  contest: { label: '竞赛作品', tagClass: 'tag--contest' },
  side: { label: '副线', tagClass: 'tag--side' },
} as const;

export type ProjectKind = keyof typeof projectKinds;

/** 卡片/详情里优先强调的技能与工具；其余视为场景说明 */
const skillTagSet = new Set([
  'SQL',
  'Python',
  'Tableau',
  'Pandas',
  'pdfplumber',
  '可视化',
  'AI 辅助开发',
  '搜索产品',
]);

/** 拆成技能 / 说明；卡片通常只展示技能 */
export function splitProjectTags(tags: string[]) {
  const skills: string[] = [];
  const meta: string[] = [];
  for (const tag of tags) {
    if (skillTagSet.has(tag)) skills.push(tag);
    else meta.push(tag);
  }
  return { skills, meta };
}
