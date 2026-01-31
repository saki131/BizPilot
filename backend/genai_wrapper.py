import os
import json
import logging
import time

try:
    import google.genai as genai_new
    HAS_GENAI_NEW = True
except Exception:
    genai_new = None
    HAS_GENAI_NEW = False

try:
    import google.generativeai as genai_legacy
    HAS_GENAI_LEGACY = True
except Exception:
    genai_legacy = None
    HAS_GENAI_LEGACY = False

logger = logging.getLogger(__name__)

# Global state for API key rotation
_API_KEYS = []
_CURRENT_KEY_INDEX = 0
_FAILED_KEYS = set()  # Track keys that have failed


def set_api_keys(api_keys: list[str]):
    """Set multiple API keys for rotation."""
    global _API_KEYS, _CURRENT_KEY_INDEX, _FAILED_KEYS
    _API_KEYS = [key for key in api_keys if key]
    _CURRENT_KEY_INDEX = 0
    _FAILED_KEYS = set()
    print(f"[DEBUG genai_wrapper] Loaded {len(_API_KEYS)} API keys for rotation")


def get_next_api_key() -> str:
    """Get next available API key, skipping failed ones."""
    global _CURRENT_KEY_INDEX
    
    if not _API_KEYS:
        raise RuntimeError("No API keys configured")
    
    # Try all keys once
    attempts = 0
    while attempts < len(_API_KEYS):
        key = _API_KEYS[_CURRENT_KEY_INDEX]
        
        # Skip failed keys if we haven't exhausted all options
        if key not in _FAILED_KEYS or attempts >= len(_API_KEYS) - len(_FAILED_KEYS):
            return key
        
        _CURRENT_KEY_INDEX = (_CURRENT_KEY_INDEX + 1) % len(_API_KEYS)
        attempts += 1
    
    # All keys have failed, clear failed set and try again
    print("[WARN genai_wrapper] All API keys have failed, resetting failed key tracking")
    _FAILED_KEYS.clear()
    return _API_KEYS[_CURRENT_KEY_INDEX]


def mark_key_as_failed(api_key: str):
    """Mark an API key as failed."""
    global _CURRENT_KEY_INDEX
    _FAILED_KEYS.add(api_key)
    print(f"[WARN genai_wrapper] Marked API key ...{api_key[-10:]} as failed ({len(_FAILED_KEYS)}/{len(_API_KEYS)} failed)")
    
    # Move to next key
    _CURRENT_KEY_INDEX = (_CURRENT_KEY_INDEX + 1) % len(_API_KEYS)


def is_quota_exceeded_error(error: Exception) -> bool:
    """Check if error is due to quota/rate limit exceeded."""
    error_str = str(error).lower()
    quota_keywords = [
        "quota",
        "rate limit",
        "resource exhausted",
        "429",
        "too many requests",
        "limit exceeded",
    ]
    return any(keyword in error_str for keyword in quota_keywords)


def configure(api_key: str):
    """Configure available GenAI client. Prefer new `google.genai` if installed.

    If neither package is installed, this function is a no-op and later calls
    will raise a clear error.
    """
    # Always override GOOGLE_API_KEY environment variable to ensure consistent API key usage
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key  # Also set GEMINI_API_KEY for consistency
        print(f"[DEBUG genai_wrapper] Set GOOGLE_API_KEY and GEMINI_API_KEY to ...{api_key[-10:]}")
    
    if HAS_GENAI_NEW:
        # also try to create a client instance if the SDK exposes Client
        try:
            global _GENAI_CLIENT
            _GENAI_CLIENT = genai_new.Client(api_key=api_key)
            print("[DEBUG genai_wrapper] Initialized google.genai Client")
        except Exception as e:
            _GENAI_CLIENT = None
            print(f"[DEBUG genai_wrapper] google.genai Client init failed: {e}, will use environment-based auth")
    
    # Always configure legacy SDK if available (since we prefer it in generate_content_with_image)
    if HAS_GENAI_LEGACY:
        genai_legacy.configure(api_key=api_key)
        print(f"[DEBUG genai_wrapper] Configured google.generativeai (legacy) with key ending ...{api_key[-10:]}")
    
    if not HAS_GENAI_NEW and not HAS_GENAI_LEGACY:
        print("[DEBUG genai_wrapper] No GenAI SDK installed!")


class GenAIResponse:
    def __init__(self, text: str):
        self.text = text


def generate_content_with_image(model_name: str, prompt: str, image_b64: str, max_retries: int = None):
    """Generate content using available GenAI SDK with automatic API key rotation.

    Returns a GenAIResponse-like object with `.text` containing the model output.
    The function attempts multiple common client interfaces and normalizes
    the returned text. It raises a clear error if no supported SDK is found.
    
    If max_retries is None, will try all available API keys once.
    """
    if max_retries is None:
        max_retries = len(_API_KEYS) if _API_KEYS else 1
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Get current API key
            if _API_KEYS:
                current_key = get_next_api_key()
                configure(current_key)
                print(f"[DEBUG genai_wrapper] Attempt {attempt + 1}/{max_retries} with key ...{current_key[-10:]}")
            
            # Prefer legacy SDK (more stable) until google.genai API is confirmed working
            if HAS_GENAI_LEGACY and genai_legacy is not None:
                try:
                    model = genai_legacy.GenerativeModel(model_name)
                    response = model.generate_content([
                        prompt,
                        {
                            "mime_type": "image/jpeg",
                            "data": image_b64,
                        },
                    ])
                    print(f"[DEBUG genai_wrapper] Successfully generated content with key ...{current_key[-10:]}")
                    return response
                except Exception as e:
                    # Check if this is a quota error
                    if is_quota_exceeded_error(e):
                        logger.warning(f"Quota exceeded for API key ...{current_key[-10:]}, trying next key")
                        mark_key_as_failed(current_key)
                        last_error = e
                        
                        # If this was the last retry, raise the error
                        if attempt >= max_retries - 1:
                            raise
                        
                        # Wait a bit before retrying with next key
                        time.sleep(1)
                        continue
                    else:
                        # Non-quota error, raise immediately
                        logger.exception("google.generativeai call failed")
                        raise RuntimeError(f"google.generativeai call failed: {e}")

            # Try new SDK if legacy not available
            if HAS_GENAI_NEW and genai_new is not None:
                try:
                    # decode base64 image to bytes
                    import base64 as _b64
                    image_bytes = _b64.b64decode(image_b64)

                    # use existing client if configured, else create one
                    client = globals().get("_GENAI_CLIENT")
                    if client is None:
                        try:
                            client = genai_new.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
                        except Exception:
                            client = genai_new.Client()

                    # Call the recommended generate API: model + input with text and image
                    if hasattr(client, "generate"):
                        resp = client.generate(model=model_name, input=[{"content": prompt}, {"image": {"image_bytes": image_bytes}}])
                    elif hasattr(client, "generate_text"):
                        # Some versions separate text generation; fallback to text-only call
                        resp = client.generate_text(model=model_name, input=prompt)
                    else:
                        raise RuntimeError("google.genai client does not expose a supported generate method")

                    text = _extract_text_from_response(resp)
                    print(f"[DEBUG genai_wrapper] Successfully generated content with key ...{current_key[-10:]}")
                    return GenAIResponse(text=text)
                except Exception as e:
                    # Check if this is a quota error
                    if is_quota_exceeded_error(e):
                        logger.warning(f"Quota exceeded for API key ...{current_key[-10:]}, trying next key")
                        mark_key_as_failed(current_key)
                        last_error = e
                        
                        # If this was the last retry, raise the error
                        if attempt >= max_retries - 1:
                            raise
                        
                        # Wait a bit before retrying with next key
                        time.sleep(1)
                        continue
                    else:
                        # Non-quota error, raise immediately
                        logger.exception("google.genai call failed")
                        raise RuntimeError(f"google.genai call failed: {e}")
            
            # If we get here without SDK, raise error
            raise RuntimeError("No supported GenAI SDK installed (google.genai or google.generativeai).")
            
        except Exception as e:
            # If not a quota error or last attempt, raise
            if not is_quota_exceeded_error(e) or attempt >= max_retries - 1:
                raise
            last_error = e
    
    # If all retries exhausted, raise last error
    if last_error:
        raise last_error
    raise RuntimeError("All API keys exhausted")


def _extract_text_from_response(resp) -> str:
    """Attempt to extract human text from various response shapes."""
    try:
        # common: resp.text
        if hasattr(resp, "text") and resp.text:
            return str(resp.text)

        # google-genai may return an object with .output which is a list
        out = getattr(resp, "output", None)
        if out:
            try:
                first = out[0]
                # content may be attribute or dict
                if hasattr(first, "content"):
                    cont = first.content
                    if isinstance(cont, (list, tuple)) and len(cont) > 0:
                        item = cont[0]
                        if hasattr(item, "text"):
                            return str(item.text)
                        return str(item)
                    return str(cont)
                # fallback stringify
                return str(first)
            except Exception:
                pass

        # maybe dict-like
        if isinstance(resp, dict):
            # try common keys
            for k in ("text", "output_text", "content", "result"):
                if k in resp and resp[k]:
                    return str(resp[k])
            return json.dumps(resp)

        # fallback
        return str(resp)
    except Exception:
        return str(resp)
