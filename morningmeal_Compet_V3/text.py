import pathlib

# 읽어올 텍스트/코드 파일 확장자
exts = {'.py', '.json'}
# 제외할 폴더 (캐시 및 에셋 제외)
exclude = {'__pycache__', '.git', '.venv', 'assets'}

with open('project_code.txt', 'w', encoding='utf-8') as out:
    for p in sorted(pathlib.Path('.').rglob('*')):
        if p.is_file() and p.suffix in exts and not any(part in exclude for part in p.parts):
            out.write(f"\n{'='*50}\nFILE: {p.as_posix()}\n{'='*50}\n\n")
            out.write(p.read_text(encoding='utf-8', errors='ignore'))
            out.write("\n")

print("project_code.txt 생성이 완료되었습니다!")