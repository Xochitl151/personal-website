# 数据目录 · 按编号找文件

> 面试被问「数据哪来的」→ 先背 **`docs/02-面试/00-纯记忆版.md`**；细节见 **`03-数据说明与面试口径.md`**

---

## 目录结构

```
data/
├── 00-手动下载说明.md
├── 01-招投标搜索/              ← 关键词练习（个人 Tableau，≠ 实习 3800+）
├── 02-电商漏斗/
├── 03-交易明细/
└── 04-用户套餐分析/            ← 实习主分析公网演示（套餐/开通/地区练习表）
```

---

## 04 · 用户套餐分析（网站优先 · 实习主分析）

| 文件 | 用途 |
|------|------|
| `raw-telco-customer-churn.csv` | IBM Telco 公开集原文（7043） |
| `01-用户练习明细.csv` | 中文映射明细 |
| `02-套餐开通汇总.csv` | 页内 Demo（合同 × 在网） |
| `03-业务类型分布汇总.csv` | 页内 Demo（互联网业务） |

对应项目：`/projects/operator-user-analytics`  
来源：https://www.kaggle.com/datasets/blastchar/telco-customer-churn  
**不能说**是公司原始用户表。

---

## 01 · 招投标搜索（个人关键词练习）

| 文件 | 行数 | 用途 |
|------|------|------|
| `01-练习小样本.csv` | ~99 | Tableau 入门 |
| `02-实习级练习.csv` | 5456 | 关键词 CTR 练习看板 |

与实习用户 3800+ **无关**。步骤：`docs/03-数据分析/03-Tableau实习级看板指南.md`

---

## 02 · 电商漏斗（网站练习）

| 路径 | 来源 | 用途 |
|------|------|------|
| `01-漏斗汇总_按渠道.csv` | 本地汇总 | Tableau 漏斗图（最快） |
| `02-UCI购物意图/` | [UCI 468](https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset) | 原始会话表 |
| `03-UCI点击流/` | [UCI 553](https://archive.ics.uci.edu/dataset/553/clickstream+data+for+online+shopping) | 点击路径分析 |
| `04-Olist巴西电商/` | [Kaggle Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | 订单状态漏斗 |

复制也在：`assets/projects/03-ecommerce-funnel/raw/`

---

## 03 · 交易明细（可选加深）

放 UCI Online Retail II，用于 RFM / 复购分析。  
下载步骤：`00-手动下载说明.md` §1

---

## 重新下载

```bash
py -3 scripts/download_datasets.py
```

失败 → `00-手动下载说明.md`
