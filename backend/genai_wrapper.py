import os
import json
import logging

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


def configure(api_key: str):
    """Configure available GenAI client. Prefer new `google.genai` if installed.

    If neither package is installed, this function is a no-op and later calls
    will raise a clear error.
    """
    if HAS_GENAI_NEW:
        # google.genai typically uses environment-based auth; set env var as fallback
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
        # also try to create a client instance if the SDK exposes Client
        try:
            global _GENAI_CLIENT
            _GENAI_CLIENT = genai_new.Client(api_key=api_key)
            logger.info("Initialized google.genai Client")
        except Exception:
            _GENAI_CLIENT = None
            logger.info("google.genai available; will use environment-based auth")
    elif HAS_GENAI_LEGACY:
        genai_legacy.configure(api_key=api_key)
        logger.info("Configured google.generativeai (legacy)")
    else:
        logger.warning("No GenAI SDK installed (google.genai or google.generativeai). Calls will fail until installed.")


class GenAIResponse:
    def __init__(self, text: str):
        self.text = text


def generate_content_with_image(model_name: str, prompt: str, image_b64: str):
    """Generate content using available GenAI SDK.

    Returns a GenAIResponse-like object with `.text` containing the model output.
    The function attempts multiple common client interfaces and normalizes
    the returned text. It raises a clear error if no supported SDK is found.
    """
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
            return response
        except Exception as e:
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
            return GenAIResponse(text=text)
        except Exception as e:
            logger.exception("google.genai call failed")
            raise RuntimeError(f"google.genai call failed: {e}")

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
            return GenAIResponse(text=text)
        except Exception as e:
            logger.exception("google.genai call failed")
            raise RuntimeError(f"google.genai call failed: {e}")

    raise RuntimeError("No supported GenAI SDK installed (google.genai or google.generativeai).")


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
