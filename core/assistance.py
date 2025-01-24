import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
import json
from datetime import datetime
from openai import OpenAI

from database.orm import get_db_session, ClauseKeywordMapping, SpecialClause, ContractTemplate
from config import DEEPSEEK_CONFIG

class ContractAssistant:
    """智能合同助手，负责理解用户需求并提供建议"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_CONFIG['api_key'],
            base_url=DEEPSEEK_CONFIG['base_url']
        )
        self.session, _ = get_db_session()
        
        # 加载所有静态资源
        self.available_templates = self._load_available_templates()
        self.available_clauses = self._load_available_clauses()
        self.clause_relationships = self._load_clause_relationships()
        
        # 初始化会话状态
        self.current_contract = None
        self.initial_requirements = None
        self.modification_history = []
        
        # System prompts
        self.initial_system_prompt = self._load_initial_prompt()
        self.modification_system_prompt = self._load_modification_prompt()

    def _load_available_templates(self) -> Dict:
        """加载所有可用的合同模板"""
        templates = {}
        db_templates = self.session.query(ContractTemplate).all()
        for template in db_templates:
            templates[template.type] = {
                'id': template.id,
                'type': template.type,
                'version': template.version,
                'description': template.description,
                'sections': template.sections,
                'features': template.features
            }
        return templates

    def _load_available_clauses(self) -> Dict:
        """加载所有可用的特殊条款"""
        clauses = {}
        db_clauses = self.session.query(SpecialClause).all()
        for clause in db_clauses:
            clauses[clause.clause_type] = {
                'title': clause.title,
                'category': clause.category,
                'content': clause.content,
                'variables': clause.variables
            }
        return clauses

    def _load_clause_relationships(self) -> Dict:
        """加载条款之间的关联关系"""
        relationships = {}
        mappings = self.session.query(ClauseKeywordMapping).all()
        for mapping in mappings:
            if mapping.clause_type not in relationships:
                relationships[mapping.clause_type] = []
            # 从JSON字段中获取关键词列表
            keywords = json.loads(mapping.keywords) if isinstance(mapping.keywords, str) else mapping.keywords
            if isinstance(keywords, list):
                for keyword in keywords:
                    relationships[mapping.clause_type].append({
                        'keyword': keyword,
                        'weight': 1.0  # 默认权重
                    })
            elif isinstance(keywords, dict):
                for keyword, weight in keywords.items():
                    relationships[mapping.clause_type].append({
                        'keyword': keyword,
                        'weight': float(weight)
                    })
        return relationships

    def _generate_ai_context(self) -> Dict:
        """生成完整的AI上下文"""
        context = {
            "static_resources": {
                "templates": self.available_templates,
                "clauses": self.available_clauses,
                "relationships": self.clause_relationships
            },
            "session_state": {
                "current_contract": self.current_contract,
                "initial_requirements": self.initial_requirements,
                "modification_history": self.modification_history
            }
        }
        return context

    def _load_initial_prompt(self) -> str:
        """加载初始需求分析的system prompt"""
        return """You are a legal assistant specialized in contract generation. Your task is to analyze the initial requirements and suggest the most appropriate contract template and clauses.

IMPORTANT: Always generate the response in English, regardless of the input language.

Available Resources:
1. Contract Templates: Templates for different types of contracts
2. Special Clauses: A library of special clauses that can be added to contracts
3. Clause Relationships: Relationships between different clauses

Please format your response as a JSON object with this structure:
{
    "template_type": "residential_lease",
    "basic_info": {
        "parties": {
            "party1": {
                "name": "string",
                "type": "string",
                "contact": "string"
            }
        },
        "property": {
            "type": "string",
            "address": "string (must include province, e.g., 'Toronto, ON' or 'Vancouver, BC')",
            "features": ["string"]
        },
        "term": {
            "start_date": "string (YYYY-MM-DD)",
            "duration": {
                "amount": number,
                "unit": "string (days/months/years)"
            }
        }
    },
    "suggested_clauses": [
        {
            "clause_type": "string",
            "reason": "string"
        }
    ]
}

Guidelines:
1. ONLY include fields that are explicitly mentioned in the user's requirements
2. For missing information, use "To be filled" as placeholder
3. ALWAYS include the province in the address (e.g., "Toronto, ON" or "Vancouver, BC")
4. Do not assume any default values for lease duration or other terms
5. Keep all field names and values in English"""

    def _load_modification_prompt(self) -> str:
        """加载合同修改的system prompt"""
        return """You are a legal assistant helping to modify contracts. Your role is to analyze modification requests and suggest appropriate changes.

Please format your response as a JSON object with this structure:
{
    "modifications": [
        {
            "type": "basic_info",
            "action": "modify",
            "target": {
                "section": "parties",
                "field": "party1"
            },
            "value": {
                "name": "New Name",
                "contact": "new@email.com"
            }
        },
        {
            "type": "clause",
            "action": "add",
            "clause_type": "pet_agreement",
            "value": {
                "variables": {
                    "max_pets": 2,
                    "permitted_pets": ["cats", "small dogs"],
                    "pet_deposit": 500,
                    "monthly_pet_rent": 50,
                    "size_restrictions": "under 20kg",
                    "breed_restrictions": "no aggressive breeds",
                    "insurance_requirements": "liability coverage required"
                }
            }
        }
    ]
}

Available modifications:
1. Basic Info:
   - type: "basic_info"
   - action: "modify"
   - target: {"section": "section_name", "field": "field_name"}
   - value: new value for the field

2. Special Clauses:
   - type: "clause"
   - action: "add", "remove", or "modify"
   - clause_type: type of the clause
   - value: {
       "variables": {
           "variable_name": "value"
       }
   }

Remember to:
1. Include all required variables for special clauses
2. Format dates in ISO format (YYYY-MM-DD)
3. Use proper currency values (numbers without currency symbols)
4. Validate all values against contract rules
"""

    def interact_with_ai(self, user_input: str, interaction_type: str = "modification") -> Dict:
        """与AI交互的统一接口"""
        context = self._generate_ai_context()
        
        # 根据交互类型选择不同的system prompt
        system_prompt = (
            self.initial_system_prompt if interaction_type == "initial" 
            else self.modification_system_prompt
        )
        
        # 将上下文添加到system prompt
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        full_prompt = f"{system_prompt}\n\nContext:\n{context_str}"
        
        messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 调用AI API
        response = self.client.chat.completions.create(
            model=DEEPSEEK_CONFIG['model'],
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # 解析响应
        content = response.choices[0].message.content
        # 处理可能的代码块
        if "```json" in content:
            content = content.split("```json")[1]
            if "```" in content:
                content = content.split("```")[0]
        content = content.strip()
        result = json.loads(content)
        
        # 更新会话状态
        if interaction_type == "initial":
            self.initial_requirements = result
        else:
            self._apply_modifications(result)
            self.modification_history.append({
                "user_input": user_input,
                "ai_response": result,
                "timestamp": datetime.now().isoformat()
            })
        
        return result

    def _apply_modifications(self, response: Dict) -> None:
        """应用AI建议的修改"""
        if not isinstance(response, dict):
            return
            
        modifications = response.get('modifications', [])
        if not isinstance(modifications, list):
            return
            
        for mod in modifications:
            if not isinstance(mod, dict):
                continue
                
            # 验证修改的格式
            if not all(k in mod for k in ['type', 'action', 'target', 'value']):
                continue
                
            # 更新当前合同状态
            if self.current_contract is not None:
                if mod['type'] == 'basic_info':
                    target = mod.get('target', {})
                    if isinstance(target, dict):
                        section = target.get('section')
                        field = target.get('field')
                        if section and field:
                            if 'sections' not in self.current_contract:
                                self.current_contract['sections'] = {}
                            if section not in self.current_contract['sections']:
                                self.current_contract['sections'][section] = {}
                            self.current_contract['sections'][section][field] = mod['value']
                        
                elif mod['type'] == 'clause':
                    if 'special_clauses' not in self.current_contract:
                        self.current_contract['special_clauses'] = []
                    
                    if mod['action'] == 'add':
                        self.current_contract['special_clauses'].append({
                            'type': mod['target'],
                            'content': mod.get('value', {}).get('content', ''),
                            'variables': mod.get('value', {}).get('variables', {})
                        })
                    elif mod['action'] == 'remove':
                        self.current_contract['special_clauses'] = [
                            c for c in self.current_contract['special_clauses']
                            if c['type'] != mod['target']
                        ]
                    elif mod['action'] == 'modify':
                        for clause in self.current_contract['special_clauses']:
                            if clause['type'] == mod['target']:
                                clause.update(mod.get('value', {}))

    def _generate_initial_contract(self, requirements: Dict) -> Dict:
        """根据初始需求生成合同"""
        template_type = requirements.get('template_type')
        if not template_type or template_type not in self.available_templates:
            raise ValueError("Invalid template type")
            
        template = self.available_templates[template_type]
        
        contract = {
            'version': template['version'],
            'type': template['type'],
            'sections': requirements.get('basic_info', {}),
            'special_clauses': []
        }
        
        # 添加建议的条款
        for clause_suggestion in requirements.get('suggested_clauses', []):
            clause_type = clause_suggestion['clause_type']
            if clause_type in self.available_clauses:
                contract['special_clauses'].append({
                    'type': clause_type,
                    'content': self.available_clauses[clause_type]['content'],
                    'variables': {}  # 初始时变量为空
                })
        
        return contract

    def _update_clause_variables(self, variables: Dict) -> None:
        """更新条款变量并重新格式化内容"""
        for clause_type, values in variables.items():
            for clause in self.current_contract['special_clauses']:
                if clause['type'] == clause_type:
                    # 更新变量
                    clause['variables'].update(values)
                    
                    # 获取原始模板
                    template = self.available_clauses.get(clause_type)
                    if template and template.get('content'):
                        try:
                            # 使用更新后的变量重新格式化内容
                            clause['content'] = template['content'].format(**clause['variables'])
                        except KeyError as e:
                            print(f"Warning: Missing variable {e} in clause")
                        except Exception as e:
                            print(f"Error formatting clause: {e}")

    def _get_structured_response(self, messages: List[Dict]) -> Dict:
        """获取AI的结构化响应"""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # 尝试提取JSON部分
        try:
            # 如果返回的是纯JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果JSON嵌入在文本中，尝试提取
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print("No valid JSON found in response")
                return {
                    "modifications": [],
                    "required_variables": {}
                }

if __name__ == "__main__":
    assistant = ContractAssistant()
    
    test_input = """I want to rent an apartment in Vancouver, budget is $2000 per month,
    need to allow cats, preferably with a balcony. Want 2 months deposit and 3 months rent in advance.
    Starting from next month 1st, for a duration of 1 year."""
    
    requirements = assistant.interact_with_ai(test_input, interaction_type="initial")
    print("\nExtracted requirements:")
    print(json.dumps(requirements, ensure_ascii=False, indent=2))
    
    test_modification = """I want to add a clause about maintenance responsibilities for the garden.
    Also update the start date to next week and increase the rent to $2100 per month."""
    
    modification = assistant.interact_with_ai(test_modification)
    print("\nExtracted modification request:")
    print(json.dumps(modification, ensure_ascii=False, indent=2))