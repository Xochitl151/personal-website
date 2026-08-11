# 图片与证书放哪

> **网站只读 `public/`**。`assets/images/` 是原件仓库，改完要 **复制到 public** 才会在浏览器里出现。

---

## 展示位置（推荐）

| 材料 | 放哪 | 网站展示 |
|------|------|----------|
| 认证杯 PDF、CET4、学籍报告 | `credentials/` → 复制到 `public/files/credentials/` | **关于页** → 荣誉与证明 / 教育 |
| 泰迪杯特医食品二等奖 PNG | `credentials/teddy-cup-award-B.png` | **特医项目页** + 关于页 |
| 证件照 | `private/` | ❌ 不上站 |
| 项目分析图 | `assets/projects/.../screenshots/` → `public/images/projects/...` | 各 **项目页** |

---

## `credentials/` 文件与 public 路径

| 原件（assets） | 网站路径（public） | 关于页 |
|----------------|-------------------|--------|
| `认证杯-2023-第十六届-二等奖.pdf` | `/files/credentials/certification-cup-2023-second-prize.pdf` | 荣誉与证明 |
| `CET4.pdf` | `/files/credentials/cet4.pdf` | 荣誉与证明 |
| `教育部学籍在线验证报告_徐华凤 .pdf` | `/files/credentials/xuexin-enrollment-verification.pdf` | 教育 |
| `teddy-cup-award-B.png`（特医食品 · **二等奖**） | `/images/projects/special-food/teddy-cup-award-b.png` | 泰迪杯项目页 + 关于页 |
| `teddy-cup-award-A.png`（自动化生产线 · 三等奖，**另一题**） | 不上特医项目页 | 勿与 B 混用 |

**校级奖学金**：没有电子版，关于页只写文字。

新增 PDF：放进 `credentials/` 后复制到 `public/files/credentials/`，再在 `src/pages/about.astro` 加一行链接。

---

## 为什么之前看不到

文件在 **`assets/images/credentials/`** 不会自动上网站；必须复制到 **`public/files/credentials/`**（或图片到 `public/images/`）。

**面试只背**：`docs/02-面试/00-纯记忆版.md`
