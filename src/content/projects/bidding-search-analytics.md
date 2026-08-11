---
title: 招投标关键词分析练习（个人）
summary: 个人练习：按招投标检索场景构造关键词与渠道表，练习口径、CTR 对比与 Tableau 看板；与实习用户套餐分析、招投标建站项目均分开。
takeaway: 从关键词与渠道行为中找出「高搜低点击」等问题，把发现写成可验证的优化建议。
role: 独立完成选题、口径定义、练习数据分析与 Tableau Public 发布。
date: 2025-10-01
tags: [个人练习, SQL, Python, Tableau]
kind: independent
featured: true
order: 4
metrics:
  - label: 性质
    value: 个人练习
    hint: 非实习 3800+ 用户表
  - label: 练习表
    value: 5400+ 行
    hint: 关键词 × 日期 × 渠道
  - label: 交付
    value: 在线看板
    hint: Tableau Public
pipeline:
  - 口径定义
  - 练习数据
  - Tableau 看板
  - 结论与建议
findings:
  - title: 高搜低点击词应优先优化
    detail: 练习数据上，「开标记录」「电子招投标」等词搜索量不低，但 CTR 约 51%～53%，低于热门词均值。
    action: 优化结果摘要与排序，下一周期回看 CTR 是否回升。
  - title: 付费渠道意图匹配待核对
    detail: 「付费推广」带来访问量，但停留与点击弱于直接访问、站内来源。
    action: 核对推广落地页与搜索意图是否一致。
demos:
  - bidding-insights
  - chart-gallery
charts:
  - src: /images/projects/bidding-search/tableau-dashboard-full.png
    label: 仪表板
    alt: Tableau 仪表板全屏（练习数据）
    proves: 一屏呈现 KPI、Top 词、趋势与渠道对比，适合周度复盘沟通。
    limits: Public 看板为练习/模拟数据，不是实习内网原始日志。
    next: 业务侧用脱敏汇总按同一指标复算；改版效果用前后对比或 A/B 验证。
  - src: /images/projects/bidding-search/tableau-keyword-scatter.png
    label: 关键词散点
    alt: 关键词搜索量与点击率散点（练习数据）
    proves: 可标出「量不低但 CTR 偏弱」的词，进入优化清单。
    limits: 观察性相关，不能证明改摘要一定提升 CTR。
    next: 挑选若干词改结果摘要/排序，下一周期回看 CTR 与停留。
lenses:
  - id: data
    label: 数据分析
    bullets:
      - 先对齐分子分母（搜索、点击、停留），再谈发现。
      - 输出结构：发现 → 可能原因 → 建议验证；不做因果断言。
      - 与实习「用户套餐分析」不是同一份数据。
  - id: ai
    label: 产品与交付
    bullets:
      - 用于练习「上线检索产品后如何看数据」的方法。
      - 招投标建站见实习工程项目页；用户分析见套餐分析页。
externalLinks:
  - label: Tableau Public 看板
    href: https://public.tableau.com/app/profile/.80835515/viz/_17808428000990/1?publish=yes
disclaimer: 个人练习。与实习 3800+ 用户套餐数据无关；与招投标站点是否正式运营无关。仅作关键词分析与 Tableau 方法演示。
---

## 背景

这是 **个人练习**：按招投标检索场景构造关键词 × 渠道表，练习指标口径与看板。  
实习主分析是 [广电用户套餐与开通分析](/projects/operator-user-analytics)；招投标 **建站** 见 [招投标信息采集与搜索站点](/projects/bidding-search-engine)。

## 我做了什么

1. **对齐指标**：搜索次数、关键词、点击率等。  
2. **练习数据**：按场景字段准备练习表。  
3. **分析与交付**：关键词频次与 CTR、渠道对比；Tableau 看板。

## 证据

上方可切换渠道查看关键词 Top；完整看板见 Tableau Public。

## 局限

练习分布不等于任何公司真实业务；不能做因果推断。
