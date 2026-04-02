"""代码执行接口 - 沙箱安全执行 Python/Java 代码"""
import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from common.models.response import ResponseModel

# 获取 Python 可执行文件绝对路径（Windows 必须用完整路径）
PYTHON_EXE = sys.executable
JAVA_CMD = shutil.which("javac") or "javac"
JAVA_RUN = shutil.which("java") or "java"

router = APIRouter(prefix="/code", tags=["代码执行"])
logger = logging.getLogger(__name__)

# 超时时间（秒）
EXEC_TIMEOUT = 30
# 允许的代码最大字符数
MAX_CODE_LENGTH = 50000
# 临时文件保留时间（秒）
TEMP_FILE_TTL = 300


class CodeExecuteRequest(BaseModel):
    code: str = Field(..., description="源代码")
    language: Literal["python", "java"] = Field(..., description="语言类型")
    timeout: int = Field(default=15, ge=1, le=60, description="超时时间(秒)")
    stdin: Optional[str] = Field(default=None, description="标准输入")


class CodeExecuteResponse(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None


def _sanitize_filename(name: str) -> str:
    """生成安全文件名"""
    return hashlib.sha256(name.encode()).hexdigest()[:16]


async def _run_process(
    cmd: list[str],
    cwd: str,
    stdin_data: Optional[str] = None,
    timeout: int = 30
) -> tuple[int, str, str]:
    """异步执行进程，返回 (exit_code, stdout, stderr)"""

    def _sync_run():
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = p.communicate(
            input=stdin_data.encode("utf-8") if stdin_data else None,
            timeout=timeout
        )
        return p.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_sync_run),
            timeout=timeout + 5
        )
    except asyncio.TimeoutError:
        return (-1, "", f"执行超时（{timeout}秒）")
    except Exception as e:
        logger.error(f"[code/execute] subprocess spawn error: cmd={cmd}, cwd={cwd}, error={type(e).__name__}: {str(e)}")
        return (-1, "", f"执行错误: {type(e).__name__}: {str(e)}")


# pygame 2.6.1 + Python 3.13 on Windows: SysFont crashes on int registry values.
# Patch pygame.font to fall back to the default font when this happens.
PYGAME_PATCH = '''
try:
    import pygame.font
    _orig_sf = pygame.font.SysFont
    def _safe_sf(name, size, bold=False, italic=False):
        try:
            return _orig_sf(name, size, bold, italic)
        except (TypeError, OSError):
            return pygame.font.Font(None, size)
    pygame.font.SysFont = _safe_sf
except Exception:
    pass
'''

async def execute_python(code: str, stdin: Optional[str] = None, timeout: int = 15) -> CodeExecuteResponse:
    """执行 Python 代码（subprocess）"""
    start = datetime.now()
    sanitized = _sanitize_filename(code[:100])
    tmp_dir = tempfile.mkdtemp(prefix=f"py_{sanitized}_")
    try:
        code_path = Path(tmp_dir) / "main.py"
        code_path.write_text(PYGAME_PATCH + "\n" + code, encoding="utf-8")
        exit_code, stdout, stderr = await _run_process(
            [PYTHON_EXE, "-u", "main.py"],
            cwd=tmp_dir,
            stdin_data=stdin,
            timeout=timeout
        )
        elapsed = (datetime.now() - start).total_seconds()
        return CodeExecuteResponse(
            success=exit_code == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=round(elapsed, 3),
            error=None if exit_code == 0 else (stderr or "执行失败")
        )
    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        return CodeExecuteResponse(success=False, error=str(e), execution_time=round(elapsed, 3))
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


async def execute_java(code: str, stdin: Optional[str] = None, timeout: int = 30) -> CodeExecuteResponse:
    """执行 Java 代码（subprocess）"""
    start = datetime.now()
    sanitized = _sanitize_filename(code[:100])
    tmp_dir = tempfile.mkdtemp(prefix=f"java_{sanitized}_")
    try:
        lines = code.splitlines()
        class_name = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class ") and "{" in stripped:
                parts = stripped.split()
                if len(parts) >= 2:
                    cls_part = parts[1].split("{")[0].strip()
                    class_name = cls_part
                    break

        if not class_name:
            class_name = f"Main_{sanitized[:8]}"

        java_file = Path(tmp_dir) / f"{class_name}.java"
        java_file.write_text(code, encoding="utf-8")

        compile_cmd = [JAVA_CMD, f"{class_name}.java"]
        c_exit, c_out, c_err = await _run_process(compile_cmd, cwd=tmp_dir, timeout=30)
        if c_exit != 0:
            elapsed = (datetime.now() - start).total_seconds()
            return CodeExecuteResponse(
                success=False,
                stderr=f"编译错误:\n{c_err}",
                exit_code=c_exit,
                execution_time=round(elapsed, 3),
                error=f"编译失败: {c_err}"
            )

        run_cmd = [JAVA_RUN, "-cp", tmp_dir, class_name]
        r_exit, stdout, stderr = await _run_process(run_cmd, cwd=tmp_dir, stdin_data=stdin, timeout=timeout)
        elapsed = (datetime.now() - start).total_seconds()
        return CodeExecuteResponse(
            success=r_exit == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=r_exit,
            execution_time=round(elapsed, 3),
            error=None if r_exit == 0 else (stderr or "运行失败")
        )
    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        return CodeExecuteResponse(success=False, error=str(e), execution_time=round(elapsed, 3))
    finally:
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


@router.post("/execute", response_model=ResponseModel)
async def run_code(req: CodeExecuteRequest):
    """
    执行代码（Python / Java）
    
    - **code**: 源代码内容
    - **language**: python 或 java
    - **timeout**: 超时时间(秒)，默认15秒
    - **stdin**: 可选的标准输入
    """
    code = req.code.strip()
    lang = req.language.lower()

    if not code:
        return ResponseModel(code=400, message="代码不能为空")

    if len(code) > MAX_CODE_LENGTH:
        return ResponseModel(code=400, message=f"代码过长，最大 {MAX_CODE_LENGTH} 字符")

    timeout = min(req.timeout or 15, 60)

    logger.info(f"[code/execute] lang={lang}, len={len(code)}, timeout={timeout}")

    try:
        if lang == "python":
            result = await execute_python(code, req.stdin, timeout)
        elif lang == "java":
            result = await execute_java(code, req.stdin, timeout)
        else:
            return ResponseModel(code=400, message=f"不支持的语言: {lang}，仅支持 python 和 java")

        return ResponseModel(
            code=200 if result.success else 200,
            message="执行成功" if result.success else "执行出错",
            data={
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "error": result.error
            }
        )
    except Exception as e:
        logger.error(f"代码执行异常: {e}")
        return ResponseModel(code=500, message=f"服务器执行异常: {str(e)}")
