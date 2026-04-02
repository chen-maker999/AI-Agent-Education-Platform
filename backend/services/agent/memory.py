"""Agent 内存系统 - 支持会话级别和持久化记忆"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from enum import Enum


class MemoryScope(str, Enum):
    """记忆范围"""
    SESSION = "session"   # 会话级别
    AGENT = "agent"       # Agent 持久化
    USER = "user"         # 用户级别
    PROJECT = "project"   # 项目级别


class MemoryEntry:
    """记忆条目"""
    def __init__(
        self,
        id: str,
        content: str,
        scope: MemoryScope,
        agent_id: str = None,
        user_id: str = None,
        session_id: str = None,
        created_at: str = None,
        updated_at: str = None,
        importance: float = 1.0,  # 重要性评分 0-1
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = id
        self.content = content
        self.scope = scope
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
        self.importance = importance
        self.tags = tags or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "scope": self.scope.value if isinstance(self.scope, MemoryScope) else self.scope,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            scope=MemoryScope(data.get("scope", "session")),
            agent_id=data.get("agent_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            importance=data.get("importance", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


class AgentMemory:
    """Agent 内存管理器"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent / "memory"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存文件路径
        self.memory_files = {
            MemoryScope.SESSION: self.base_dir / "sessions",
            MemoryScope.AGENT: self.base_dir / "agents",
            MemoryScope.USER: self.base_dir / "users",
            MemoryScope.PROJECT: self.base_dir / "projects",
        }
        
        # 创建目录
        for dir_path in self.memory_files.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._cache: Dict[str, List[MemoryEntry]] = {}
    
    def _get_memory_file(self, scope: MemoryScope, entity_id: str) -> Path:
        """获取记忆文件路径"""
        return self.memory_files[scope] / f"{entity_id}.json"
    
    def _load_memories(self, scope: MemoryScope, entity_id: str) -> List[MemoryEntry]:
        """加载记忆"""
        cache_key = f"{scope.value}:{entity_id}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = self._get_memory_file(scope, entity_id)
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                memories = [MemoryEntry.from_dict(m) for m in data]
                self._cache[cache_key] = memories
                return memories
        except Exception:
            return []
    
    def _save_memories(self, scope: MemoryScope, entity_id: str, memories: List[MemoryEntry]):
        """保存记忆"""
        cache_key = f"{scope.value}:{entity_id}"
        file_path = self._get_memory_file(scope, entity_id)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([m.to_dict() for m in memories], f, ensure_ascii=False, indent=2)
            self._cache[cache_key] = memories
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def add_memory(
        self,
        content: str,
        scope: MemoryScope,
        agent_id: str = None,
        user_id: str = None,
        session_id: str = None,
        entity_id: str = None,
        importance: float = 1.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> MemoryEntry:
        """添加记忆"""
        import uuid
        
        # 确定实体 ID
        if entity_id is None:
            if scope == MemoryScope.SESSION:
                entity_id = session_id or "default"
            elif scope == MemoryScope.AGENT:
                entity_id = agent_id or "default"
            elif scope == MemoryScope.USER:
                entity_id = user_id or "default"
            else:
                entity_id = "default"
        
        # 创建记忆条目
        memory = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            scope=scope,
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            importance=importance,
            tags=tags,
            metadata=metadata
        )
        
        # 加载现有记忆
        memories = self._load_memories(scope, entity_id)
        
        # 添加新记忆
        memories.append(memory)
        
        # 保存
        self._save_memories(scope, entity_id, memories)
        
        return memory
    
    def get_memories(
        self,
        scope: MemoryScope,
        entity_id: str = None,
        user_id: str = None,
        session_id: str = None,
        agent_id: str = None,
        min_importance: float = 0.0,
        tags: List[str] = None,
        limit: int = None
    ) -> List[MemoryEntry]:
        """获取记忆"""
        # 确定实体 ID
        if entity_id is None:
            if scope == MemoryScope.SESSION:
                entity_id = session_id or "default"
            elif scope == MemoryScope.AGENT:
                entity_id = agent_id or "default"
            elif scope == MemoryScope.USER:
                entity_id = user_id or "default"
            else:
                entity_id = "default"
        
        memories = self._load_memories(scope, entity_id)
        
        # 过滤
        filtered = []
        for m in memories:
            if m.importance < min_importance:
                continue
            if tags and not any(t in m.tags for t in tags):
                continue
            filtered.append(m)
        
        # 排序（按重要性降序，按时间降序）
        filtered.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        
        # 限制数量
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def search_memories(
        self,
        query: str,
        scope: MemoryScope = None,
        entity_id: str = None,
        user_id: str = None,
        session_id: str = None,
        agent_id: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """搜索记忆"""
        results = []
        scopes = [scope] if scope else list(MemoryScope)
        
        for s in scopes:
            memories = self.get_memories(
                scope=s,
                entity_id=entity_id,
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id
            )
            
            # 简单关键词匹配
            for m in memories:
                if query.lower() in m.content.lower():
                    results.append(m)
        
        # 排序
        results.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        
        return results[:limit]
    
    def update_memory(self, memory_id: str, content: str = None, importance: float = None) -> bool:
        """更新记忆"""
        for scope in MemoryScope:
            memories = self._load_memories(scope, "default")  # 需要遍历所有文件
            
            for m in memories:
                if m.id == memory_id:
                    if content is not None:
                        m.content = content
                    if importance is not None:
                        m.importance = importance
                    m.updated_at = datetime.utcnow().isoformat()
                    self._save_memories(scope, "default", memories)
                    return True
        
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        for scope in MemoryScope:
            # 需要遍历所有实体
            for file_path in self.memory_files[scope].glob("*.json"):
                try:
                    memories = self._load_memories(scope, file_path.stem)
                    original_len = len(memories)
                    memories = [m for m in memories if m.id != memory_id]
                    
                    if len(memories) < original_len:
                        self._save_memories(scope, file_path.stem, memories)
                        return True
                except Exception:
                    pass
        
        return False
    
    def get_session_memory(self, session_id: str, limit: int = 10) -> str:
        """获取会话记忆内容"""
        memories = self.get_memories(
            scope=MemoryScope.SESSION,
            session_id=session_id,
            limit=limit
        )
        
        if not memories:
            return ""
        
        return "\n".join([m.content for m in memories])
    
    def get_agent_memory(self, agent_id: str, limit: int = 20) -> str:
        """获取 Agent 持久记忆"""
        memories = self.get_memories(
            scope=MemoryScope.AGENT,
            agent_id=agent_id,
            limit=limit
        )
        
        if not memories:
            return ""
        
        return "\n".join([f"- {m.content}" for m in memories])
    
    def get_user_memory(self, user_id: str, limit: int = 10) -> str:
        """获取用户记忆"""
        memories = self.get_memories(
            scope=MemoryScope.USER,
            user_id=user_id,
            limit=limit
        )
        
        if not memories:
            return ""
        
        return "\n".join([f"- {m.content}" for m in memories])
    
    def clear_session(self, session_id: str) -> int:
        """清除会话记忆"""
        memories = self._load_memories(MemoryScope.SESSION, session_id)
        count = len(memories)
        
        if count > 0:
            self._save_memories(MemoryScope.SESSION, session_id, [])
        
        return count
    
    def compact_memories(
        self,
        scope: MemoryScope,
        entity_id: str,
        max_memories: int = 50,
        min_importance: float = 0.5
    ) -> int:
        """压缩记忆，只保留重要的"""
        memories = self._load_memories(scope, entity_id)
        
        if len(memories) <= max_memories:
            return 0
        
        # 过滤低重要性的
        important = [m for m in memories if m.importance >= min_importance]
        
        # 如果还是太多，只保留最重要的
        if len(important) > max_memories:
            important.sort(key=lambda x: x.importance, reverse=True)
            important = important[:max_memories]
        
        removed = len(memories) - len(important)
        
        if removed > 0:
            self._save_memories(scope, entity_id, important)
        
        return removed
    
    def get_memory_stats(self, scope: MemoryScope, entity_id: str = None) -> Dict[str, Any]:
        """获取记忆统计"""
        if entity_id:
            memories = self._load_memories(scope, entity_id)
            return {
                "scope": scope.value,
                "entity_id": entity_id,
                "total": len(memories),
                "avg_importance": sum(m.importance for m in memories) / len(memories) if memories else 0,
                "tags": list(set(t for m in memories for t in m.tags))
            }
        else:
            total = 0
            all_tags = set()
            for file_path in self.memory_files[scope].glob("*.json"):
                memories = self._load_memories(scope, file_path.stem)
                total += len(memories)
                for m in memories:
                    all_tags.update(m.tags)
            
            return {
                "scope": scope.value,
                "entity_count": len(list(self.memory_files[scope].glob("*.json"))),
                "total_memories": total,
                "all_tags": list(all_tags)
            }


# 全局内存实例
agent_memory = AgentMemory()


# ===== 便捷函数 =====

def add_session_memory(
    session_id: str,
    content: str,
    importance: float = 1.0,
    tags: List[str] = None
) -> MemoryEntry:
    """添加会话记忆"""
    return agent_memory.add_memory(
        content=content,
        scope=MemoryScope.SESSION,
        session_id=session_id,
        importance=importance,
        tags=tags
    )


def get_session_memory(session_id: str, limit: int = 10) -> str:
    """获取会话记忆"""
    return agent_memory.get_session_memory(session_id, limit)


def add_agent_memory(
    agent_id: str,
    content: str,
    importance: float = 1.0,
    tags: List[str] = None
) -> MemoryEntry:
    """添加 Agent 记忆"""
    return agent_memory.add_memory(
        content=content,
        scope=MemoryScope.AGENT,
        agent_id=agent_id,
        importance=importance,
        tags=tags
    )


def get_agent_memory(agent_id: str, limit: int = 20) -> str:
    """获取 Agent 记忆"""
    return agent_memory.get_agent_memory(agent_id, limit)


def add_user_memory(
    user_id: str,
    content: str,
    importance: float = 1.0,
    tags: List[str] = None
) -> MemoryEntry:
    """添加用户记忆"""
    return agent_memory.add_memory(
        content=content,
        scope=MemoryScope.USER,
        user_id=user_id,
        importance=importance,
        tags=tags
    )


def get_user_memory(user_id: str, limit: int = 10) -> str:
    """获取用户记忆"""
    return agent_memory.get_user_memory(user_id, limit)
