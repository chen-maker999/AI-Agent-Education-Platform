"""
生成扩展测试数据集

基于现有 20 个样本，扩展到 100+ 样本
覆盖更多 Java 知识点、作业场景和实验报告场景
"""

import json
from datetime import datetime

# 基础样本模板
BASE_SAMPLES = [
    # Java 基础概念 (1-20)
    {
        "query_id": "Q001",
        "query_text": "Java 中什么是继承？如何实现继承？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["继承", "extends", "父类", "子类", "继承关系"],
        "expected_answer": "继承是面向对象编程的三大特性之一。在 Java 中，使用 extends 关键字实现继承，子类可以继承父类的属性和方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 继承章节"
    },
    {
        "query_id": "Q002",
        "query_text": "Java 中的多态是什么意思？请举例说明。",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["多态", "重写", "override", "父类引用", "子类对象"],
        "expected_answer": "多态是指同一个方法调用在不同对象上可以有不同的执行结果。主要通过方法重写和父类引用指向子类对象来实现。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 多态章节"
    },
    {
        "query_id": "Q003",
        "query_text": "Java 中的封装有什么好处？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["封装", "private", "访问控制", "安全性", "隐藏"],
        "expected_answer": "封装可以隐藏对象的内部细节，只暴露公共接口，提高代码的安全性和可维护性。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 封装章节"
    },
    {
        "query_id": "Q004",
        "query_text": "Java 中的抽象类和接口有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["抽象类", "接口", "abstract", "implements", "区别", "多重继承"],
        "expected_answer": "抽象类可以有构造方法和非抽象方法，子类使用 extends 继承；接口只能有常量和抽象方法 (Java 8 前)，类使用 implements 实现。一个类只能继承一个抽象类但可以实现多个接口。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 抽象类与接口章节"
    },
    {
        "query_id": "Q005",
        "query_text": "Java 中的异常处理机制是怎样的？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["异常", "try", "catch", "finally", "throw", "throws"],
        "expected_answer": "Java 使用 try-catch-finally 结构处理异常。try 块包含可能抛出异常的代码，catch 块捕获并处理异常，finally 块无论是否发生异常都会执行。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 异常处理章节"
    },
    {
        "query_id": "Q006",
        "query_text": "Java 中的集合框架有哪些主要接口和类？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["集合", "List", "Set", "Map", "ArrayList", "HashMap", "接口"],
        "expected_answer": "Java 集合框架主要包括 List(有序可重复)、Set(无序不重复)、Map(键值对) 三大接口。常用实现类有 ArrayList、LinkedList、HashSet、TreeSet、HashMap、TreeMap 等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 集合章节"
    },
    {
        "query_id": "Q007",
        "query_text": "Java 中的泛型有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["泛型", "类型参数", "类型安全", "类型擦除", "Generic"],
        "expected_answer": "泛型提供了编译时类型安全检查，避免了类型转换错误，使代码更简洁。泛型在编译后会被擦除为原始类型。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 泛型章节"
    },
    {
        "query_id": "Q008",
        "query_text": "Java 中的内部类有哪些类型？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["内部类", "成员内部类", "静态内部类", "局部内部类", "匿名内部类"],
        "expected_answer": "Java 中的内部类分为四种：成员内部类、静态内部类、局部内部类 (定义在方法中) 和匿名内部类 (没有名字的内部类)。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 内部类章节"
    },
    {
        "query_id": "Q009",
        "query_text": "Java 中的 Lambda 表达式是什么？有什么优点？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Lambda", "函数式编程", "函数式接口", "箭头运算符", "->"],
        "expected_answer": "Lambda 表达式是 Java 8 引入的函数式编程特性，使用->符号表示。它可以简化匿名内部类的写法，使代码更简洁，支持流式操作。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Lambda 表达式章节"
    },
    {
        "query_id": "Q010",
        "query_text": "Java 中的 Stream API 有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Stream", "流", "filter", "map", "reduce", "函数式", "聚合"],
        "expected_answer": "Stream API 用于处理集合数据，支持函数式操作如 filter 过滤、map 转换、reduce 聚合等。它采用惰性求值和链式调用，可以高效处理大数据。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Stream 章节"
    },
    {
        "query_id": "Q011",
        "query_text": "Java 作业中如何实现一个学生类？",
        "category": "java_homework",
        "difficulty_level": "easy",
        "expected_keywords": ["类", "学生", "属性", "方法", "构造器", "封装"],
        "expected_answer": "学生类应包含学号、姓名、成绩等属性，以及相应的 getter/setter 方法、构造方法和 toString 方法。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q012",
        "query_text": "Java 作业中如何实现继承和多态的例子？",
        "category": "java_homework",
        "difficulty_level": "medium",
        "expected_keywords": ["继承", "多态", "extends", "重写", "作业", "克隆"],
        "expected_answer": "可以定义一个 Animal 父类，然后创建 Dog、Cat 子类继承并重写 makeSound 方法，通过父类引用调用子类对象的方法展示多态。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q013",
        "query_text": "Java 作业中如何使用集合框架存储学生信息？",
        "category": "java_homework",
        "difficulty_level": "medium",
        "expected_keywords": ["集合", "ArrayList", "HashMap", "学生", "存储", "泛型"],
        "expected_answer": "可以使用 ArrayList<Student>存储多个学生对象，或使用 HashMap<String, Student>以学号为键存储学生信息。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q014",
        "query_text": "Java 作业中异常处理应该如何实现？",
        "category": "java_homework",
        "difficulty_level": "easy",
        "expected_keywords": ["异常", "try-catch", "作业", "错误处理", "抛出"],
        "expected_answer": "在可能出错的代码周围使用 try-catch 块，捕获特定异常类型，进行适当的错误处理或提示。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q015",
        "query_text": "Java 作业中接口如何使用？",
        "category": "java_homework",
        "difficulty_level": "medium",
        "expected_keywords": ["接口", "implements", "抽象方法", "作业", "常量"],
        "expected_answer": "定义接口使用 interface 关键字，类使用 implements 实现接口，必须实现接口中的所有抽象方法。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q016",
        "query_text": "计算机科学与技术专业导论实验的目的是什么？",
        "category": "experiment_report",
        "difficulty_level": "easy",
        "expected_keywords": ["实验目的", "计算机导论", "专业认知", "了解"],
        "expected_answer": "计算机导论实验旨在帮助学生了解计算机科学与技术专业的基本概念、发展历程和未来方向。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q017",
        "query_text": "实验报告中如何描述实验过程和结果？",
        "category": "experiment_report",
        "difficulty_level": "easy",
        "expected_keywords": ["实验过程", "实验结果", "步骤", "分析", "记录"],
        "expected_answer": "实验报告应详细记录实验步骤、操作方法、观察到的现象和得到的数据，并对结果进行分析和总结。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q018",
        "query_text": "实验报告中的实验总结应该包含哪些内容？",
        "category": "experiment_report",
        "difficulty_level": "easy",
        "expected_keywords": ["实验总结", "心得体会", "收获", "不足", "改进"],
        "expected_answer": "实验总结应包含实验收获、遇到的问题及解决方法、对实验内容的理解加深、以及需要改进的地方。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q019",
        "query_text": "Java 中 final 关键字有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["final", "常量", "不可变", "修饰符", "继承"],
        "expected_answer": "final 可以修饰类 (不可继承)、方法 (不可重写)、变量 (只能赋值一次)。final 变量即为常量。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 修饰符章节"
    },
    {
        "query_id": "Q020",
        "query_text": "Java 中的构造方法有什么特点？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["构造方法", "构造函数", "初始化", "new", "重载"],
        "expected_answer": "构造方法用于初始化对象，方法名与类名相同，没有返回类型，在 new 对象时自动调用。可以重载构造方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 类与对象章节"
    },
]

# 新增样本 (21-120)
NEW_SAMPLES = [
    # Java 数据类型和变量 (21-30)
    {
        "query_id": "Q021",
        "query_text": "Java 中有哪些基本数据类型？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["基本数据类型", "int", "double", "boolean", "char"],
        "expected_answer": "Java 有 8 种基本数据类型：byte、short、int、long(整数类型)，float、double(浮点类型)，char(字符类型)，boolean(布尔类型)。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 数据类型章节"
    },
    {
        "query_id": "Q022",
        "query_text": "Java 中的自动装箱和拆箱是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["装箱", "拆箱", "包装类", "Integer", "自动转换"],
        "expected_answer": "自动装箱是将基本类型自动转换为包装类类型，自动拆箱是将包装类自动转换为基本类型。例如 int 和 Integer 之间的转换。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 包装类章节"
    },
    {
        "query_id": "Q023",
        "query_text": "Java 中 String 和 StringBuilder 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["String", "StringBuilder", "可变", "不可变", "性能"],
        "expected_answer": "String 是不可变的，每次修改都会创建新对象；StringBuilder 是可变的，适合频繁修改字符串的场景，性能更好。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 字符串章节"
    },
    {
        "query_id": "Q024",
        "query_text": "Java 中的访问修饰符有哪些？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["访问修饰符", "public", "private", "protected", "default"],
        "expected_answer": "Java 有四种访问修饰符：public(公共)、protected(受保护)、default(默认，不写)、private(私有)，访问范围依次减小。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 访问控制章节"
    },
    {
        "query_id": "Q025",
        "query_text": "Java 中的 static 关键字有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["static", "静态", "类变量", "类方法", "共享"],
        "expected_answer": "static 修饰的成员属于类而不是对象，所有对象共享同一份静态成员。静态方法只能访问静态变量和其他静态方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 静态成员章节"
    },
    {
        "query_id": "Q026",
        "query_text": "Java 中的 this 关键字指什么？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["this", "当前对象", "引用", "调用构造器"],
        "expected_answer": "this 关键字指向当前对象的引用，可用于区分成员变量和局部变量，也可用于调用其他构造方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - this 关键字章节"
    },
    {
        "query_id": "Q027",
        "query_text": "Java 中的 super 关键字有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["super", "父类", "调用父类方法", "调用父类构造器"],
        "expected_answer": "super 用于引用父类对象，可以调用父类的构造方法、成员变量和被重写的方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - super 关键字章节"
    },
    {
        "query_id": "Q028",
        "query_text": "Java 中的方法重载和重写有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["重载", "重写", "override", "overload", "区别"],
        "expected_answer": "重载发生在同一类中，方法名相同参数不同；重写发生在父子类之间，子类重新定义父类的方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 方法章节"
    },
    {
        "query_id": "Q029",
        "query_text": "Java 中的可变参数如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["可变参数", "varargs", "...", "不定参数"],
        "expected_answer": "可变参数使用...表示，允许方法接收任意数量的同类型参数。可变参数必须是参数列表的最后一个。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 方法参数章节"
    },
    {
        "query_id": "Q030",
        "query_text": "Java 中的枚举类型有什么特点？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["枚举", "enum", "常量", "类型安全"],
        "expected_answer": "枚举是一种特殊的类，用于定义一组常量。枚举类型提供了类型安全和代码可读性，可以包含构造方法、字段和方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 枚举章节"
    },
    
    # Java 集合框架深入 (31-45)
    {
        "query_id": "Q031",
        "query_text": "ArrayList 和 LinkedList 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["ArrayList", "LinkedList", "数组", "链表", "性能对比"],
        "expected_answer": "ArrayList 基于动态数组，随机访问快；LinkedList 基于双向链表，插入删除快。ArrayList 适合查询多的场景，LinkedList 适合增删多的场景。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 集合章节"
    },
    {
        "query_id": "Q032",
        "query_text": "HashMap 的工作原理是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["HashMap", "哈希表", "桶", "链表", "红黑树", "put", "get"],
        "expected_answer": "HashMap 基于哈希表实现，使用 key 的 hashCode 计算存储位置。Java 8 中当链表长度超过 8 时转换为红黑树，提高查询效率。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Map 章节"
    },
    {
        "query_id": "Q033",
        "query_text": "HashSet 如何保证元素不重复？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["HashSet", "不重复", "hashCode", "equals"],
        "expected_answer": "HashSet 通过 hashCode 和 equals 方法保证元素不重复。添加元素时先计算 hashCode，如果相同再调用 equals 比较。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Set 章节"
    },
    {
        "query_id": "Q034",
        "query_text": "TreeMap 和 HashMap 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["TreeMap", "HashMap", "排序", "红黑树", "哈希表"],
        "expected_answer": "TreeMap 基于红黑树，元素按键的自然顺序或自定义比较器排序；HashMap 基于哈希表，不保证顺序。TreeMap 查询稍慢但有序。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Map 章节"
    },
    {
        "query_id": "Q035",
        "query_text": "Java 中的 Iterator 如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["Iterator", "迭代器", "hasNext", "next", "遍历"],
        "expected_answer": "Iterator 用于遍历集合，主要方法有 hasNext() 判断是否有下一个元素，next() 获取下一个元素，remove() 删除当前元素。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 迭代器章节"
    },
    {
        "query_id": "Q036",
        "query_text": "Java 中的 Comparable 和 Comparator 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Comparable", "Comparator", "比较器", "排序", "compareTo", "compare"],
        "expected_answer": "Comparable 是自然排序，类实现 compareTo 方法；Comparator 是定制排序，实现 compare 方法。一个类只能有一个自然排序但可以有多个定制排序。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 排序章节"
    },
    {
        "query_id": "Q037",
        "query_text": "Java 中的 ConcurrentHashMap 有什么特点？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["ConcurrentHashMap", "线程安全", "并发", "分段锁", "CAS"],
        "expected_answer": "ConcurrentHashMap 是线程安全的 HashMap，Java 8 使用 CAS+synchronized 实现，比 Hashtable 性能更好。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 并发集合章节"
    },
    {
        "query_id": "Q038",
        "query_text": "Java 中的 PriorityQueue 是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["PriorityQueue", "优先队列", "堆", "排序"],
        "expected_answer": "PriorityQueue 是基于优先堆的队列，元素按优先级出队。默认是最小堆，可以通过 Comparator 自定义排序。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 队列章节"
    },
    {
        "query_id": "Q039",
        "query_text": "Java 中的 Arrays 工具类有哪些常用方法？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["Arrays", "工具类", "sort", "binarySearch", "fill", "copyOf"],
        "expected_answer": "Arrays 提供了数组操作方法：sort 排序、binarySearch 二分查找、fill 填充、copyOf 复制、equals 比较、toString 转字符串等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 数组章节"
    },
    {
        "query_id": "Q040",
        "query_text": "Java 中的 Collections 工具类有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["Collections", "工具类", "排序", "查找", "同步"],
        "expected_answer": "Collections 提供了集合操作方法：sort 排序、shuffle 洗牌、reverse 反转、binarySearch 查找、synchronizedXxx 同步包装等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 集合工具章节"
    },
    
    # Java 异常处理深入 (41-50)
    {
        "query_id": "Q041",
        "query_text": "Java 中的异常分为哪几类？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["异常分类", "checked", "unchecked", "Error", "Exception"],
        "expected_answer": "Java 异常分为 Error(错误) 和 Exception(异常)。Exception 又分为 checked(编译时检查) 和 unchecked(运行时) 异常。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 异常章节"
    },
    {
        "query_id": "Q042",
        "query_text": "Java 中的 try-with-resources 是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["try-with-resources", "自动关闭", "AutoCloseable", "资源管理"],
        "expected_answer": "try-with-resources 是 Java 7 引入的语法，自动关闭实现了 AutoCloseable 接口的资源，无需手动调用 close 方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 异常处理章节"
    },
    {
        "query_id": "Q043",
        "query_text": "Java 中如何自定义异常类？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["自定义异常", "继承", "Exception", "构造方法"],
        "expected_answer": "自定义异常需要继承 Exception 或 RuntimeException 类，提供构造方法调用父类构造器，可以添加自定义属性和方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 自定义异常章节"
    },
    {
        "query_id": "Q044",
        "query_text": "Java 中的 throw 和 throws 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["throw", "throws", "抛出异常", "区别"],
        "expected_answer": "throw 用于在方法体内抛出一个具体异常对象；throws 用于方法声明，表示该方法可能抛出的异常类型。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 异常抛出章节"
    },
    {
        "query_id": "Q045",
        "query_text": "Java 中 finally 块一定会执行吗？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["finally", "一定执行", "System.exit", "特殊情况"],
        "expected_answer": "finally 块通常会执行，但在 System.exit() 调用、线程死亡、JVM 崩溃等极端情况下不会执行。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - finally 章节"
    },
    
    # Java IO 和 NIO (46-55)
    {
        "query_id": "Q046",
        "query_text": "Java 中的 IO 流分为哪几类？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["IO 流", "字节流", "字符流", "InputStream", "Reader"],
        "expected_answer": "Java IO 流分为字节流 (InputStream/OutputStream) 和字符流 (Reader/Writer)。字节流处理二进制数据，字符流处理文本数据。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - IO 章节"
    },
    {
        "query_id": "Q047",
        "query_text": "Java 中的 BufferedReader 有什么优点？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["BufferedReader", "缓冲", "readLine", "性能"],
        "expected_answer": "BufferedReader 提供缓冲功能，减少磁盘读写次数，提高读取效率。readLine 方法可以一次读取一行文本。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 缓冲流章节"
    },
    {
        "query_id": "Q048",
        "query_text": "Java 中的序列化是什么？如何实现？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["序列化", "Serializable", "对象持久化", "transient"],
        "expected_answer": "序列化是将对象转换为字节流的过程，实现 Serializable 接口即可。transient 修饰的字段不会被序列化。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 序列化章节"
    },
    {
        "query_id": "Q049",
        "query_text": "Java 中的 File 类如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["File", "文件", "路径", "创建", "删除"],
        "expected_answer": "File 类表示文件或目录的路径名，可以创建、删除、检查文件是否存在、获取文件信息等，但不能读写文件内容。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - File 章节"
    },
    {
        "query_id": "Q050",
        "query_text": "Java 中的 NIO 和传统 IO 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["NIO", "IO", "缓冲区", "通道", "选择器", "非阻塞"],
        "expected_answer": "NIO 基于缓冲区和通道，支持非阻塞 IO 和选择器，适合高并发场景；传统 IO 基于流，是阻塞式的。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - NIO 章节"
    },
    
    # Java 多线程 (51-65)
    {
        "query_id": "Q051",
        "query_text": "Java 中如何创建线程？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["线程", "Thread", "Runnable", "创建"],
        "expected_answer": "创建线程有两种方式：继承 Thread 类重写 run 方法，或实现 Runnable 接口作为 Thread 的参数。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 线程章节"
    },
    {
        "query_id": "Q052",
        "query_text": "Java 中的 synchronized 关键字有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["synchronized", "同步", "锁", "线程安全"],
        "expected_answer": "synchronized 用于保证线程同步，可以修饰方法或代码块，确保同一时刻只有一个线程执行同步代码。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 同步章节"
    },
    {
        "query_id": "Q053",
        "query_text": "Java 中的 volatile 关键字有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["volatile", "可见性", "有序性", "内存屏障"],
        "expected_answer": "volatile 保证变量的可见性 (一个线程修改后其他线程立即可见) 和有序性 (禁止指令重排序)，但不保证原子性。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - volatile 章节"
    },
    {
        "query_id": "Q054",
        "query_text": "Java 中的线程池有什么好处？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["线程池", "ExecutorService", "复用", "性能"],
        "expected_answer": "线程池可以复用线程，减少线程创建销毁的开销，控制并发数量，提高响应速度。常用 Executors 工厂类创建。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 线程池章节"
    },
    {
        "query_id": "Q055",
        "query_text": "Java 中的 wait 和 sleep 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["wait", "sleep", "区别", "锁释放"],
        "expected_answer": "wait 是 Object 的方法，会释放锁，需要 notify 唤醒；sleep 是 Thread 的方法，不释放锁，时间到自动唤醒。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 线程通信章节"
    },
    {
        "query_id": "Q056",
        "query_text": "Java 中的 ThreadLocal 是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["ThreadLocal", "线程本地变量", "隔离", "副本"],
        "expected_answer": "ThreadLocal 为每个线程提供独立的变量副本，实现线程间数据隔离，常用于数据库连接、Session 管理等场景。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - ThreadLocal 章节"
    },
    {
        "query_id": "Q057",
        "query_text": "Java 中的 CountDownLatch 如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["CountDownLatch", "倒计时", "等待", "并发工具"],
        "expected_answer": "CountDownLatch 允许一个或多个线程等待其他线程完成操作。初始化时指定计数，countDown 减 1，await 等待计数归零。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 并发工具章节"
    },
    {
        "query_id": "Q058",
        "query_text": "Java 中的 ReentrantLock 和 synchronized 有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["ReentrantLock", "synchronized", "锁", "区别"],
        "expected_answer": "ReentrantLock 是 API 层面的锁，支持公平锁、可中断、超时等特性；synchronized 是 JVM 层面的锁，使用更简单。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 锁章节"
    },
    {
        "query_id": "Q059",
        "query_text": "Java 中的 Callable 和 Future 是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Callable", "Future", "返回值", "异步"],
        "expected_answer": "Callable 类似 Runnable 但有返回值，Future 用于获取异步计算的结果。通常配合线程池使用。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - Callable 章节"
    },
    {
        "query_id": "Q060",
        "query_text": "Java 中的原子类 AtomicInteger 有什么特点？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["AtomicInteger", "原子操作", "CAS", "线程安全"],
        "expected_answer": "AtomicInteger 提供原子操作，基于 CAS 实现，无需加锁即可保证线程安全，性能优于 synchronized。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 原子类章节"
    },
    
    # Java 8+ 新特性 (61-75)
    {
        "query_id": "Q061",
        "query_text": "Java 8 中的 Optional 类有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Optional", "空指针", "null 检查", "函数式"],
        "expected_answer": "Optional 用于包装可能为 null 的值，避免空指针异常。常用方法有 ofNullable、orElse、ifPresent 等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Optional 章节"
    },
    {
        "query_id": "Q062",
        "query_text": "Java 8 中的方法引用如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["方法引用", "::", "Lambda", "简化"],
        "expected_answer": "方法引用使用::运算符，是 Lambda 表达式的简化形式。包括静态方法引用、实例方法引用、构造器引用等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 方法引用章节"
    },
    {
        "query_id": "Q063",
        "query_text": "Java 8 中的 Stream 如何并行处理？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["parallelStream", "并行", "并发", "性能"],
        "expected_answer": "使用 parallelStream() 或 stream().parallel() 创建并行流，利用多核 CPU 并行处理数据，适合大数据量场景。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 并行流章节"
    },
    {
        "query_id": "Q064",
        "query_text": "Java 8 中的 Collectors 有哪些常用方法？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Collectors", "toList", "toMap", "joining", "groupingBy"],
        "expected_answer": "Collectors 提供了收集操作：toList 转列表、toMap 转 Map、joining 拼接字符串、groupingBy 分组、summingInt 求和等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Collectors 章节"
    },
    {
        "query_id": "Q065",
        "query_text": "Java 9 中的 Stream 有什么新特性？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["Java 9", "Stream", "takeWhile", "dropWhile", "iterate"],
        "expected_answer": "Java 9 为 Stream 添加了 takeWhile、dropWhile 方法，以及支持三个参数的 iterate 方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Java9 新特性章节"
    },
    
    # 设计模式 (76-85)
    {
        "query_id": "Q076",
        "query_text": "Java 中的单例模式如何实现？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["单例", "Singleton", "饿汉式", "懒汉式", "双重检查"],
        "expected_answer": "单例模式确保一个类只有一个实例。实现方式有饿汉式、懒汉式、双重检查锁定、静态内部类、枚举等。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 设计模式章节"
    },
    {
        "query_id": "Q077",
        "query_text": "Java 中的工厂模式有什么优点？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["工厂模式", "解耦", "创建对象", "扩展性"],
        "expected_answer": "工厂模式将对象创建与使用分离，降低耦合度，便于扩展和维护。有简单工厂、工厂方法、抽象工厂三种形式。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 工厂模式章节"
    },
    {
        "query_id": "Q078",
        "query_text": "Java 中的观察者模式如何实现？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["观察者", "Observer", "发布订阅", "事件监听"],
        "expected_answer": "观察者模式定义对象间一对多依赖，主题变化时通知所有观察者。Java 提供了 Observable 类和 Observer 接口。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 观察者模式章节"
    },
    
    # 作业场景题 (86-100)
    {
        "query_id": "Q086",
        "query_text": "Java 作业中如何设计一个图书管理系统？",
        "category": "java_homework",
        "difficulty_level": "hard",
        "expected_keywords": ["图书管理", "系统设计", "类设计", "增删改查"],
        "expected_answer": "图书管理系统需要设计 Book 类、User 类、Library 类等，实现图书的增删改查、借阅归还等功能。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q087",
        "query_text": "Java 作业中如何实现一个简单的计算器？",
        "category": "java_homework",
        "difficulty_level": "easy",
        "expected_keywords": ["计算器", "加减乘除", "方法", "作业"],
        "expected_answer": "计算器可以定义 add、subtract、multiply、divide 方法，接收两个参数返回计算结果，注意处理除零异常。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q088",
        "query_text": "Java 作业中如何实现文件的读写操作？",
        "category": "java_homework",
        "difficulty_level": "medium",
        "expected_keywords": ["文件读写", "IO", "BufferedReader", "FileWriter", "作业"],
        "expected_answer": "使用 BufferedReader 读取文件，FileWriter 或 BufferedWriter 写入文件，注意使用 try-with-resources 自动关闭流。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q089",
        "query_text": "Java 作业中如何实现多线程下载器？",
        "category": "java_homework",
        "difficulty_level": "hard",
        "expected_keywords": ["多线程", "下载器", "线程池", "并发", "作业"],
        "expected_answer": "多线程下载器可以使用线程池管理多个下载线程，每个线程负责下载文件的一部分，最后合并。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q090",
        "query_text": "Java 作业中如何实现一个简单的聊天程序？",
        "category": "java_homework",
        "difficulty_level": "hard",
        "expected_keywords": ["聊天程序", "Socket", "网络编程", "多线程", "作业"],
        "expected_answer": "聊天程序使用 Socket 编程，服务器端用 ServerSocket 监听端口，客户端用 Socket 连接，使用多线程处理多个客户端。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    
    # 实验报告场景题 (91-100)
    {
        "query_id": "Q091",
        "query_text": "实验报告中如何分析实验数据？",
        "category": "experiment_report",
        "difficulty_level": "medium",
        "expected_keywords": ["数据分析", "图表", "对比", "结论"],
        "expected_answer": "实验数据分析应包括数据整理、图表展示、对比分析、异常值处理等，最后得出科学合理的结论。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q092",
        "query_text": "实验报告中的参考文献如何格式？",
        "category": "experiment_report",
        "difficulty_level": "easy",
        "expected_keywords": ["参考文献", "格式", "引用", "规范"],
        "expected_answer": "参考文献应按规范格式列出，包括作者、标题、出版社/期刊、年份等信息，按出现顺序或字母顺序排列。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q093",
        "query_text": "实验报告中如何描述实验环境？",
        "category": "experiment_report",
        "difficulty_level": "easy",
        "expected_keywords": ["实验环境", "硬件", "软件", "配置"],
        "expected_answer": "实验环境应详细描述硬件配置 (CPU、内存等)、软件环境 (操作系统、开发工具、版本等)、网络环境等。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q094",
        "query_text": "实验报告中如何处理实验失败的情况？",
        "category": "experiment_report",
        "difficulty_level": "medium",
        "expected_keywords": ["实验失败", "问题分析", "解决方案", "反思"],
        "expected_answer": "实验失败时应详细记录失败现象，分析可能原因，尝试解决方案，并在总结中反思改进措施。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q095",
        "query_text": "实验报告的摘要应该怎么写？",
        "category": "experiment_report",
        "difficulty_level": "medium",
        "expected_keywords": ["摘要", "概述", "目的", "方法", "结论"],
        "expected_answer": "摘要应简明扼要地概括实验目的、方法、主要结果和结论，一般 200-300 字，让读者快速了解实验内容。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q096",
        "query_text": "Java 中的注释有哪些类型？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["注释", "单行", "多行", "文档注释", "javadoc"],
        "expected_answer": "Java 有三种注释：单行注释//、多行注释/* */、文档注释/** */。文档注释可用于生成 API 文档。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 基础章节"
    },
    {
        "query_id": "Q097",
        "query_text": "Java 中的运算符有哪些？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["运算符", "算术", "关系", "逻辑", "位运算"],
        "expected_answer": "Java 运算符包括算术运算符 (+-*/)、关系运算符 (><==)、逻辑运算符 (&&||!)、位运算符 (&|^~)、赋值运算符等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 运算符章节"
    },
    {
        "query_id": "Q098",
        "query_text": "Java 中的流程控制语句有哪些？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["流程控制", "if", "switch", "for", "while"],
        "expected_answer": "Java 流程控制包括条件语句 (if-else、switch-case) 和循环语句 (for、while、do-while)，以及 break、continue 跳转语句。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 流程控制章节"
    },
    {
        "query_id": "Q099",
        "query_text": "Java 中的数组如何声明和初始化？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["数组", "声明", "初始化", "遍历"],
        "expected_answer": "数组声明：int[] arr 或 int arr[]；初始化：new int[5] 或{1,2,3}；遍历：for 循环或 foreach 循环。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 数组章节"
    },
    {
        "query_id": "Q100",
        "query_text": "Java 中的包 (package) 有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["包", "package", "命名空间", "组织", "import"],
        "expected_answer": "包用于组织类，提供命名空间管理，避免命名冲突。使用 package 声明包，import 导入其他包的类。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 包章节"
    },
    {
        "query_id": "Q101",
        "query_text": "Java 中的递归方法如何实现？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["递归", "基线条件", "递归调用", "栈"],
        "expected_answer": "递归方法需要定义基线条件 (终止条件) 和递归调用。每次递归调用都会将当前状态压入栈，直到达到基线条件。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 方法章节"
    },
    {
        "query_id": "Q102",
        "query_text": "Java 中的浅拷贝和深拷贝有什么区别？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["浅拷贝", "深拷贝", "clone", "引用复制"],
        "expected_answer": "浅拷贝只复制对象本身和基本类型字段，引用类型字段仍指向原对象；深拷贝会递归复制所有引用对象，创建完全独立的新对象。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 克隆章节"
    },
    {
        "query_id": "Q103",
        "query_text": "Java 中的反射机制是什么？有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["反射", "Class", "运行时", "动态代理", "框架"],
        "expected_answer": "反射允许在运行时获取类的信息并操作对象的属性和方法。广泛用于框架开发、动态代理、依赖注入等场景。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 反射章节"
    },
    {
        "query_id": "Q104",
        "query_text": "Java 中的注解 (Annotation) 如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["注解", "Annotation", "元数据", "自定义注解"],
        "expected_answer": "注解是代码中的元数据，可用于编译检查、运行时处理。可以自定义注解，配合反射实现各种框架功能。",
        "source_document_hint": "Core Java Volume II Advanced Features 11th Edition.pdf - 注解章节"
    },
    {
        "query_id": "Q105",
        "query_text": "Java 中的泛型擦除是什么？有什么影响？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["泛型擦除", "类型擦除", "运行时", "桥接方法"],
        "expected_answer": "泛型擦除是指泛型信息在编译后被擦除，运行时无法获取泛型类型。这导致无法创建泛型数组、无法使用 instanceof 检查泛型类型等限制。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 泛型章节"
    },
    
    # 补充样本 (106-120)
    {
        "query_id": "Q106",
        "query_text": "Java 中的正则表达式如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["正则表达式", "Pattern", "Matcher", "匹配", "分组"],
        "expected_answer": "Java 使用 Pattern 和 Matcher 类处理正则表达式。Pattern 编译正则，Matcher 执行匹配，支持 find、matches、group 等操作。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 正则表达式章节"
    },
    {
        "query_id": "Q107",
        "query_text": "Java 中的日期时间 API 有哪些？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["日期时间", "LocalDate", "LocalDateTime", "DateTimeFormatter", "Java8"],
        "expected_answer": "Java 8 引入了新的日期时间 API：LocalDate(日期)、LocalTime(时间)、LocalDateTime(日期时间)、DateTimeFormatter(格式化)，比旧 API 更简洁安全。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 日期时间章节"
    },
    {
        "query_id": "Q108",
        "query_text": "Java 中的 BigDecimal 有什么用途？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["BigDecimal", "精确计算", "浮点数", "货币"],
        "expected_answer": "BigDecimal 用于精确的浮点数运算，避免 double 的精度丢失问题，适合金融计算等对精度要求高的场景。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 数值类型章节"
    },
    {
        "query_id": "Q109",
        "query_text": "Java 中的 Random 类如何生成随机数？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["Random", "随机数", "nextInt", "nextDouble"],
        "expected_answer": "Random 类提供多种随机数生成方法：nextInt 生成随机整数，nextDouble 生成 0-1 之间的随机小数，nextBoolean 生成随机布尔值。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 随机数章节"
    },
    {
        "query_id": "Q110",
        "query_text": "Java 中的 Math 类有哪些常用方法？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["Math", "数学函数", "sqrt", "pow", "abs", "round"],
        "expected_answer": "Math 类提供数学运算方法：sqrt 开平方、pow 幂运算、abs 绝对值、round 四舍五入、max/min 最大最小值、random 随机数等。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Math 章节"
    },
    {
        "query_id": "Q111",
        "query_text": "Java 作业中如何实现一个简单的银行系统？",
        "category": "java_homework",
        "difficulty_level": "hard",
        "expected_keywords": ["银行系统", "账户", "存款", "取款", "转账", "作业"],
        "expected_answer": "银行系统需要设计 Account 类，包含账户号、余额等属性，实现存款、取款、转账、查询余额等方法，注意线程安全和异常处理。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q112",
        "query_text": "Java 作业中如何实现学生成绩管理系统？",
        "category": "java_homework",
        "difficulty_level": "hard",
        "expected_keywords": ["成绩管理", "学生", "课程", "分数", "统计", "作业"],
        "expected_answer": "成绩管理系统需要设计 Student、Course、Score 等类，实现成绩录入、查询、统计 (平均分、最高分、排名) 等功能。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q113",
        "query_text": "Java 作业中如何实现一个简单的游戏 (如猜数字)？",
        "category": "java_homework",
        "difficulty_level": "medium",
        "expected_keywords": ["游戏", "猜数字", "随机数", "循环", "作业"],
        "expected_answer": "猜数字游戏使用 Random 生成随机数，用循环接收用户输入，根据输入给出提示 (大了/小了)，直到猜中为止。",
        "source_document_hint": "面向对象程序设计（Java）（作业）"
    },
    {
        "query_id": "Q114",
        "query_text": "实验报告中如何绘制实验结果图表？",
        "category": "experiment_report",
        "difficulty_level": "medium",
        "expected_keywords": ["图表", "可视化", "Excel", "数据展示"],
        "expected_answer": "实验结果图表可使用 Excel、Python matplotlib 等工具绘制，选择合适的图表类型 (柱状图、折线图、饼图等)，清晰展示数据关系。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q115",
        "query_text": "实验报告中如何进行误差分析？",
        "category": "experiment_report",
        "difficulty_level": "medium",
        "expected_keywords": ["误差分析", "系统误差", "随机误差", "精度"],
        "expected_answer": "误差分析应包括误差来源识别 (系统误差、随机误差)、误差计算、误差对结果的影响分析、减小误差的方法等。",
        "source_document_hint": "计算机科学与技术专业导论（实验报告）"
    },
    {
        "query_id": "Q116",
        "query_text": "Java 中的断言 (assert) 如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["断言", "assert", "调试", "条件检查"],
        "expected_answer": "断言用于调试和测试，assert 后跟布尔表达式，表达式为 false 时抛出 AssertionError。生产环境通常禁用断言。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 断言章节"
    },
    {
        "query_id": "Q117",
        "query_text": "Java 中的枚举如何定义方法和属性？",
        "category": "java_fundamentals",
        "difficulty_level": "hard",
        "expected_keywords": ["枚举", "enum", "方法", "属性", "构造器"],
        "expected_answer": "枚举可以像普通类一样定义属性、方法和构造器。每个枚举常量可以有自己的实现，枚举还可以实现接口。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - 枚举进阶章节"
    },
    {
        "query_id": "Q118",
        "query_text": "Java 中的 var 关键字 (Java 10+) 有什么作用？",
        "category": "java_fundamentals",
        "difficulty_level": "easy",
        "expected_keywords": ["var", "类型推断", "局部变量", "Java10"],
        "expected_answer": "var 用于局部变量类型推断，编译器根据初始化值推断变量类型。var 不是关键字，仍可作为变量名使用。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Java10 新特性章节"
    },
    {
        "query_id": "Q119",
        "query_text": "Java 中的 record 类 (Java 14+) 是什么？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["record", "数据类", "不可变", "Java14"],
        "expected_answer": "record 是 Java 14 引入的语法，用于创建不可变的数据类，自动生成构造器、getter、equals、hashCode、toString 方法。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Java14 新特性章节"
    },
    {
        "query_id": "Q120",
        "query_text": "Java 中的 switch 表达式 (Java 14+) 如何使用？",
        "category": "java_fundamentals",
        "difficulty_level": "medium",
        "expected_keywords": ["switch 表达式", "箭头语法", "yield", "Java14"],
        "expected_answer": "Java 14 改进了 switch，支持箭头语法 (->) 和作为表达式返回值。使用 yield 关键字返回值，无需 break。",
        "source_document_hint": "Core Java Volume I Fundamentals 11th Edition.pdf - Java14 新特性章节"
    },
]

def generate_dataset():
    """生成完整的测试数据集"""
    all_samples = BASE_SAMPLES + NEW_SAMPLES
    
    # 计算分布
    category_dist = {}
    difficulty_dist = {}
    
    for sample in all_samples:
        cat = sample["category"]
        diff = sample["difficulty_level"]
        category_dist[cat] = category_dist.get(cat, 0) + 1
        difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
    
    dataset = {
        "description": "RAG 系统评估测试数据集 - 基于 rag-data 导入的课程资料",
        "version": "2.0.0",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "total_samples": len(all_samples),
        "samples": all_samples,
        "category_distribution": category_dist,
        "difficulty_distribution": difficulty_dist,
        "coverage": {
            "java_fundamentals": "Java 基础概念、数据类型、集合框架、异常处理、IO、多线程、Java8+ 新特性、设计模式",
            "java_homework": "学生类实现、继承多态示例、集合应用、异常处理、文件 IO、综合项目",
            "experiment_report": "实验目的、过程记录、数据分析、总结反思、报告格式"
        }
    }
    
    return dataset


if __name__ == "__main__":
    dataset = generate_dataset()
    
    # 保存为 JSON 文件
    output_path = "evaluation_tools/test_dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"测试数据集已生成：{output_path}")
    print(f"  总样本数：{dataset['total_samples']}")
    print(f"  类别分布：{dataset['category_distribution']}")
    print(f"  难度分布：{dataset['difficulty_distribution']}")
