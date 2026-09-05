"""
中国政府采购网爬虫脚本
功能：爬取最近一周的招标公告数据
特点：使用 requests + BeautifulSoup 解析HTML
"""
# ==================== 导入模块 ====================
import json
import requests
from bs4 import BeautifulSoup
import time
import re
import os
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlunparse
from datetime import datetime, timedelta

# 导入日志工具模块
from utils.logger import setup_logging, get_logger
# 导入数据处理工具模块
from utils.data_processor import clean_data_item
from paths import OUTPUTS_DIR

# ==================== 配置加载 ====================
# 从 config.py 加载关键词配置，失败则使用默认值
try:
    from config import KEYWORDS as CFG_KEYWORDS
except Exception:
    CFG_KEYWORDS = ["专线", "短信", "智慧", "公有云", "私有云", "政务云", "云计算", "云"]

KEYWORDS = CFG_KEYWORDS

# 初始化日志
setup_logging(log_dir='logs')
logger = get_logger(__name__)


def modify_url_page(url: str, page_num: int) -> str:
    """修改URL中的页码参数
    
    Args:
        url: 原始URL
        page_num: 页码
    
    Returns:
        str: 修改后的URL
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['page_index'] = [str(page_num)]
    new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
    new_parsed = parsed_url._replace(query=new_query)
    return urlunparse(new_parsed)


def is_within_one_week(date_str: str) -> bool:
    """检查日期是否在最近一周内
    
    Args:
        date_str: 日期字符串（格式：YYYY-MM-DD）
    
    Returns:
        bool: True表示在一周内，False表示不在或格式错误
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        one_week_ago = datetime.now() - timedelta(days=7)
        one_week_ago = one_week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        return date >= one_week_ago
    except ValueError:
        return False


def crawl_announcements_by_keyword(base_url: str, keyword: str, page_limit: int = 3) -> List[Dict[str, Any]]:
    """根据关键词爬取最近一周的公告
    
    Args:
        base_url: 基础URL
        keyword: 搜索关键词
        page_limit: 最大爬取页数
    
    Returns:
        List[Dict]: 公告数据列表，每个元素包含 title, url, time, source, keyword
    """
    announcements = []
    seen_entries = set()
    one_week_ago = datetime.now() - timedelta(days=7)
    start_date_str = one_week_ago.strftime("%Y%%3A%m%%3A%d")
    today_str = datetime.now().strftime("%Y%%3A%m%%3A%d")

    # 更新URL参数
    parsed_url = urlparse(base_url)
    query_params = parse_qs(parsed_url.query)
    query_params['start_time'] = [start_date_str]
    query_params['end_time'] = [today_str]
    query_params['kw'] = [requests.utils.quote(keyword)]
    new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
    base_url = urlunparse(parsed_url._replace(query=new_query))

    # 请求头设置
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://search.ccgp.gov.cn/"
    }

    session = requests.Session()
    session.headers.update(headers)

    for page in range(1, page_limit + 1):
        retries = 2
        while retries > 0:
            try:
                current_url = modify_url_page(base_url, page)
                response = session.get(current_url, timeout=15)
                response.raise_for_status()
                response.encoding = "utf-8"

                soup = BeautifulSoup(response.text, "html.parser")
                result_list = soup.find("ul", class_="vT-srch-result-list-bid")
                if not result_list:
                    break

                items = result_list.find_all("li")
                if not items:
                    break

                # 处理公告项
                for item in items:
                    # 提取日期
                    date = "未知日期"
                    date_span = item.find("span")
                    if date_span:
                        date_match = re.search(r"(\d{4})\.(\d{2})\.(\d{2}) \d{2}:\d{2}:\d{2}", date_span.text)
                        if date_match:
                            year, month, day = date_match.groups()
                            date = f"{year}-{month}-{day}"

                    if not is_within_one_week(date):
                        continue

                    # 提取标题和链接
                    a_tag = item.find("a")
                    if a_tag and a_tag.text.strip():
                        title = a_tag.text.strip()
                        link = a_tag.get("href", "").strip()

                        # 标准化链接
                        if link.startswith("//"):
                            link = f"https:{link}"
                        elif link.startswith("/"):
                            link = f"https://search.ccgp.gov.cn{link}"
                        elif not link.startswith("http"):
                            link = f"https://search.ccgp.gov.cn/{link}"

                        entry_key = (title, link)
                        if entry_key not in seen_entries:
                            seen_entries.add(entry_key)
                            # 创建数据项并清洗
                            raw_item = {
                                "title": title,
                                "url": link,
                                "time": date,
                                "source": "中国政府采购网",
                                "keyword": keyword
                            }
                            # 使用统一的数据清洗函数
                            cleaned_item = clean_data_item(raw_item)
                            announcements.append(cleaned_item)

                time.sleep(2)  # 页面间隔
                break

            except Exception as e:
                retries -= 1
                if retries == 0:
                    logger.warning(f"关键词「{keyword}」第{page}页爬取失败: {e}")
                    break
                logger.debug(f"关键词「{keyword}」第{page}页重试中...")
                time.sleep(2)

        if not result_list or not items:
            break

    announcements.sort(key=lambda x: x["time"], reverse=True)
    return announcements


def save_to_json(announcements: List[Dict[str, Any]]) -> None:
    """保存数据到JSON文件
    
    Args:
        announcements: 公告数据列表
    """
    if not announcements:
        logger.warning("没有获取到数据")
        return

    filename = "1_ChinaGovernment.json"
    # 使用 paths.py 中统一管理的 OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = OUTPUTS_DIR / filename

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(announcements, f, ensure_ascii=False, indent=4)
        logger.info(f"数据已保存到: {save_path}，共{len(announcements)}条记录")
    except Exception as e:
        logger.error(f"保存失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("中国政府采购网爬虫开始运行")
        logger.info("=" * 50)
        
        base_url = "https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=0&dbselect=bidx&kw=&timeType=3&displayZone=&zoneId=&pppStatus=0&agentName="
        
        all_announcements = []
        
        logger.info("开始爬取最近一周数据...")
        for idx, keyword in enumerate(KEYWORDS, 1):
            # 爬取每个关键词
            data = crawl_announcements_by_keyword(base_url, keyword, page_limit=3)
            all_announcements.extend(data)
            logger.info(f"完成关键词 {idx}/{len(KEYWORDS)}: {keyword} ({len(data)}条)")
            time.sleep(3)  # 关键词间隔
        
        # 全局去重
        seen = set()
        unique_data = []
        for item in all_announcements:
            key = (item["title"], item["url"])
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        # 按日期排序
        unique_data.sort(key=lambda x: x["time"], reverse=True)
        
        # 保存结果
        save_to_json(unique_data)
        logger.info("=" * 50)
        logger.info("爬取完成")
        logger.info("=" * 50)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)