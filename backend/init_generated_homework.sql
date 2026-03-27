-- 生成作业表
CREATE TABLE IF NOT EXISTS generated_homework (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    homework_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    course VARCHAR(100),
    course_id VARCHAR(100),
    source_type VARCHAR(50) DEFAULT 'knowledge_base',
    source_doc_id VARCHAR(100),
    file_url TEXT,
    file_size INTEGER DEFAULT 0,
    file_key VARCHAR(500),
    question_count INTEGER DEFAULT 0,
    difficulty VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    created_by VARCHAR(100),
    generation_params JSON DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_generated_homework_homework_id ON generated_homework(homework_id);
CREATE INDEX IF NOT EXISTS idx_generated_homework_course_id ON generated_homework(course_id);
CREATE INDEX IF NOT EXISTS idx_generated_homework_status ON generated_homework(status);
CREATE INDEX IF NOT EXISTS idx_generated_homework_created_at ON generated_homework(created_at);
