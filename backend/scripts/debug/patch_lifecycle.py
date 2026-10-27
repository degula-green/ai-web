import os

file_path = "e:/AI内容自动化/backend/app/core/lifecycle.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the specific line, ignoring whitespace/exact match if needed
lines = content.splitlines()
new_lines = []
found = False
for line in lines:
    if "task_repository = TaskRepository()" in line:
        # Preserve indentation
        indent = line[:line.find("task_repository")]
        new_lines.append(f"{indent}task_repository = TaskRepository(session_factory)")
        found = True
    else:
        new_lines.append(line)

if found:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print("Successfully updated lifecycle.py")
else:
    print("Could not find the target line in lifecycle.py")
