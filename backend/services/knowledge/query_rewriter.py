"""
查询改写器 - 将中文查询转换为英文关键词

用于解决跨语言检索问题（中文查询 vs 英文文档）
"""

from typing import List, Dict


class QueryRewriter:
    """查询改写器 - 不使用 LLM"""

    # 领域特定词典（计算机教育领域）
    # P11 优化：基于 F1 瓶颈分析扩展词表，提升 Recall
    KEYWORD_TRANSLATIONS = {
        # ========== Java 基础核心概念 ==========
        "继承": ["inheritance", "extends", "subclass", "superclass", "base class", "derived class"],
        "多态": ["polymorphism", "override", "overriding", "redefine", "runtime polymorphism", "dynamic binding"],
        "封装": ["encapsulation", "private", "protected", "public", "access control", "data hiding"],
        "抽象": ["abstraction", "abstract", "abstract class", "interface", "generalization"],
        "接口": ["interface", "API", "contract", "implementation", "implements"],
        "类": ["class", "object", "instance", "template", "blueprint"],
        "对象": ["object", "instance", "reference", "new"],
        "方法": ["method", "function", "behavior", "operation", "member function"],
        "变量": ["variable", "field", "member variable", "data member", "attribute"],
        "参数": ["parameter", "argument", "input", "pass by value", "pass by reference"],
        "返回": ["return", "value", "result", "output", "return type"],
        "构造": ["constructor", "new", "initialize", "instantiation", "create object"],
        "静态": ["static", "class member", "class method", "shared"],
        "最终": ["final", "finally", "constant", "immutable", "cannot extend"],
        "公共": ["public", "accessible", "visibility"],
        "私有": ["private", "hidden", "access control"],
        "保护": ["protected", "subclass access", "inheritance"],
        "异常": ["exception", "throw", "catch", "try", "error", "runtime exception"],
        "处理": ["handle", "handling", "process", "deal with", "exception handling"],
        "输入": ["input", "InputStream", "Scanner", "System.in", "read"],
        "输出": ["output", "OutputStream", "System.out", "PrintStream", "write"],
        "文件": ["file", "File", "IOException", "FileInputStream", "FileOutputStream"],
        "读取": ["read", "Reader", "InputStream", "BufferedReader"],
        "写入": ["write", "Writer", "OutputStream", "BufferedWriter"],

        # ========== 数据类型和泛型 ==========
        "字符串": ["String", "char", "character", "StringBuilder", "StringBuffer"],
        "整数": ["int", "Integer", "long", "short", "byte", "number"],
        "浮点": ["float", "double", "decimal", "precision"],
        "布尔": ["boolean", "Boolean", "true", "false", "condition"],
        "数组": ["array", "Array", "[]", "element", "index", "dimension"],
        "列表": ["List", "ArrayList", "LinkedList", "Collection", "generic"],
        "集合": ["Collection", "Set", "Map", "List", "framework", "container"],
        "映射": ["Map", "HashMap", "TreeMap", "Hashtable", "key-value"],
        "泛型": ["generics", "generic type", "type parameter", "type safety", "wildcard"],
        "类型": ["type", "class", "data type", "primitive", "reference type"],

        # ========== 面向对象高级特性 ==========
        "抽象类": ["abstract class", "abstract method", "cannot instantiate", "subclass implement"],
        "内部类": ["inner class", "nested class", "static nested", "non-static nested", "anonymous class"],
        "匿名类": ["anonymous class", "anonymous inner class", "no name", "inline"],
        "枚举": ["enum", "enumeration", "constant", "fixed set"],
        "注解": ["annotation", "metadata", "@Override", "@Deprecated", "@SuppressWarnings"],
        "反射": ["reflection", "reflect", "Class object", "getMethod", "getField", "introspection"],
        "序列化": ["serialization", "Serializable", "writeObject", "readObject", "transient"],

        # ========== 内部类和嵌套类 ==========
        "内部类": ["inner class", "nested class", "static nested class", "non-static nested class", "anonymous class", "local class", "member class"],
        "嵌套类": ["nested class", "static nested", "inner class", "enclosing class"],
        "匿名类": ["anonymous class", "anonymous inner class", "no name", "inline", "new Class()"],
        "局部类": ["local class", "local inner class", "method scope", "block scope"],
        "成员类": ["member class", "member inner class", "field level"],
        "外部类": ["outer class", "enclosing class", "top-level class"],

        # ========== 并发和锁 ==========
        "可重入锁": ["ReentrantLock", "reentrant", "lock", "tryLock", "unlock"],
        "读写锁": ["ReentrantReadWriteLock", "read lock", "write lock", "shared lock", "exclusive lock"],
        "条件变量": ["Condition", "await", "signal", "signalAll", "wait", "notify"],
        "信号量": ["Semaphore", "permit", "acquire", "release", "counting semaphore"],
        "屏障": ["Barrier", "CyclicBarrier", "barrier", "synchronization barrier"],
        "倒计时锁存器": ["CountDownLatch", "latch", "count down", "await", "synchronization aid", "concurrent utility"],
        "交换器": ["Exchanger", "exchange", "thread exchange", "rendezvous"],
        "线程安全": ["thread-safe", "thread safety", "concurrent", "synchronized", "atomic"],
        "volatile": ["volatile", "visibility", "happens-before", "memory barrier", "atomic write"],
        "synchronized": ["synchronized", "monitor", "lock", "mutex", "intrinsic lock"],
        "并行": ["parallel", "parallelism", "concurrent", "simultaneous", "multi-thread"],
        "并行处理": ["parallel processing", "parallelize", "parallel stream", "concurrent processing"],
        "并发工具": ["concurrent utility", "concurrent tool", "synchronization aid", "thread coordination"],
        "等待": ["wait", "await", "block", "suspend", "pause"],

        # ========== Stream API ==========
        "流式": ["stream", "Stream API", "pipeline", "intermediate operation", "terminal operation"],
        "并行流": ["parallel stream", "parallel processing", "parallelize", "concurrent stream"],
        "串行流": ["sequential stream", "sequential processing", "serial stream"],
        "收集器": ["Collector", "Collectors", "toList", "toSet", "toMap", "groupingBy", "partitioningBy"],
        "归约操作": ["reduction", "reduce", "accumulate", "fold", "aggregation"],
        "中间操作": ["intermediate operation", "lazy evaluation", "filter", "map", "flatMap", "sorted"],
        "终端操作": ["terminal operation", "eager evaluation", "collect", "forEach", "reduce", "count"],

        # ========== 设计模式 ==========
        "工厂模式": ["Factory pattern", "Factory method", "Simple Factory", "Factory Design Pattern", "creational pattern", "object creation", "encapsulation"],
        "抽象工厂": ["Abstract Factory", "abstract factory method", "family of objects", "creational pattern"],
        "单例模式": ["Singleton pattern", "singleton", "single instance", "lazy initialization", "eager initialization"],
        "建造者模式": ["Builder pattern", "Builder", "step-by-step construction", "telescoping constructor"],
        "原型模式": ["Prototype pattern", "Prototype", "clone", "copy", "deep copy", "shallow copy"],
        "适配器模式": ["Adapter pattern", "Adapter", "wrapper", "interface conversion", "legacy code"],
        "装饰器模式": ["Decorator pattern", "Decorator", "wrapper", "add responsibility", "composition"],
        "代理模式": ["Proxy pattern", "Proxy", "surrogate", "virtual proxy", "remote proxy", "protection proxy"],
        "观察者模式": ["Observer pattern", "Observer", "publish-subscribe", "event listener", "notification"],
        "策略模式": ["Strategy pattern", "Strategy", "algorithm family", "interchangeable", "composition over inheritance"],
        "模板模式": ["Template Method pattern", "Template", "skeleton", "hook method", "abstract class"],
        "设计模式": ["Design pattern", "software design", "best practice", "architecture pattern"],
        "系统设计": ["System design", "architecture", "class design", "module design", "component design"],

        # ========== 递归和算法 ==========
        "递归": ["recursion", "recursive", "recursive method", "recursive call", "base case", "recursive case", "stack", "stack overflow"],
        "迭代": ["iteration", "iterative", "loop", "for loop", "while loop", "non-recursive"],
        "回溯": ["backtracking", "backtrack", "depth-first search", "DFS", "pruning"],
        "分治": ["divide and conquer", "divide-and-conquer", "split", "merge", "subproblem"],
        "动态规划": ["dynamic programming", "DP", "memoization", "optimal substructure", "overlapping subproblems"],
        "贪心": ["greedy", "greedy algorithm", "greedy approach", "local optimum"],
        "递归调用": ["recursive call", "recursion", "function call", "call stack"],
        "基线条件": ["base case", "termination condition", "stopping condition", "exit condition"],

        # ========== 泛型高级特性 ==========
        "类型擦除": ["type erasure", "erasure", "type inference", "bridge method", "generic type erasure"],
        "泛型擦除": ["type erasure", "erasure", "generic type erasure", "compile time", "runtime type"],
        "类型推断": ["type inference", "diamond operator", "<>", "compiler inference"],
        "通配符": ["wildcard", "?", "upper bounded wildcard", "lower bounded wildcard", "unbounded wildcard"],
        "上界": ["upper bound", "extends", "bounded type parameter", "covariance"],
        "下界": ["lower bound", "super", "bounded type parameter", "contravariance"],
        "PECS": ["PECS", "Producer Extends Consumer Super", "producer-consumer"],

        # ========== 内部类细分类型 ==========
        "成员内部类": ["member inner class", "member class", "instance field", "class level"],
        "静态内部类": ["static nested class", "static inner class", "class level", "no outer reference"],
        "局部内部类": ["local inner class", "local class", "method scope", "block scope"],

        # ========== Lambda 和函数式编程 ==========
        "Lambda": ["lambda", "lambda expression", "->", "functional interface", "anonymous function"],
        "表达式": ["expression", "lambda", "operator", "statement"],
        "函数式": ["functional", "Function", "Predicate", "Consumer", "Supplier", "functional programming"],
        "流": ["Stream", "stream", "pipeline", "intermediate operation", "terminal operation"],
        "过滤": ["filter", "Predicate", "condition", "select"],
        "映射": ["map", "transform", "convert", "Function"],
        "归约": ["reduce", "accumulate", "aggregate", "collector"],

        # ========== 并发编程 ==========
        "线程": ["thread", "Thread", "Runnable", "run", "start"],
        "进程": ["process", "thread", "concurrent", "parallel"],
        "同步": ["synchronization", "synchronized", "lock", "monitor", "thread-safe"],
        "异步": ["asynchronous", "async", "non-blocking", "future", "callback"],
        "锁": ["lock", "Lock", "ReentrantLock", "synchronized", "mutex"],
        "并发": ["concurrent", "concurrency", "thread-safe", "atomic", "volatile"],
        "原子": ["atomic", "AtomicInteger", "AtomicReference", "CAS", "compare-and-swap"],
        "线程池": ["thread pool", "Executor", "ExecutorService", "ThreadPoolExecutor"],

        # ========== 操作动词 ==========
        "创建": ["create", "new", "instantiate", "generate", "build"],
        "实现": ["implement", "implementation", "code", "develop"],
        "定义": ["define", "definition", "declare", "declaration"],
        "使用": ["use", "using", "utilize", "apply", "employ"],
        "调用": ["call", "invoke", "execute method", "method invocation"],
        "执行": ["execute", "run", "perform", "carry out"],
        "编译": ["compile", "compiler", "javac", "bytecode", "class file"],
        "运行": ["run", "execute", "java", "JVM", "runtime"],
        "继承": ["inherit", "extends", "derive", "subclass"],
        "重写": ["override", "redefine", "overwrite", "supersede"],
        "重载": ["overload", "overloading", "same name", "different parameters"],

        # ========== 概念和特性 ==========
        "转换": ["cast", "convert", "parse", "type cast", "type conversion"],
        "比较": ["compare", "equals", "compareTo", "equality", "comparison"],
        "排序": ["sort", "Comparable", "Comparator", "ordering", "arrange"],
        "搜索": ["search", "find", "indexOf", "lookup", "query"],
        "遍历": ["iterate", "loop", "for", "while", "traverse", "iteration"],
        "循环": ["loop", "for", "while", "do-while", "iteration", "repeat"],

        # ========== 区别和对比 ==========
        "区别": ["difference", "vs", "compare", "distinction", "contrast"],
        "关系": ["relationship", "relation", "connection", "association"],
        "作用": ["purpose", "function", "role", "use case"],
        "好处": ["benefit", "advantage", "merit", "why use"],
        "特点": ["feature", "characteristic", "property", "trait"],
        "意思": ["meaning", "definition", "what is", "explain"],
        "是什么": ["what is", "definition", "concept", "introduction"],
        "为什么": ["why", "reason", "purpose", "rationale"],
        "如何": ["how to", "how", "way", "approach", "method"],
        "怎样": ["how to", "how", "way", "approach"],

        # ========== 教育和作业相关 ==========
        "作业": ["assignment", "homework", "task", "project", "exercise"],
        "实验": ["experiment", "lab", "practical", "hands-on"],
        "报告": ["report", "documentation", "summary", "conclusion"],
        "代码": ["code", "snippet", "example", "sample", "source code"],
        "程序": ["program", "application", "software", "code"],
        "例子": ["example", "sample", "demonstration", "illustration", "code example"],
        "示例": ["example", "sample", "demo", "code snippet"],
        "举例": ["example", "for example", "such as", "demonstrate"],
        "图书管理": ["library management", "book management", "library system", "book borrowing"],
        "增删改查": ["CRUD", "create read update delete", "add remove modify query", "basic operations"],
        "数据分析": ["data analysis", "analyze data", "statistical analysis", "data processing"],
        "图表": ["chart", "graph", "diagram", "plot", "visualization"],
        "对比": ["comparison", "compare", "contrast", "difference"],
        "结论": ["conclusion", "summary", "finding", "result"],

        # ========== 停用词（不翻译） ==========
        "什么": [],
        "是": [],
        "的": [],
        "中": [],
        "里": [],
        "外": [],
        "上": [],
        "下": [],
        "请": [],
        "问": [],
        "哪些": [],
        "哪个": [],
        "谁": [],
        "哪里": [],
    }

    # 缩写映射（缩写 -> 全称）
    ABBREVIATIONS = {
        # Java 相关
        "JVM": ["Java Virtual Machine", "Java 虚拟机"],
        "JRE": ["Java Runtime Environment", "Java 运行时环境"],
        "JDK": ["Java Development Kit", "Java 开发工具包"],
        "API": ["Application Programming Interface", "应用程序接口"],
        "SDK": ["Software Development Kit", "软件开发工具包"],
        "IDE": ["Integrated Development Environment", "集成开发环境"],
        "OOP": ["Object-Oriented Programming", "面向对象编程"],
        "AOP": ["Aspect-Oriented Programming", "面向切面编程"],
        "MVC": ["Model-View-Controller", "模型视图控制器"],
        "MVP": ["Model-View-Presenter", "模型视图展示器"],
        "MVVM": ["Model-View-ViewModel", "模型视图视图模型"],
        "ORM": ["Object-Relational Mapping", "对象关系映射"],
        "JPA": ["Java Persistence API", "Java 持久化 API"],
        "JDBC": ["Java Database Connectivity", "Java 数据库连接"],
        "JNDI": ["Java Naming and Directory Interface", "Java 命名和目录接口"],
        "JMS": ["Java Message Service", "Java 消息服务"],
        "JTA": ["Java Transaction API", "Java 事务 API"],
        "JAX": ["Java API for XML", "Java XML API"],
        "JSP": ["JavaServer Pages", "Java 服务器页面"],
        "Servlet": ["Servlet", "小服务程序"],
        "POJO": ["Plain Old Java Object", "简单 Java 对象"],
        "Bean": ["JavaBean", "组件"],
        "DAO": ["Data Access Object", "数据访问对象"],
        "DTO": ["Data Transfer Object", "数据传输对象"],
        "VO": ["Value Object", "值对象"],
        "BO": ["Business Object", "业务对象"],
        
        # 通用编程
        "CPU": ["Central Processing Unit", "中央处理器"],
        "GPU": ["Graphics Processing Unit", "图形处理器"],
        "RAM": ["Random Access Memory", "随机存取存储器"],
        "ROM": ["Read-Only Memory", "只读存储器"],
        "OS": ["Operating System", "操作系统"],
        "DB": ["Database", "数据库"],
        "DBMS": ["Database Management System", "数据库管理系统"],
        "SQL": ["Structured Query Language", "结构化查询语言"],
        "NoSQL": ["Not Only SQL", "非关系型数据库"],
        "HTTP": ["HyperText Transfer Protocol", "超文本传输协议"],
        "HTTPS": ["HyperText Transfer Protocol Secure", "安全超文本传输协议"],
        "TCP": ["Transmission Control Protocol", "传输控制协议"],
        "IP": ["Internet Protocol", "网际协议"],
        "URL": ["Uniform Resource Locator", "统一资源定位符"],
        "URI": ["Uniform Resource Identifier", "统一资源标识符"],
        "XML": ["eXtensible Markup Language", "可扩展标记语言"],
        "JSON": ["JavaScript Object Notation", "JavaScript 对象表示法"],
        "HTML": ["HyperText Markup Language", "超文本标记语言"],
        "CSS": ["Cascading Style Sheets", "层叠样式表"],
        "DOM": ["Document Object Model", "文档对象模型"],
        "SAX": ["Simple API for XML", "简单 XML API"],
        "IO": ["Input/Output", "输入输出"],
        "NIO": ["New IO", "非阻塞 IO"],
        "BIO": ["Blocking IO", "阻塞 IO"],
        "GC": ["Garbage Collection", "垃圾回收"],
        "JIT": ["Just In Time", "即时编译"],
        "AOT": ["Ahead Of Time", "提前编译"],
        "CLI": ["Command Line Interface", "命令行界面"],
        "GUI": ["Graphical User Interface", "图形用户界面"],
        "UI": ["User Interface", "用户界面"],
        "UX": ["User Experience", "用户体验"],
        "QA": ["Quality Assurance", "质量保证"],
        "TDD": ["Test-Driven Development", "测试驱动开发"],
        "BDD": ["Behavior-Driven Development", "行为驱动开发"],
        "CI": ["Continuous Integration", "持续集成"],
        "CD": ["Continuous Deployment/Delivery", "持续部署/交付"],
        "DevOps": ["Development and Operations", "开发运维"],
        "SaaS": ["Software as a Service", "软件即服务"],
        "PaaS": ["Platform as a Service", "平台即服务"],
        "IaaS": ["Infrastructure as a Service", "基础设施即服务"],
        "REST": ["Representational State Transfer", "表述性状态转移"],
        "SOAP": ["Simple Object Access Protocol", "简单对象访问协议"],
        "RPC": ["Remote Procedure Call", "远程过程调用"],
        "RMI": ["Remote Method Invocation", "远程方法调用"],
        "SOA": ["Service-Oriented Architecture", "面向服务的架构"],
        "EDA": ["Event-Driven Architecture", "事件驱动架构"],
        "DDD": ["Domain-Driven Design", "领域驱动设计"],
        "UML": ["Unified Modeling Language", "统一建模语言"],
        "ER": ["Entity-Relationship", "实体关系"],
        "PK": ["Primary Key", "主键"],
        "FK": ["Foreign Key", "外键"],
        "Index": ["Index", "索引"],
        "BTree": ["B-Tree", "B 树"],
        "Hash": ["Hash", "哈希"],
        "LRU": ["Least Recently Used", "最近最少使用"],
        "FIFO": ["First In First Out", "先进先出"],
        "LIFO": ["Last In First Out", "后进先出"],
        "DFS": ["Depth-First Search", "深度优先搜索"],
        "BFS": ["Breadth-First Search", "广度优先搜索"],
        "BST": ["Binary Search Tree", "二叉搜索树"],
        "AVL": ["AVL Tree", "AVL 树"],
        "RB": ["Red-Black Tree", "红黑树"],
    }

    # 停用词
    STOPWORDS = {
        '的', '是', '在', '和', '了', '有', '我', '你', '他', '她', '它', '们',
        '这', '那', '个', '与', '或', '及', '等', '为', '以', '于', '也', '就',
        '都', '而', '着', '一个', '没有', '我们', '你们', '可以', '进行', '使用',
        '来', '去', '很', '更', '最', '把', '被', '让', '叫', '使', '令',
        '中', '上', '下', '里', '外', '前', '后', '时', '候', '请', '问',
        '什么', '怎样', '如何', '为什么', '哪些', '哪个', '谁', '哪里'
    }

    def __init__(self):
        self.translations = self.KEYWORD_TRANSLATIONS
        self.abbreviations = self.ABBREVIATIONS
        self.stopwords = self.STOPWORDS

    def rewrite(self, query: str, intent: str = "general") -> List[str]:
        """
        改写查询

        策略：
        1. 提取中文关键词
        2. 翻译为英文
        3. 处理缩写
        4. 返回原始查询 + 扩展关键词

        Args:
            query: 原始中文查询
            intent: 意图类型（用于调整改写策略）

        Returns:
            扩展后的查询列表
        """
        # 简单的字符匹配提取关键词
        expanded_terms = []

        # 1. 尝试匹配多字词（中文关键词翻译）
        for term, translations in self.translations.items():
            if term in query and translations:
                expanded_terms.extend(translations)

        # 2. 处理缩写（缩写 -> 全称）
        for abbr, full_names in self.abbreviations.items():
            if abbr.upper() in query.upper():
                # 添加全称（英文）
                expanded_terms.extend([name for name in full_names if not any('\u4e00' <= c <= '\u9fff' for c in name)])

        # 3. 提取英文单词（直接使用）
        import re
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', query)
        expanded_terms.extend(english_words)

        # 去重（保持顺序）
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen and len(term) > 1:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms
    
    def get_search_query(self, query: str) -> str:
        """
        生成用于检索的查询
        
        返回：原始查询 + 扩展的英文关键词
        """
        expanded = self.rewrite(query)
        
        if expanded:
            # 组合原始查询和英文关键词
            return query + " " + " ".join(expanded)
        
        return query
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词（包含中文和英文）
        """
        keywords = []
        
        # 提取已知的中文关键词
        for term in self.translations.keys():
            if term in query and term not in self.stopwords:
                keywords.append(term)
        
        # 提取英文单词
        import re
        english_words = re.findall(r'[a-zA-Z]+', query)
        keywords.extend(english_words)
        
        return keywords


# 全局实例
_rewriter = QueryRewriter()


def rewrite_query(query: str) -> str:
    """改写查询（便捷函数）"""
    return _rewriter.get_search_query(query)


def extract_keywords(query: str) -> List[str]:
    """提取关键词（便捷函数）"""
    return _rewriter.extract_keywords(query)
