"""
全国公共资源交易平台爬虫脚本
功能：通过API接口爬取交易公告数据
特点：直接请求API，无需处理JavaScript，速度快
"""
# ==================== 导入模块 ====================
import requests
import json
import os
import time
from datetime import datetime, timedelta

# 导入日志工具模块
from utils.logger import setup_logging, get_logger
# 导入数据处理工具模块
from utils.data_processor import clean_data_item
# 导入重试装饰器
from utils.retry import retry_on_exception
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

# ==================== 时间范围配置 ====================
# 计算时间范围：一个月前至今
today = datetime.now()
one_month_ago = today - timedelta(days=30)
start_date = one_month_ago.strftime('%Y-%m-%d')
end_date = today.strftime('%Y-%m-%d')

# ==================== API 配置 ====================
# 全国公共资源交易平台API地址
API_URL = 'https://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp'

# 请求头配置（模拟浏览器请求）
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://deal.ggzy.gov.cn',
    'Pragma': 'no-cache',
    'Referer': 'https://deal.ggzy.gov.cn/ds/deal/dealList.jsp?HEADER_DEAL_TYPE=02',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}


# ==================== 数据请求函数 ====================
def get_base_data():
    """构建基础请求参数
    
    返回包含时间范围、交易类型等基础参数的字典
    """
    return {
        'TIMEBEGIN_SHOW': start_date,
        'TIMEEND_SHOW': end_date,
        'TIMEBEGIN': start_date,
        'TIMEEND': end_date,
        'SOURCE_TYPE': '1',        # 数据源类型
        'DEAL_TIME': '04',          # 交易时间类型
        'DEAL_CLASSIFY': '02',      # 交易分类
        'DEAL_STAGE': '0200',       # 交易阶段
        'DEAL_PROVINCE': '0',       # 省份（0表示全部）
        'DEAL_CITY': '0',           # 城市（0表示全部）
        'DEAL_PLATFORM': '0',       # 交易平台（0表示全部）
        'BID_PLATFORM': '0',        # 招标平台（0表示全部）
        'DEAL_TRADE': '0',          # 交易行业（0表示全部）
        'isShowAll': '1',           # 是否显示全部
    }


@retry_on_exception(
    max_attempts=3,
    delay=2.0,
    backoff=2.0,
    exceptions=(requests.exceptions.RequestException, Exception)
)
def _fetch_deal_data_internal(keyword, page_number):
    """内部函数：实际执行API请求（使用重试装饰器）"""
    data = get_base_data()
    data['FINDTXT'] = keyword
    data['PAGENUMBER'] = str(page_number)
    
    response = requests.post(API_URL, headers=HEADERS, data=data, timeout=15)
    response.raise_for_status()
    return response.json()


def get_deal_data(keyword, page_number, max_retries=3):
    """获取指定关键词和页码的数据（统一重试机制）
    
    Args:
        keyword: 搜索关键词
        page_number: 页码（从1开始）
        max_retries: 最大重试次数（已由装饰器处理）
    
    Returns:
        成功返回JSON数据，失败返回None
    """
    try:
        return _fetch_deal_data_internal(keyword, page_number)
    except Exception as e:
        logger.error(f"关键词「{keyword}」请求第{page_number}页数据失败: {e}")
        return None


# ==================== 数据提取函数 ====================
def extract_data(response_data, keyword):
    """从API响应中提取标题、时间和URL
    
    Args:
        response_data: API返回的JSON数据
        keyword: 当前搜索的关键词
    
    Returns:
        提取后的数据列表，每个元素包含 title, url, time, source, keyword
    """
    if not response_data or 'data' not in response_data:
        return []

    extracted_data = []
    for item in response_data['data']:
        # 确保必要字段存在
        if 'title' in item and 'url' in item and 'timeShow' in item:
            raw_item = {
                'title': item['title'],
                'url': item['url'],
                'time': item['timeShow'],
                'source': "全国公共资源交易平台",
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
    2. 获取每页数据（当前固定获取2页）
    3. 提取并合并数据
    4. 去重处理
    5. 保存到 outputs 目录
    """
    all_data = []  # 存储所有关键词的所有数据

    # 步骤1：遍历每个关键词
    for keyword in KEYWORDS:
        logger.info(f"开始爬取关键词：{keyword}")

        # 步骤2：获取第1页和第2页的数据
        # 注意：当前固定只爬取2页，如需更多数据可增加页数
        page_1_data = get_deal_data(keyword, 1)
        time.sleep(2)  # 请求间隔，避免被限流
        
        page_2_data = get_deal_data(keyword, 2)
        time.sleep(2)  # 请求间隔

        # 步骤3：提取数据
        page_1_extracted = extract_data(page_1_data, keyword) if page_1_data else []
        page_2_extracted = extract_data(page_2_data, keyword) if page_2_data else []

        # 合并当前关键词的数据
        keyword_data = page_1_extracted + page_2_extracted
        logger.info(f"关键词「{keyword}」获取到 {len(keyword_data)} 条数据")

        # 添加到总数据中
        all_data.extend(keyword_data)

    # 步骤4：去重处理（基于URL）
    unique_data = []
    seen_urls = set()
    for item in all_data:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            unique_data.append(item)

    logger.info(f"去重后共获取到 {len(unique_data)} 条数据")

    # 步骤5：保存到 outputs 目录
    filename = "3_PublicResources.json"
    # 使用 paths.py 中统一管理的 OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = OUTPUTS_DIR / filename
    
    try:
        with open(save_path, "w", encoding="utf-8") as jsonfile:
            json.dump(unique_data, jsonfile, ensure_ascii=False, indent=4)
        logger.info(f"JSON文件已保存到: {save_path}")
    except Exception as e:
        logger.error(f"保存失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("全国公共资源交易平台爬虫开始运行")
        logger.info("=" * 50)
        main()
        logger.info("=" * 50)
        logger.info("爬虫运行完成")
        logger.info("=" * 50)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)