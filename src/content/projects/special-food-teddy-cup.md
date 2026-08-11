---
title: 特医食品数据分析（泰迪杯）
summary: 泰迪杯 B 题：用 Python 批量解析国食注字 PDF，抽取营养成分与适用人群，完成统计可视化与选品筛选。
takeaway: 把特医食品 PDF 说明书变成结构化数据，并从登记趋势、人群分布、成分等维度支撑选品。
role: 数据分析：PDF 批量抽取、字段清洗、适用人群归类、可视化与产品筛选逻辑。
date: 2024-05-01
tags: [泰迪杯, Python, pdfplumber, 可视化, Pandas]
kind: contest
featured: true
order: 3
metrics:
  - label: 赛题
    value: 泰迪杯 B 题
    hint: 特医食品
  - label: 数据
    value: 182 份 PDF
    hint: 国食注字说明书
  - label: 成绩
    value: 二等奖
    hint: 数据分析技能赛
pipeline:
  - PDF 抽表
  - 人群归类
  - 可视化
  - 选品筛选
findings:
  - title: PDF 版式差异是主要难点
    detail: 部分文件缺表头、列数不齐；用日志与跳过规则保证批量跑通，并对结果抽检。
    action: 对异常样例单独复核，避免静默错误进入下游表。
  - title: 婴配类占登记主体
    detail: 旭日图显示特医婴配食品在样本中占比最高，1 岁以上品类结构更分散。
    action: 选品时先按人群类别收窄，再按症状关键词过滤。
demos:
  - chart-gallery
  - product-picker
awardImage: /images/projects/special-food/teddy-cup-award-b.jpg
awardCaption: 第七届泰迪杯数据挖掘挑战赛 B 题 · 特医食品方向 · 二等奖
charts:
  - src: /images/projects/special-food/2.1.png
    label: 获批量趋势
    alt: 不同登记年份与产品来源的获批量趋势
    proves: 2018 年后获批量明显上升，进口与国产来源并存。
    limits: 仅赛题样本时间窗，不代表全市场增速。
    next: 业务选品时应用最新注册库按同一口径复算趋势。
  - src: /images/projects/special-food/2.2.png
    label: 人群分布
    alt: 产品来源与适用人群类别分布（旭日图）
    proves: 婴配类在结构中占主导，1 岁以上品类分布更分散。
    limits: 人群标签依赖 PDF 文本归类规则，边界样本可能被粗分。
    next: 抽检归类错误率；必要时用更细标签二次校验。
  - src: /images/projects/special-food/2.3.png
    label: 类别获批
    alt: 不同产品类别的获批量
    proves: 氨基酸、水解、全营养等类别获批量差异明显。
    limits: 柱高是样本内计数，不能直接当作市场份额。
    next: 结合渠道可得性，把「登记多」转成可落地的候选清单。
  - src: /images/projects/special-food/2.4.png
    label: 成分分布
    alt: 脂肪与蛋白质含量频数分布
    proves: 成分分布呈右偏，极端值需单独标注口径。
    limits: 未做配方合规判定，只描述分布形态。
    next: 对极端值回溯原 PDF；选品时设定成分区间后再人工复核。
  - src: /images/projects/special-food/2.5.png
    label: 适用词云
    alt: 适用人群词云
    proves: 「过敏」「消化吸收」「营养补充」等为高频适用场景词。
    limits: 词云偏展示，频次受表述习惯影响，不是严谨统计检验。
    next: 用关键词规则做筛选（见页内选品），并抽样核对说明书原文。
lenses:
  - id: data
    label: 数据分析
    bullets:
      - 核心：非结构化 PDF → 结构化表，含异常日志与抽检。
      - 交付：趋势 / 结构 / 成分分布 + 可筛产品，而不只是出图。
      - 边界：赛题样本不等于全市场；结论带局限与验证方式。
  - id: ai
    label: 产品与交付
    bullets:
      - 闭环：抽取 → 清洗 → 可视化 → 选品筛选，页内可演示。
      - 人机分工：脚本提速批量处理，版式异常靠规则与人工抽检。
      - 价值：从说明书文本到「按人群/症状给出候选」的决策辅助。
disclaimer: 泰迪杯比赛项目；PDF 为赛题/公开注册信息材料，与实习公司业务无关。
---

## 背景

特殊医学用途配方食品的注册信息分散在大量 **国食注字** 系列 PDF 说明书中，版式不统一。第七届泰迪杯 B 题要求：将 PDF 转为结构化表 → 统计可视化 → 按人群/症状筛选产品。

## 我做了什么

1. **抽取清洗**：用 pdfplumber 抽取营养成分表与适用人群，再清洗归类。  
2. **统计可视化**：Matplotlib 产出获批量趋势、旭日图、类别柱状、成分分布与词云。  
3. **选品筛选**：按适用人群类别与症状关键词筛选候选产品（见上方选品筛选）。

## 局限

PDF 抽取无法完全自动化；赛题样本不等于全市场；页内选品演示为脱敏样本子集。
