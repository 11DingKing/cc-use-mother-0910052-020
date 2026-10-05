"""业务模块说明。"""
import logging
import time
import requests
from typing import Optional
from app.core.config import settings, get_deepseek_config_from_db
from app.core.exceptions import DeepSeekAPIException

logger = logging.getLogger(__name__)

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1  # 基础延迟（秒）
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}  # 可重试的HTTP状态码


class DeepSeekService:
    """业务模块说明。"""
    
    @staticmethod
    def get_config():
        """业务模块说明。"""
        try:
            return get_deepseek_config_from_db()
        except Exception as e:
            logger.warning(f"从数据库读取配置失败，使用环境变量: {e}")
            return {
                "api_key": settings.DEEPSEEK_API_KEY,
                "api_url": settings.DEEPSEEK_API_URL,
                "timeout": settings.DEEPSEEK_TIMEOUT
            }
    
    @staticmethod
    def generate_text(prompt: str, max_tokens: int = 2000) -> str:
        """业务模块说明。"""
        config = DeepSeekService.get_config()
        
        if not config["api_key"]:
            raise DeepSeekAPIException("DeepSeek API密钥未配置")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"调用DeepSeek API生成文本 (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = requests.post(
                    config["api_url"],
                    headers=headers,
                    json=data,
                    timeout=config["timeout"]
                )
                
                # 处理HTTP错误
                if response.status_code != 200:
                    error_detail = ""
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", "")
                    except:
                        error_detail = response.text[:200]
                    
                    error_messages = {
                        401: "API密钥无效，请检查配置",
                        402: "API余额不足，请充值后重试",
                        403: "API访问被拒绝",
                        429: "请求过于频繁，请稍后重试",
                        500: "DeepSeek服务器错误",
                        503: "DeepSeek服务暂时不可用"
                    }
                    
                    msg = error_messages.get(response.status_code, f"API请求失败 ({response.status_code})")
                    if error_detail:
                        msg += f": {error_detail}"
                    
                    # 判断是否可重试
                    if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES - 1:
                        delay = RETRY_BASE_DELAY * (2 ** attempt)  # 指数退避
                        logger.warning(f"API请求失败 ({response.status_code})，{delay}秒后重试...")
                        time.sleep(delay)
                        last_exception = DeepSeekAPIException(msg)
                        continue
                    
                    raise DeepSeekAPIException(msg)
                
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    logger.info("DeepSeek API调用成功")
                    return content.strip()
                else:
                    raise DeepSeekAPIException(f"API返回格式异常: {result}")
                    
            except requests.exceptions.Timeout:
                last_exception = DeepSeekAPIException("DeepSeek API请求超时")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"API请求超时，{delay}秒后重试...")
                    time.sleep(delay)
                    continue
                raise last_exception
            except requests.exceptions.RequestException as e:
                last_exception = DeepSeekAPIException(f"DeepSeek API请求失败: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"API请求异常，{delay}秒后重试: {e}")
                    time.sleep(delay)
                    continue
                raise last_exception
            except DeepSeekAPIException:
                raise
            except Exception as e:
                logger.error(f"DeepSeek API调用异常: {e}", exc_info=True)
                raise DeepSeekAPIException(f"DeepSeek API调用异常: {str(e)}")
        
        # 所有重试都失败
        if last_exception:
            raise last_exception
        raise DeepSeekAPIException("DeepSeek API调用失败")
    
    @staticmethod
    def generate_title(keywords: list, knowledge_base_content: str = "", existing_titles: list = None) -> str:
        """业务模块说明。"""
        keywords_str = "、".join(keywords) if keywords else ""
        
        # SEO优化的提示词
        prompt = f"""请基于以下关键词生成一个SEO优化的文章标题。

关键词：{keywords_str}

要求：
1. 标题长度控制在30-60个字符
2. 自然包含所有关键词，避免关键词堆砌
3. 标题要有吸引力，能引起读者兴趣
4. 符合中文表达习惯
5. 避免使用特殊符号
6. 标题要有独特性和创意"""
        
        # 如果有已生成的标题，要求避免重复
        if existing_titles:
            titles_str = "\n".join([f"- {t}" for t in existing_titles])
            prompt += f"""

以下标题已经使用过，请生成一个完全不同的新标题（角度、表达方式都要不同）：
{titles_str}"""
        
        if knowledge_base_content:
            # 如果有关联知识库，添加相关内容摘要
            kb_summary = knowledge_base_content[:500] + "..." if len(knowledge_base_content) > 500 else knowledge_base_content
            prompt += f"\n\n参考内容摘要：{kb_summary}"
        
        prompt += "\n\n请只返回标题文本，不要包含其他说明。"
        
        return DeepSeekService.generate_text(prompt, max_tokens=100)
    
    @staticmethod
    def generate_content(title: str, keywords: list, knowledge_base_content: str = "") -> str:
        """业务模块说明。"""
        keywords_str = "、".join(keywords) if keywords else ""
        
        # SEO优化的提示词
        prompt = f"""请基于以下标题和关键词，生成一篇完整的、SEO优化的文章。

标题：{title}
关键词：{keywords_str}

要求：
1. 文章长度在800-1500字之间
2. 自然融入所有关键词，关键词密度控制在2%-5%
3. 文章结构清晰，包含引言、正文、结论
4. 内容要有价值，逻辑连贯，可读性强
5. 使用小标题（H2/H3）组织内容
6. 避免关键词堆砌，保持自然流畅
7. 使用HTML格式输出（段落用<p>标签，标题用<h2>、<h3>标签）

请直接输出文章内容，不要包含其他说明。"""
        
        if knowledge_base_content:
            # 添加知识库内容作为参考
            prompt += f"\n\n参考内容（请基于以下内容进行创作，但不要直接复制）：\n{knowledge_base_content[:2000]}"
        
        # max_tokens 说明：
        # - 中文字符约 1.5-2 tokens/字
        # - 目标 1500 字 ≈ 2250-3000 tokens
        # - 加上 HTML 标签开销，设置 4000 tokens 确保不截断
        return DeepSeekService.generate_text(prompt, max_tokens=4000)
    
    @staticmethod
    def generate_article(keywords: list, knowledge_base_content: str = "", existing_titles: list = None) -> dict:
        """业务模块说明。"""
        keywords_str = "、".join(keywords) if keywords else ""
        
        # Prompt 设计：要求 AI 先构思标题，再基于标题生成内容
        prompt = f"""请基于以下关键词，生成一篇完整的SEO优化文章。

【第一步】先构思一个吸引人的标题
【第二步】基于标题生成完整的文章内容

关键词：{keywords_str}

标题要求：
- 长度控制在30-60个字符
- 自然包含关键词，有吸引力
- 符合中文表达习惯

内容要求：
- 文章长度在800-1500字之间
- 自然融入关键词，密度控制在2%-5%
- 结构清晰，包含引言、正文、结论
- 使用小标题组织内容
- 使用HTML格式（段落用<p>标签，小标题用<h2>、<h3>标签）"""
        
        if existing_titles:
            titles_str = "\n".join([f"- {t}" for t in existing_titles[:5]])
            prompt += f"""

以下标题已使用，请生成完全不同的新标题：
{titles_str}"""
        
        if knowledge_base_content:
            kb_summary = knowledge_base_content[:1500] if len(knowledge_base_content) > 1500 else knowledge_base_content
            prompt += f"\n\n参考内容：\n{kb_summary}"
        
        prompt += """

请按以下格式输出：
【标题】你生成的标题
【内容】
你生成的HTML格式文章内容"""
        
        result = DeepSeekService.generate_text(prompt, max_tokens=4500)
        
        # 解析结果
        title = ""
        content = ""
        
        if "【标题】" in result and "【内容】" in result:
            parts = result.split("【内容】")
            title_part = parts[0]
            content = parts[1].strip() if len(parts) > 1 else ""
            
            # 提取标题
            if "【标题】" in title_part:
                title = title_part.split("【标题】")[1].strip()
        else:
            # 备用解析：第一行作为标题
            lines = result.strip().split("\n")
            title = lines[0].strip().lstrip("#").strip()
            content = "\n".join(lines[1:]).strip()
        
        # 清理标题
        title = title.replace("【", "").replace("】", "").strip()
        if not title:
            title = "未命名文章"
        
        return {"title": title, "content": content}
