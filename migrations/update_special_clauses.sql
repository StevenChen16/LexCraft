-- 备份原表
CREATE TABLE special_clauses_backup AS SELECT * FROM special_clauses;

-- 删除原表
DROP TABLE special_clauses;

-- 创建新表
CREATE TABLE special_clauses (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) UNIQUE,
    title VARCHAR(100),
    content TEXT,
    variables JSONB DEFAULT '{}',
    compatibility JSONB DEFAULT '{}',
    requirements JSONB DEFAULT '[]',
    validation JSONB DEFAULT '{}',
    property_types JSONB DEFAULT '[]',
    features JSONB DEFAULT '[]',
    province VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建翻译表
CREATE TABLE clause_translations (
    id SERIAL PRIMARY KEY,
    clause_id INTEGER REFERENCES special_clauses(id),
    language VARCHAR(10),
    title VARCHAR(100),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(clause_id, language)
);

-- 创建合同结构表
CREATE TABLE contract_structures (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES contract_templates(id),
    sections JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入示例条款数据
INSERT INTO special_clauses (type, title, content, variables, compatibility, requirements, property_types, features, province) VALUES
('balcony', 'Balcony Usage Terms', 
'1. The rental unit includes a private balcony for Tenant use.
2. Tenant must keep the balcony clean and well-maintained.
3. No alterations or installations without written permission.
4. BBQs and other cooking equipment must comply with strata rules.
5. No storage of unsightly items or debris on balcony.
6. Plants must be properly contained to prevent water damage.
7. No items to be hung over balcony railings.',
'{}', '{"incompatible": []}', '[]', '["apartment", "condo"]', '["balcony"]', 'British Columbia');

INSERT INTO special_clauses (type, title, content, variables, compatibility, requirements, property_types, features, province) VALUES
('gas_stove', 'Gas Stove Usage Terms',
'1. Tenant is permitted to use gas stove equipment.
2. Tenant must:
   - Maintain valid home insurance covering fire and gas incidents
   - Regularly check gas equipment safety
   - Report any abnormalities immediately
3. Tenant insurance must cover:
   - Fire damage from gas equipment use
   - Gas leak damage
   - Related personal injury liability
4. Before using gas equipment, tenant must:
   - Provide valid insurance proof
   - Understand emergency procedures
5. In case of gas leak:
   - Immediately shut off gas valve
   - Open windows for ventilation
   - Do not operate any electrical switches
   - Notify property management immediately',
'{}', '{"incompatible": []}', '["insurance_required"]', '["apartment", "house"]', '["gas_utilities"]', 'British Columbia');

-- 插入中文翻译
INSERT INTO clause_translations (clause_id, language, title, content) VALUES
(1, 'zh_CN', '阳台使用条款',
'1. 租赁单位包含一个供租户使用的私人阳台。
2. 租户必须保持阳台清洁和维护良好。
3. 未经书面许可，不得进行改动或安装。
4. 烧烤和其他烹饪设备必须符合大厦规定。
5. 阳台上不得存放不雅物品或垃圾。
6. 植物必须妥善放置以防止漏水损坏。
7. 不得在阳台栏杆上悬挂物品。');

INSERT INTO clause_translations (clause_id, language, title, content) VALUES
(2, 'zh_CN', '天然气设备使用条款',
'1. 租户被允许使用天然气灶具。
2. 租户必须：
   - 确保有有效的房屋保险，包括火灾和天然气事故保障
   - 定期检查天然气设备的安全状况
   - 发现任何异常及时报告
3. 租户的保险必须覆盖：
   - 因使用天然气设备导致的火灾损失
   - 天然气泄漏造成的损害
   - 相关的人身伤害责任
4. 在使用天然气设备前，租户需要：
   - 提供有效的保险证明
   - 了解紧急情况处理程序
5. 如发现天然气泄漏：
   - 立即关闭气阀
   - 打开窗户通风
   - 不要开关任何电器
   - 立即通知物业管理处');

-- 插入示例合同结构
INSERT INTO contract_structures (template_id, sections) VALUES
(47, '[
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
  }
]'::jsonb);
