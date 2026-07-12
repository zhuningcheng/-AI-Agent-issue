import json
import sys
import os
from collections import Counter

# Windows 控制台编码处理
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# =====================================================
# 校验规则
# =====================================================

REQUIRED_FIELDS = [
    "issue_id",
    "issue_number",
    "repo",
    "title",
    "body",
    "state",
    "author",
    "created_at",
    "updated_at",
    "labels",
    "reactions",
    "comments",
]


def is_pr(item):
    """判断是否为 Pull Request（GitHub issue API 返回的 PR 包含 pull_request 字段）"""
    return item.get("pull_request") is not None


def is_discussion(item):
    """
    判断是否为 GitHub Discussion
    Discussions 通常没有 issue_number 或带有特定标识
    这里通过 labels 中包含 'Discussion' 或 title/body 特征判断
    """
    labels = item.get("labels", [])
    if isinstance(labels, list):
        for label in labels:
            label_name = label if isinstance(label, str) else label.get("name", "")
            if "discussion" in label_name.lower():
                return True
    return False


def is_commit(item):
    """
    判断是否为 Commit 相关条目
    Commit 消息通常不含 issue_number，或 title 以特定模式开头
    """
    title = item.get("title", "") or ""
    # Commit 条目一般不会有正常的 issue body，且 title 很短
    # 这里主要依靠 pull_request 字段和 labels 判断
    return False


def should_exclude(item):
    """综合判断是否应该排除"""
    if is_pr(item):
        return "Pull Request"
    if is_discussion(item):
        return "Discussion"
    return None


def validate_fields(item, line_num):
    """检查必填字段是否存在且非空（除 body 允许 null 外）"""
    missing = []
    for field in REQUIRED_FIELDS:
        if field == "body":
            continue  # body 允许为 null
        if field not in item or item[field] is None:
            missing.append(field)
    return missing


def validate_jsonl(filepath):
    """校验单个 JSONL 文件"""
    filename = os.path.basename(filepath)

    print(f"\n{'='*60}")
    print(f"校验文件: {filename}")
    print(f"{'='*60}")

    if not os.path.exists(filepath):
        print(f"  文件不存在，跳过")
        return

    total_lines = 0
    valid_lines = 0
    parse_errors = 0

    issue_id_counter = Counter()
    issue_number_counter = Counter()

    excluded_pr = 0
    excluded_discussion = 0
    excluded_commit = 0

    field_errors = []  # (line_num, missing_fields)

    seen_ids = set()
    dup_ids = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            total_lines += 1

            # 解析 JSON
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                parse_errors += 1
                if parse_errors <= 5:
                    print(f"  行 {line_num}: JSON 解析错误 - {e}")
                continue

            # 排除 PR / Discussion / Commit
            exclude_reason = should_exclude(item)
            if exclude_reason == "Pull Request":
                excluded_pr += 1
                continue
            elif exclude_reason == "Discussion":
                excluded_discussion += 1
                continue

            # 检查 issue_id 重复
            iid = item.get("issue_id")
            if iid is not None:
                issue_id_counter[iid] += 1
                if iid in seen_ids:
                    dup_ids.append((line_num, iid))
                seen_ids.add(iid)

            # 检查 issue_number 重复（同一 repo 内）
            inum = item.get("issue_number")
            repo = item.get("repo", "unknown")
            if inum is not None:
                issue_number_counter[(repo, inum)] += 1

            # 检查必填字段
            missing = validate_fields(item, line_num)
            if missing:
                field_errors.append((line_num, missing))

            valid_lines += 1

    # =====================================================
    # 输出报告
    # =====================================================

    print(f"\n  总行数: {total_lines}")
    print(f"  解析失败: {parse_errors}")
    print(f"  排除 Pull Request: {excluded_pr}")
    print(f"  排除 Discussion: {excluded_discussion}")
    print(f"  有效条目: {valid_lines}")

    # issue_id 重复
    dup_issue_ids = {iid: count for iid, count in issue_id_counter.items() if count > 1}
    if dup_issue_ids:
        print(f"\n  [!] issue_id 重复 ({len(dup_issue_ids)} 个 ID 重复):")
        for iid, count in sorted(dup_issue_ids.items())[:20]:
            print(f"    issue_id={iid} 出现 {count} 次")
        if len(dup_issue_ids) > 20:
            print(f"    ... 还有 {len(dup_issue_ids) - 20} 个")
    else:
        print(f"\n  [OK] 无 issue_id 重复")

    # issue_number 重复（同 repo）
    dup_numbers = {k: v for k, v in issue_number_counter.items() if v > 1}
    if dup_numbers:
        print(f"\n  [!] issue_number 重复 ({len(dup_numbers)} 个):")
        for (repo, num), count in sorted(dup_numbers.items())[:20]:
            print(f"    repo={repo}, issue_number={num} 出现 {count} 次")
    else:
        print(f"\n  [OK] 无 issue_number 重复")

    # 字段缺失
    if field_errors:
        print(f"\n  [!] 字段缺失 ({len(field_errors)} 条):")
        for line_num, missing in field_errors[:10]:
            print(f"    行 {line_num}: 缺少 {missing}")
        if len(field_errors) > 10:
            print(f"    ... 还有 {len(field_errors) - 10} 条")
    else:
        print(f"\n  [OK] 所有必填字段完整")

    # 解析错误
    if parse_errors:
        print(f"\n  [!] JSON 解析错误: {parse_errors} 条")
    else:
        print(f"\n  [OK] 无 JSON 解析错误")

    return {
        "total": total_lines,
        "valid": valid_lines,
        "parse_errors": parse_errors,
        "excluded_pr": excluded_pr,
        "excluded_discussion": excluded_discussion,
        "dup_issue_ids": len(dup_issue_ids),
        "dup_issue_numbers": len(dup_numbers),
        "field_errors": len(field_errors),
    }


def clean_jsonl(filepath, dry_run=True):
    """
    清理 JSONL 文件：去重 + 排除不需要的条目
    dry_run=True 只打印统计，不写文件
    dry_run=False 实际写入新文件
    """
    filename = os.path.basename(filepath)
    output_path = filepath.replace(".jsonl", "_cleaned.jsonl")

    print(f"\n{'='*60}")
    if dry_run:
        print(f"清理预览（不写入）: {filename}")
    else:
        print(f"清理输出: {output_path}")
    print(f"{'='*60}")

    seen_ids = set()
    kept = 0
    skipped_dup = 0
    skipped_pr = 0
    skipped_discussion = 0
    skipped_parse = 0

    if not dry_run:
        out = open(output_path, "w", encoding="utf-8")

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                skipped_parse += 1
                continue

            # 排除 PR / Discussion
            if is_pr(item):
                skipped_pr += 1
                continue
            if is_discussion(item):
                skipped_discussion += 1
                continue

            iid = item.get("issue_id")
            if iid in seen_ids:
                skipped_dup += 1
                continue
            seen_ids.add(iid)

            kept += 1
            if not dry_run:
                out.write(line + "\n")

    if not dry_run:
        out.close()

    print(f"  保留: {kept}")
    print(f"  跳过重复: {skipped_dup}")
    print(f"  跳过 PR: {skipped_pr}")
    print(f"  跳过 Discussion: {skipped_discussion}")
    print(f"  跳过解析失败: {skipped_parse}")

    if not dry_run:
        print(f"\n  已写入: {output_path}")


import argparse


def main():
    parser = argparse.ArgumentParser(description="GitHub Issues JSONL 数据校验工具")
    parser.add_argument(
        "files",
        nargs="*",
        help="要校验的 JSONL 文件路径（默认校验 data/ 下所有文件）",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="执行清理：去重 + 排除 PR/Discussion，输出 _cleaned.jsonl",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="与 --clean 配合使用：实际写入文件（否则仅预览）",
    )
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    jsonl_files = []
    for f in sorted(os.listdir(data_dir)):
        if f.endswith(".jsonl"):
            jsonl_files.append(os.path.join(data_dir, f))

    if not jsonl_files:
        print("未找到 data/ 目录下的 JSONL 文件")
        sys.exit(1)

    print("=" * 60)
    print("GitHub Issues 数据校验工具")
    print("=" * 60)

    files = args.files if args.files else jsonl_files

    if args.clean:
        for filepath in files:
            clean_jsonl(filepath, dry_run=not args.write)
        return

    results = {}
    for filepath in files:
        result = validate_jsonl(filepath)
        results[os.path.basename(filepath)] = result

    # 汇总
    print(f"\n{'='*60}")
    print("汇总")
    print(f"{'='*60}")

    total = sum(r["total"] for r in results.values())
    valid = sum(r["valid"] for r in results.values())
    errors = sum(r["parse_errors"] for r in results.values())
    prs = sum(r["excluded_pr"] for r in results.values())
    discussions = sum(r["excluded_discussion"] for r in results.values())
    dups = sum(r["dup_issue_ids"] for r in results.values())
    field_errs = sum(r["field_errors"] for r in results.values())

    print(f"  总条目: {total}")
    print(f"  有效: {valid}")
    print(f"  排除 PR: {prs}")
    print(f"  排除 Discussion: {discussions}")
    print(f"  重复 issue_id: {dups}")
    print(f"  字段缺失: {field_errs}")
    print(f"  解析错误: {errors}")

    # 清理提示
    if dups > 0 or prs > 0 or discussions > 0 or errors > 0:
        print(f"\n{'='*60}")
        print("清理操作")
        print(f"{'='*60}")
        print("运行以下命令生成清理后的文件:")
        for filepath in files:
            print(f"  python {os.path.basename(__file__)} --clean --write {filepath}")


if __name__ == "__main__":
    main()
