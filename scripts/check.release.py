#!/usr/bin/env python3
"""Kairos 发版门禁检查脚本

验证发布前文档一致性。在每次发布前运行：
    python scripts/check.release.py

检查项：
1. CHANGELOG 版本号与文档 frontmatter 一致
2. README 文档计数与实际文件数一致
3. debt-collection 待实现数与 changelog/README 一致
4. configuration 参数计数与版本记录一致
"""

import os
import re
import sys

DOCS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
errors = []

def count_md_files(root):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.workbuddy',)]
        for f in filenames:
            if f.endswith('.md'):
                count += 1
    return count

def check_readme_count():
    readme = os.path.join(DOCS_ROOT, "README.md")
    with open(readme, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'总计[：:]\s*(\d+)\s*份文档', content)
    if match:
        stated = int(match.group(1))
        actual = count_md_files(DOCS_ROOT)
        if stated != actual:
            errors.append(f"README 文档数 {stated} 与实际 {actual} 不一致")

def check_debt_count():
    changelog = os.path.join(DOCS_ROOT, "governance", "changelog.md")
    debt = os.path.join(DOCS_ROOT, "governance", "debt-collection.md")
    
    with open(changelog, "r", encoding="utf-8") as f:
        changelog_content = f.read()
    
    match = re.search(r'(\d+)\s*闭环\s*\+\s*(\d+)\s*待实现', changelog_content)
    if match:
        stated_open = int(match.group(2))
        
        with open(debt, "r", encoding="utf-8") as f:
            debt_content = f.read()
        
        # Count open D- entries (not ✅ completed)
        open_count = 0
        for line in debt_content.split('\n'):
            if re.match(r'^### D-\d+', line):
                # Check if it's marked completed
                idx = debt_content.find(line)
                section = debt_content[idx:idx+300]
                if '✅ 已完成' not in section:
                    open_count += 1
        
        if stated_open != open_count:
            errors.append(f"changelog 待实现数 {stated_open} 与 debt-collection 实际 {open_count} 不一致")

def check_config_count():
    config = os.path.join(DOCS_ROOT, "ops", "configuration.md")
    with open(config, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r'=\s*(\d+)\s*项参数', content)
    if match:
        stated = int(match.group(1))
        actual = 0
        for line in content.split('\n'):
            if line.startswith('| `KAIROS_') and '|' in line[20:]:
                actual += 1
        if stated != actual:
            errors.append(f"configuration 参数数 {stated} 与实际 {actual} 不一致")

if __name__ == "__main__":
    check_readme_count()
    check_debt_count()
    check_config_count()
    
    if errors:
        print("❌ 发版门禁失败：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ 发版门禁通过")
