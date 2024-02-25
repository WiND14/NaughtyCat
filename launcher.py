import os

import global_space
import cat_footprints
import catch_ehentai

def init():
    """
    初始化环境相关的变量
    """
    # 系统调用里文件夹路径的字符串最后不带\\, 后面的目录统一结尾不带\\
    global_space.handler["env_dir"] = os.path.dirname(os.path.abspath(__file__))
    return

def main():
    init()
    cat_footprints.init()
    try:
        catch_ehentai.init()
    except catch_ehentai.FinishException:
        return
    catch_ehentai.loop()
    return

if __name__ == "__main__":
    main()
