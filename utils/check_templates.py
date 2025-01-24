# in scripts/check_templates.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.orm import ContractTemplate, get_db_session
import json

def check_templates():
    """检查合同模板"""
    session, _ = get_db_session()
    templates = session.query(ContractTemplate).all()
    
    print(f"\n找到 {len(templates)} 个模板:")
    for template in templates:
        print(f"\n模板 ID: {template.id}")
        print(f"省份: {template.province}")
        print(f"类型: {template.type}")
        print(f"版本: {template.version}")
        print("\n模板结构:")
        print(json.dumps(template.template_json, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    check_templates()