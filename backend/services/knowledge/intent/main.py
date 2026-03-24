"""意图识别服务 - 基于 BERT 的意图分类器"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os
import pickle
import numpy as np

try:
    from transformers import BertTokenizer, BertForSequenceClassification
    from transformers import Trainer, TrainingArguments
    import torch
    from torch.utils.data import Dataset
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    BertTokenizer = None
    BertForSequenceClassification = None

router = APIRouter(prefix="/intent", tags=["Intent Recognition"])


# ==================== 配置 ====================
class IntentConfig:
    """意图识别配置"""
    # 模型配置
    MODEL_NAME = "bert-base-chinese"  # 中文 BERT 基础模型
    MAX_LENGTH = 128  # 最大序列长度
    NUM_LABELS = 6  # 意图类别数

    # 模型路径
    MODEL_DIR = "data/intent_model"
    MODEL_PATH = os.path.join(MODEL_DIR, "intent_bert.pth")
    TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer")
    LABEL_MAP_PATH = os.path.join(MODEL_DIR, "label_map.json")

    # 推理配置
    INFERENCE_BATCH_SIZE = 16
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu" if BERT_AVAILABLE else "cpu"

    # 意图类型定义
    INTENT_TYPES = {
        "concept_explanation": "概念解释",  # 什么是 X
        "relation_query": "关系查询",  # X 和 Y 的区别
        "code_question": "代码问题",  # 如何实现 X
        "history_review": "历史回顾",  # 我之前学过
        "exercise_find": "题目查找",  # 练习题
        "general": "通用查询"
    }


# ==================== 数据模型 ====================
class IntentRequest(BaseModel):
    """意图识别请求"""
    query: str
    course_id: Optional[str] = None
    student_id: Optional[str] = None


class IntentResponse(BaseModel):
    """意图识别响应"""
    query: str
    intent: str
    confidence: float
    all_scores: Dict[str, float]
    keywords: List[str]
    model_type: str  # "bert" or "rule"


class TrainRequest(BaseModel):
    """训练请求"""
    training_data: List[Dict[str, str]]  # [{text, label}, ...]
    epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 2e-5


# ==================== 数据集 ====================
class IntentDataset(Dataset):
    """意图识别数据集"""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


# ==================== BERT 意图分类器 ====================
class BERTIntentClassifier:
    """
    基于 BERT 的意图分类器

    功能:
    - 使用预训练的中文 BERT 模型
    - 支持微调和增量训练
    - 输出意图类别和置信度
    - 支持模型持久化
    """

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.label_map: Dict[int, str] = {}
        self.str_to_int_label: Dict[str, int] = {}
        self.is_loaded = False
        self.device = IntentConfig.DEVICE

        # 初始化标签映射
        self._init_label_map()

    def _init_label_map(self):
        """初始化标签映射"""
        intent_types = list(IntentConfig.INTENT_TYPES.keys())
        self.label_map = {i: label for i, label in enumerate(intent_types)}
        self.str_to_int_label = {label: i for i, label in self.label_map.items()}

    def load_model(self) -> bool:
        """加载模型"""
        if not BERT_AVAILABLE:
            print("[Intent] BERT 库未安装，使用规则分类器")
            return False

        try:
            # 加载分词器
            if os.path.exists(IntentConfig.TOKENIZER_PATH):
                self.tokenizer = BertTokenizer.from_pretrained(IntentConfig.TOKENIZER_PATH)
            else:
                self.tokenizer = BertTokenizer.from_pretrained(IntentConfig.MODEL_NAME)

            # 加载模型
            if os.path.exists(IntentConfig.MODEL_PATH):
                self.model = BertForSequenceClassification.from_pretrained(
                    IntentConfig.MODEL_NAME,
                    num_labels=IntentConfig.NUM_LABELS
                )
                checkpoint = torch.load(IntentConfig.MODEL_PATH, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.model.to(self.device)

                # 加载标签映射
                if os.path.exists(IntentConfig.LABEL_MAP_PATH):
                    with open(IntentConfig.LABEL_MAP_PATH, 'r', encoding='utf-8') as f:
                        label_map = json.load(f)
                        self.label_map = {int(k): v for k, v in label_map.items()}
                        self.str_to_int_label = {v: k for k, v in self.label_map.items()}

                self.is_loaded = True
                print(f"[Intent] BERT 模型已加载：{IntentConfig.MODEL_PATH}")
            else:
                print("[Intent] 模型文件不存在，使用基础模型")
                self.model = BertForSequenceClassification.from_pretrained(
                    IntentConfig.MODEL_NAME,
                    num_labels=IntentConfig.NUM_LABELS
                )
                self.model.to(self.device)

            return True
        except Exception as e:
            print(f"[Intent] 模型加载失败：{e}")
            return False

    def save_model(self):
        """保存模型"""
        if not self.model or not self.tokenizer:
            return False

        try:
            os.makedirs(IntentConfig.MODEL_DIR, exist_ok=True)

            # 保存模型权重
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'label_map': self.label_map
            }, IntentConfig.MODEL_PATH)

            # 保存分词器
            self.tokenizer.save_pretrained(IntentConfig.TOKENIZER_PATH)

            # 保存标签映射
            with open(IntentConfig.LABEL_MAP_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.label_map, f, ensure_ascii=False, indent=2)

            print(f"[Intent] 模型已保存：{IntentConfig.MODEL_PATH}")
            return True
        except Exception as e:
            print(f"[Intent] 模型保存失败：{e}")
            return False

    def train(self, training_data: List[Dict[str, str]], epochs: int = 3,
              batch_size: int = 16, learning_rate: float = 2e-5) -> Dict:
        """
        微调训练模型

        Args:
            training_data: 训练数据 [{text, label}, ...]
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率

        Returns:
            训练结果
        """
        if not BERT_AVAILABLE:
            return {"error": "BERT 库未安装"}

        if not self.model or not self.tokenizer:
            self.load_model()

        # 准备数据
        texts = [item['text'] for item in training_data]
        labels = [self.str_to_int_label.get(item['label'], 0) for item in training_data]

        # 创建数据集
        dataset = IntentDataset(texts, labels, self.tokenizer, IntentConfig.MAX_LENGTH)

        # 训练参数
        training_args = TrainingArguments(
            output_dir=IntentConfig.MODEL_DIR,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=100,
            logging_dir='./logs',
            logging_steps=50,
            save_steps=500,
            save_total_limit=2,
            fp16=self.device == 'cuda',
        )

        # 创建 Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
        )

        # 开始训练
        print(f"[Intent] 开始训练，{len(texts)} 条样本，{epochs} 轮")
        trainer.train()

        # 保存模型
        self.save_model()

        return {
            "status": "success",
            "samples": len(texts),
            "epochs": epochs,
            "model_path": IntentConfig.MODEL_PATH
        }

    def predict(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """
        预测意图

        Args:
            query: 查询文本

        Returns:
            (intent, confidence, all_scores)
        """
        if not self.model or not self.tokenizer:
            # 降级到规则分类
            return self._rule_predict(query)

        try:
            # 分词
            inputs = self.tokenizer.encode_plus(
                query,
                add_special_tokens=True,
                max_length=IntentConfig.MAX_LENGTH,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )

            # 推理
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(
                    inputs['input_ids'].to(self.device),
                    attention_mask=inputs['attention_mask'].to(self.device)
                )

                # 计算概率
                probs = torch.softmax(outputs.logits, dim=1)
                confidence, predicted = torch.max(probs, 1)

                # 获取所有类别的分数
                all_scores = {}
                for i, prob in enumerate(probs[0]):
                    label = self.label_map.get(i, f"label_{i}")
                    all_scores[label] = round(prob.item(), 4)

                intent = self.label_map.get(predicted.item(), "general")
                conf = round(confidence.item(), 4)

                return intent, conf, all_scores
        except Exception as e:
            print(f"[Intent] 预测失败：{e}，降级到规则分类")
            return self._rule_predict(query)

    def _rule_predict(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """规则分类器（降级方案）"""
        query_lower = query.lower()

        # 关键词规则
        rules = {
            "concept_explanation": ["什么是", "解释", "定义", "含义", "意思", "概念", "介绍"],
            "relation_query": ["关系", "联系", "区别", "差异", "对比", "关联"],
            "code_question": ["代码", "编程", "实现", "怎么写", "函数", "方法", "类"],
            "history_review": ["历史", "记录", "之前", "曾经", "上次", "回顾"],
            "exercise_find": ["题目", "练习", "习题", "试题", "考题", "刷题"]
        }

        scores = {intent: 0.0 for intent in IntentConfig.INTENT_TYPES.keys()}

        # 关键词匹配
        for intent, keywords in rules.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[intent] += 0.3

        # 问题类型分析
        if any(p in query_lower for p in ["什么", "啥", "what"]):
            scores["concept_explanation"] += 0.2
        if any(p in query_lower for p in ["怎么", "如何", "how"]):
            scores["code_question"] += 0.2

        # 找到最高分
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        # 计算置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > sorted_scores[1]:
            confidence = min(0.95, 0.5 + (sorted_scores[0] - sorted_scores[1]) * 0.5)
        else:
            confidence = 0.5

        # 如果没有明显意图，返回通用
        if max_score < 0.2:
            max_intent = "general"
            confidence = 0.5

        return max_intent, confidence, scores

    def get_stats(self) -> Dict:
        """获取模型统计信息"""
        return {
            "model_loaded": self.is_loaded,
            "model_path": IntentConfig.MODEL_PATH,
            "device": self.device,
            "num_labels": len(self.label_map),
            "label_map": self.label_map,
            "bert_available": BERT_AVAILABLE
        }


# ==================== 全局实例 ====================
intent_classifier = BERTIntentClassifier()


@router.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    intent_classifier.load_model()
    print(f"[Intent] 意图识别服务初始化完成，设备：{IntentConfig.DEVICE}")


# ==================== API 接口 ====================
@router.post("/classify", response_model=IntentResponse)
async def classify_intent(request: IntentRequest):
    """
    意图分类

    分析查询的意图类型
    """
    start_time = datetime.now()

    # 意图识别
    intent, confidence, all_scores = intent_classifier.predict(request.query)

    # 提取关键词
    keywords = _extract_keywords(request.query)

    processing_time = (datetime.now() - start_time).total_seconds()

    return IntentResponse(
        query=request.query,
        intent=intent,
        confidence=confidence,
        all_scores=all_scores,
        keywords=keywords,
        model_type="bert" if intent_classifier.is_loaded else "rule"
    )


@router.post("/train")
async def train_model(request: TrainRequest):
    """
    训练意图识别模型

    使用标注数据微调 BERT 模型
    """
    result = intent_classifier.train(
        training_data=request.training_data,
        epochs=request.epochs,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate
    )

    return {
        "code": 200 if "error" not in result else 500,
        "message": "训练完成" if "error" not in result else "训练失败",
        "data": result
    }


@router.get("/model/stats")
async def get_model_stats():
    """获取模型统计信息"""
    return {
        "code": 200,
        "data": intent_classifier.get_stats()
    }


@router.post("/model/save")
async def save_model():
    """保存模型到磁盘"""
    success = intent_classifier.save_model()
    return {
        "code": 200 if success else 500,
        "message": "模型已保存" if success else "保存失败"
    }


@router.post("/model/reload")
async def reload_model():
    """重新加载模型"""
    success = intent_classifier.load_model()
    return {
        "code": 200 if success else 500,
        "message": "模型已重新加载" if success else "加载失败"
    }


@router.get("/intents")
async def list_intents():
    """列出所有意图类型"""
    return {
        "code": 200,
        "data": {
            "intents": IntentConfig.INTENT_TYPES,
            "num_labels": len(IntentConfig.INTENT_TYPES)
        }
    }


# ==================== 工具函数 ====================
def _extract_keywords(text: str) -> List[str]:
    """提取关键词"""
    try:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=False)
        return keywords
    except ImportError:
        import re
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text)
        return words[:10]


@router.post("/batch/classify")
async def batch_classify(queries: List[str]):
    """批量意图分类"""
    results = []
    for query in queries:
        intent, confidence, all_scores = intent_classifier.predict(query)
        results.append({
            "query": query,
            "intent": intent,
            "confidence": confidence,
            "all_scores": all_scores
        })
    return {
        "code": 200,
        "data": {
            "results": results,
            "total": len(results)
        }
    }
