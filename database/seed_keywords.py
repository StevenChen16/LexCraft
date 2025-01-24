from orm import ClauseKeywordMapping, get_db_session
import json

def seed_keyword_mappings():
    """初始化条款关键词映射"""
    session, _ = get_db_session()
    
    # 定义映射数据
    mappings = [
        {
            'clause_type': 'appliances',
            'keywords': [
                '天然气', '煤气', 'gas', '灶', '燃气', '电器', 'appliance',
                '洗衣机', '烘干机', '冰箱', '微波炉', '洗碗机'
            ],
            'variables_template': {
                'appliance_list': {
                    'type': 'string',
                    'extract_from': ['设备名称', '电器名称', 'appliance'],
                    'default': '未指定设备'
                },
                'insurance_required': {
                    'type': 'boolean',
                    'extract_from': ['保险', '责任', 'insurance', 'liability'],
                    'default': True
                }
            },
            'description': '电器使用相关条款'
        },
        {
            'clause_type': 'internet',
            'keywords': [
                '网络', '宽带', 'internet', 'wifi', 'broadband', '上网',
                '网速', '带宽', '网线', '路由器'
            ],
            'variables_template': {
                'service_provider': {
                    'type': 'string',
                    'extract_from': ['供应商', '服务商', 'provider'],
                    'default': '未指定供应商'
                },
                'speed_requirement': {
                    'type': 'string',
                    'extract_from': ['速度', '带宽', 'speed', 'bandwidth'],
                    'default': '基础网络服务'
                },
                'cost_sharing': {
                    'type': 'boolean',
                    'extract_from': ['费用分担', '共同承担', 'share', 'cost'],
                    'default': False
                }
            },
            'description': '网络服务相关条款'
        },
        {
            'clause_type': 'parking',
            'keywords': [
                '停车', '车位', 'parking', '车库', 'garage', '地下停车场'
            ],
            'variables_template': {
                'space_number': {
                    'type': 'string',
                    'extract_from': ['车位号', '编号', 'number'],
                    'default': '未指定'
                },
                'parking_fee': {
                    'type': 'number',
                    'extract_from': ['费用', '价格', 'fee', 'cost'],
                    'default': 0
                }
            },
            'description': '停车相关条款'
        }
    ]
    
    try:
        # 清除现有映射
        session.query(ClauseKeywordMapping).delete()
        
        # 添加新映射
        for mapping in mappings:
            keyword_mapping = ClauseKeywordMapping(
                clause_type=mapping['clause_type'],
                keywords=json.dumps(mapping['keywords']),
                variables_template=json.dumps(mapping['variables_template']),
                description=mapping['description']
            )
            session.add(keyword_mapping)
        
        session.commit()
        print("关键词映射初始化成功")
        
    except Exception as e:
        session.rollback()
        print(f"初始化失败: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    seed_keyword_mappings()
