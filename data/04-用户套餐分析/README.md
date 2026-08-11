# 04 · 用户套餐分析（实习主分析 · 公网用公开集）

> 对应网站：`/projects/operator-user-analytics`

## 数据从哪来

| 文件 | 说明 |
|------|------|
| `raw-telco-customer-churn.csv` | **IBM Telco Customer Churn** 公开集原文（7043 行） |
| `01-用户练习明细.csv` | 映射后的中文分析表 |
| `02-套餐开通汇总.csv` | 套餐合同 × 在网/已流失 |
| `03-业务类型分布汇总.csv` | 互联网业务类型分布 |

来源（任选其一即可核对）：  
- https://www.kaggle.com/datasets/blastchar/telco-customer-churn  
- 本仓库下载镜像：GitHub `IBM/telco-customer-churn-on-icp4d` 的 `Telco-Customer-Churn.csv`

## 字段怎么对应简历

| 简历/实习说法 | 公开集字段 |
|---------------|------------|
| 套餐 | `Contract` → 月付 / 一年 / 两年 |
| 开通/在网 | `Churn` → 在网 / 已流失；另有 `PhoneService` / `InternetService` |
| 地区 | 公开集**无**中国地区；实习内网另做 |

## 面试怎么说

「实习 3800+ 是内网用户业务表。作品集用公开电信客户数据演示同类结构分析，不是公司原表。」
