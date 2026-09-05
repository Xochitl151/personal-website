"""
中国邮政爬虫脚本
功能：通过API接口爬取中国邮政招标公告数据
特点：直接请求API，过滤一个月内的数据
注意：当前只爬取第1页，如需更多数据可增加页数
"""
# ==================== 导入模块 ====================
import json
import os
import time
from datetime import datetime, timedelta
import requests
import re
from urllib.parse import urljoin

# 导入日志工具模块
from utils.logger import setup_logging, get_logger
# 导入数据处理工具模块
from utils.data_processor import clean_data_item
# 导入重试装饰器
from paths import OUTPUTS_DIR
from utils.retry import retry_on_exception

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

# ==================== API 配置 ====================
# 中国邮政搜索API地址
BASE_URL = 'https://iframe.chinapost.com.cn/jsp/util/Search.jsp?community=ChinaPostJT&lucenelist=1813902036'
HOST = 'https://www.chinapost.com.cn'

# 请求头配置（模拟浏览器请求）
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.chinapost.com.cn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.chinapost.com.cn/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
}

# ==================== 时间范围配置 ====================
# 计算时间范围：一个月前至今（用于过滤数据）
ONE_MONTH_AGO = datetime.now() - timedelta(days=30)


# ==================== 数据请求函数 ====================
@retry_on_exception(
    max_attempts=3,
    delay=2.0,
    backoff=2.0,
    exceptions=(requests.exceptions.RequestException, Exception)
)
def _fetch_chinapost_data_internal(keyword, page_number):
    """内部函数：实际执行API请求（使用重试装饰器）"""
    data = {
        'q': keyword,
        'page': str(page_number)
    }
    
    time.sleep(1)  # 请求间隔，避免被限流
    response = requests.post(BASE_URL, headers=HEADERS, data=data, timeout=10)
    response.raise_for_status()
    return response.json()


def get_chinapost_data(keyword, page_number, max_retries=3):
    """获取指定关键词和页码的数据（统一重试机制）
    
    Args:
        keyword: 搜索关键词
        page_number: 页码（从1开始）
        max_retries: 最大重试次数（已由装饰器处理）
    
    Returns:
        成功返回JSON数据，失败返回None
    """
    try:
        return _fetch_chinapost_data_internal(keyword, page_number)
    except Exception as e:
        logger.error(f"关键词 '{keyword}' 第{page_number}页失败: {e}")
        return None


# ==================== 数据处理函数 ====================
def clean_html(text):
    """去除HTML标签
    
    Args:
        text: 包含HTML标签的文本
    
    Returns:
        清理后的纯文本
    """
    if not text:
        return ""
    return re.sub(r'<.*?>', '', text).strip()


def is_within_one_month(date_str):
    """判断日期是否在一个月内
    
    Args:
        date_str: 日期字符串（格式：YYYY-MM-DD）
    
    Returns:
        True表示在一个月内，False表示不在或格式错误
    """
    if not date_str:
        return False
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj >= ONE_MONTH_AGO
    except ValueError:
        # 日期格式不匹配，返回False
        return False
    except Exception:
        return False


# ==================== 数据提取函数 ====================
def extract_chinapost_data(response_data, keyword):
    """从API响应中提取标题、时间和URL
    
    Args:
        response_data: API返回的JSON数据
        keyword: 当前搜索的关键词
    
    Returns:
        提取后的数据列表（只包含一个月内的数据），每个元素包含 title, url, time, source, keyword
    """
    extracted_data = []
    if not response_data or 'data' not in response_data:
        return extracted_data

    for item in response_data['data']:
        title = clean_html(item.get('title', ''))
        url = urljoin(HOST, item.get('url', ''))
        time_str = item.get('time', '')

        # 只保留一个月内的数据
        if time_str and is_within_one_month(time_str):
            raw_item = {
                'title': title,
                'url': url,
                'time': time_str,
                'source': "中国邮政",
                'keyword': keyword
            }
            # 使用统一的数据清洗函数
            cleaned_item = clean_data_item(raw_item)
            extracted_data.append(cleaned_item)
    return extracted_data


# ==================== 主流程 ====================
def main():
    """主函数：爬取所有关键词的数据并保存
    
    流程：
    1. 遍历每个关键词
    2. 获取每页数据（当前固定只爬取第1页）
    3. 提取并过滤数据（只保留一个月内的数据）
    4. 去重处理
    5. 保存到 outputs 目录
    
    注意：当前只爬取第1页，如需更多数据可修改页数列表
    """
    all_data = []
    seen_urls = set()

    # 步骤1：遍历每个关键词
    for keyword in KEYWORDS:
        logger.info(f"爬取关键词: {keyword}")
        
        # 步骤2：获取数据（当前固定只爬取第1页）
        # 注意：如需更多数据，可修改为 [1, 2, 3] 等
        for page in [1]:
            response_data = get_chinapost_data(keyword, page)
            if not response_data:
                continue

            # 步骤3：提取数据（自动过滤一个月内的数据）
            page_data = extract_chinapost_data(response_data, keyword)
            
            # 步骤4：去重并添加到总数据
            for item in page_data:
                if item['url'] not in seen_urls:
                    seen_urls.add(item['url'])
                    all_data.append(item)
        
        logger.info(f"关键词 '{keyword}' 完成，当前累计: {len(all_data)}")
        time.sleep(2)  # 关键词间隔，避免被限流

    # 步骤5：保存到 outputs 目录
    filename = "4_ChinaPost.json"
    # 使用 paths.py 中统一管理的 OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = OUTPUTS_DIR / filename
    
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info(f"结果：共 {len(all_data)} 条数据，已保存到 {save_path}")
    except Exception as e:
        logger.error(f"保存失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("中国邮政爬虫开始运行")
        logger.info("=" * 50)
        main()
        logger.info("=" * 50)
        logger.info("爬虫运行完成")
        logger.info("=" * 50)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)