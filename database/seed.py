# database/seed.py
import psycopg2
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def seed_ontario_rental_template():
    """导入Ontario租赁合同模板"""
    
    # Ontario租赁合同的结构化数据
    ontario_template = {
        "title": "Residential Tenancy Agreement",
        "sections": [
            {
                "id": "parties",
                "title": "1. Parties to the Agreement",
                "fields": [
                    {
                        "name": "landlord_legal_name",
                        "label": "Landlord's Legal Name",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "tenant_names",
                        "label": "Tenant(s)",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "first_name": {"type": "text"},
                                "last_name": {"type": "text"}
                            }
                        },
                        "required": True
                    }
                ]
            },
            {
                "id": "rental_unit",
                "title": "2. Rental Unit",
                "fields": [
                    {
                        "name": "unit_number",
                        "label": "Unit",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "street_number",
                        "label": "Street Number",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "street_name",
                        "label": "Street Name",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "city",
                        "label": "City",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "province",
                        "label": "Province",
                        "type": "text",
                        "required": True,
                        "default": "Ontario"
                    },
                    {
                        "name": "postal_code",
                        "label": "Postal Code",
                        "type": "text",
                        "required": True
                    }
                ]
            },
            {
                "id": "term",
                "title": "3. Term of Tenancy",
                "fields": [
                    {
                        "name": "start_date",
                        "label": "Start Date",
                        "type": "date",
                        "required": True
                    },
                    {
                        "name": "end_date",
                        "label": "End Date",
                        "type": "date",
                        "required": True
                    },
                    {
                        "name": "term_type",
                        "label": "Term Type",
                        "type": "enum",
                        "options": ["fixed", "month-to-month"],
                        "required": True
                    }
                ]
            },
            {
                "id": "rent",
                "title": "4. Rent",
                "fields": [
                    {
                        "name": "base_rent",
                        "label": "Base Rent",
                        "type": "number",
                        "required": True
                    },
                    {
                        "name": "payment_frequency",
                        "label": "Payment Frequency",
                        "type": "enum",
                        "options": ["monthly", "weekly", "bi-weekly"],
                        "required": True,
                        "default": "monthly"
                    },
                    {
                        "name": "payment_due_date",
                        "label": "Payment Due Date",
                        "type": "number",
                        "min": 1,
                        "max": 31,
                        "required": True,
                        "default": 1
                    },
                    {
                        "name": "payment_methods",
                        "label": "Accepted Payment Methods",
                        "type": "array",
                        "items": {
                            "type": "enum",
                            "options": ["e-transfer", "check", "cash", "direct_deposit"]
                        },
                        "required": True
                    }
                ]
            },
            {
                "id": "utilities",
                "title": "5. Utilities and Services",
                "fields": [
                    {
                        "name": "included_utilities",
                        "label": "Included Utilities",
                        "type": "array",
                        "items": {
                            "type": "enum",
                            "options": ["heat", "electricity", "water", "gas", "internet", "cable"]
                        },
                        "required": True
                    }
                ]
            }
        ]
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 插入合同模板
    cur.execute("""
        INSERT INTO contract_templates 
        (province, type, version, effective_date, template_json)
        VALUES 
        (%s, %s, %s, %s, %s)
        ON CONFLICT (province, type, version) DO UPDATE
        SET template_json = EXCLUDED.template_json,
            effective_date = EXCLUDED.effective_date
    """, ('Ontario', 'residential_lease', '2024-01', '2024-01-01', json.dumps(ontario_template)))
    
    template_id = cur.fetchone()[0] if cur.rowcount > 0 else None
    
    if template_id:
        # 插入字段定义
        for section in ontario_template['sections']:
            for field in section['fields']:
                cur.execute("""
                    INSERT INTO template_fields
                    (template_id, field_name, field_type, section, is_required)
                    VALUES
                    (%s, %s, %s, %s, %s)
                    ON CONFLICT (template_id, field_name) DO UPDATE
                    SET field_type = EXCLUDED.field_type,
                        section = EXCLUDED.section,
                        is_required = EXCLUDED.is_required
                """, (template_id, field['name'], field['type'], section['id'], field.get('required', False)))
    
    conn.commit()
    print("Ontario rental template updated successfully")
    
    cur.close()
    conn.close()

def seed_ontario_special_clauses():
    """添加安大略省常用特殊条款"""
    clauses = [
        {
            "province": "Ontario",
            "category": "pets",
            "clause_type": "pet_agreement",
            "title": "宠物协议",
            "display_name": "宠物协议",
            "content": """
            宠物协议:
            1. 许可的宠物
               - 允许的宠物类型: {permitted_pets}
               - 最大数量: {max_pets}只
               - 体型限制: {size_restrictions}
               - 品种限制: {breed_restrictions}
               
            2. 宠物押金和费用
               - 宠物押金: ${pet_deposit}
               - 每月宠物租金: ${monthly_pet_rent}
               - 需购买的保险: {insurance_requirements}
               
            3. 租客责任
               - 保持宠物疫苗接种记录更新
               - 及时清理宠物粪便
               - 防止宠物噪音打扰他人
               - 在公共区域保持宠物拴绳
               - 承担宠物造成的所有损坏
               
            4. 特殊规定
               - 宠物活动区域: {activity_areas}
               - 宠物美容和清洁: {grooming_requirements}
               - 宠物行为要求: {behavior_requirements}
            """,
            "required_variables": [
                "permitted_pets",
                "max_pets",
                "size_restrictions",
                "breed_restrictions",
                "pet_deposit",
                "monthly_pet_rent",
                "insurance_requirements",
                "activity_areas",
                "grooming_requirements",
                "behavior_requirements"
            ]
        },
        {
            "province": "Ontario",
            "category": "storage_and_parking",
            "clause_type": "storage_and_parking",
            "title": "储物柜和停车位使用协议",
            "display_name": "储物柜和停车位使用协议",
            "content": """
            储物柜和停车位使用协议:
            
            1. 停车位
               1.1 分配详情
                   - 车位编号: {parking_space}
                   - 月租费用: ${parking_fee}
                   - 位置描述: {parking_location}
                   
               1.2 使用规则
                   - 仅限已登记车辆使用
                   - 禁止存放危险物品
                   - 需遵守物业停车场管理规定
                   - 车辆尺寸限制: {vehicle_size_limit}
                   
               1.3 租客责任
                   - 保持停车位清洁
                   - 及时报告任何损坏
                   - 不得转租或分租
                   - 车辆漏油处理: {oil_leak_policy}
               
            2. 储物柜
               2.1 分配详情
                   - 储物柜编号: {locker_number}
                   - 月租费用: ${storage_fee}
                   - 位置描述: {locker_location}
                   
               2.2 使用规则
                   - 仅供存放个人物品
                   - 禁止存放危险或违禁品
                   - 需遵守物业储物柜使用规定
                   - 储存限制: {storage_restrictions}
                   
               2.3 租客责任
                   - 保持储物柜清洁
                   - 及时报告任何损坏
                   - 不得转租或分租
                   - 物品保险要求: {insurance_requirements}
            """,
            "required_variables": [
                "parking_space",
                "parking_fee",
                "parking_location",
                "vehicle_size_limit",
                "oil_leak_policy",
                "locker_number",
                "storage_fee",
                "locker_location",
                "storage_restrictions",
                "insurance_requirements"
            ]
        },
        {
            "province": "Ontario",
            "category": "appliances",
            "clause_type": "gas_stove_usage",
            "title": "煤气炉使用协议",
            "display_name": "煤气炉使用协议",
            "content": """
            煤气炉使用协议:
            
            1. 使用权限
               1.1 允许的用途
                   - 烹饪和加热食物
                   - 使用时间: {operation_hours}
                   
               1.2 禁止的用途
                   - 取暖用途
                   - 其他未经许可的用途
                   
               1.3 使用条件
                   - 完成安全培训: {safety_training}
                   - 阅读使用手册
                   - 遵守使用时间限制
            
            2. 安全要求
               2.1 定期检查
                   - 每月检查频率: {monthly_inspection}
                   - 专业维护周期: {maintenance_cycle}
                   - 部件更换计划: {replacement_schedule}
                   
               2.2 安全措施
                   - 使用时保持通风
                   - 发现异味立即关闭
                   - 定期清洁设备
                   - 周围无易燃物
                   
               2.3 应急程序
                   - 闻到煤气味立即开窗
                   - 关闭总阀门位置: {main_valve_location}
                   - 紧急联系电话: {emergency_contact}
                   - 疏散路线: {evacuation_route}
            
            3. 保险要求
               - 必需的保险类型: {required_insurance}
               - 最低保额: ${minimum_coverage}
               - 保险证明提交: {proof_submission}
            """,
            "required_variables": [
                "operation_hours",
                "safety_training",
                "monthly_inspection",
                "maintenance_cycle",
                "replacement_schedule",
                "main_valve_location",
                "emergency_contact",
                "evacuation_route",
                "required_insurance",
                "minimum_coverage",
                "proof_submission"
            ]
        },
        {
            "province": "Ontario",
            "category": "parking",
            "clause_type": "parking",
            "title": "停车位使用协议",
            "display_name": "停车位使用协议",
            "content": json.dumps({
                "rules": [
                    "停车位仅供承租人使用",
                    "不得存放危险物品",
                    "需遵守物业停车场管理规定",
                    "禁止在停车位进行车辆维修",
                    "禁止占用其他车位",
                    "保持停车场通道畅通"
                ],
                "responsibilities": [
                    "保持停车位清洁",
                    "及时报告任何损坏",
                    "不得转租或分租",
                    "不得在停车位存放杂物",
                    "遵守停车场限速要求",
                    "车辆漏油及时处理"
                ]
            })
        },
        {
            "province": "Ontario",
            "category": "storage",
            "clause_type": "storage",
            "title": "储物柜使用协议",
            "display_name": "储物柜使用协议",
            "content": json.dumps({
                "rules": [
                    "储物柜仅供存放个人物品",
                    "不得存放危险或违禁品",
                    "需遵守物业储物柜使用规定",
                    "禁止存放易腐物品",
                    "禁止存放贵重物品",
                    "禁止在储物柜内进行任何活动"
                ],
                "responsibilities": [
                    "保持储物柜清洁",
                    "及时报告任何损坏",
                    "不得转租或分租",
                    "定期检查储存物品",
                    "确保储物柜安全锁闭",
                    "不得改装或损坏储物柜"
                ]
            })
        },
        {
            "province": "Ontario",
            "category": "appliance",
            "clause_type": "gas_stove_usage",
            "title": "煤气炉使用协议",
            "display_name": "煤气炉使用协议",
            "content": json.dumps({
                "permissions": {
                    "allowed_usage": ["烹饪", "加热", "烘焙"],
                    "restricted_usage": ["取暖", "其他用途", "商业用途"],
                    "operation_hours": "6:00 AM - 11:00 PM"
                },
                "safety_requirements": {
                    "inspections": [
                        "每月检查煤气管道",
                        "每季度专业维护",
                        "及时更换老化部件",
                        "定期清洁排气系统",
                        "检查安全阀门功能",
                        "维护记录存档"
                    ],
                    "safety_measures": [
                        "使用时保持通风",
                        "发现异味立即关闭",
                        "定期清洁设备",
                        "保持周围无易燃物",
                        "不得自行维修",
                        "正确使用点火装置"
                    ],
                    "emergency_procedures": [
                        "闻到煤气味立即打开窗户",
                        "关闭总阀门",
                        "拨打紧急电话",
                        "通知房东或物业",
                        "疏散人员",
                        "不得开启电器"
                    ]
                }
            })
        },
        {
            "province": "Ontario",
            "category": "maintenance",
            "clause_type": "snow_removal",
            "title": "冬季铲雪责任协议",
            "display_name": "冬季铲雪责任协议",
            "content": json.dumps({
                "responsibilities": {
                    "landlord": [
                        "负责所有公共区域和通道的积雪清理",
                        "确保紧急出口和消防通道无积雪阻塞",
                        "可委托专业铲雪服务公司执行铲雪工作",
                        "负责铲雪相关的所有费用",
                        "确保在降雪后24小时内完成铲雪工作",
                        "维护除雪设备和除冰材料的供应"
                    ],
                    "tenant": [
                        "报告任何危险的积雪或结冰情况",
                        "不得干扰铲雪工作的进行",
                        "确保个人物品不妨碍铲雪工作",
                        "遵守临时停车规定以配合铲雪工作"
                    ]
                },
                "schedule": {
                    "regular_hours": "7:00 AM - 10:00 PM",
                    "emergency_response": "24小时",
                    "priority_areas": [
                        "入口通道",
                        "紧急出口",
                        "停车场主要通道",
                        "垃圾处理区域"
                    ]
                },
                "safety_measures": [
                    "使用环保除冰剂",
                    "设置防滑警示标志",
                    "保持照明系统工作正常",
                    "定期检查屋顶积雪情况"
                ]
            }),
            "required_variables": []
        }
    ]
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 确保required_variables列是TEXT类型而不是ARRAY
    cur.execute("""
        ALTER TABLE IF EXISTS special_clauses 
        ALTER COLUMN required_variables TYPE TEXT
    """)
    
    for clause in clauses:
        # 将required_variables转换为JSON字符串
        required_vars_json = json.dumps(clause.get("required_variables", []))
        
        cur.execute("""
            INSERT INTO special_clauses 
            (province, category, clause_type, title, display_name, content, required_variables)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (clause_type) DO UPDATE
            SET content = EXCLUDED.content,
                required_variables = EXCLUDED.required_variables,
                display_name = EXCLUDED.display_name
        """, (
            clause["province"],
            clause["category"],
            clause["clause_type"],
            clause["title"],
            clause["display_name"],
            clause["content"],
            required_vars_json  # 使用JSON字符串
        ))
    
    conn.commit()
    print("Ontario special clauses updated successfully")
    
    cur.close()
    conn.close()

def add_bc_special_clauses():
    """添加BC省的特殊条款"""
    clauses = [
        {
            "province": "British Columbia",
            "category": "pet",
            "clause_type": "pet_addendum",
            "title": "Pet Addendum",
            "content": """
            Pet Addendum:
            1. The Landlord permits the Tenant to keep cats in the rental unit.
            2. The Tenant is responsible for any damage caused by their pets.
            3. The Tenant must maintain cleanliness and control pet noise.
            4. A pet damage deposit of $XXX is required.
            """,
            "variables": {}
        },
        {
            "province": "British Columbia",
            "category": "balcony",
            "clause_type": "balcony_usage",
            "title": "Balcony Usage Terms",
            "content": """
            Balcony Usage Terms:
            1. The rental unit includes a private balcony for Tenant use.
            2. Tenant must keep the balcony clean and well-maintained.
            3. No alterations or installations without written permission.
            4. BBQs and other cooking equipment must comply with strata rules.
            """,
            "variables": {}
        }
    ]
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    for clause in clauses:
        cur.execute("""
            INSERT INTO special_clauses 
            (province, category, clause_type, title, content, variables)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            clause['province'],
            clause['category'],
            clause['clause_type'],
            clause['title'],
            clause['content'],
            json.dumps(clause['variables'])
        ))
    
    conn.commit()
    print("BC special clauses added successfully")
    
    cur.close()
    conn.close()

def seed_bc_rental_template():
    """导入BC省租赁合同模板"""
    bc_template = {
        "title": "Residential Tenancy Agreement",
        "sections": [
            {
                "id": "parties",
                "title": "Parties",
                "fields": [
                    {
                        "name": "landlord_name",
                        "type": "text",
                        "label": "Landlord's Name",
                        "required": True
                    },
                    {
                        "name": "tenant_name",
                        "type": "text",
                        "label": "Tenant's Name",
                        "required": True
                    }
                ]
            },
            {
                "id": "property",
                "title": "Rental Property",
                "fields": [
                    {
                        "name": "address",
                        "type": "text",
                        "label": "Property Address",
                        "required": True
                    },
                    {
                        "name": "city",
                        "type": "text",
                        "label": "City",
                        "required": True,
                        "value": "Vancouver"  # 默认值
                    }
                ]
            },
            {
                "id": "terms",
                "title": "Rental Terms",
                "fields": [
                    {
                        "name": "rent_amount",
                        "type": "currency",
                        "label": "Monthly Rent",
                        "required": True
                    },
                    {
                        "name": "start_date",
                        "type": "date",
                        "label": "Start Date",
                        "required": True
                    },
                    {
                        "name": "term",
                        "type": "text",
                        "label": "Rental Term",
                        "required": True
                    }
                ]
            }
        ]
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO contract_templates 
        (province, type, version, effective_date, template_json)
        VALUES 
        (%s, %s, %s, %s, %s)
    """, ('British Columbia', 'rental', '1.0', '2025-01-01', 
          json.dumps(bc_template)))
    
    conn.commit()
    print("BC rental template added successfully")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    seed_ontario_special_clauses()