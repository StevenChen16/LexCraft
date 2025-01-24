-- 备份原表
CREATE TABLE IF NOT EXISTS contract_templates_backup AS SELECT * FROM contract_templates;

-- 更新合同模板表
ALTER TABLE contract_templates
DROP COLUMN IF EXISTS effective_date,
DROP COLUMN IF EXISTS template_json,
ALTER COLUMN province DROP NOT NULL;  -- 移除province的not-null约束

ALTER TABLE contract_templates
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS sections JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS features JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS property_types JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 插入示例模板
INSERT INTO contract_templates (
    type, version, description, sections, features, property_types, province
) VALUES (
    'rental',
    '1.0',
    '标准租赁合同模板，适用于住宅物业',
    '[
        {
            "title": "Parties",
            "fields": [
                {
                    "name": "landlord_last_name",
                    "label": "Landlord Last Name",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "landlord_first_middle_names",
                    "label": "Landlord First and Middle Names",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "tenant_last_name",
                    "label": "Tenant Last Name",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "tenant_first_middle_names",
                    "label": "Tenant First and Middle Names",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "tenant_phone",
                    "label": "Tenant Phone Number",
                    "type": "text",
                    "required": false
                },
                {
                    "name": "tenant_email",
                    "label": "Tenant Email Address",
                    "type": "email",
                    "required": false
                }
            ]
        },
        {
            "title": "Rental Unit",
            "fields": [
                {
                    "name": "unit_number",
                    "label": "Unit Number",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "street_address",
                    "label": "Street Number and Name",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "postal_code",
                    "label": "Postal Code",
                    "type": "text",
                    "required": true,
                    "validation": {
                        "pattern": "^[A-Za-z]\\d[A-Za-z][ -]?\\d[A-Za-z]\\d$"
                    }
                },
                {
                    "name": "city",
                    "label": "City",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "province",
                    "label": "Province",
                    "type": "text",
                    "required": true
                }
            ]
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
            ]
        },
        {
            "title": "Rent",
            "fields": [
                {
                    "name": "rent_amount",
                    "label": "Rent Amount",
                    "type": "number",
                    "required": true,
                    "validation": {
                        "min": 0
                    }
                },
                {
                    "name": "rent_payment_frequency",
                    "label": "Rent Payment Frequency",
                    "type": "select",
                    "options": ["monthly", "weekly"],
                    "required": true
                },
                {
                    "name": "rent_due_date",
                    "label": "Rent Due Date",
                    "type": "number",
                    "required": true,
                    "validation": {
                        "min": 1,
                        "max": 31
                    }
                }
            ]
        }
    ]'::jsonb,
    '["pets", "balcony", "parking", "storage"]'::jsonb,
    '["apartment", "house", "condo"]'::jsonb,
    'ON'  -- 设置默认省份为安大略省
);
