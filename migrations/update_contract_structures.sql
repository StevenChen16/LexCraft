-- 删除旧表（如果存在）
DROP TABLE IF EXISTS contract_structures;

-- 创建合同结构表
CREATE TABLE contract_structures (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES contract_templates(id),
    sections JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id)
);

-- 为模板ID 49 插入合同结构
INSERT INTO contract_structures (template_id, sections) VALUES (
    49,
    '[
        {
            "title": "Parties",
            "fields": [
                {
                    "name": "landlord_name",
                    "label": "Landlord Name",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "landlord_contact",
                    "label": "Landlord Contact",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "tenant_name",
                    "label": "Tenant Name",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "tenant_contact",
                    "label": "Tenant Contact",
                    "type": "text",
                    "required": true
                }
            ],
            "required": true
        },
        {
            "title": "Rental Unit",
            "fields": [
                {
                    "name": "property_address",
                    "label": "Property Address",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "unit_number",
                    "label": "Unit Number",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "property_type",
                    "label": "Property Type",
                    "type": "select",
                    "options": ["apartment", "house", "condo"],
                    "required": true
                }
            ],
            "required": true
        },
        {
            "title": "Term",
            "fields": [
                {
                    "name": "start_date",
                    "label": "Start Date",
                    "type": "date",
                    "required": true
                },
                {
                    "name": "end_date",
                    "label": "End Date",
                    "type": "date",
                    "required": true
                },
                {
                    "name": "term_type",
                    "label": "Term Type",
                    "type": "select",
                    "options": ["fixed", "month-to-month"],
                    "required": true
                }
            ],
            "required": true
        },
        {
            "title": "Rent",
            "fields": [
                {
                    "name": "rent_amount",
                    "label": "Monthly Rent Amount",
                    "type": "number",
                    "required": true,
                    "validation": {
                        "min": 0
                    }
                },
                {
                    "name": "rent_payment_frequency",
                    "label": "Payment Frequency",
                    "type": "select",
                    "options": ["monthly", "weekly"],
                    "required": true
                },
                {
                    "name": "rent_due_date",
                    "label": "Payment Due Date",
                    "type": "number",
                    "required": true,
                    "validation": {
                        "min": 1,
                        "max": 31
                    }
                }
            ],
            "required": true
        }
    ]'::jsonb
);

-- 添加触发器以自动更新updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contract_structures_updated_at
    BEFORE UPDATE ON contract_structures
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
