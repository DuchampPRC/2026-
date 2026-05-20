import os
import re

from customs_pipeline.config import DEFAULT_YEAR, get_input_dir


def rename_customs_files(target_dir=None, year=DEFAULT_YEAR):
    if target_dir is None:
        target_dir = get_input_dir(year)
    renamed = []

    for filename in os.listdir(target_dir):
        if filename.endswith(('.doc', '.docx')):
            match = re.search(r'([\u4e00-\u9fa5]+海关)', filename)
            if match:
                ext = os.path.splitext(filename)[1]
                # 保留年份前缀，如 "2026上海海关.doc"
                new_name = f"{year}{match.group(1)}{ext}"

                if new_name != filename:
                    old_path = os.path.join(target_dir, filename)
                    new_path = os.path.join(target_dir, new_name)
                    os.rename(old_path, new_path)
                    renamed.append((filename, new_name))
                    print(f'已重命名: {filename} -> {new_name}')

    print(f"\n=== {year}年所有文件名 ===")
    for filename in os.listdir(target_dir):
        if filename.endswith(('.doc', '.docx')):
            print(filename)

    return renamed


if __name__ == '__main__':
    rename_customs_files()
