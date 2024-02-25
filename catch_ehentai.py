import os
import random
import time

import yaml
import requests
from bs4 import BeautifulSoup

import global_space
import cat_footprints

FINISH = 0
CHECKING = 1

class FinishException(Exception):
    def __init__(self) -> None:
        super().__init__("上一批图集已完成")
        return
class ConnectionException(Exception):
    def __init__(self) -> None:
        super().__init__("链接请求未达")
        return
class ResponseException(Exception):
    def __init__(self) -> None:
        super().__init__("链接应答错误")
        return
class OriginLinkNotFoundException(Exception):
    def __init__(self) -> None:
        super().__init__("未找到原始图片的链接")
        return
class ImgConnectionException(Exception):
    def __init__(self) -> None:
        super().__init__("图床链接未达")
        return
class ImgResponseException(Exception):
    def __init__(self) -> None:
        super().__init__("图床应答错误")
        return
class DownloadException(Exception):
    def __init__(self) -> None:
        super().__init__("获取图片失败")
        return


def is_same_pict_set(begin_url: str, cur_url: str) -> bool:
    begin_pict = begin_url.split('/')[-1]
    begin_id = begin_pict.split('-')[0]
    cur_pict = cur_url.split('/')[-1]
    cur_id = cur_pict.split('-')[0]
    return begin_id == cur_id

def init():
    config_file_path = global_space.handler["env_dir"] + '\\' + "config.yaml"
    with open(config_file_path, "r", encoding="utf-8") as f:
        file_data: dict = yaml.safe_load(f)
        global_space.handler["config"] = file_data
    
    global_space.handler["config"]["record_file_path"] = "{}\\{}".format(
        global_space.handler["env_dir"], 
        global_space.handler["config"]["record_file_name"]
    )
    
    # 检查是否有存档记录
    if os.path.exists(global_space.handler["config"]["record_file_path"]):
        with open(global_space.handler["config"]["record_file_path"], "r", encoding="utf-8") as f:
            file_data: dict = yaml.safe_load(f)
            # 上一批已结束
            if file_data["status"] == FINISH:
                if is_same_pict_set(global_space.handler["config"]["begin_url"], file_data["url"]):
                    raise FinishException
            else:
                global_space.handler["config"]["begin_url"] = file_data["url"]
    
    # 整理格式
    global_space.handler["config"]["img_save_dir"] = "{}\\{}\\{}".format(
        global_space.handler["config"]["img_save_root_dir"], 
        global_space.handler["config"]["artist"],
        global_space.handler["config"]["package"]
    )
    global_space.handler["config"]["retry_max_times"] = int(global_space.handler["config"]["retry_max_times"])
    
    return

def record(url: str, tag: int):
    with open(global_space.handler["config"]["record_file_path"], "w", encoding="utf-8") as f:
        f.write("url: {}\n".format(url))
        f.write("status: {}\n".format(tag))
    return

def parse_link(content: str):
    """
    提取压缩的图片, 即预览图
    """
    soup = BeautifulSoup(content, "html.parser")
    # 提取压缩过的jpg
    target_pict_div = soup.find("div", id="i3")
    next_link_a = target_pict_div.find("a")
    target_pict_img = next_link_a.find("img")
    next_link = next_link_a.attrs["href"]
    img_link = target_pict_img.attrs["src"]
    return img_link, next_link

def parse_origin_link(content: str):
    """
    尝试提取原始图片链接
    """
    soup = BeautifulSoup(content, "html.parser")
    target_pict_div = soup.find("div", id="i6")
    all_div = target_pict_div.find_all("div")
    if len(all_div) == 4:
        target = all_div[-1].find("a")
        return target.attrs["href"]
    raise OriginLinkNotFoundException

def get_img(img_link: str):
    logger: cat_footprints.Footprints = global_space.handler["cat_foot"]
    config = global_space.handler["config"]
    filename = img_link.split("/")[-1]
    if not os.path.exists(config["img_save_dir"]):
        os.makedirs(config["img_save_dir"])
    file_path = config["img_save_dir"] + '\\' + filename
    try:
        response = requests.get(img_link, stream=True, timeout=config["timeout_second"] * 2)
    except KeyboardInterrupt:
        raise 
    except Exception as e:
        logger.input_log(str(e), logger.DEBUG)
        raise ImgConnectionException
    
    if response.status_code != 200:
        logger.input_log(str(response.status_code), logger.DEBUG)
        raise ImgResponseException
    
    try:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=config["download_chunk_size"]):
                if chunk:
                    f.write(chunk)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.input_log(str(e), logger.DEBUG)
        raise DownloadException
    return

def logic(url: str):
    """
    仅处理逻辑, 异常均抛出给到上层
    """
    logger: cat_footprints.Footprints = global_space.handler["cat_foot"]
    config = global_space.handler["config"]
    
    # 尝试访问
    try:
        response = requests.get(
            url, 
            headers=config["headers"], 
            timeout=config["timeout_second"], 
            allow_redirects=False
        )
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.input_log(str(e), logger.DEBUG)
        raise ConnectionException
    
    # 检查连接的返回
    if response.status_code != 200:
        logger.input_log(str(response.status_code), logger.DEBUG)
        raise ResponseException
    
    html_content = response.text
    img_link, next_link = parse_link(html_content)
    
    # 抓取原始图片需要登录账号, 暂未知如何模拟js行为
    # try:
    #     origin_img_link = parse_origin_link(html_content)
    #     # 有风险, 如果原始图片的连接是个死链, 那么就永远都连不上了
    #     img_link = origin_img_link
    #     logger.input_log("目标更改为原图链接: " + origin_img_link, logger.DEBUG)
    # except OriginLinkNotFoundException as e:
    #     logger.input_log(str(e), logger.DEBUG)
    
    # 尝试下载
    try:
        get_img(img_link)
    except (
        KeyboardInterrupt, 
        ImgConnectionException, 
        ImgResponseException, 
        DownloadException,
    ):
        raise
    
    return next_link

def loop():
    config = global_space.handler["config"]
    logger: cat_footprints.Footprints = global_space.handler["cat_foot"]
    
    current_url = config["begin_url"]
    img_num = 0
    retry = 0
    cd_time = 0.0
    while True:
        if config["retry_max_times"] > 0 and retry == config["retry_max_times"]:
            logger.input_log("图集抓取未完成...", logger.WARN)
            break
        try:
            # 这个判断也放在try块里, 在线程睡眠时也检测ctrl-c
            if cd_time > 0:
                rest = min(0.5, cd_time)
                cd_time -= rest
                time.sleep(rest)
                continue
            else:
                record(current_url, CHECKING)
                logger.input_log("尝试( {} )抓取图片( {} ), 中断按CTRL-C".format(retry, img_num), logger.INFO)
                logger.input_log("target: " + current_url, logger.DEBUG)
                try:
                    next_link = logic(current_url)
                except KeyboardInterrupt:
                    raise
                except (
                    ConnectionException, 
                    ResponseException, 
                    ImgConnectionException, 
                    ImgResponseException, 
                    DownloadException, 
                ) as e:
                    logger.input_log(str(e), logger.WARN)
                    retry += 1
                    continue
                
                if current_url == next_link:
                    record(current_url, FINISH)
                    logger.input_log("图集抓取完毕, 本次共抓取 {} 张图片".format(img_num + 1), logger.INFO)
                    break
                else:
                    current_url = next_link
                
                cd_time = config["base_cd_second"] + random.random() * config["random_cd_second_limit"]
                logger.input_log("完成抓取, 等待 {:.8f} s".format(cd_time), logger.INFO)
                retry = 0
                img_num += 1
                
        except KeyboardInterrupt:
            logger.input_log("中断运行", logger.INFO)
            break
        except Exception as e:
            logger.input_log(str(e), logger.DEBUG)
            logger.input_log("进程错误", logger.ERROR)
            break
        
    return
