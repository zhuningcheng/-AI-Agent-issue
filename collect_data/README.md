# collect_data

GitHub Issues 数据采集工具，用于爬取指定仓库的 Issue 数据并保存为 JSONL 格式。

## 功能

- 增量爬取 GitHub Issues（基于 `since` 参数）
- 自动过滤 Pull Request
- 采集 Issue 详情、评论、Reaction 数据
- 数据校验与去重

## 文件说明

| 文件 | 说明 |
|------|------|
| `github_client.py` | GitHub API 客户端（Token 认证、分页） |
| `utils.py` | 通用工具函数（数据获取、存储、元数据管理） |
| `crawler_openclaw.py` | OpenClaw 仓库爬虫入口 |
| `crawler_hermers.py` | Hermes-agent 仓库爬虫入口 |
| `validate_data.py` | 数据校验与去重工具 |
| `update_openclaw.py` | OpenClaw 数据更新脚本 |
| `update_hermers.py` | Hermes 数据更新脚本 |
| `data/*.jsonl` | 爬取的数据文件（Git LFS 管理） |
| `metadata/*.json` | 爬虫元数据（上次爬取时间） |

## 使用方法

### 1. 配置环境变量

```bash
# .env 文件中设置
GITHUB_TOKEN=your_token
```

### 2. 运行爬虫

```bash
# 爬取 OpenClaw 仓库
python crawler_openclaw.py

# 爬取 Hermes-agent 仓库
python crawler_hermers.py
```

### 3. 数据校验

```bash
# 校验所有 data/ 下的 JSONL 文件
python validate_data.py

# 校验指定文件
python validate_data.py data/hermes.jsonl

# 清理重复数据（预览模式）
python validate_data.py --clean data/hermes.jsonl

# 清理重复数据（写入文件）
python validate_data.py --clean --write data/hermes.jsonl
```

## 数据格式

每条记录包含：

- `repo` — 仓库名称
- `issue_id` — GitHub Issue 唯一 ID
- `issue_number` — Issue 编号
- `title` / `body` — 标题和正文
- `state` — 状态（open/closed）
- `author` — 作者
- `created_at` / `updated_at` / `closed_at` — 时间戳
- `labels` — 标签列表
- `reactions` — Reaction 统计
- `comments` — 评论列表（作者、时间、内容）

## 校验规则

校验工具会检查以下内容：

- `issue_id` 是否重复
- 同一 repo 内 `issue_number` 是否重复
- 必填字段是否缺失
- 是否为合法 JSON 格式
- 排除 PR、Discussion、Commits 等非 Issue 数据
