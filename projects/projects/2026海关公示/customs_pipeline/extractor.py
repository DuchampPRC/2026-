import csv
import os
import re

from customs_pipeline.config import DEFAULT_YEAR, get_input_dir, get_output_dir, get_temp_docx_dir
from customs_pipeline.converter import convert_doc_to_docx


def extract_district(filename):
    # 支持带年份前缀的文件名，如 "2026上海海关.docx"
    m = re.search(r'([\u4e00-\u9fa5]+海关)', filename)
    return m.group(1) if m else ''


def find_header_row(table):
    keywords = ['姓名', '职位', '代码', '准考证', '学历', '院校', '工作', '性别', '关区']
    for i, row in enumerate(table.rows[:4]):
        texts = [cell.text.strip().replace('\n', '').replace(' ', '') for cell in row.cells]
        score = sum(1 for k in keywords if any(k in t for t in texts))
        if score >= 3:
            return i, [cell.text.strip() for cell in row.cells]
    return -1, []


def parse_docx(docx_path, district):
    from docx import Document
    doc = Document(docx_path)
    results = []

    for table in doc.tables:
        idx, headers = find_header_row(table)
        if idx == -1:
            continue

        col_map = {}
        for c, h in enumerate(headers):
            h_clean = h.replace('\n', '').replace(' ', '')
            if any(x in h_clean for x in ['职位', '代码', '岗位']):
                col_map['position'] = c
            elif '姓名' in h_clean:
                col_map['name'] = c
            elif '性别' in h_clean:
                col_map['gender'] = c
            elif '准考证' in h_clean:
                col_map['exam_id'] = c
            elif '学历' in h_clean:
                col_map['edu'] = c
            elif '毕业院校' in h_clean or '院校' in h_clean:
                col_map['school'] = c
            elif '工作' in h_clean and '单位' in h_clean:
                col_map['work'] = c
            elif '关区' in h_clean or '招录机关' in h_clean:
                col_map['district'] = c

        if 'name' not in col_map:
            continue

        for row in table.rows[idx + 1:]:
            cells = [cell.text.strip().replace('\n', '').replace('\r', '') for cell in row.cells]
            if len(cells) <= max(col_map.values()):
                continue

            name = cells[col_map['name']]
            if not name or name in ['姓名', '合计', '备注', '/'] or '公示' in name:
                continue

            results.append({
                '关区': cells[col_map.get('district', 0)] if 'district' in col_map else district,
                '拟录用职位及代码': cells[col_map.get('position', 0)] if 'position' in col_map else '',
                '姓名': name,
                '性别': cells[col_map.get('gender', 0)] if 'gender' in col_map else '',
                '准考证号': cells[col_map.get('exam_id', 0)] if 'exam_id' in col_map else '',
                '学历': cells[col_map.get('edu', 0)] if 'edu' in col_map else '',
                '毕业院校': cells[col_map.get('school', 0)] if 'school' in col_map else '',
                '工作单位': cells[col_map.get('work', 0)] if 'work' in col_map else '',
            })

    return results


def build_csv(auto_convert=True, docx_dir=None, year=DEFAULT_YEAR):
    input_dir = get_input_dir(year)
    output_dir = get_output_dir(year)
    if docx_dir is None:
        docx_dir = get_temp_docx_dir(year)
    os.makedirs(output_dir, exist_ok=True)

    all_data = []
    if auto_convert:
        try:
            convert_doc_to_docx(input_dir=input_dir, year=year)
        except RuntimeError as e:
            print(f"[转换提示] {e}")
            print("将继续处理目录中已有的 .docx 文件")

    if not os.path.exists(docx_dir):
        os.makedirs(docx_dir, exist_ok=True)

    files = [f for f in os.listdir(docx_dir) if f.lower().endswith('.docx')]
    doc_files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith('.doc') and not f.lower().endswith('.docx')
    ]

    if not files and doc_files:
        print(f"\n发现 {len(doc_files)} 个 .doc 文件，但没有可解析的 .docx 文件。")
        print("请先安装 pywin32，并确认本机 Word/WPS 可用，然后运行 python -m customs_pipeline.converter。")
        print(f"也可以手动将 downloads/{year} 目录中的 .doc 文件另存为 .docx 后再运行 python main.py。")
        return False

    if not files:
        print(f"\n未发现 .docx 文件，请先将公示文件放入 downloads/{year} 目录。")
        return False

    for filename in files:
        filepath = os.path.join(docx_dir, filename)
        district = extract_district(filename)
        print(f"处理: {filename}")
        try:
            data = parse_docx(filepath, district)
            all_data.extend(data)
            print(f"  -> {len(data)} 条")
        except Exception as e:
            print(f"  [异常] {filename}: {e}")

    if all_data:
        out = os.path.join(output_dir, f'{year}海关公示汇总.csv')
        cols = ['关区', '拟录用职位及代码', '姓名', '性别', '准考证号', '学历', '毕业院校', '工作单位']
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            writer.writerows(all_data)
        print(f"\n完成，共 {len(all_data)} 条，保存至: {out}")
        return True

    print("\n未提取到数据")
    return False


if __name__ == '__main__':
    build_csv()
