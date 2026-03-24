"""
结果合并器 - 两路召回结果合并 + 重排序

策略:
- 加权融合分数
- 去重 (同一 doc_id 合并)
- 重排序 (按融合分数)
- 多样性保护 (可选)
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger("result_merger")


class ResultMerger:
    """
    结果合并器
    
    合并来自静态库和动态库的检索结果
    """
    
    def __init__(self,
                 static_weight: float = 0.6,
                 dynamic_weight: float = 0.4,
                 use_diversity: bool = False,
                 diversity_threshold: float = 0.8):
        """
        Args:
            static_weight: 静态库结果权重
            dynamic_weight: 动态库结果权重
            use_diversity: 是否启用多样性保护
            diversity_threshold: 多样性阈值 (内容相似度超过此值的会被降权)
        """
        self.static_weight = static_weight
        self.dynamic_weight = dynamic_weight
        self.use_diversity = use_diversity
        self.diversity_threshold = diversity_threshold
    
    def _compute_content_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度 (简单版本：基于词重叠)
        
        TODO: 可以使用更复杂的算法如 Jaccard、余弦相似度等
        """
        # 简单分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def merge(self,
              static_results: List[Dict[str, Any]],
              dynamic_results: List[Dict[str, Any]],
              top_k: int = 10) -> List[Dict[str, Any]]:
        """
        合并两路召回结果
        
        算法:
        1. 加权融合分数 (静态库结果 * static_weight, 动态库结果 * dynamic_weight)
        2. 按 doc_id 去重 (同一文档保留最高分)
        3. 按融合分数降序排序
        4. 应用多样性保护 (可选)
        5. 返回 top_k
        
        Args:
            static_results: 静态库检索结果
            dynamic_results: 动态库检索结果
            top_k: 返回结果数
        
        Returns:
            合并后的 Top-K 结果
        """
        logger.debug(f"合并结果：静态库{len(static_results)}个，动态库{len(dynamic_results)}个")
        
        # 1. 构建 doc_id 到结果的映射
        doc_map: Dict[str, Dict[str, Any]] = {}
        
        # 处理静态库结果
        for result in static_results:
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            # 应用权重
            weighted_score = result.get("score", 0) * self.static_weight
            
            doc_map[doc_id] = {
                **result,
                "final_score": weighted_score,
                "channels": ["static"],
                "static_score": result.get("score", 0),
                "dynamic_score": 0.0
            }
        
        # 处理动态库结果
        for result in dynamic_results:
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            # 应用权重
            weighted_score = result.get("score", 0) * self.dynamic_weight
            
            if doc_id in doc_map:
                # 文档已存在，累加分数
                doc_map[doc_id]["final_score"] += weighted_score
                doc_map[doc_id]["channels"].append("dynamic")
                doc_map[doc_id]["dynamic_score"] = result.get("score", 0)
            else:
                # 新文档
                doc_map[doc_id] = {
                    **result,
                    "final_score": weighted_score,
                    "channels": ["dynamic"],
                    "static_score": 0.0,
                    "dynamic_score": result.get("score", 0)
                }
        
        # 2. 转换为列表并排序
        merged_results = list(doc_map.values())
        merged_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # 3. 应用多样性保护 (可选)
        if self.use_diversity:
            merged_results = self._apply_diversity(merged_results)
        
        # 4. 返回 top_k
        final_results = merged_results[:top_k]
        
        # 5. 添加排名信息
        for i, result in enumerate(final_results):
            result["rank"] = i + 1
        
        logger.info(f"合并完成：共{len(final_results)}个结果")
        return final_results
    
    def _apply_diversity(self, 
                         results: List[Dict[str, Any]],
                         max_similar: int = 2) -> List[Dict[str, Any]]:
        """
        应用多样性保护
        
        防止返回过多相似内容
        
        Args:
            results: 排序后的结果列表
            max_similar: 最多允许多少个相似文档连续出现
        
        Returns:
            应用多样性后的结果
        """
        if not results:
            return results
        
        diversified = []
        skip_count = 0
        
        for result in results:
            content = result.get("content", "")
            
            # 检查与已选结果的相似度
            is_too_similar = False
            for selected in diversified[-max_similar:]:
                similarity = self._compute_content_similarity(
                    content,
                    selected.get("content", "")
                )
                if similarity > self.diversity_threshold:
                    is_too_similar = True
                    break
            
            if is_too_similar:
                # 降权处理，而不是完全过滤
                result["final_score"] *= 0.5  # 降权 50%
                result["diversity_penalized"] = True
                skip_count += 1
            
            diversified.append(result)
        
        # 重新排序
        diversified.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        logger.debug(f"多样性保护：降权{skip_count}个结果")
        return diversified
    
    def merge_with_reciprocal_rank(self,
                                    static_results: List[Dict[str, Any]],
                                    dynamic_results: List[Dict[str, Any]],
                                    top_k: int = 10) -> List[Dict[str, Any]]:
        """
        使用倒数融合 (Reciprocal Rank Fusion, RRF) 合并结果
        
        RRF 是一种常用的多路召回合并算法，不依赖分数绝对值
        
        公式：RRF(d) = Σ 1 / (k + rank_i(d))
        其中 k 是常数 (通常 60)，rank_i 是文档在第 i 路结果中的排名
        
        Args:
            static_results: 静态库结果 (已按分数排序)
            dynamic_results: 动态库结果 (已按分数排序)
            top_k: 返回结果数
        
        Returns:
            合并后的 Top-K 结果
        """
        # 计算 RRF 分数
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}
        
        # 静态库 RRF 分数
        k = 60  # RRF 常数
        for rank, result in enumerate(static_results):
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            rrf_score = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            
            if doc_id not in doc_map:
                doc_map[doc_id] = {**result, "channels": ["static"]}
            else:
                doc_map[doc_id]["channels"].append("static")
        
        # 动态库 RRF 分数
        for rank, result in enumerate(dynamic_results):
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            rrf_score = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            
            if doc_id not in doc_map:
                doc_map[doc_id] = {**result, "channels": ["dynamic"]}
            else:
                doc_map[doc_id]["channels"].append("dynamic")
        
        # 添加 RRF 分数到结果
        for doc_id, rrf_score in rrf_scores.items():
            if doc_id in doc_map:
                doc_map[doc_id]["rrf_score"] = rrf_score
                doc_map[doc_id]["final_score"] = rrf_score
        
        # 排序并返回 top_k
        merged_results = list(doc_map.values())
        merged_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        
        final_results = merged_results[:top_k]
        
        # 添加排名
        for i, result in enumerate(final_results):
            result["rank"] = i + 1
        
        return final_results
    
    def get_stats(self, 
                  static_results: List[Dict[str, Any]],
                  dynamic_results: List[Dict[str, Any]],
                  merged_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取合并统计信息"""
        # 统计来源分布
        static_only = sum(1 for r in merged_results if r.get("channels") == ["static"])
        dynamic_only = sum(1 for r in merged_results if r.get("channels") == ["dynamic"])
        both = sum(1 for r in merged_results if "static" in r.get("channels", []) and "dynamic" in r.get("channels", []))
        
        return {
            "static_input": len(static_results),
            "dynamic_input": len(dynamic_results),
            "merged_output": len(merged_results),
            "static_only": static_only,
            "dynamic_only": dynamic_only,
            "overlap": both,
            "diversity_enabled": self.use_diversity
        }
