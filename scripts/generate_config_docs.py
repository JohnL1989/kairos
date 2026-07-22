#!/usr/bin/env python3
"""从 configuration.md 自动生成参数索引与版本记录。

用法：
    python scripts/generate_config_docs.py
    
验证配置参数表与版本记录计数一致。
"""

import os
import re

DOCS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
CONFIG_PATH = os.path.join(DOCS_ROOT, "ops", "configuration.md")

def parse_parameters():
    """Extract all config parameters from configuration.md tables."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    params = []
    current_section = ""
    in_table = False
    
    for line in content.split('\n'):
        sec_match = re.match(r'^###?\s+(§?\d[^\n]*)', line)
        if sec_match:
            current_section = sec_match.group(1).strip()
        
        param_match = re.match(r'^\| `(KAIROS_[A-Z_0-9]+)`', line)
        if param_match:
            params.append((current_section, param_match.group(1)))
    
    return params

def count_by_section(params):
    """Count parameters per section."""
    counts = {}
    for section, name in params:
        sec_key = section.split('—')[0].split('（')[0].strip()
        counts[sec_key] = counts.get(sec_key, 0) + 1
    return counts

if __name__ == "__main__":
    params = parse_parameters()
    counts = count_by_section(params)
    
    print(f"总参数数: {len(params)}")
    print("\n各节参数数:")
    for sec, count in sorted(counts.items()):
        print(f"  {sec}: {count}项")
    
    # Validate against version record
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    stated_total = re.search(r'=\s*(\d+)\s*项参数', content)
    if stated_total:
        stated = int(stated_total.group(1))
        if stated != len(params):
            print(f"\n⚠️ 版本记录声称 {stated} 项，实际 {len(params)} 项")
