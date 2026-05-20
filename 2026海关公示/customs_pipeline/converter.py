import os
import shutil

from customs_pipeline.config import DEFAULT_YEAR, get_input_dir, get_temp_docx_dir


WORD_PROCESSORS = [
    ("Microsoft Word", "Word.Application"),
    ("WPS Writer", "KWPS.Application"),
    ("WPS Office", "WPS.Application"),
]


def create_word_processor(win32com):
    last_error = None

    for app_name, prog_id in WORD_PROCESSORS:
        try:
            app = win32com.client.DispatchEx(prog_id)
            return app_name, app
        except Exception as exc:
            last_error = exc

        try:
            app = win32com.client.Dispatch(prog_id)
            return app_name, app
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "未能启动 Microsoft Word 或 WPS。请确认本机已安装 Word/WPS，"
        "且对应的 COM 组件已正确注册。"
    ) from last_error


def open_document(app, doc_path):
    documents = app.Documents
    try:
        return documents.Open(
            FileName=doc_path,
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
        )
    except Exception:
        return documents.Open(doc_path)


def save_as_docx(document, docx_path):
    try:
        document.SaveAs2(docx_path, FileFormat=16)
    except Exception:
        document.SaveAs(docx_path, FileFormat=16)


def close_document(document):
    try:
        document.Close(False)
    except Exception as exc:
        print(f"  [警告] 关闭文档失败: {exc}")


def quit_app(app):
    if app is None:
        return

    try:
        app.Quit()
    except Exception as exc:
        print(f"  [警告] 关闭 Word/WPS 失败，请手动检查是否有残留进程: {exc}")


def sync_existing_docx(input_dir=None, output_dir=None, overwrite=False, year=DEFAULT_YEAR):
    if input_dir is None:
        input_dir = get_input_dir(year)
    if output_dir is None:
        output_dir = get_temp_docx_dir(year)
    os.makedirs(output_dir, exist_ok=True)
    synced_files = []

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith('.docx'):
            continue

        src = os.path.abspath(os.path.join(input_dir, filename))
        dst = os.path.abspath(os.path.join(output_dir, filename))

        if os.path.exists(dst) and not overwrite:
            synced_files.append(dst)
            continue

        shutil.copy2(src, dst)
        synced_files.append(dst)
        print(f"同步已有 docx: {filename} -> temp/{year}/docx")

    return synced_files


def convert_doc_to_docx(input_dir=None, output_dir=None, overwrite=False, year=DEFAULT_YEAR):
    """Convert .doc files in input_dir to .docx with Word or WPS."""
    if input_dir is None:
        input_dir = get_input_dir(year)
    if output_dir is None:
        output_dir = get_temp_docx_dir(year)
    os.makedirs(output_dir, exist_ok=True)
    converted_files = sync_existing_docx(input_dir, output_dir, overwrite=overwrite, year=year)

    doc_files = [
        filename for filename in os.listdir(input_dir)
        if filename.lower().endswith('.doc') and not filename.lower().endswith('.docx')
    ]

    if not doc_files:
        print("未发现需要转换的 .doc 文件")
        return converted_files

    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "缺少 pywin32，无法调用 Word/WPS 转换 .doc 文件。"
            "请先运行: pip install pywin32"
        ) from exc

    failed_files = []
    processor_name = None

    for filename in doc_files:
        doc_path = os.path.abspath(os.path.join(input_dir, filename))
        docx_path = os.path.abspath(os.path.join(output_dir, os.path.splitext(filename)[0] + ".docx"))

        if os.path.exists(docx_path) and not overwrite:
            print(f"跳过: {os.path.basename(docx_path)} 已存在")
            converted_files.append(docx_path)
            continue

        print(f"转换: {filename} -> {os.path.basename(docx_path)}")
        app = None
        document = None

        try:
            app_name, app = create_word_processor(win32com)
            if processor_name != app_name:
                print(f"使用 {app_name} 转换文件")
                processor_name = app_name

            try:
                app.Visible = False
            except Exception:
                pass
            try:
                app.DisplayAlerts = 0
            except Exception:
                pass

            document = open_document(app, doc_path)
            save_as_docx(document, docx_path)
            converted_files.append(docx_path)
        except Exception as exc:
            failed_files.append((filename, exc))
            print(f"  [失败] {filename}: {exc}")
        finally:
            if document is not None:
                close_document(document)
            quit_app(app)

    print(f"temp/{year}/docx 当前可用 .docx 文件 {len(converted_files)} 个")
    if failed_files:
        print(f"转换失败 {len(failed_files)} 个文件，可重新运行或手动另存为 .docx：")
        for filename, _ in failed_files:
            print(f"  - {filename}")
    return converted_files


if __name__ == '__main__':
    try:
        convert_doc_to_docx()
    except RuntimeError as e:
        print(f"[转换失败] {e}")
