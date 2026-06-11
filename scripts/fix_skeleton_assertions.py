"""移除测试文件中的骨架 L4Behavior/L6Snapshot 类（AttackBehavior/L5EdgeCases 已覆盖）."""
import re
import sys
from pathlib import Path

def remove_skeleton_classes(filepath: Path) -> bool:
    """Read file, remove L4Behavior and L6Snapshot classes with skeleton assertions."""
    content = filepath.read_text(encoding="utf-8")
    if "assert card is not None" not in content:
        return False

    lines = content.split("\n")
    new_lines = []
    skip_until_next_class = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a skeleton class to remove
        if re.match(r'class Test\w+L4Behavior:', line) or re.match(r'class Test\w+L6Snapshot:', line):
            # Verify this class contains skeleton assertions before removing
            class_start = i
            class_end = len(lines)
            for j in range(i + 1, len(lines)):
                if re.match(r'^class\s+', lines[j]):
                    class_end = j
                    break
            class_body = "\n".join(lines[class_start:class_end])
            if "assert card is not None" in class_body:
                # Skip this entire class
                skip_until_next_class = True
                i = class_end
                # Trim trailing blank lines before the next class
                while new_lines and not new_lines[-1].strip():
                    new_lines.pop()
                continue
            else:
                # Class doesn't contain skeleton assertions, keep it
                pass

        new_lines.append(line)
        i += 1

    if len(new_lines) != len(lines):
        filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"  Cleaned: {filepath.name}")
        return True
    return False

def main():
    root = Path("tests/cards/generated")
    files = sorted(root.rglob("test_*.py"))
    cleaned = 0
    for fp in files:
        if remove_skeleton_classes(fp):
            cleaned += 1
    print(f"\nCleaned {cleaned} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
