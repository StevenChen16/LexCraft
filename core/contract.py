# in core/contract.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.orm import ContractTemplate, SpecialClause, ClauseKeywordMapping, get_db_session
import json

class ContractProcessor:
    """处理合同的生成和定制"""
    
    def __init__(self):
        """初始化合同对象"""
        self.session, _ = get_db_session()
        
    def generate_initial_contract(self, requirements: Dict) -> Dict:
        """根据初始需求生成合同"""
        try:
            # 1. 选择基础模板
            template = self._select_template(requirements)
            if not template:
                raise Exception(f"No template found for province: {requirements['province']}")
            
            # 2. 获取符合需求的特殊条款
            special_clauses = self._get_special_clauses(requirements)
            
            # 3. 生成定制化合同，替换变量
            contract = self._customize_contract(template, requirements, special_clauses)
            
            # 4. 初始化修改历史
            contract['modification_history'] = []
            contract['current_version'] = 1
            
            return contract
            
        except Exception as e:
            print(f"Error generating initial contract: {e}")
            return None
        finally:
            if hasattr(self, 'session'):
                self.session.close()

    def modify_contract(self, current_contract: Dict, modification_request: Dict) -> Tuple[Dict, List[str]]:
        """根据用户的修改要求更新合同"""
        try:
            # 1. 分析修改请求，识别需要添加/删除的条款
            clauses_to_add, clauses_to_remove = self._analyze_modification(modification_request)
            
            # 2. 创建新版本的合同
            new_contract = json.loads(json.dumps(current_contract))
            changes_made = []
            
            # 3. 移除指定的条款
            if clauses_to_remove:
                changes_made.extend(self._remove_clauses(new_contract, clauses_to_remove))
            
            # 4. 添加新条款
            if clauses_to_add:
                changes_made.extend(self._add_clauses(new_contract, clauses_to_add))
            
            # 5. 替换变量
            if 'variables' in modification_request:
                changes_made.extend(self._update_variables(new_contract, modification_request['variables']))
            
            # 6. 更新版本信息
            new_contract['current_version'] += 1
            new_contract['modification_history'].append({
                'version': new_contract['current_version'],
                'changes': changes_made,
                'timestamp': datetime.now().isoformat()
            })
            
            return new_contract, changes_made
            
        except Exception as e:
            print(f"Error modifying contract: {e}")
            return current_contract, [f"Error: {str(e)}"]

    def _analyze_modification(self, modification_request: Dict) -> Tuple[List[str], List[str]]:
        """分析修改请求，确定需要添加和删除的条款"""
        add_clauses = []
        remove_clauses = []
        
        # 从请求中提取关键信息
        for requirement in modification_request.get('requirements', []):
            # 查询数据库找到匹配的条款
            matching_clauses = self.session.query(SpecialClause).filter(
                SpecialClause.prerequisites.contains(requirement)
            ).all()
            
            for clause in matching_clauses:
                if requirement.get('action') == 'add':
                    add_clauses.append(clause)
                elif requirement.get('action') == 'remove':
                    remove_clauses.append(clause)
        
        return add_clauses, remove_clauses

    def _get_special_clauses(self, requirements: Dict) -> List[str]:
        """根据需求获取特殊条款"""
        special_clauses = []
        
        try:
            # 从数据库获取关键词映射
            keyword_mappings = self.session.query(ClauseKeywordMapping).all()
            
            # 分析需求中的关键词
            requirement_text = json.dumps(requirements, ensure_ascii=False).lower()
            
            for mapping in keyword_mappings:
                keywords = json.loads(mapping.keywords) if isinstance(mapping.keywords, str) else mapping.keywords
                
                # 检查关键词匹配
                if isinstance(keywords, list):
                    if any(keyword.lower() in requirement_text for keyword in keywords):
                        special_clauses.append(mapping.clause_type)
                elif isinstance(keywords, dict):
                    for keyword, weight in keywords.items():
                        if keyword.lower() in requirement_text:
                            special_clauses.append(mapping.clause_type)
                            break
            
            # 检查条款兼容性
            compatible_clauses = self._check_clause_compatibility(special_clauses, requirements.get('province'))
            
            return compatible_clauses
            
        except Exception as e:
            print(f"Error getting special clauses: {str(e)}")
            return []

    def _check_clause_compatibility(self, clause_types: List[str], province: str) -> List[str]:
        """检查条款兼容性"""
        compatible_clauses = []
        
        try:
            for clause_type in clause_types:
                clause = self.session.query(SpecialClause).filter_by(
                    clause_type=clause_type,
                    province=province
                ).first()
                
                if clause:
                    # 检查条款是否适用于当前省份
                    if clause.province and clause.province != province:
                        continue
                        
                    # 检查条款之间的兼容性
                    compatibility = json.loads(clause.compatibility) if isinstance(clause.compatibility, str) else clause.compatibility
                    
                    # 如果没有兼容性要求或者兼容性要求满足
                    if not compatibility or all(
                        comp_type in compatible_clauses 
                        for comp_type in compatibility.get('required', [])
                    ):
                        compatible_clauses.append(clause_type)
            
            return compatible_clauses
            
        except Exception as e:
            print(f"Error checking clause compatibility: {str(e)}")
            return []

    def _update_variables(self, contract: Dict, variables: Dict) -> List[str]:
        """更新合同中的变量"""
        changes = []
        for section in contract['sections']:
            for field in section['fields']:
                field_name = field['name']
                if field_name in variables:
                    old_value = field.get('value', 'N/A')
                    field['value'] = variables[field_name]
                    changes.append(f"Updated {field_name} from {old_value} to {variables[field_name]}")
        
        # 更新特殊条款中的变量
        if 'special_clauses' in contract:
            for clause in contract['special_clauses']:
                for var_name, var_value in variables.items():
                    if f"{{{var_name}}}" in clause['content']:
                        old_content = clause['content']
                        clause['content'] = clause['content'].replace(f"{{{var_name}}}", str(var_value))
                        changes.append(f"Updated variable {var_name} in clause {clause['id']}")
        
        return changes