import os
import shutil

from customs_pipeline.config import DEFAULT_YEAR, get_temp_dir


def cleanup_temp(temp_dir=None, year=DEFAULT_YEAR):
    if temp_dir is None:
        temp_dir = get_temp_dir(year)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"已删除临时目录: {temp_dir}")
        return True

    print(f"临时目录不存在，无需清理: {temp_dir}")
    return False


if __name__ == '__main__':
    cleanup_temp()
