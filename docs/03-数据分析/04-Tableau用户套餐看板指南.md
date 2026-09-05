# Tableau · 用户套餐看板（短版）

> 改图时查。逐步点选全文 → `assets/_doc-backup/04-Tableau用户套餐看板指南-完整版.md`  
> 数据：`data/04-用户套餐分析/01-用户练习明细.csv` · 业务化：[05-套餐页业务化说明.md](05-套餐页业务化说明.md)

**页脚：** 公开数据 IBM Telco；广电实习期间专题；非公司原表。

---

## 验收

1. KPI：用户数、在网用户、在网率（可选月付占比）  
2. 套餐合同：月付/一年/两年 · 用户数 + 在网率  
3. 互联网业务结构；至少 1 个筛选器；页脚声明  
4. 已发 Tableau Public  

**已发布：** https://public.tableau.com/app/profile/.80835515/viz/_17861988284190/sheet5?publish=yes  

---

## 必做计算字段

| 名称 | 公式 |
|------|------|
| 是否在网 | `IF [open_status] = "在网" THEN 1 ELSE 0 END` |
| 在网率 | `SUM([是否在网]) / COUNTD([customer_id])` → 百分比格式 |

主字段：`package_type`、`open_status`、`service_type`、`customer_id`（COUNTD）、`tenure_months`

---

## 工作表清单 → 拼仪表板

`KPI_用户数` · `KPI_在网用户` · `KPI_在网率` · `套餐_结构` · `业务_结构` ·（可选）`tenure_分布`

布局：上排 KPI → 套餐大图 → 业务结构 → 底文本声明。筛选器：`package_type` / `service_type` 应用到各图。

---

## 截图（可选）

放到 `public/images/projects/operator-user/`：整板 + 套餐对比特写。做好告诉我挂项目页。

---

## 常见坑

| 现象 | 处理 |
|------|------|
| 在网率 0～1 | 设百分比 |
| customer_id 被求和 | 改 COUNTD |
| 中文乱码 | 用 `01-用户练习明细.csv` / UTF-8 |
| 和招投标 Tableau 混 | 那是已下线练习；本篇只服务套餐页 |

口述 → `docs/02-面试/00-纯记忆版.md`
