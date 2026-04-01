"""Kimi API client for LLM interactions."""

import json
import asyncio
import base64
from typing import Optional, List, Dict, Any, Union
from common.core.config import settings
import httpx


class KimiClient:
    """Kimi API client with multimodal support (vision, file understanding)."""

    # 支持 image_url 的视觉模型
    # Kimi 视觉模型
    VISION_MODELS = {"kimi-k2.5", "kimi-k2.5-flash"}
    # Moonshot 视觉模型（支持 image_url 传入图片内容）
    VISION_MODELS |= {
        "moonshot-v1-8k-vision-preview",
        "moonshot-v1-32k-vision-preview",
        "moonshot-v1-128k-vision-preview",
    }

    # Supported file formats for file-extract
    SUPPORTED_FILE_EXTENSIONS = {
        ".pdf", ".txt", ".csv", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".md", ".jpeg", ".jpg", ".png", ".bmp", ".gif", ".svg", ".svgz", ".webp",
        ".ico", ".xbm", ".dib", ".pjp", ".tif", ".tiff", ".pjpeg", ".avif",
        ".dot", ".apng", ".epub", ".jfif", ".html", ".json", ".mobi", ".log",
        ".go", ".h", ".c", ".cpp", ".cxx", ".cc", ".cs", ".java", ".js", ".css",
        ".jsp", ".php", ".py", ".py3", ".asp", ".yaml", ".yml", ".ini", ".conf",
        ".ts", ".tsx"
    }

    # MIME type to extension mapping
    MIME_TO_EXT = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-powerpoint": ".ppt",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "text/html": ".html",
        "text/markdown": ".md",
        "text/x-python": ".py",
        "application/json": ".json",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }

    def __init__(self, api_key: str = None, endpoint: str = None, model: str = None):
        self.api_key = api_key or settings.KIMI_API_KEY
        self.endpoint = endpoint or settings.KIMI_API_ENDPOINT
        self.model = model or settings.KIMI_MODEL
        self.timeout = httpx.Timeout(settings.KIMI_TIMEOUT * 2.0, connect=10.0)
        self.max_retries = 5
        self.retry_delay = 1.0

    def is_vision_model(self, model: str = None) -> bool:
        """Check if the model supports vision/file understanding."""
        model = model or self.model
        return model in self.VISION_MODELS

    def is_image_url(self, url_or_data: str) -> bool:
        """Check if the content is a base64 image URL."""
        return url_or_data.startswith("data:image/") or url_or_data.startswith("http")

    def build_image_url_block(self, image_data: str, detail: str = "auto") -> Dict[str, Any]:
        """
        Build an image_url content block for vision.
        
        Args:
            image_data: Base64 encoded image data (with or without data URI prefix) or URL
            detail: Detail level - "low", "high", or "auto"
        
        Returns:
            Content block dict for the API
        """
        # Ensure proper base64 format
        if not image_data.startswith("data:") and not image_data.startswith("http"):
            image_data = f"data:image/jpeg;base64,{image_data}"
        
        return {
            "type": "image_url",
            "image_url": {
                "url": image_data,
                "detail": detail
            }
        }

    def build_file_block(self, file_id: str, type_: str = "file") -> Dict[str, Any]:
        """
        Build a file content block for file-extract understanding.
        
        Args:
            file_id: The file_id returned from upload_file()
            type_: "file" for regular files
        
        Returns:
            Content block dict for the API
        """
        return {
            "type": "file",
            "file": {
                "type": type_,
                "source": {
                    "type": "uploaded_file",
                    "file_id": file_id
                }
            }
        }

    def build_text_block(self, text: str) -> Dict[str, Any]:
        """Build a text content block."""
        return {
            "type": "text",
            "text": text
        }

    def parse_multimodal_messages(
        self,
        messages: List[Dict[str, Any]],
        model: str = None
    ) -> List[Dict[str, Any]]:
        """
        Parse and validate messages for multimodal content.
        
        For vision models, properly formats:
        - Base64 images: converted to image_url blocks
        - File references: converted to file blocks
        - Mixed content: combines text, image_url, and file blocks
        
        Args:
            messages: Raw messages that may contain base64 images or file references
            model: Model name (uses self.model if not provided)
        
        Returns:
            Properly formatted messages for the API
        """
        import logging
        logger = logging.getLogger(__name__)
        
        model = model or self.model
        use_vision = self.is_vision_model(model)
        
        if not use_vision:
            # For non-vision models, keep original format
            return messages
        
        parsed_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle string content (simple text)
            if isinstance(content, str):
                parsed_messages.append({"role": role, "content": content})
                continue
            
            # Handle list content (multimodal)
            if isinstance(content, list):
                parsed_content = []
                
                for item in content:
                    # Already a properly formatted block
                    if isinstance(item, dict):
                        item_type = item.get("type", "")
                        
                        # Validate existing blocks
                        if item_type == "image_url":
                            # Ensure detail field exists
                            img_url = item.get("image_url", {})
                            if isinstance(img_url, dict):
                                if "detail" not in img_url:
                                    img_url["detail"] = "auto"
                                parsed_content.append(item)
                            else:
                                # String URL, wrap it
                                parsed_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": img_url, "detail": "auto"}
                                })
                        
                        elif item_type == "file":
                            # Validate file block
                            if "file_id" in str(item):
                                parsed_content.append(item)
                        
                        elif item_type == "text":
                            parsed_content.append(item)
                        
                        else:
                            # Unknown type, keep as-is
                            parsed_content.append(item)
                    
                    # Handle raw base64 image data
                    elif isinstance(item, str):
                        if self.is_image_url(item):
                            parsed_content.append(self.build_image_url_block(item))
                        else:
                            # Plain text string
                            parsed_content.append(self.build_text_block(item))
                    
                    # Handle (text, image_url) tuples or tuples with file refs
                    elif isinstance(item, tuple):
                        parsed_content.append({"type": "text", "text": str(item[0])})
                        if len(item) > 1 and self.is_image_url(str(item[1])):
                            parsed_content.append(self.build_image_url_block(str(item[1])))
                
                parsed_messages.append({"role": role, "content": parsed_content})
            
            else:
                # Unknown content type, convert to string
                parsed_messages.append({"role": role, "content": str(content)})
        
        return parsed_messages

    async def upload_file(
        self,
        file_data: Union[str, bytes],
        mime_type: str,
        purpose: str,
        filename: str = None
    ) -> Optional[str]:
        """
        Upload file to Kimi API and return file_id.
        
        Supports three purpose types:
        - "file-extract": For document content extraction (PDF, DOC, images with OCR, etc.)
        - "image": For image understanding with vision model
        - "video": For video understanding with vision model
        
        Args:
            file_data: Base64 encoded string or raw bytes
            mime_type: MIME type of the file
            purpose: "file-extract" | "image" | "video"
            filename: Optional filename with extension
        
        Returns:
            file_id if successful, otherwise None
        """
        if not self.api_key:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Convert bytes to base64 if needed
        if isinstance(file_data, bytes):
            clean_data = base64.b64encode(file_data).decode()
        else:
            # Clean base64 data (remove prefix like data:xxx;base64,)
            clean_data = file_data
            if ',' in file_data:
                clean_data = file_data.split(',')[-1]
        
        # Decode to bytes for size check and upload
        try:
            file_bytes = base64.b64decode(clean_data)
        except Exception as e:
            logger.error(f"Base64 decode failed: {str(e)}")
            return None
        
        # Check file size (Kimi API limit: 30MB for files, 10MB for images/videos)
        file_size_mb = len(file_bytes) / (1024 * 1024)
        max_size = 30 if purpose == "file-extract" else 10
        if file_size_mb > max_size:
            logger.warning(f"File size {file_size_mb:.2f}MB exceeds limit {max_size}MB for purpose={purpose}")
            return None
        
        # Determine file extension
        ext = None
        if filename:
            import os
            _, ext = os.path.splitext(filename.lower())
        
        if not ext:
            ext = self.MIME_TO_EXT.get(mime_type, ".bin")
        
        # Ensure proper extension for images (Kimi prefers .jpg for JPEG)
        if mime_type == "image/jpeg" and ext == ".jpeg":
            ext = ".jpg"
        
        # Create multipart form-data
        from io import BytesIO
        file_obj = BytesIO(file_bytes)
        
        url = f"{self.endpoint}/files"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            "file": (f"file{ext}", file_obj, mime_type)
        }
        data = {"purpose": purpose}
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, files=files, data=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get("id")
                    logger.info(f"Kimi file upload success: file_id={file_id}, purpose={purpose}, size={file_size_mb:.2f}MB")
                    return file_id
                else:
                    logger.error(f"Kimi file upload failed: status={response.status_code}, detail={response.text}")
                    return None
        except Exception as e:
            logger.error(f"Kimi file upload exception: {str(e)}")
            return None

    async def upload_image_for_vision(
        self,
        image_data: Union[str, bytes],
        mime_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Upload image for vision understanding (kimi-k2.5).
        
        Args:
            image_data: Base64 encoded or raw bytes
            mime_type: MIME type (default: image/jpeg)
        
        Returns:
            file_id if successful, otherwise None
        """
        return await self.upload_file(image_data, mime_type, purpose="image")

    async def upload_video_for_vision(
        self,
        video_data: Union[str, bytes],
        mime_type: str = "video/mp4"
    ) -> Optional[str]:
        """
        Upload video for vision understanding (kimi-k2.5).
        
        Args:
            video_data: Base64 encoded or raw bytes
            mime_type: MIME type (default: video/mp4)
        
        Returns:
            file_id if successful, otherwise None
        """
        return await self.upload_file(video_data, mime_type, purpose="video")

    async def upload_document_for_extraction(
        self,
        file_data: Union[str, bytes],
        mime_type: str,
        filename: str = None
    ) -> Optional[str]:
        """
        Upload document for content extraction.
        
        Supports: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, images with OCR, etc.
        
        Args:
            file_data: Base64 encoded or raw bytes
            mime_type: MIME type of the document
            filename: Optional filename with extension
        
        Returns:
            file_id if successful, otherwise None
        """
        return await self.upload_file(file_data, mime_type, purpose="file-extract", filename=filename)

    async def upload_and_extract_file(
        self,
        file_data: Union[str, bytes],
        mime_type: str,
        filename: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload file and prepare for content extraction or vision understanding.
        
        Automatically determines the appropriate purpose:
        - Images (image/*): uploaded for vision understanding
        - Videos (video/*): uploaded for video understanding
        - Documents: uploaded for content extraction
        
        Args:
            file_data: Base64 encoded or raw bytes
            mime_type: MIME type of the file
            filename: Optional filename for better handling
        
        Returns:
            {
                "type": "file",
                "file_id": "xxx"  # Kimi returned file_id
            }
            Returns None if failed
        """
        if not self.api_key:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Determine purpose based on MIME type
        if mime_type.startswith("image/"):
            purpose = "image"  # For vision understanding
        elif mime_type.startswith("video/"):
            purpose = "video"
        else:
            purpose = "file-extract"  # For document extraction
        
        # Upload file to get file_id
        file_id = await self.upload_file(file_data, mime_type, purpose, filename)
        
        if file_id:
            logger.info(f"File upload success: file_id={file_id}, mime={mime_type}")
            return {
                "type": "file",
                "file_id": file_id
            }
        else:
            logger.warning(f"File upload failed")
            return None

    async def upload_and_preview_file(
        self,
        file_data: Union[str, bytes],
        mime_type: str,
        filename: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload file and immediately get preview/understanding.
        
        This is a convenience method that:
        1. Uploads the file
        2. Gets file content for preview
        3. Returns structured result
        
        Args:
            file_data: Base64 encoded or raw bytes
            mime_type: MIME type of the file
            filename: Optional filename
        
        Returns:
            {
                "file_id": "xxx",
                "content": "extracted text or description",
                "type": "file" | "image" | "video"
            }
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Upload first
        upload_result = await self.upload_and_extract_file(file_data, mime_type, filename)
        if not upload_result:
            return None
        
        file_id = upload_result.get("file_id")
        
        # Get content for file-extract type
        if mime_type.startswith("image/"):
            # For images, return success (vision model will handle)
            return {
                "file_id": file_id,
                "type": "image",
                "content": None  # Vision model will describe the image
            }
        elif mime_type.startswith("video/"):
            return {
                "file_id": file_id,
                "type": "video",
                "content": None  # Vision model will describe the video
            }
        else:
            # For documents, get extracted content
            content = await self.get_file_content(file_id)
            return {
                "file_id": file_id,
                "type": "document",
                "content": content
            }

    async def get_file_content(self, file_id: str) -> Optional[str]:
        """
        获取文件抽取内容（用于 file-extract 类型的文件）
        
        Args:
            file_id: 上传文件后获得的 file_id
        
        Returns:
            文件抽取内容（文本）如果成功，否则 None
        """
        if not self.api_key:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        content_url = f"{self.endpoint}/files/{file_id}/content"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(content_url, headers=headers)
                
                if response.status_code == 200:
                    file_content = response.text
                    logger.info(f"文件内容获取成功: file_id={file_id}, content_len={len(file_content)}")
                    return file_content
                else:
                    logger.warning(f"文件内容获取失败: status={response.status_code}, detail={response.text}")
                    return None
        except Exception as e:
            logger.error(f"文件内容获取异常: {str(e)}")
            return None

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Kimi API with retry logic.
        
        Supports multimodal messages with images and files for kimi-k2.5:
        - image_url blocks: For base64 encoded images or image URLs
        - file blocks: For uploaded file references (with file_id)
        - text blocks: For plain text
        
        Args:
            messages: List of message dicts with role and content
            temperature: Sampling temperature (kimi-k2.5 requires 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Penalty for repeated tokens
            presence_penalty: Penalty for new topics
            model: Model name (defaults to self.model)
            tools: Tool definitions for function calling
        
        Returns:
            API response dict with choices and content
        """
        if not self.api_key:
            return {"error": "Kimi API key not configured", "choices": [{"message": {"content": "API key not configured"}}]}

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        model = model or self.model
        is_kimi_k25 = model in {"kimi-k2.5", "kimi-k2.5-flash"}

        # kimi-k2.5 model requires temperature=1
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 1.0 if is_kimi_k25 else temperature,
            "max_tokens": max_tokens,
        }

        # Add optional parameters
        if top_p and top_p != 0.9 and not is_kimi_k25:
            payload["top_p"] = top_p
        elif is_kimi_k25:
            # kimi-k2.5 固定要求 top_p=0.95
            payload["top_p"] = 0.95
        if frequency_penalty != 0.0:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty != 0.0:
            payload["presence_penalty"] = presence_penalty

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Kimi API request: model={model}, messages_count={len(messages)}, has_tools={bool(tools)}")
        
        # Log message structure for debugging
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if isinstance(content, list):
                logger.info(f"Kimi API message {i}: role={role}, content_blocks={len(content)}")
                for j, block in enumerate(content):
                    if isinstance(block, dict):
                        block_type = block.get("type", "unknown")
                        if block_type == "image_url":
                            url_str = block.get("image_url", {}).get("url", "")
                            logger.info(f"  Block {j}: type=image_url, url_len={len(url_str)}")
                        elif block_type == "file":
                            file_info = block.get("file", {})
                            source = file_info.get("source", {})
                            file_id = source.get("file_id", "")
                            logger.info(f"  Block {j}: type=file, file_id={file_id}")
                        elif block_type == "text":
                            text_preview = block.get("text", "")[:100]
                            logger.info(f"  Block {j}: type=text, text={text_preview}...")
            else:
                content_preview = content[:100] if isinstance(content, str) else str(content)[:100]
                logger.info(f"Kimi API message {i}: role={role}, content={content_preview}...")
        
        # Retry logic for rate limits and transient errors
        last_error = None
        retry_delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        # Rate limit - retry with exponential backoff
                        last_error = f"API rate limit exceeded (429)"
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            return {"error": f"API error: {response.status_code} - Rate limit exceeded after {self.max_retries} retries", "detail": response.text}
                    else:
                        error_detail = response.text
                        logger.warning(f"Kimi API response: status={response.status_code}, detail={error_detail}")
                        
                        # For vision/file errors, provide more context
                        if "vision" in error_detail.lower() or "file" in error_detail.lower():
                            logger.warning(f"Kimi API multimodal error: model={model}, is_vision={self.is_vision_model(model)}")
                        
                        return {"error": f"API error: {response.status_code}", "detail": error_detail}

            except httpx.RequestError as e:
                last_error = f"Connection error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            except asyncio.TimeoutError:
                last_error = f"Request timeout: exceeded {self.timeout} seconds"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue

        logger.warning(f"Kimi API call failed: {last_error}, attempts={self.max_retries}")
        return {"error": last_error or "Unknown error"}

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """Send streaming chat completion request to Kimi API."""
        if not self.api_key:
            yield "data: {\"error\": \"API key not configured\"}\n\n"
            return

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        model = model or self.model
        is_kimi_k25 = model == "kimi-k2.5"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 1.0 if is_kimi_k25 else temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        if top_p and top_p != 0.9 and not is_kimi_k25:
            payload["top_p"] = top_p
        elif is_kimi_k25:
            # kimi-k2.5 固定要求 top_p=0.95
            payload["top_p"] = 0.95
        if frequency_penalty != 0.0:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty != 0.0:
            payload["presence_penalty"] = presence_penalty

        if tools:
            payload["tools"] = tools

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Kimi Stream API request: model={model}, messages_count={len(messages)}, has_tools={bool(tools)}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                yield line + "\n"
                            elif line == "data: [DONE]":
                                yield "data: [DONE]\n\n"
                                break
                    elif response.status_code == 429:
                        yield f"data: {{\"error\": \"API rate limit exceeded\"}}\n\n"
                    else:
                        yield f"data: {{\"error\": \"API error: {response.status_code}\"}}\n\n"
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    # ========== High-level helper methods ==========

    async def vision_chat(
        self,
        prompt: str,
        images: List[Union[str, bytes]] = None,
        files: List[str] = None,
        system_prompt: str = "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全、有帮助、准确的回答。同时，你会拒绝一切涉及恐怖主义、种族歧视、黄色暴力等问题的回答。",
        **kwargs
    ) -> str:
        """
        Convenience method for vision chat with images and/or uploaded files.
        
        Args:
            prompt: User's question/prompt
            images: List of base64 encoded images or raw bytes
            files: List of file_ids from uploaded files
            system_prompt: System prompt
            **kwargs: Additional parameters for chat()
        
        Returns:
            Model's response text
        """
        content_blocks = []
        
        if images:
            for img in images:
                if isinstance(img, bytes):
                    b64 = base64.b64encode(img).decode()
                    content_blocks.append(self.build_image_url_block(b64))
                else:
                    content_blocks.append(self.build_image_url_block(img))
        
        if files:
            for file_id in files:
                content_blocks.append(self.build_file_block(file_id))
        
        content_blocks.append(self.build_text_block(prompt))
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_blocks}
        ]
        
        result = await self.chat(messages, **kwargs)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return result.get("error", "Unknown error")

    async def document_chat(
        self,
        prompt: str,
        file_data: Union[str, bytes],
        mime_type: str,
        filename: str = None,
        system_prompt: str = "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全、有帮助、准确的回答。同时，你会拒绝一切涉及恐怖主义、种族歧视、黄色暴力等问题的回答。",
        **kwargs
    ) -> str:
        """
        Convenience method for document understanding.
        
        Uploads the document and asks the model to understand it.
        
        Args:
            prompt: User's question about the document
            file_data: Base64 encoded or raw bytes of the document
            mime_type: MIME type of the document
            filename: Optional filename with extension
            system_prompt: System prompt
            **kwargs: Additional parameters for chat()
        
        Returns:
            Model's response text
        """
        file_id = await self.upload_document_for_extraction(file_data, mime_type, filename)
        if not file_id:
            return "文件上传失败，请检查文件格式和大小"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                self.build_file_block(file_id),
                self.build_text_block(prompt)
            ]}
        ]
        
        result = await self.chat(messages, **kwargs)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return result.get("error", "Unknown error")

    async def extract_document_content(self, file_data: Union[str, bytes], mime_type: str) -> Optional[str]:
        """Extract text content from a document using file-extract."""
        file_id = await self.upload_document_for_extraction(file_data, mime_type)
        if not file_id:
            return None
        
        return await self.get_file_content(file_id)

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful teaching assistant.",
        **kwargs
    ) -> str:
        """Simple chat completion with single prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        result = await self.chat(messages, **kwargs)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return result.get("error", "Unknown error")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Send chat completion request with streaming response."""
        if not self.api_key:
            yield "API key not configured"
            return

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式输出
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # 去掉 "data: " 前缀
                                if data.strip() == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data)
                                    choices = chunk_data.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        yield f"Error: {response.status_code} - {error_text.decode()}"

        except httpx.RequestError as e:
            yield f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            yield f"Request timeout"
        except Exception as e:
            yield f"Error: {str(e)}"

    async def chat_stream_simple(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful teaching assistant.",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Simple streaming chat completion."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        async for chunk in self.chat_stream(messages, **kwargs):
            yield chunk


# Singleton instance
kimi_client = KimiClient()


async def get_kimi_response(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    **kwargs
) -> str:
    """Get response from Kimi API."""
    return await kimi_client.chat_completion(prompt, system_prompt, **kwargs)


async def get_kimi_stream(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    **kwargs
) -> AsyncGenerator[str, None]:
    """Get streaming response from Kimi API."""
    async for chunk in kimi_client.chat_stream_simple(prompt, system_prompt, **kwargs):
        yield chunk
