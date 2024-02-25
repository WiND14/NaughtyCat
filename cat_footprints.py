# 标准库, 三方库, 自用库
import logging
import sys
import os
import datetime

import global_space

class Footprints():
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    def __init__(self) -> None:
        self.log_dir = global_space.handler["env_dir"] + "\\log\\"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.today = datetime.datetime.now()
        self.pages = 0
        self.lines = 0
        self.max_lines = 200
        
        file_name = self.generate_file_name()
        
        self.my_logger = logging.getLogger("cat_footprints")
        self.my_logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s')
        self.file_handler = logging.FileHandler(filename=file_name, mode="w", encoding="utf-8")   # 打开时清空, 创建对象时马上打开文件
        self.file_handler.setFormatter(self.formatter)
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.stream_handler.setLevel(logging.INFO)
        self.stream_handler.setFormatter(self.formatter)
        
        self.my_logger.addHandler(self.file_handler)
        self.my_logger.addHandler(self.stream_handler)
        return
    
    def is_next_day(self):
        t = datetime.datetime.now()
        if t.year > self.today.year or t.month > self.today.month or t.day > self.today.day:
            return True
        return False
    
    def generate_file_name(self) -> str:
        file_name = self.log_dir + self.today.strftime("%y%m%d") + "_{}.log"
        # 不覆盖已有页中, 即使中途有空页, 写完后就跳过已有的页
        while os.path.exists(file_name.format(self.pages)):
            self.pages += 1
        file_name = file_name.format(self.pages)
        return file_name
    
    def input_log(self, message: str, level: int):
        # 每次写日志先检查时间, 判断是否要跳页
        is_next = self.is_next_day()
        is_max_lines = self.lines >= self.max_lines
        if is_next or is_max_lines:
            if is_next:
                self.today = datetime.datetime.now()
                self.pages = 0
            file_name = self.generate_file_name()
            
            self.my_logger.removeHandler(self.file_handler)
            self.file_handler = logging.FileHandler(filename=file_name, mode="w", encoding="utf-8")
            self.file_handler.setFormatter(self.formatter)
            self.my_logger.addHandler(self.file_handler)
            
            self.lines = 0
        
        if level == self.DEBUG:
            self.my_logger.debug(message)
        elif level == self.INFO:
            self.my_logger.info(message)
        elif level == self.WARN:
            self.my_logger.warning(message)
        elif level == self.ERROR:
            self.my_logger.error(message)
        
        self.lines += 1
        return

def init():
    global_space.handler["cat_foot"] = Footprints()
    return

# def test():
#     o = Footprints()
#     for i in range(22):
#         o.input_log(str(i), 1)
#     return

# if __name__ == "__main__":
#     test()
    