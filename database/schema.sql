-- 合同模板表
CREATE TABLE contract_templates (
    id SERIAL PRIMARY KEY,
    province TEXT NOT NULL,
    type TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date DATE,
    template_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 字段定义表
CREATE TABLE template_fields (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES contract_templates(id),
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL,
    section TEXT NOT NULL,
    is_required BOOLEAN,
    validation_rules JSONB,
    default_value TEXT,
    description TEXT
);

-- 选项值表(用于下拉选择等)
CREATE TABLE field_options (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES template_fields(id),
    option_value TEXT NOT NULL,
    option_label TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE
);

-- 特殊条款表
CREATE TABLE special_clauses (
    id SERIAL PRIMARY KEY,
    province TEXT NOT NULL,
    category TEXT NOT NULL,
    clause_text TEXT NOT NULL,
    variables JSONB,
    prerequisites JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 法律解释表
CREATE TABLE legal_explanations (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES template_fields(id),
    province TEXT NOT NULL,
    explanation TEXT NOT NULL,
    legal_reference TEXT
);