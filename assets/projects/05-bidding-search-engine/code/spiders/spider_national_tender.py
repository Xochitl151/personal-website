"""
全国招标公告公示网站爬虫（Playwright 版本）

执行流程概览：
1. 依次访问多个关键词的列表页（关键词配置在 KEYWORDS 中）；
2. 优先监听 searchkeyword 接口，尝试解密 dataList 获取详情链接；
3. 接口失败时回退到 DOM 遍历，并尝试仿 Selenium 手法打开详情页；
4. 汇总所有关键词的结果，落地 JSON 文件，字段包含 title/url/time/source/keyword。
"""
import json
import os
import time
import random
import re
import base64
from urllib.parse import quote
from datetime import datetime
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Optional shared config (fallback to local defaults if missing)
try:
    from config import KEYWORDS as CFG_KEYWORDS, HEADLESS as CFG_HEADLESS, TIMEOUT_MS as CFG_TIMEOUT_MS, MAX_RETRIES as CFG_MAX_RETRIES, STORAGE_STATE as CFG_STORAGE_STATE
except Exception:
    CFG_KEYWORDS = ["专线", "短信", "智慧", "公有云", "私有云", "政务云", "云计算", "云"]
    CFG_HEADLESS = True
    CFG_TIMEOUT_MS = 60000
    CFG_MAX_RETRIES = 3
    CFG_STORAGE_STATE = "storage_state.json"

# 导入工具模块
from utils.logger import setup_logging, get_logger
from utils.retry import retry_on_exception
from paths import OUTPUTS_DIR

# ==================== 辅助工具函数 ====================

def des_ecb_pkcs7_decrypt_base64(cipher_b64: str, key_str: str = "***REDACTED***") -> str:
    """
    使用 DES-ECB + PKCS7 方式对 base64 密文解密，返回明文字符串
    密钥：***REDACTED***（8字节 DES）
    """
    try:
        from Crypto.Cipher import DES
        from Crypto.Util.Padding import unpad
    except Exception as e:
        raise RuntimeError("缺少pycryptodome依赖，请先安装: pip install pycryptodome") from e

    raw = base64.b64decode(cipher_b64)
    key = key_str.encode("utf-8")  # 密钥正好是8字节
    cipher = DES.new(key, DES.MODE_ECB)
    plain = cipher.decrypt(raw)
    # 使用 unpad(r, 8) 方式，与用户提供的代码一致
    plain = unpad(plain, 8)
    return plain.decode("utf-8", errors="ignore")

def try_parse_api_payload(txt: str) -> Optional[dict]:
    """
    尝试将接口返回解析为 dict：
    - 直接 JSON
    - JSON 中 data/t 字段是密文（base64），再解密
    - 文本整体是密文（base64），尝试多密钥解密
    """
    # 1) 直接 JSON
    try:
        obj = json.loads(txt)
        if isinstance(obj, dict):
            # 如果 data/t 是字符串，尝试当作密文解
            for enc_key in ("data", "t", "payload", "cipherText", "cipher"):
                enc_val = obj.get(enc_key)
                if isinstance(enc_val, str) and len(enc_val) > 50:
                    parsed = try_decrypt_and_parse(enc_val)
                    if parsed:
                        return parsed
            return obj
        if isinstance(obj, list):
            return {"data": {"dataList": obj}}
    except Exception:
        pass
    # 2) 文本整体当作密文
    return try_decrypt_and_parse(txt)

def try_decrypt_and_parse(enc_b64: str) -> Optional[dict]:
    """
    针对 base64 密文，尝试多密钥/多方式解密为 JSON 对象
    """
    candidate_keys = [
        "***REDACTED***",      # 已脱敏
        "***REDACTED***",      # 已脱敏
        "***REDACTED***",      # 已脱敏
    ]
    for key in candidate_keys:
        for variant in ("pkcs7_8", "pkcs7_block", "no_unpad"):
            try:
                from Crypto.Cipher import DES
                from Crypto.Util.Padding import unpad
                raw = base64.b64decode(enc_b64)
                k = key.encode("utf-8")[:8]
                cipher = DES.new(k, DES.MODE_ECB)
                plain = cipher.decrypt(raw)
                if variant == "pkcs7_8":
                    plain = unpad(plain, 8)
                elif variant == "pkcs7_block":
                    plain = unpad(plain, DES.block_size, style="pkcs7")
                # no_unpad: 原样
                s = plain.decode("utf-8", errors="ignore")
                if s and s.strip().startswith(("{", "[")):
                    try:
                        obj = json.loads(s)
                        logger.info(f"DES解密成功，key={key}, variant={variant}")
                        return obj if isinstance(obj, dict) else {"data": {"dataList": obj}}
                    except Exception:
                        # 解密成功但不是 JSON
                        logger.debug(f"解密为非JSON，前100字符: {s[:100]}")
                        continue
            except Exception as e:
                logger.debug(f"DES尝试失败: key={key}, variant={variant}, err={e}")
                continue
    logger.debug("多轮DES解密均失败")
    return None


# ==================== 配置和初始化 ====================

setup_logging(log_dir='logs')
logger = get_logger(__name__)

# 环境变量配置
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true' if os.getenv('HEADLESS') else CFG_HEADLESS
TIMEOUT = int(os.getenv('PLAYWRIGHT_TIMEOUT', str(CFG_TIMEOUT_MS)))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', str(CFG_MAX_RETRIES)))
WAIT_TIME = int(os.getenv('WAIT_TIME', '15'))
STORAGE_STATE_PATH = os.getenv('STORAGE_STATE_PATH', CFG_STORAGE_STATE)  # 会话持久化文件
SOURCE_NAME = "全国招标公告公示"
KEYWORDS = CFG_KEYWORDS


# ==================== 页面加载函数 ====================

@retry_on_exception(
    max_attempts=MAX_RETRIES,
    delay=3.0,
    backoff=2.0,
    exceptions=(Exception, PlaywrightTimeoutError)
)
def load_page_with_retry(page, url, wait_time=WAIT_TIME):
    """加载页面（带重试机制）"""
    logger.debug(f"访问目标页面: {url}")
    try:
        # 对于前端SPA，networkidle 容易卡死，改为 domcontentloaded，并补充手动等待
        page.goto(url, wait_until='domcontentloaded', timeout=TIMEOUT)
        # 等待常见加载状态，避免路由未稳定
        try:
            page.wait_for_load_state('load', timeout=15000)
        except Exception:
            pass
        # 显式等待页面主容器或任一内容片段出现（容错）
        try:
            page.wait_for_selector("xpath=/html/body/div[1]/div/div[3]/div[2]/div[1]", timeout=20000)
        except Exception:
            # 容器可能变动，退而求其次等待任意列表项
            try:
                page.wait_for_selector("xpath=//div[contains(@class,'left_body')]", timeout=10000)
            except Exception:
                pass
        logger.debug(f"页面加载完成，等待 {wait_time} 秒确保内容渲染...")
        time.sleep(wait_time)
        
        # 随机滚动模拟用户行为
        scroll_times = random.randint(3, 8)
        for i in range(scroll_times):
            scroll_distance = random.randint(100, 300)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            time.sleep(random.uniform(0.5, 1.5))
        time.sleep(random.uniform(1, 2))
        
        logger.debug("页面加载完成，开始提取数据...")
        return True
    except PlaywrightTimeoutError as e:
        logger.debug(f"页面加载超时: {e}，将重试...")
        raise
    except Exception as e:
        logger.debug(f"页面加载失败: {e}")
        raise


# ==================== 数据提取函数 ====================

def extract_tender_info(page, keyword: str):
    """
    提取招标信息
    
    策略：
    1. 优先：监听 searchkeywordTitle 接口，DES解密获取 dataList，直接生成结果
    2. 回退：如果接口失败，通过点击标题元素在新标签页打开，读取URL获取uuid
    """
    tender_list = []
    collected_data_list = []  # 存储接口返回的 dataList
    
    try:
        # ========== 策略1：监听接口响应，尝试解密获取 dataList ==========
        def on_response(response):
            """监听网络响应，尝试解密 searchkeywordTitle 接口"""
            try:
                url = response.url or ""
                # 检查是否是目标接口：放宽匹配以提高命中
                looks_data_api = (
                    ("searchkeyword" in url) or
                    ("searchkeywordTitle" in url) or
                    ("bulletin" in url) or
                    ("list" in url) or
                    ("detail" in url) or
                    url.endswith(".json")
                )
                if not looks_data_api:
                    return
                
                try:
                    # 尝试获取响应文本（可能是加密的）
                    txt = response.text()
                    if not txt or len(txt) < 100:
                        return
                    
                    # 通用解析：支持JSON、JSON内密文、纯密文
                    data = try_parse_api_payload(txt)
                    if not data:
                        logger.debug(f"无法解析接口响应，前120字符: {txt[:120]}")
                        return
                    
                    # 提取 dataList
                    dl = None
                    if isinstance(data, dict):
                        # 常见结构 data.dataList
                        if isinstance(data.get("data"), dict) and isinstance(data["data"].get("dataList"), list):
                            dl = data["data"]["dataList"]
                        # 兼容 dataList / rows / list 直挂
                        elif isinstance(data.get("dataList"), list):
                            dl = data["dataList"]
                        elif isinstance(data.get("rows"), list):
                            dl = data["rows"]
                        elif isinstance(data.get("list"), list):
                            dl = data["list"]

                    if isinstance(dl, list) and len(dl) > 0:
                        collected_data_list.clear()
                        collected_data_list.extend(dl)
                        logger.debug(f"成功获取接口 dataList，共 {len(dl)} 条（keyword={keyword}）")
                        
                        # 调试文件：保存接口返回的原始 dataList 数据到 logs/dataList_latest.json
                        # 用途：便于调试和排查数据提取问题
                        # 注意：这是调试文件，可以手动删除，不影响程序运行
                        try:
                            os.makedirs('logs', exist_ok=True)
                            with open('logs/dataList_latest.json', 'w', encoding='utf-8') as f:
                                json.dump(dl, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug(f"处理接口响应失败: {e}")
            except Exception as e:
                logger.debug(f"监听响应出错: {e}")
        
        # 绑定监听器（需要在页面加载前绑定）
        page.on("response", on_response)
        
        # 刷新页面以触发接口请求（如果页面已加载）
        try:
            page.reload(wait_until='networkidle', timeout=TIMEOUT)
            time.sleep(5)  # 等待接口响应
        except Exception:
            pass
        
        # ========== 如果成功获取 dataList，直接生成结果 ==========
        if collected_data_list:
            logger.debug(f"使用接口 dataList 直接生成结果（{len(collected_data_list)} 条, keyword={keyword}）")
            for entry in collected_data_list:
                if not isinstance(entry, dict):
                    continue
                
                # 提取标题（去除HTML标签）
                raw_title = entry.get('noticeName') or entry.get('title') or entry.get('bulletinTitle') or ''
                title = re.sub(r"<[^>]+>", "", str(raw_title)).strip()
                if not title:
                    continue
                
                # 提取时间
                raw_time = entry.get('noticeSendTime') or entry.get('time') or entry.get('timeShow') or ''
                time_info = str(raw_time)[:10] if raw_time else "未提取"
                
                # 提取uuid（尝试多个可能的字段名）
                uuid = None
                # 先尝试常见的字段名
                for k in ('bulletinID', 'bulletinUuid', 'id', 'uuid', 'bulletinId', 'bulletin_id', 'noticeUuid', 'noticeId'):
                    v = entry.get(k)
                    if v:
                        v_str = str(v).strip()
                        # 检查是否是UUID格式（支持32位hex或带短横线）
                        if re.match(r'^([a-f0-9]{32}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$', v_str, re.IGNORECASE):
                            uuid = v_str
                            logger.debug(f"从字段 {k} 提取到UUID: {uuid}")
                            break
                
                # 如果还没找到，尝试遍历所有字段查找UUID格式的值
                if not uuid:
                    for k, v in entry.items():
                        if v and isinstance(v, (str, int)):
                            v_str = str(v).strip()
                            if re.match(r'^([a-f0-9]{32}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$', v_str, re.IGNORECASE):
                                uuid = v_str
                                logger.debug(f"从字段 {k} 提取到UUID: {uuid}")
                                break
                
                # 构建详情链接
                if uuid:
                    url = f"https://ctbpsp.com/#/bulletinDetail?uuid={uuid}&inpvalue=%E7%9F%AD%E4%BF%A1&dataSource=0&tenderAgency="
                    logger.debug(f"构建详情URL: {url[:80]}...")
                else:
                    url = f"https://ctbpsp.com/#/bulletinList?keyWords=%E7%9F%AD%E4%BF%A1&itemIndex={len(tender_list)}"
                    logger.debug(f"无法获取UUID，使用列表页URL。条目字段: {list(entry.keys())[:10]}")
                
                tender_list.append({
                    'title': title,
                    'url': url,
                    'time': time_info,
                    'source': SOURCE_NAME,
                    'keyword': keyword,
                })
            
            if tender_list:
                logger.debug(f"数据提取完成（接口方式），共找到 {len(tender_list)} 条记录，keyword={keyword}")
                return tender_list
        
        # ========== 策略2：回退到DOM提取 + 点击新标签页方式（类似5-selenium.py） ==========
        logger.debug(f"接口方式失败，回退到DOM提取方式... keyword={keyword}")
        
        container_xpath = "/html/body/div[1]/div/div[3]/div[2]/div[1]"
        try:
            page.wait_for_selector(f"xpath={container_xpath}", timeout=30000)
        except PlaywrightTimeoutError:
            logger.warning("容器元素未找到")
        
        item_index = 2
        max_items = 100
        
        while item_index <= max_items:
            try:
                item_xpath = f"{container_xpath}/div[{item_index}]"
                item_locator = page.locator(f"xpath={item_xpath}")
                
                if item_locator.count() == 0:
                    logger.debug(f"未找到第 {item_index} 个项目，停止提取")
                    break
                
                # 提取项目名称
                project_name_locator = page.locator(f"xpath={item_xpath}/p")
                project_name = ""
                try:
                    project_name_elements = project_name_locator.all()
                    for elem in project_name_elements:
                        try:
                            text = elem.inner_text(timeout=5000).strip()
                            if text:
                                project_name += text
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"提取项目名称失败: {e}")
                
                project_name = project_name.strip()
                if not project_name:
                    logger.debug(f"第 {item_index} 个项目名称为空，跳过")
                    item_index += 1
                    continue
                
                # 提取时间信息
                time_info = "未提取"
                try:
                    time_locator = page.locator(f"xpath={item_xpath}/div/span[4]")
                    if time_locator.count() > 0:
                        time_str = time_locator.first.inner_text(timeout=5000).strip()
                        if time_str.startswith("接收时间:"):
                            time_str = time_str[len("接收时间:"):].strip()
                        if time_str:
                            datetime.strptime(time_str, "%Y-%m-%d")
                            time_info = time_str
                except (ValueError, Exception):
                    pass
                
                # 提取详情链接：优先从 a[href] 直接取（参考 5-selenium.py 先读属性），不行再新标签页打开
                detail_link = "未提取"
                try:
                    # 优先使用 p.left_body_name，否则使用第一个 p 元素
                    title_locator = page.locator(f"xpath={item_xpath}//p[contains(@class,'left_body_name')]")
                    if title_locator.count() == 0 and project_name_locator.count() > 0:
                        title_locator = project_name_locator.first
                    elif title_locator.count() > 0:
                        title_locator = title_locator.first
                    else:
                        title_locator = None
                    
                    if title_locator:
                        # 先尝试直接读取最近的 a 标签 href
                        try:
                            href = page.evaluate("""(el) => {
                                const a = el.closest('a');
                                return a ? a.getAttribute('href') : null;
                            }""", title_locator)
                            if href and isinstance(href, str):
                                # 绝对或 hash 路由地址均可
                                if 'uuid=' in href or 'bulletinDetail' in href:
                                    # 规范化为绝对地址
                                    if href.startswith('#/'):
                                        href = f"https://ctbpsp.com/{href}"
                                    elif href.startswith('/#/'):
                                        href = f"https://ctbpsp.com{href}"
                                    detail_link = href
                        except Exception:
                            pass
                        
                        # 如果 href 未取到或无 uuid，再尝试在新标签页打开
                        if detail_link == "未提取":
                            # 设置在新标签页打开
                            try:
                                page.evaluate("""(el) => {
                                    let a = el.closest('a');
                                    if (a) { a.setAttribute('target','_blank'); }
                                }""", title_locator)
                            except Exception:
                                pass
                            
                            # 点击并等待新标签页打开
                            try:
                                with page.context.expect_page(timeout=5000) as new_page_info:
                                    # 使用 JS 触发 click，模拟 selenium 的 execute_script 点击
                                    page.evaluate("""(el) => el.click()""", title_locator)
                                new_page = new_page_info.value
                                new_page.wait_for_load_state('domcontentloaded', timeout=5000)
                                time.sleep(1.5)  # 等待路由稳定
                                new_url = new_page.url or ""
                                
                                # 从URL中提取uuid
                                if ('bulletinDetail' in new_url) and ('uuid=' in new_url):
                                    uuid_match = re.search(r'uuid=([a-f0-9\\-]{36}|[a-f0-9]{32})', new_url, re.IGNORECASE)
                                    if uuid_match:
                                        uuid = uuid_match.group(1)
                                        detail_link = f"https://ctbpsp.com/#/bulletinDetail?uuid={uuid}&inpvalue=%E7%9F%AD%E4%BF%A1&dataSource=0&tenderAgency="
                                    else:
                                        detail_link = new_url
                                elif new_url:
                                    detail_link = new_url
                                
                                new_page.close()
                            except Exception as e:
                                logger.debug(f"点击获取URL失败: {e}（可能遇到人机验证）")
                except Exception as e:
                    logger.debug(f"提取详情链接失败: {e}")
                
                # 如果仍然无法获取，使用列表页URL
                if detail_link == "未提取":
                    detail_link = "https://ctbpsp.com/#/bulletinList?keyWords=%E7%9F%AD%E4%BF%A1"
                
                tender_list.append({
                    'title': project_name,
                    'url': detail_link,
                    'time': time_info,
                    'source': SOURCE_NAME,
                    'keyword': keyword,
                })
                
                logger.debug(f"提取项目 {item_index}: {project_name[:50]}...")
                item_index += 1
                time.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"提取第 {item_index} 个项目时出错: {e}，继续下一个...")
                item_index += 1
                continue
        
        # 移除监听器
        try:
            page.off("response", on_response)
        except Exception:
            pass
        
        logger.debug(f"数据提取完成，共找到 {len(tender_list)} 条记录，keyword={keyword}")
        return tender_list
        
    except Exception as e:
        error_msg = f"数据提取失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return []


# ==================== 保存函数 ====================

def save_to_json(tender_list, filename="5_NationalTender.json"):
    """保存数据到JSON文件"""
    if not tender_list:
        logger.debug("无有效数据可保存")
        return False
    
    try:
        # 使用 paths.py 中统一管理的 OUTPUTS_DIR
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        save_path = OUTPUTS_DIR / filename
        if os.path.exists(save_path):
            os.remove(save_path)
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(tender_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到 {save_path}")
        return True
    except Exception as e:
        error_msg = f"保存文件失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False


# ==================== 主函数 ====================

def main():
    """主函数"""
    logger.debug("=== 招标信息爬虫启动 ===")
    aggregated_results = []
    
    browser = None
    context = None
    try:
        with sync_playwright() as p:
            logger.debug(f"启动浏览器（headless={HEADLESS}）...")
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ] if HEADLESS else []
            )
            
            # 创建上下文（加载会话文件以减少验证）
            context_kwargs = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'locale': 'zh-CN',
                'timezone_id': 'Asia/Shanghai',
            }
            if os.path.exists(STORAGE_STATE_PATH):
                logger.debug(f"加载会话文件: {STORAGE_STATE_PATH}")
                context_kwargs['storage_state'] = STORAGE_STATE_PATH
            
            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            
            # 防检测
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                delete navigator.webdriver;
            """)
            
            try:
                # 逐个关键词爬取
                for keyword in KEYWORDS:
                    target_url = f"https://ctbpsp.com/#/bulletinList?keyWords={quote(keyword)}"
                    logger.info(f"开始: {keyword}")
                    
                    try:
                        load_page_with_retry(page, target_url, wait_time=WAIT_TIME)
                        keyword_results = extract_tender_info(page, keyword)
                        aggregated_results.extend(keyword_results)
                        logger.info(f"结束: {keyword}，本次 {len(keyword_results)} 条")
                    except Exception as kw_err:
                        logger.error(f"关键词 {keyword} 处理失败: {kw_err}", exc_info=True)
                        continue
                
                # 保存汇总数据
                if aggregated_results:
                    save_to_json(aggregated_results)
                    return True
                logger.debug("未提取到有效招标信息")
                return False
                    
            except Exception as e:
                logger.error(f"爬取过程出错: {e}", exc_info=True)
                return False
            finally:
                logger.debug("关闭浏览器...")
                # 保存会话（便于下次复用，减少验证）
                try:
                    if context:
                        context.storage_state(path=STORAGE_STATE_PATH)
                        logger.debug(f"已保存会话到: {STORAGE_STATE_PATH}")
                except Exception as e:
                    logger.debug(f"保存会话失败: {e}")
                if browser:
                    browser.close()
                    
    except Exception as e:
        logger.error(f"爬取过程中发生严重错误: {e}", exc_info=True)
        if browser:
            try:
                browser.close()
            except:
                pass
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        exit(1)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        exit(1)
