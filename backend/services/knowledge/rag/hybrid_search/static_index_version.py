"""
静态库版本管理 - 支持一致性检查和回滚

功能:
- 版本号管理 (每次重建 +1)
- 记录构建时间、文档数、词表大小
- 支持版本查询和回滚
- 支持一致性检查
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class StaticIndexVersion:
    """静态库版本信息"""
    version: int
    build_time: str
    doc_count: int
    vocab_size: int
    matrix_shape: tuple
    file_hash: str
    is_active: bool = True


class StaticIndexVersionManager:
    """
    静态库版本管理器

    管理多个版本的静态库，支持回滚和历史查询
    """

    def __init__(self, base_path: str = "data/static_index_versions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.version_file = self.base_path / "versions.json"
        self.current_version = 0
        self.versions: List[StaticIndexVersion] = []

        self._load_versions()

    def _load_versions(self):
        """加载版本历史"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.versions = [
                        StaticIndexVersion(**v) for v in data.get('versions', [])
                    ]
                    self.current_version = data.get('current_version', 0)
            except Exception as e:
                print(f"[StaticIndexVersion] 加载版本历史失败：{e}")
                self.versions = []
                self.current_version = 0

    def _save_versions(self):
        """保存版本历史"""
        data = {
            'versions': [asdict(v) for v in self.versions],
            'current_version': self.current_version
        }
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        if not file_path.exists():
            return ""

        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def create_version(
        self,
        doc_count: int,
        vocab_size: int,
        matrix_shape: tuple,
        model_path: str,
        matrix_path: str
    ) -> StaticIndexVersion:
        """
        创建新版本

        Args:
            doc_count: 文档数
            vocab_size: 词表大小
            matrix_shape: 矩阵形状
            model_path: 模型文件路径
            matrix_path: 矩阵文件路径

        Returns:
            版本信息
        """
        # 新版本号
        new_version = self.current_version + 1

        # 计算文件哈希
        model_hash = self._compute_file_hash(Path(model_path))
        matrix_hash = self._compute_file_hash(Path(matrix_path))
        file_hash = hashlib.md5(f"{model_hash}{matrix_hash}".encode()).hexdigest()

        # 创建版本信息
        version = StaticIndexVersion(
            version=new_version,
            build_time=datetime.now().isoformat(),
            doc_count=doc_count,
            vocab_size=vocab_size,
            matrix_shape=matrix_shape,
            file_hash=file_hash,
            is_active=True
        )

        # 将旧版本标记为非活跃
        for v in self.versions:
            v.is_active = False

        # 添加新版本
        self.versions.append(version)
        self.current_version = new_version

        # 保存版本历史
        self._save_versions()

        # 备份当前版本
        version_dir = self.base_path / f"v{new_version}"
        version_dir.mkdir(parents=True, exist_ok=True)

        # 复制文件到版本目录
        if os.path.exists(model_path):
            shutil.copy(model_path, version_dir / "model.pkl")
        if os.path.exists(matrix_path):
            shutil.copy(matrix_path, version_dir / "matrix.npz")

        # 保存版本信息
        version_info_path = version_dir / "version_info.json"
        with open(version_info_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(version), f, ensure_ascii=False, indent=2)

        print(f"[StaticIndexVersion] 创建新版本 v{new_version}: {doc_count} 个文档")
        return version

    def get_current_version(self) -> Optional[StaticIndexVersion]:
        """获取当前版本"""
        for v in self.versions:
            if v.is_active:
                return v
        return None

    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [asdict(v) for v in self.versions]

    def rollback_to_version(self, version: int) -> bool:
        """
        回滚到指定版本

        Args:
            version: 目标版本号

        Returns:
            是否成功
        """
        # 查找目标版本
        target_version = None
        for v in self.versions:
            if v.version == version:
                target_version = v
                break

        if target_version is None:
            print(f"[StaticIndexVersion] 版本 v{version} 不存在")
            return False

        # 检查版本文件是否存在
        version_dir = self.base_path / f"v{version}"
        if not version_dir.exists():
            print(f"[StaticIndexVersion] 版本 v{version} 的文件不存在")
            return False

        # 恢复文件
        model_src = version_dir / "model.pkl"
        matrix_src = version_dir / "matrix.npz"

        model_dst = Path("data/tfidf_static_model.pkl")
        matrix_dst = Path("data/tfidf_static_matrix.dat.npz")

        if model_src.exists():
            shutil.copy(model_src, model_dst)
        if matrix_src.exists():
            shutil.copy(matrix_src, matrix_dst)

        # 更新版本状态
        for v in self.versions:
            v.is_active = (v.version == version)
        self.current_version = version
        self._save_versions()

        print(f"[StaticIndexVersion] 已回滚到版本 v{version}")
        return True

    def check_consistency(self) -> Dict[str, Any]:
        """
        检查当前版本一致性

        Returns:
            检查结果
        """
        current = self.get_current_version()
        if current is None:
            return {
                'consistent': False,
                'error': '当前版本不存在'
            }

        # 检查文件是否存在
        model_path = Path("data/tfidf_static_model.pkl")
        matrix_path = Path("data/tfidf_static_matrix.dat.npz")

        if not model_path.exists():
            return {
                'consistent': False,
                'error': '模型文件不存在'
            }

        if not matrix_path.exists():
            return {
                'consistent': False,
                'error': '矩阵文件不存在'
            }

        # 计算当前文件哈希
        current_hash = self._compute_file_hash(model_path)
        current_hash += self._compute_file_hash(matrix_path)
        current_hash = hashlib.md5(current_hash.encode()).hexdigest()

        # 对比哈希
        if current_hash != current.file_hash:
            return {
                'consistent': False,
                'error': '文件哈希不匹配，可能已被修改',
                'expected_hash': current.file_hash,
                'current_hash': current_hash
            }

        return {
            'consistent': True,
            'version': current.version,
            'build_time': current.build_time,
            'doc_count': current.doc_count,
            'vocab_size': current.vocab_size
        }

    def cleanup_old_versions(self, keep_last_n: int = 3):
        """
        清理旧版本，只保留最近 N 个

        Args:
            keep_last_n: 保留的版本数
        """
        if len(self.versions) <= keep_last_n:
            return

        # 排序版本
        sorted_versions = sorted(self.versions, key=lambda v: v.version, reverse=True)
        versions_to_keep = sorted_versions[:keep_last_n]
        versions_to_delete = sorted_versions[keep_last_n:]

        # 删除旧版本目录
        for v in versions_to_delete:
            version_dir = self.base_path / f"v{v.version}"
            if version_dir.exists():
                shutil.rmtree(version_dir)
                print(f"[StaticIndexVersion] 删除旧版本 v{v.version}")

        # 从列表中移除
        self.versions = versions_to_keep
        self._save_versions()


# 全局版本管理器实例
_version_manager: Optional[StaticIndexVersionManager] = None


def get_version_manager() -> StaticIndexVersionManager:
    """获取版本管理器单例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = StaticIndexVersionManager()
    return _version_manager


# 便捷函数
def create_static_index_version(
    doc_count: int,
    vocab_size: int,
    matrix_shape: tuple,
    model_path: str,
    matrix_path: str
) -> StaticIndexVersion:
    """创建静态库版本"""
    return get_version_manager().create_version(
        doc_count, vocab_size, matrix_shape, model_path, matrix_path
    )


def get_current_static_index_version() -> Optional[StaticIndexVersion]:
    """获取当前静态库版本"""
    return get_version_manager().get_current_version()


def check_static_index_consistency() -> Dict[str, Any]:
    """检查静态库一致性"""
    return get_version_manager().check_consistency()


def rollback_static_index_to_version(version: int) -> bool:
    """回滚静态库到指定版本"""
    return get_version_manager().rollback_to_version(version)


if __name__ == "__main__":
    # 测试版本管理
    manager = get_version_manager()

    print("版本历史:")
    for v in manager.get_version_history():
        print(f"  v{v['version']}: {v['doc_count']} docs, {v['build_time']}")

    print("\n一致性检查:")
    result = manager.check_consistency()
    print(f"  {result}")
