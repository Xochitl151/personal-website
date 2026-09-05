"""
广东政府采购网爬虫脚本（Playwright版本）
功能：自动处理cookie和请求头，支持验证码识别，适用于需要JavaScript渲染的场景
"""
# ==================== 导入模块 ====================
import json
import os
import sys
import io
import contextlib
import base64
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from ddddocr import DdddOcr
from PIL import Image
import requests

# 设置 Windows 控制台输出编码为 UTF-8
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        os.system('chcp 65001 >nul 2>&1')
    except Exception:
        pass

# 抑制 onnxruntime 输出
os.environ.setdefault('ORT_DISABLE_COLOR', '1')
os.environ.setdefault('ORT_LOGGING_LEVEL', 'ERROR')
os.environ.setdefault('ORT_LOG_SEVERITY_LEVEL', '3')
os.environ.setdefault('COLOREDLOGS_DISABLE_COLORS', '1')
try:
    import onnxruntime as ort
    if hasattr(ort, 'set_default_logger_severity'):
        ort.set_default_logger_severity(ort.logging.LogSeverity.FATAL)
except Exception:
    pass

# 导入工具模块
from utils.logger import setup_logging, get_logger
from utils.ocr_manager import get_ocr_manager
from utils.proxy_pool import create_proxy_pool_from_config, ProxyPool
from paths import OUTPUTS_DIR

# ==================== 配置加载 ====================
# 从 config.py 加载配置，失败则使用默认值
try:
    from config import KEYWORDS as CFG_KEYWORDS, HEADLESS as CFG_HEADLESS, TIMEOUT_MS as CFG_TIMEOUT_MS, MAX_RETRIES as CFG_MAX_RETRIES
    from config import REQUEST_BLOCK_RESOURCE_TYPES as CFG_BLOCK_TYPES
    from config import PROXY_URL as CFG_PROXY_URL, PROXY_USERNAME as CFG_PROXY_USERNAME, PROXY_PASSWORD as CFG_PROXY_PASSWORD
except Exception:
    CFG_KEYWORDS = ['专线', '短信', '智慧', '公有云', '私有云', '政务云', '云']
    CFG_HEADLESS = True
    CFG_TIMEOUT_MS = 60000
    CFG_MAX_RETRIES = 3
    CFG_BLOCK_TYPES = ['image', 'font', 'media']
    CFG_PROXY_URL = ""
    CFG_PROXY_USERNAME = None
    CFG_PROXY_PASSWORD = None

# 初始化日志
requests.packages.urllib3.disable_warnings()

setup_logging(log_dir='logs')
logger = get_logger(__name__)

# 环境变量配置（优先级高于配置文件）
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true' if os.getenv('HEADLESS') else CFG_HEADLESS
TIMEOUT = int(os.getenv('PLAYWRIGHT_TIMEOUT', str(CFG_TIMEOUT_MS)))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', str(CFG_MAX_RETRIES)))
PROXY_URL = os.getenv('PROXY_URL', (CFG_PROXY_URL if 'CFG_PROXY_URL' in globals() else "")).strip()
PROXY_USERNAME = os.getenv('PROXY_USERNAME', (CFG_PROXY_USERNAME if 'CFG_PROXY_USERNAME' in globals() else None)) or None
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', (CFG_PROXY_PASSWORD if 'CFG_PROXY_PASSWORD' in globals() else None)) or None
BLOCK_RESOURCE_TYPES = CFG_BLOCK_TYPES
MAX_CAPTCHA_ATTEMPTS = int(os.getenv('GD_CAPTCHA_ATTEMPTS', '5'))
MAX_CAPTCHA_GLOBAL_FAILURES = int(os.getenv('GD_CAPTCHA_MAX_FAILURES', '20'))
CAPTCHA_FAILURE_BACKOFF_LIMIT = int(os.getenv('GD_CAPTCHA_BACKOFF_LIMIT', '60'))
LOG_VERBOSE = os.getenv('GD_LOG_VERBOSE', 'false').lower() == 'true'

# API 地址配置
API_BASE_URL = 'https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/info/selectInfoForIndex'
VERIFY_URL = 'https://gdgpo.czt.gd.gov.cn/gpcms/rest/web/v2/index/getVerify'
KEYWORDS = CFG_KEYWORDS

# PIL 兼容性处理
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS


# ==================== 自定义异常 ====================
class CaptchaFetchError(Exception):
    """验证码服务持续失败"""
    pass


# ==================== 工具函数 ====================
def log_fetch_warning(message: str) -> None:
    """
    控制日志噪音：在非调试模式下降级为 DEBUG，启用 GD_LOG_VERBOSE=true 可恢复 WARNING。
    """
    if LOG_VERBOSE:
        logger.warning(message)
    else:
        logger.debug(message)


@contextlib.contextmanager
def suppress_onnx_output():
    """抑制 onnxruntime 的输出"""
    import platform
    old_stderr = sys.stderr
    old_stderr_fileno = sys.stderr.fileno() if hasattr(sys.stderr, 'fileno') else None
    try:
        if platform.system() == 'Windows':
            null_file = open('NUL', 'w')
            sys.stderr = null_file
            if old_stderr_fileno is not None:
                try:
                    os.dup2(null_file.fileno(), old_stderr_fileno)
                except:
                    pass
        else:
            null_file = open('/dev/null', 'w')
            sys.stderr = null_file
            if old_stderr_fileno is not None:
                try:
                    os.dup2(null_file.fileno(), old_stderr_fileno)
                except:
                    pass
        yield
    finally:
        if 'null_file' in locals():
            null_file.close()
        sys.stderr = old_stderr


# 初始化 OCR 管理器（支持多个OCR服务，自动切换）
ocr_manager = get_ocr_manager()
logger.info(f"OCR管理器初始化完成，可用服务: {ocr_manager.get_stats()['available_services']}")

# 初始化代理池（如果配置了代理）
proxy_pool = create_proxy_pool_from_config()
if proxy_pool:
    logger.info(f"代理池初始化完成，可用代理: {proxy_pool.get_stats()['available_proxies']}")
else:
    logger.info("未配置代理池，使用直连")

REQUESTS_PROXY_CONFIG = None


def generate_detail_link(item):
    """为每个项目生成详情页面链接"""
    base_url = "https://gdgpo.czt.gd.gov.cn/maincms-web/noticeGd"
    params = {
        'type': 'notice',
        'id': item.get('id')
    }
    query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v])
    return f"{base_url}?{query_string}"


def format_time(raw_time):
    """将时间格式化为 YYYY-MM-DD 格式"""
    if not raw_time:
        return ""
    try:
        if len(raw_time) >= 10:
            date_part = raw_time[:10]
            datetime.strptime(date_part, "%Y-%m-%d")
            return date_part
        else:
            for fmt in ["%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(raw_time, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return raw_time
    except Exception:
        return raw_time


def format_project_data(item):
    """格式化项目数据为标准格式"""
    detail_link = generate_detail_link(item)
    formatted_time = format_time(item.get('noticeTime'))
    return {
        'title': item.get('title'),
        'url': detail_link,
        'time': formatted_time,
        'source': "广东政府采购网"
    }


# ==================== 验证码处理 ====================
def _fetch_verify_image_via_page(context):
    """在页面环境内通过 fetch 获取验证码图片（更贴近前端同源上下文）"""
    tmp_page = None
    try:
        tmp_page = context.new_page()
        tmp_page.goto('https://gdgpo.czt.gd.gov.cn/', wait_until='domcontentloaded', timeout=TIMEOUT)
        script = """
            (url) => fetch(url, { credentials: 'include', headers: { 'Accept': 'image/png,image/jpeg,image/*,*/*;q=0.8' } })
                .then(r => r.ok ? r.arrayBuffer() : Promise.reject(new Error('HTTP ' + r.status)))
                .then(buf => {
                    const bytes = new Uint8Array(buf);
                    let binary = '';
                    for (let i = 0; i < bytes.length; i++) { binary += String.fromCharCode(bytes[i]); }
                    return btoa(binary);
                })
        """
        timestamp = int(time.time() * 1000)
        verify_url = f"{VERIFY_URL}?{timestamp}"
        b64 = tmp_page.evaluate(script, verify_url)
        return base64.b64decode(b64)
    finally:
        try:
            if tmp_page:
                tmp_page.close()
        except Exception:
            pass


def _normalize_image_bytes(image_bytes: bytes) -> bytes:
    """校验并将图片统一转为PNG字节，过滤返回HTML/空内容等异常"""
    if not image_bytes or len(image_bytes) < 32:
        raise ValueError("验证码字节为空或过小")
    head = image_bytes[:32].lstrip()
    # 判定是否HTML/JSON等非图片内容
    if head.startswith(b'<') or head.startswith(b'{') or b'html' in image_bytes[:256].lower():
        raise ValueError("验证码返回的不是图片内容（疑似HTML/JSON）")
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            # 统一转换为RGB模式
            if im.mode in ('P', 'RGBA', 'LA'):
                im = im.convert('RGB')
            elif im.mode not in ('RGB', 'L'):
                im = im.convert('RGB')
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            return buf.getvalue()
    except Exception as e:
        raise ValueError(f"无法解析为图片: {e}")


captcha_failure_counter = 0
# 全局标记：是否检测到不需要验证码（在同一会话中复用）
_captcha_not_required = False
# 记录连续失败次数，用于快速失败
_captcha_consecutive_failures = 0


def get_verify_code(context, max_attempts=None):
    """获取并识别验证码
    
    策略：
    1. 优先使用页面内 fetch（更贴近同源上下文）
    2. 回退到 APIRequestContext.get
    3. 图片验证和规范化
    4. OCR识别（多次尝试取众数）
    5. 字符纠正常见混淆
    
    优化：如果连续失败2次，快速失败，避免浪费时间
    """
    global captcha_failure_counter, _captcha_consecutive_failures
    
    # 快速失败：如果连续失败2次，直接抛出异常
    if _captcha_consecutive_failures >= 2:
        raise CaptchaFetchError("验证码接口连续失败，可能已不可用，将尝试不带验证码请求")
    
    if max_attempts is None:
        max_attempts = MAX_CAPTCHA_ATTEMPTS

    backoff_seconds = 2
    for attempt in range(1, max_attempts + 1):
        timestamp = int(time.time() * 1000)
        verify_url = f"{VERIFY_URL}?{timestamp}"
        # 只在第一次尝试时记录debug，减少日志噪音
        if attempt == 1:
            logger.debug(f"尝试获取验证码，第 {attempt} 次")
        try:
            image_bytes = None
            socket_hangup_count = 0  # 记录socket hang up次数

            # 策略1：页面内 fetch（更贴近同源上下文，成功率更高）
            try:
                image_bytes = _fetch_verify_image_via_page(context)
            except Exception as e_page:
                error_msg = str(e_page).lower()
                if 'socket hang up' in error_msg or 'failed to fetch' in error_msg:
                    socket_hangup_count += 1
                # 只在第一次失败时记录warning，后续降级为debug
                msg = f"验证码页面内fetch异常: {e_page}"
                if attempt == 1:
                    log_fetch_warning(msg)
                else:
                    logger.debug(f"{msg}（第{attempt}次）")

            # 策略2：APIRequestContext.get（回退方案）
            if image_bytes is None:
                try:
                    cookies = context.cookies()
                    cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                    headers = {
                        'Accept': 'image/png,image/jpeg,image/*,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Referer': 'https://gdgpo.czt.gd.gov.cn/',
                        'Origin': 'https://gdgpo.czt.gd.gov.cn',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Cookie': cookie_str,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Sec-Fetch-Dest': 'image',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'same-origin',
                        'sec-ch-ua': '"Chromium";v="120", "Not=A?Brand";v="24", "Google Chrome";v="120"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                    }
                    response = context.request.get(verify_url, headers=headers, timeout=TIMEOUT)
                    if response.status == 200:
                        image_bytes = response.body()
                    else:
                        log_fetch_warning(f"验证码接口返回状态码 {response.status}")
                except Exception as e_req:
                    error_msg = str(e_req).lower()
                    if 'socket hang up' in error_msg:
                        socket_hangup_count += 1
                    # 只在第一次失败时记录warning
                    msg = f"验证码APIRequestContext.get异常: {e_req}"
                    if attempt == 1:
                        log_fetch_warning(msg)
                    else:
                        logger.debug(f"{msg}（第{attempt}次）")

            # 策略3：Requests 直接请求（最后的备用方案）
            if image_bytes is None:
                try:
                    cookies_dict = {c['name']: c['value'] for c in context.cookies()}
                    requests_headers = {
                        'Accept': 'image/png,image/jpeg,image/*,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Referer': 'https://gdgpo.czt.gd.gov.cn/',
                        'Origin': 'https://gdgpo.czt.gd.gov.cn',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    }
                    resp = requests.get(
                        verify_url,
                        headers=requests_headers,
                        cookies=cookies_dict,
                        timeout=15,
                        verify=False,
                        proxies=REQUESTS_PROXY_CONFIG,
                    )
                    if resp.status_code == 200:
                        image_bytes = resp.content
                    else:
                        log_fetch_warning(f"requests方式获取验证码失败，状态码 {resp.status_code}")
                except Exception as req_err:
                    error_msg = str(req_err).lower()
                    if 'socket hang up' in error_msg or 'remote end closed' in error_msg:
                        socket_hangup_count += 1
                    # 只在第一次失败时记录warning
                    msg = f"验证码 requests 备用方案异常: {req_err}"
                    if attempt == 1:
                        log_fetch_warning(msg)
                    else:
                        logger.debug(f"{msg}（第{attempt}次）")
            
            # 如果所有方法都返回socket hang up，快速失败
            if image_bytes is None and socket_hangup_count >= 2:
                _captcha_consecutive_failures += 1
                if _captcha_consecutive_failures >= 2:
                    logger.warning("验证码接口连续失败（socket hang up），可能已不可用，将尝试不带验证码")
                    raise CaptchaFetchError("验证码接口不可用，将尝试不带验证码请求")

            # 如果仍未获取到图片，刷新首页后重试
            if image_bytes is None:
                try:
                    tmp_page = context.new_page()
                    tmp_page.goto('https://gdgpo.czt.gd.gov.cn/', wait_until='domcontentloaded', timeout=TIMEOUT)
                    time.sleep(2)
                    tmp_page.close()
                except Exception:
                    pass
                msg = "无法获取验证码图片"
                if 'ECONNRESET' in msg or 'HTTP 400' in msg:
                    cool = min(max(backoff_seconds * 2, 10), 60)
                    logger.warning(f"网络不稳定，冷却 {cool}s 后重试...")
                    time.sleep(cool)
                    backoff_seconds = cool
                else:
                    time.sleep(2)
                continue

            # 步骤3：图片验证和规范化
            try:
                image_bytes = _normalize_image_bytes(image_bytes)
            except Exception as bad_img:
                logger.warning(f"验证码图片无效: {bad_img}，重试获取...")
                time.sleep(2)
                continue

            # 步骤4：OCR识别（使用OCR管理器，支持多服务投票）
            with suppress_onnx_output():
                code_raw = ocr_manager.recognize(image_bytes, use_voting=True)
            
            if not code_raw:
                logger.warning("OCR未识别出验证码，重试...")
                time.sleep(2)
                continue

            # 步骤5：字符纠正常见混淆（O->0, I->1等）并截断到4位
            def normalize_captcha(s: str) -> str:
                mapping = {
                    'O': '0', 'D': '0', 'Q': '0',
                    'I': '1', 'L': '1', 'T': '1',
                    'Z': '2',
                    'S': '5',
                    'B': '8'
                }
                buf = []
                for ch in s.upper():
                    if ch.isalnum():
                        buf.append(mapping.get(ch, ch))
                return ''.join(buf)

            code = normalize_captcha(code_raw)
            if len(code) >= 4:
                code = code[:4]
                logger.debug(f"识别到验证码: {code}")
                captcha_failure_counter = 0
                _captcha_consecutive_failures = 0  # 重置连续失败计数
                return code

            logger.warning(f"验证码识别结果异常: {code_raw}，重试...")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"获取验证码失败: {e}，重试...")
            # 异常时刷新上下文cookie
            try:
                tmp_page = context.new_page()
                tmp_page.goto('https://gdgpo.czt.gd.gov.cn/', wait_until='domcontentloaded', timeout=TIMEOUT)
                time.sleep(2)
                tmp_page.close()
            except Exception:
                pass
            msg = str(e)
            if 'ECONNRESET' in msg or 'Timeout' in msg:
                cool = min(max(backoff_seconds * 2, 10), 60)
                logger.warning(f"网络不稳定，冷却 {cool}s 后重试...")
                time.sleep(cool)
                backoff_seconds = cool
            else:
                time.sleep(2)

    captcha_failure_counter += 1
    if captcha_failure_counter >= MAX_CAPTCHA_GLOBAL_FAILURES:
        raise CaptchaFetchError(
            f"验证码接口连续失败已超过 {MAX_CAPTCHA_GLOBAL_FAILURES} 次，终止当前站点爬取"
        )
    raise CaptchaFetchError("无法获取有效验证码，请稍后重试或检查验证码接口")


# ==================== 数据获取 ====================
def get_last_month_to_now_time_range():
    """获取上个月1号到当前时间的时间范围"""
    now = datetime.now()
    if now.month == 1:
        last_month = 12
        last_month_year = now.year - 1
    else:
        last_month = now.month - 1
        last_month_year = now.year
    start_of_last_month = datetime(last_month_year, last_month, 1)
    start_time_str = start_of_last_month.strftime("%Y-%m-%d 00:00:00")
    end_time_str = now.strftime("%Y-%m-%d 23:59:59")
    return start_time_str, end_time_str


def fetch_api_data(page, params_template, dynamic_params=None):
    """使用Playwright request API请求数据"""
    logger.debug("使用Playwright request API请求数据（自动携带cookie和请求头）...")
    # 使用context的request API，它会自动携带cookie
    context = page.context

    # 构建请求头（参考2.py中的请求头）
    cookies = context.cookies()
    cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive',
        'Referer': 'https://gdgpo.czt.gd.gov.cn/',
        'Origin': 'https://gdgpo.czt.gd.gov.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie_str,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'sec-ch-ua': '"Chromium";v="120", "Not=A?Brand";v="24", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    if dynamic_params:
        if dynamic_params.get('sign'):
            headers['sign'] = dynamic_params['sign']
        if dynamic_params.get('nsssjss'):
            headers['nsssjss'] = dynamic_params['nsssjss']

    global _captcha_not_required, _captcha_consecutive_failures
    
    attempt = 0
    delay = 2.0
    last_exception = None

    while attempt < MAX_RETRIES:
        try:
            # 尝试获取验证码，如果失败则尝试不带验证码请求
            verify_code = None
            if not _captcha_not_required:
                try:
                    verify_code = get_verify_code(context)
                    # 如果成功获取验证码，重置连续失败计数
                    _captcha_consecutive_failures = 0
                except CaptchaFetchError as cap_err:
                    # 验证码获取失败，尝试不带验证码请求一次
                    logger.warning(f"验证码获取失败: {cap_err}，尝试不带验证码请求...")
                    _captcha_not_required = True
                    verify_code = ""  # 使用空字符串
            else:
                # 已经检测到不需要验证码，直接使用空字符串
                verify_code = ""
                logger.debug("跳过验证码（已检测到不需要验证码）")
            
            timestamp = int(time.time() * 1000)

            if dynamic_params and dynamic_params.get('time'):
                headers['time'] = str(dynamic_params['time'])
            else:
                headers['time'] = str(timestamp)

            if dynamic_params and dynamic_params.get('url'):
                headers['url'] = dynamic_params['url']
            else:
                headers['url'] = '/gpcms/rest/web/v2/info/selectInfoForIndex'

            params = params_template.copy()
            # 如果检测到不需要验证码，使用空字符串
            params['verifyCode'] = verify_code if verify_code is not None else ""
            params['_t'] = str(timestamp)

            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            api_url = f"{API_BASE_URL}?{query_string}"

            logger.debug(f"请求URL: {api_url}")
            response = context.request.get(api_url, headers=headers, timeout=TIMEOUT)

            if response.status != 200:
                # 403错误通常表示被拒绝访问或需要验证码，如果已经尝试过不带验证码，快速失败
                if response.status == 403 and _captcha_not_required:
                    logger.error(f"API返回403错误，且已尝试不带验证码，可能被反爬虫拦截或需要验证码，跳过当前请求")
                    raise Exception(f"API请求失败，状态码: {response.status} (可能被反爬虫拦截)")
                raise Exception(f"API请求失败，状态码: {response.status}")

            data = response.json()
            if not data:
                raise Exception("API返回空数据")

            if data.get('code') != '200':
                msg = str(data.get('msg', ''))
                if data.get('code') in ('4009', 4009) or ('验证码' in msg):
                    # 如果已经尝试过不带验证码，说明确实需要验证码
                    if _captcha_not_required:
                        logger.error("接口要求验证码，但验证码接口不可用，无法继续")
                        raise Exception(f"接口返回错误: {data.get('code')} - {data.get('msg')} (验证码接口不可用)")
                    
                    # 尝试重新获取验证码并重试
                    for retry_idx in range(2):
                        logger.warning("接口提示验证码无效，立即刷新验证码重试...")
                        new_ts = int(time.time() * 1000)
                        try:
                            new_code = get_verify_code(context)
                        except CaptchaFetchError:
                            # 验证码获取失败，尝试不带验证码
                            logger.warning("验证码获取失败，尝试不带验证码...")
                            new_code = ""
                            _captcha_not_required = True
                        except Exception:
                            time.sleep(1.0)
                            continue
                        params['verifyCode'] = new_code
                        params['_t'] = str(new_ts)
                        api_url = f"{API_BASE_URL}?" + '&'.join([f"{k}={v}" for k, v in params.items()])
                        headers['time'] = str(new_ts)
                        resp2 = context.request.get(api_url, headers=headers, timeout=TIMEOUT)
                        if resp2.status != 200:
                            continue
                        data2 = resp2.json()
                        if data2 and data2.get('code') == '200':
                            return data2
                        time.sleep(0.5)
                else:
                    raise Exception(f"接口返回错误: {data.get('code')} - {data.get('msg')}")

            return data

        except CaptchaFetchError:
            raise
        except Exception as e:
            last_exception = e
            error_msg = str(e)
            
            # 403错误且已尝试不带验证码，快速失败，不重试
            if '403' in error_msg and _captcha_not_required:
                logger.error(f"API返回403错误，且已尝试不带验证码，快速失败，不重试")
                raise Exception(f"API请求失败，状态码: 403 (可能被反爬虫拦截或需要验证码)")
            
            attempt += 1
            if attempt >= MAX_RETRIES:
                break
            logger.warning(f"请求 API 失败（第 {attempt} 次）：{e}，{delay:.1f}s 后重试...")
            time.sleep(delay)
            delay = min(delay * 2, 30)

    if last_exception:
        raise last_exception
    raise Exception("API请求失败")


# ==================== 数据保存 ====================
def save_to_json(json_data, filename="2_GuangzhouGovernment.json"):
    """保存数据到 outputs 目录下的JSON文件"""
    try:
        # 使用 paths.py 中统一管理的 OUTPUTS_DIR
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        save_path = OUTPUTS_DIR / filename
        with open(save_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, ensure_ascii=False, indent=4)
        logger.info(f"数据已保存到: {save_path}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return False


# ==================== 主流程 ====================
def crawl_with_playwright():
    """使用Playwright爬取数据，自动处理cookie和请求头
    
    流程：
    1. 初始化浏览器和上下文
    2. 访问首页获取cookie和token
    3. 遍历关键词请求API数据
    4. 格式化并保存数据
    """
    logger.info("开始爬取数据...")
    
    global REQUESTS_PROXY_CONFIG

    start_time, end_time = get_last_month_to_now_time_range()
    result_data = []
    seen_urls = set()
    keyword_stats = {}
    home_url = 'https://gdgpo.czt.gd.gov.cn/'
    browser = None

    def create_context(b):
        ctx = b.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            ignore_https_errors=True,
        )
        # 预置必要 cookie
        ctx.add_cookies([
            {'name': 'regionCode','value': '440001','domain': 'gdgpo.czt.gd.gov.cn','path': '/'},
            {'name': 'regionFullName','value': '%E7%9C%81%E6%9C%AC%E7%BA%A7','domain': 'gdgpo.czt.gd.gov.cn','path': '/'},
            {'name': 'regionRemark','value': '1','domain': 'gdgpo.czt.gd.gov.cn','path': '/'},
            {'name': 'arialoadData','value': 'false','domain': 'gdgpo.czt.gd.gov.cn','path': '/'},
            {'name': 'ariauseGraymode','value': 'false','domain': 'gdgpo.czt.gd.gov.cn','path': '/'},
        ])
        return ctx
    try:
        with sync_playwright() as p:
            # 启动浏览器（支持代理池）
            launch_kwargs = {'headless': HEADLESS, 'args': ['--ignore-certificate-errors']}
            
            # 从代理池获取代理（如果可用）
            current_proxy = None
            proxy_index = None
            requests_proxy_cfg = None
            if proxy_pool:
                current_proxy = proxy_pool.get_proxy(strategy='round_robin')
                if current_proxy:
                    proxy_cfg = {'server': current_proxy['url']}
                    if current_proxy.get('username'):
                        proxy_cfg['username'] = current_proxy['username']
                    if current_proxy.get('password'):
                        proxy_cfg['password'] = current_proxy['password']
                    launch_kwargs['proxy'] = proxy_cfg
                    proxy_index = current_proxy.get('_pool_index')
                    logger.info(f"使用代理池中的代理: {current_proxy['url']} (索引: {proxy_index})")
                    requests_proxy_cfg = {
                        'http': current_proxy['url'],
                        'https': current_proxy['url'],
                    }
            elif PROXY_URL:
                # 兼容旧配置（单一代理）
                proxy_server = PROXY_URL
                if not proxy_server.lower().startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                    proxy_server = f"http://{proxy_server}"
                proxy_cfg = {'server': proxy_server}
                if PROXY_USERNAME:
                    proxy_cfg['username'] = PROXY_USERNAME
                if PROXY_PASSWORD:
                    proxy_cfg['password'] = PROXY_PASSWORD
                launch_kwargs['proxy'] = proxy_cfg
                logger.info(f"使用单一代理: {proxy_server}")
                requests_proxy_cfg = {
                    'http': proxy_server,
                    'https': proxy_server,
                }
            
            REQUESTS_PROXY_CONFIG = requests_proxy_cfg
            
            browser = p.chromium.launch(**launch_kwargs)

            context = create_context(browser)
            page = context.new_page()
            
            try:
                logger.debug("步骤1: 访问首页以获取cookie...")
                # 使用route拦截请求，添加必要的请求头
                def handle_route(route):
                    """拦截请求并添加必要的请求头"""
                    headers = route.request.headers.copy()
                    # 添加必要的请求头
                    headers['sec-ch-ua'] = '"Chromium";v="120", "Not=A?Brand";v="24", "Google Chrome";v="120"'
                    headers['sec-ch-ua-mobile'] = '?0'
                    headers['sec-ch-ua-platform'] = '"Windows"'
                    # 添加time和url参数（如果需要）
                    current_time = int(datetime.now().timestamp() * 1000)
                    headers['time'] = str(current_time)
                    headers['url'] = '/gpcms/rest/web/v2/info/selectInfoForIndex'
                    route.continue_(headers=headers)
                
                # 设置路由拦截（接口补头）
                page.route("**/gpcms/rest/web/v2/info/selectInfoForIndex**", handle_route)

                # 通用资源拦截（减少首页加载压力，保留接口与验证码）
                def block_other_resources(route):
                    req = route.request
                    url = req.url
                    rtype = req.resource_type
                    if any(key in url for key in ["/gpcms/rest/web/v2/index/getVerify", "/gpcms/rest/web/v2/info/selectInfoForIndex"]):
                        return route.continue_()
                    if rtype in BLOCK_RESOURCE_TYPES:
                        return route.abort()
                    return route.continue_()
                page.route("**/*", block_other_resources)
                
                # 步骤2：访问首页获取cookie和token（带重试机制）
                logger.debug("访问首页以获取cookie和token...")
                max_home_retries = 3
                home_loaded = False
                for home_attempt in range(max_home_retries):
                    try:
                        page.goto(home_url, wait_until='domcontentloaded', timeout=TIMEOUT)
                        time.sleep(3)  # 等待页面完全加载和cookie设置
                        home_loaded = True
                        break
                    except Exception as home_err:
                        error_msg = str(home_err).lower()
                        is_network_error = any(keyword in error_msg for keyword in ['connection', 'reset', 'timeout', 'err_'])
                        
                        if is_network_error:
                            if home_attempt < max_home_retries - 1:
                                wait_time = (home_attempt + 1) * 5  # 5秒、10秒、15秒
                                logger.warning(
                                    f"访问首页失败（网络错误: {error_msg[:80]}...），"
                                    f"{wait_time}秒后重试 ({home_attempt + 1}/{max_home_retries})"
                                )
                                time.sleep(wait_time)
                                
                                # 如果使用了代理池，标记当前代理失败
                                if proxy_pool and proxy_index is not None:
                                    logger.warning(f"标记代理 {proxy_index} 为失败")
                                    proxy_pool.mark_failed(proxy_index)
                            else:
                                logger.error(f"访问首页失败，已重试 {max_home_retries} 次，放弃")
                                raise
                        else:
                            # 非网络错误（如404、403等），直接抛出
                            logger.error(f"访问首页时发生非网络错误: {home_err}")
                            raise
                
                if not home_loaded:
                    logger.error("无法访问首页，爬虫终止")
                    return False
                
                # 从页面中获取动态参数（sign、nsssjss等）
                try:
                    dynamic_params = page.evaluate("""
                        () => {
                            const params = {};
                            // 尝试从window对象中获取动态参数
                            if (window.sign) params.sign = window.sign;
                            if (window.nsssjss) params.nsssjss = window.nsssjss;
                            if (window.time) params.time = window.time;
                            if (window.url) params.url = window.url;
                            // 尝试从localStorage或sessionStorage获取
                            try {
                                if (localStorage.getItem('sign')) params.sign = localStorage.getItem('sign');
                                if (localStorage.getItem('nsssjss')) params.nsssjss = localStorage.getItem('nsssjss');
                            } catch(e) {}
                            return params;
                        }
                    """)
                    logger.debug(f"从页面获取的动态参数: {dynamic_params}")
                except Exception as e:
                    logger.debug(f"无法从页面获取动态参数: {e}")
                    dynamic_params = {}
                
                # 步骤3：遍历关键词请求API数据
                consecutive_403_errors = 0  # 记录连续403错误次数
                max_consecutive_403 = 3  # 连续3个关键词403错误则结束爬虫
                
                for keyword in KEYWORDS:
                    logger.debug(f"关键词 {keyword} 开始请求")
                    params_template = {
                        'title': keyword,
                        'region': '',
                        'siteId': 'cd64e06a-21a7-4620-aebc-0576bab7e07a',
                        'channel': 'fca71be5-fc0c-45db-96af-f513e9abda9d',
                        'currPage': 1,
                        'pageSize': 10,
                        'noticeType': '',
                        'regionCode': '',
                        'cityOrArea': '',
                        'purchaseManner': '',
                        'openTenderCode': '',
                        'purchaser': '',
                        'agency': '',
                        'purchaseNature': '',
                        'operationStartTime': start_time.replace(' ', '+'),
                        'operationEndTime': end_time.replace(' ', '+'),
                        'verifyCode': '',
                        'subChannel': 'false',
                        '_t': '',
                    }
                    
                    # 失败时重建 context 并对当前关键词重试一次（支持代理切换）
                    data = None
                    for attempt_ctx in range(2):
                        try:
                            data = fetch_api_data(page, params_template, dynamic_params)
                            # 请求成功，标记代理成功，重置403错误计数
                            if proxy_pool and proxy_index is not None:
                                proxy_pool.mark_success(proxy_index)
                            consecutive_403_errors = 0  # 成功请求，重置403错误计数
                            break
                        except CaptchaFetchError as cap_err:
                            logger.error(f"验证码服务异常，结束广东政府采购网爬虫: {cap_err}")
                            return False
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"关键词 {keyword} 请求失败: {e}")
                            
                            # 检测403错误
                            if '403' in error_msg or '反爬虫拦截' in error_msg:
                                consecutive_403_errors += 1
                                if consecutive_403_errors >= max_consecutive_403:
                                    logger.error(f"连续 {consecutive_403_errors} 个关键词返回403错误，可能被反爬虫拦截，结束爬虫")
                                    return False
                                logger.warning(f"检测到403错误（连续 {consecutive_403_errors}/{max_consecutive_403}），跳过当前关键词，不重试")
                                # 403错误通常重试也没用，直接跳过当前关键词
                                break
                            else:
                                # 非403错误，重置计数器
                                consecutive_403_errors = 0
                            
                            # 标记代理失败（如果是代理相关错误）
                            if proxy_pool and proxy_index is not None:
                                error_msg_lower = error_msg.lower()
                                if any(err_keyword in error_msg_lower for err_keyword in ['timeout', 'connection', 'proxy', 'certificate', 'reset']):
                                    proxy_pool.mark_failed(proxy_index)
                                    logger.warning(f"标记代理 {proxy_index} 为失败，将尝试切换代理")
                            if attempt_ctx == 0:
                                logger.info("重建浏览器上下文以恢复 Cookie/指纹后重试当前关键词...")
                                try:
                                    try:
                                        page.close()
                                    except Exception:
                                        pass
                                    try:
                                        context.close()
                                    except Exception:
                                        pass
                                    context = create_context(browser)
                                    page = context.new_page()
                                    # 回到首页刷新 Cookie/Token
                                    page.goto(home_url, wait_until='domcontentloaded', timeout=TIMEOUT)
                                    time.sleep(2)
                                    # 重新设置路由拦截
                                    page.route("**/gpcms/rest/web/v2/info/selectInfoForIndex**", handle_route)
                                    # 重新尝试从页面取动态参数
                                    try:
                                        dynamic_params = page.evaluate("""
                                            () => {
                                                const params = {};
                                                if (window.sign) params.sign = window.sign;
                                                if (window.nsssjss) params.nsssjss = window.nsssjss;
                                                if (window.time) params.time = window.time;
                                                if (window.url) params.url = window.url;
                                                try {
                                                    if (localStorage.getItem('sign')) params.sign = localStorage.getItem('sign');
                                                    if (localStorage.getItem('nsssjss')) params.nsssjss = localStorage.getItem('nsssjss');
                                                } catch(e) {}
                                                return params;
                                            }
                                        """)
                                    except Exception:
                                        dynamic_params = {}
                                    time.sleep(2)
                                    continue
                                except Exception as e_ctx:
                                    logger.warning(f"重建上下文失败: {e_ctx}")
                            # 第二次或重建失败，放弃该关键词
                            time.sleep(6)
                            break

                    if not data:
                        continue
                    
                    logger.debug("处理返回数据...")
                    if data.get('code') == '200':
                        rows = data.get('data', {}).get('rows', [])
                        total = data.get('data', {}).get('total', 0)
                        keyword_stats[keyword] = total
                        logger.debug(f"关键词 {keyword} 共找到 {total} 个项目")
                        
                        for item in rows:
                            project_data = format_project_data(item)
                            if project_data['url'] in seen_urls:
                                continue
                            project_data['keyword'] = keyword
                            result_data.append(project_data)
                            seen_urls.add(project_data['url'])
                    else:
                        logger.error(f"关键词 {keyword} 请求失败，错误码: {data.get('code')}，错误信息: {data.get('msg')}")
                    
                    time.sleep(6)
                
                # 步骤4：保存数据到 outputs 目录
                if result_data:
                    if save_to_json(result_data):
                        summary = ", ".join([f"{k}={v}" for k, v in keyword_stats.items()])
                        logger.info(f"完成！保存 {len(result_data)} 条记录。统计：{summary}")
                        return True
                    else:
                        logger.error("保存数据失败")
                        return False
                else:
                    logger.warning("没有数据可保存")
                    return False
                    
            except PlaywrightTimeoutError as e:
                logger.error(f"页面加载超时: {e}")
                return False
            except Exception as e:
                logger.error(f"处理数据时发生错误: {e}", exc_info=True)
                return False
            finally:
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


if __name__ == '__main__':
    try:
        success = crawl_with_playwright()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        exit(1)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        exit(1)
