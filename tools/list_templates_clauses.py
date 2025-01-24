import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.orm import ContractTemplate, SpecialClause, get_db_session
import json

def format_json(data):
    """格式化JSON数据，处理可能的字符串形式的JSON"""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return data

def list_templates_and_clauses():
    """列出所有合同模板和特殊条款"""
    session, _ = get_db_session()  # 忽略返回的engine
    
    try:
        print("\n=== 合同模板 ===")
        print("-" * 50)
        templates = session.query(ContractTemplate).all()
        for template in templates:
            print(f"\n模板ID: {template.id}")
            print(f"类型: {template.type}")
            print(f"版本: {template.version}")
            print(f"省份: {template.province}")
            print(f"描述: {template.description}")
            
            # 处理sections
            sections = format_json(template.sections)
            if isinstance(sections, dict) and 'sections' in sections:
                section_titles = [s.get('title') for s in sections['sections'] 
                                if isinstance(s, dict) and 'title' in s]
            elif isinstance(sections, list):
                section_titles = [s.get('title') for s in sections 
                                if isinstance(s, dict) and 'title' in s]
            else:
                section_titles = []
            
            print("章节:")
            for title in section_titles:
                print(f"  - {title}")
            
            # 处理features
            features = format_json(template.features)
            if features:
                print("特殊功能:")
                if isinstance(features, list):
                    for feature in features:
                        print(f"  - {feature}")
                else:
                    print(f"  {features}")
            
            print("-" * 30)
        
        print("\n\n=== 特殊条款 ===")
        print("-" * 50)
        clauses = session.query(SpecialClause).all()
        for clause in clauses:
            print(f"\n条款ID: {clause.id}")
            print(f"类型: {clause.clause_type}")
            print(f"类别: {clause.category}")
            print(f"标题: {clause.title}")
            print(f"省份: {clause.province}")
            print(f"内容预览: {clause.content[:100]}..." if clause.content else "无内容")
            
            # 处理variables
            variables = format_json(clause.variables)
            if variables:
                print("变量:")
                for var, value in variables.items():
                    print(f"  - {var}: {value}")
            
            print("-" * 30)
            
    finally:
        session.close()

if __name__ == "__main__":
    list_templates_and_clauses()
