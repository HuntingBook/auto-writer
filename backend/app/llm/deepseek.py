import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APIError

logger = logging.getLogger("deepseek")


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
def deepseek_chat(*, api_key: str, base_url: str, model: str, system: str, user: str) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
            timeout=120.0,
        )
        msg = resp.choices[0].message
        return msg.content or ""
    except Exception as e:
        logger.error(f"DeepSeek Chat API failed: {e}")
        raise


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
def deepseek_embed(*, api_key: str, base_url: str, model: str, text: str) -> list[float]:
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.embeddings.create(model=model, input=text, timeout=30.0)
        data = resp.data[0]
        return list(data.embedding)
    except Exception as e:
        logger.error(f"DeepSeek Embed API failed: {e}")
        raise
