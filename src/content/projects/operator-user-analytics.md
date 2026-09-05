---
title: 广电用户场景 · 套餐与在网分析
summary: 智慧广电实习期间的公开数据专题：用 IBM Telco 做套餐结构与在网率分析及看板。同属广电用户场景，数据与公司口径不同。
takeaway: 对比不同套餐合同的用户规模与在网率，找出短合约在网偏低的结构信号，并用看板呈现。
lookFor: 套餐合同 / 互联网业务切换
role: 智慧广电实习期间 · 公开数据专题：清洗汇总、结构对比与 Tableau 看板。
date: 2025-08-01
dateLabel: "2025.08 – 2025.12"
tags: [广电场景, Python, Tableau, 用户分析]
kind: independent
featured: true
order: 1
metrics:
  - label: 数据
    value: Telco 7043
    hint: IBM 公开电信客户集
  - label: 维度
    value: 套餐 / 在网 / 业务
    hint: 合同类型与互联网业务
  - label: 本页交付
    value: 表 + 看板
    hint: 页内可切换表与 Tableau 截图 / 外链
pipeline:
  - 取数与校验
  - 口径统一
  - 结构分析
  - 看板与页内演示
findings:
  - title: 月付套餐在网率明显偏低
    detail: 月付用户规模最大，在网率约 57%，低于一年约 89%、两年约 97%。
    action: 可优先关注短合约用户的续约与开通引导，下周期再看在网率变化。
  - title: 互联网业务类型可作开通结构视图
    detail: 光纤、DSL、未开通互联网的用户规模与在网率不同，适合对照「开通类」结构。
    action: 排查时可按业务类型切开看规模与在网差异。
demos:
  - user-insights
  - chart-gallery
charts:
  - src: /images/projects/operator-user/tableau-dashboard-full.jpg
    label: 仪表板
    alt: 客户结构看板全屏（IBM Telco 公开数据）
    proves: 一屏呈现用户数/在网率 KPI、套餐与业务结构、在网月数分布。
    limits: 公开数据，非公司原表。
    next: 业务侧可用自有套餐口径做同结构对比。
  - src: /images/projects/operator-user/tableau-package-compare.jpg
    label: 套餐对比
    alt: 套餐结构：月付 / 一年 / 两年用户数与在网率（IBM Telco）
    proves: 月付用户最多但在网率 57.3%，低于一年 88.7%、两年 97.2%。
    limits: 观察性结论，不作因果断言。
    next: 建议核对短合约续约与开通，下周期再验证。
lenses:
  - id: data
    label: 数据分析
    bullets:
      - 公开数据：合同类型 ≈ 套餐，在网 ≈ 留存结果。
      - 结论按「观察 → 可能原因 → 建议验证」表述。
      - 广电实习同场景；本页数据与公司口径不同。
  - id: ai
    label: 产品与交付
    bullets:
      - 本页：可切换汇总表 + Tableau 看板截图与外链。
      - 同期招投标为工程项目，与本页分开。
externalLinks:
  - label: Tableau Public（外链）
    href: https://public.tableau.com/app/profile/.80835515/viz/_17861988284190/sheet5?publish=yes
  - label: 数据来源（Kaggle Telco）
    href: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
disclaimer: 智慧广电实习期间的公开数据专题。IBM Telco Customer Churn（约 7043 行）；同属广电用户场景，非公司原表。
---

## 背景

智慧广电实习（2025.08–2025.12）同属**广电用户**业务场景。本页是实习期间完成的 **公开数据专题**：用 IBM Telco Customer Churn 做套餐结构与在网率分析（合同≈套餐、在网≈留存、互联网业务≈开通类服务）。数据与公司口径不同。同期工程项目见 [招投标信息采集与搜索](/projects/bidding-search-engine)。

## 我做了什么

1. **清洗与口径**：整理套餐合同、在网状态、互联网业务等字段。  
2. **结构对比**：按套餐看用户数与在网率；按业务类型看开通类结构。  
3. **展示**：Tableau 看板；本页提供可切换汇总表与看板截图。

## 本页提供什么

- 按套餐合同 / 按互联网业务的汇总表（可切换）  
- Tableau 整板与套餐对比截图，以及 Public 外链  
