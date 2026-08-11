---
title: 广电用户套餐与开通分析（实习）
summary: 实习期间围绕用户套餐、开通、地区等业务字段做清洗与结构分析；公网用 IBM Telco 公开客户数据演示同类型结构分析与看板。
takeaway: 把用户业务表整理成可统计的套餐 / 在网结构，对比不同合同的在网率，供业务跟踪。
role: 智慧广电实习 · 数据分析：取数、清洗、口径统一、结构分析与报表展示。
date: 2025-08-01
tags: [实习, SQL, Python, Excel, Tableau, 用户分析]
kind: intern
featured: true
order: 1
metrics:
  - label: 实习数据
    value: 3800+ 行
    hint: 内网用户业务表，不外传
  - label: 公网演示
    value: Telco 7043
    hint: IBM 公开电信客户集
  - label: 维度
    value: 套餐 / 在网 / 业务
    hint: 公开集无中国地区字段
pipeline:
  - 取数与校验
  - 口径统一
  - 结构分析
  - 报表与看板
findings:
  - title: 月付套餐在网率明显偏低（公开集）
    detail: IBM Telco 练习数据上，月付用户规模最大，但在网率低于一年/两年合约，流失更集中。
    action: 观察性结论：可优先关注短合约用户的续约与开通引导；实习内网需按本公司口径复算。
  - title: 互联网业务类型可对照开通结构
    detail: 光纤、DSL、未开通互联网的用户规模与在网率不同，适合作为「开通类业务」结构视图。
    action: 公开集无中国地区字段；地区分布以实习内网分析为准。
demos:
  - user-insights
  - chart-gallery
charts:
  - src: /images/projects/operator-user/tableau-dashboard-full.png
    label: 仪表板
    alt: 客户结构看板全屏（IBM Telco 公开数据）
    proves: 一屏呈现用户数/在网率 KPI、套餐与业务结构、在网月数分布，适合说明交付形态。
    limits: 公开集演示，不是广电内网原表；数字勿说成实习 3800+ 实数。
    next: 面试用内网口径复述套餐/开通/地区；公网看板证明 Tableau 能力。
lenses:
  - id: data
    label: 数据分析
    bullets:
      - 实习：套餐 / 开通 / 地区（内网 3800+）。
      - 公网：IBM Telco 演示合同类型与在网率对比。
      - 发现写法：发现 → 可能原因 → 建议验证。
  - id: ai
    label: 产品与交付
    bullets:
      - 交付形态是业务可看的结构表与看板。
      - 同期招投标站点是工程项目，与本页分析分开。
externalLinks:
  - label: Tableau Public 看板
    href: https://public.tableau.com/app/profile/.80835515/viz/_17861988284190/sheet5?publish=yes
  - label: 数据来源说明（Kaggle Telco）
    href: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
disclaimer: 实习分析项目。简历 3800+ 为实习内网有效规模（不可外传）。本页交互基于 IBM Telco Customer Churn 公开数据集（约 7043 行，虚构电信公司样本），用于演示「套餐合同 / 在网 / 业务类型」结构分析，不是广电公司原始用户表。字段映射：Contract→套餐合同，Churn→在网/已流失，InternetService→互联网业务。
---

## 背景

智慧广电实习（2025.08–2025.12）数据分析主线是：**用户套餐、开通、地区** 等业务字段的整理与统计。公网不能放公司原表，因此用 **IBM Telco Customer Churn** 公开集做同类型演示（合同≈套餐、在网≈留存/开通结果、互联网业务≈开通类服务）。同期另有 [招投标信息采集与搜索站点](/projects/bidding-search-engine)。

## 我做了什么（实习）

1. **取数与清洗**：SQL 提取用户业务数据，Python / Excel 校验。  
2. **口径统一**：规范套餐、开通、地区等字段。  
3. **结构分析与展示**：按维度汇总，Excel / Tableau 报表辅助跟踪。

## 本页提供什么（公网）

- 基于公开 Telco 数据的 **按套餐合同 / 按互联网业务** 表。  
- 说明方法与口径，**不等于**实习内网数字。

## 局限

公开集为国外虚构电信样本，无中国地区字段；结论需用实习内网数据复算后再用于业务决策。
