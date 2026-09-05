---
title: 招投标信息采集与搜索（实习）
summary: 用 Python 从 5 个政务站点采集公告，清洗入库后做成可检索站点。
takeaway: 把 5 个信息源的招投标公告采集入库，做成可检索、可筛选、可导出 CSV 的搜索站点。
lookFor: 采集链路与联调截图
role: 智慧广电实习 · 多源爬虫取数为主，并参与检索站点部分开发 / 测试 / 部署。
date: 2025-08-01
dateLabel: "2025.08 – 2025.12"
tags: [实习, Python, 爬虫, Playwright, 搜索站点]
kind: intern
featured: true
order: 3
metrics:
  - label: 采集来源
    value: 5 个站点
    hint: 政府采购 / 公共资源 / 邮政等
  - label: 联调库规模
    value: 约 9000+ 条
    hint: 验收截图最高约 9321
  - label: 页内样例
    value: 676 条
    hint: 公开公告导出子集
pipeline:
  - 目标网站 · 5 站
  - Python 爬虫
  - 清洗入库
  - 搜索 · 筛选导出
pipelineLabel: 采集链路
pipelineHighlight: 1
findings:
  - title: 多源站点要分别适配
    detail: 各站字段与反爬不同：简单站用 requests + BeautifulSoup，复杂站用 Playwright（广东站含验证码 OCR）。
    action: 覆盖 5 个公开信息源；联调截图与页内样例证明可入库、可检索。
  - title: 采集结果进入检索站
    detail: 标题、时间、来源、关键词入库后，支持检索、筛选、CSV 导出与手动触发爬取。
    action: 截图为联调环境（约 8600+ / 9321）；页内表为 676 条公开公告子集。
demos:
  - chart-gallery
  - bidding-browse
  - feature-explorer
charts:
  - src: /images/projects/bidding-search-engine/ui-search-home.jpg
    label: 搜索首页
    alt: 招投标搜索首页：关键词、快捷词、日期与来源筛选、导出 CSV
    proves: 入库后可在站内检索；该帧约 8600+，与联调约 9000+ 同量级。
    limits: 联调环境截图，非公网可登录站；条数随爬取变化。
    next: 下方样例表演示同一套字段（标题 / 时间 / 来源 / 关键词）。
  - src: /images/projects/bidding-search-engine/ui-list-crawl-status.jpg
    label: 列表与爬取
    alt: 结果列表与爬取运行状态（约 9321）
    proves: 列表含标题、时间、来源、关键词；可手动触发爬取并看运行状态。
    limits: 含浏览器 Network 面板，为联调验收截图。
    next: 脚本密钥已剥离，公网页不要求再跑通全源。
lenses:
  - id: ai
    label: 产品与交付
    bullets:
      - 主线：5 站采集 → 清洗入库 → 检索 / 筛选 / 导出。
      - 证据：联调截图（约 9000+）+ 676 条公开公告样例。
      - 完成联调验收，未长期正式运营。
  - id: data
    label: 数据分析
    bullets:
      - 说明数据从哪来、如何可查；用户结构专题见套餐页。
      - 样例字段：标题、时间、来源、关键词。
disclaimer: 实习项目。约 9000+ 为联调验收截图规模（最高约 9321）；页内 676 条为公开公告导出子集。脚本密钥已剥离，非可再跑通工程。未长期正式运营。
---

## 背景

招投标信息分散在多个政务公开站点。实习于广东智慧广电物联网科技有限公司（2025.08–2025.12），参与 **招投标信息采集与搜索**：以 **Python 多源爬虫** 为主，清洗入库后做成可检索站点，并参与部分开发 / 测试 / 部署。完成联调验收，**未长期正式运营**。同期用户结构专题见 [广电用户场景 · 套餐与在网分析](/projects/operator-user-analytics)。

## 我做了什么

1. **多源采集（重点）**：覆盖中国政府采购网、广东政府采购网、公共资源交易平台等 5 站；简单站 `requests` + BeautifulSoup，复杂站 Playwright（广东站含验证码 OCR）。  
2. **清洗入库**：统一标题、时间、来源、关键词等字段。  
3. **检索站点**：参与检索、筛选、列表、CSV 导出与爬取更新等模块的开发、测试与部署。  
4. **范围**：止于采集与检索。本页不贴可跑通整仓代码。

## 本页提供什么

- 采集链路与多源适配说明  
- 联调 UI 截图（约 8600+ / 9321）  
- 676 条公开公告样例检索  

## 局限

未长期正式运营；页内为公开公告样例（非联调全量）。脚本密钥已剥离。
