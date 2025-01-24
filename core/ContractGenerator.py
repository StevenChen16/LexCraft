# in core/contract_generator.py

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .assistance import ContractAssistant
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.orm import (
    ContractTemplate, 
    ContractStructure, 
    SpecialClause, 
    ClauseTranslation,
    get_db_session
)
from dateutil.relativedelta import relativedelta
import traceback

class ContractGenerator:
    """Responsible for generating and modifying contracts"""
    
    def __init__(self):
        """初始化合同生成器"""
        self.session, _ = get_db_session()
    
    def get_available_templates(self, requirements: Dict) -> List[Dict]:
        """获取可用的合同模板"""
        try:
            # 从数据库查询所有模板
            templates = []
            db_templates = self.session.query(ContractTemplate).all()
            
            for template in db_templates:
                # 解析 JSON 字段
                sections = json.loads(template.sections) if template.sections else {}
                features = json.loads(template.features) if template.features else []
                property_types = json.loads(template.property_types) if template.property_types else []
                
                template_data = {
                    'id': template.id,
                    'type': template.type,
                    'version': template.version,
                    'description': template.description,
                    'sections': sections,
                    'features': features,
                    'property_types': property_types,
                    'province': template.province
                }
                templates.append(template_data)
            
            if not templates:
                print("Warning: No contract templates found in database")
            
            return templates
            
        except Exception as e:
            print(f"Error getting available templates: {e}")
            traceback.print_exc()
            return []
            
    def select_template(self, templates: List[Dict], requirements: Dict) -> Dict:
        """选择最合适的合同模板"""
        best_match = {
            'template': None,
            'score': 0,
            'match_reasons': {}
        }
        
        for template in templates:
            score = 0
            match_reasons = {
                'property_type': False,
                'features': set(),
                'sections': [],
                'province': False
            }
            
            # 1. 省份匹配（最高优先级）
            template_province = template.get('province')
            required_province = self._get_province_from_requirements(requirements)
            if template_province and required_province and template_province.lower() == required_province.lower():
                score += 50  # 省份匹配得高分
                match_reasons['province'] = True
            elif template_province != required_province:
                continue  # 跳过不匹配省份的模板
            
            # 2. 物业类型匹配
            required_property_type = requirements.get('property_type')
            template_property_types = template.get('property_types', [])
            if required_property_type and required_property_type in template_property_types:
                score += 10
                match_reasons['property_type'] = True
            
            # 3. 特殊功能匹配
            special_requirements = requirements.get('special_requirements', {})
            template_features = template.get('features', [])
            
            matching_features = {
                feature for feature, needed in special_requirements.items()
                if needed and feature in template_features
            }
            score += len(matching_features) * 5
            match_reasons['features'] = matching_features
            
            # 4. 章节完整性
            template_sections = template.get('sections', {})
            sections_list = list(template_sections.keys()) if template_sections else []
            score += len(sections_list)
            match_reasons['sections'] = sections_list
            
            # 更新最佳匹配
            if score > best_match['score']:
                template['score'] = score
                template['match_reasons'] = match_reasons
                best_match = {
                    'template': template,
                    'score': score,
                    'match_reasons': match_reasons
                }
        
        if not best_match['template']:
            raise ValueError("未找到合适的合同模板")
        
        return best_match['template']

    def generate_initial_contract(self, requirements: Dict) -> Dict:
        """生成初始合同"""
        try:
            # 获取合同模板
            template = self._get_contract_template(requirements)
            if not template:
                print("未找到合适的合同模板")
                return None

            # 创建基本合同结构
            contract = {
                'version': template.get('version', '1.0'),
                'type': template.get('type', 'residential_lease'),
                'sections': {
                    'parties': {},
                    'property': {},
                    'term': {},
                    'rent': {}
                },
                'special_clauses': [],
                'custom_clauses': []
            }

            # 填充基本信息
            if requirements.get('property'):
                contract['sections']['property'] = requirements['property']

            if requirements.get('rent'):
                contract['sections']['rent'] = requirements['rent']

            if requirements.get('term'):
                contract['sections']['term'] = requirements['term']

            # 处理特殊条款
            if requirements.get('special_requirements'):
                for clause_type, needed in requirements['special_requirements'].items():
                    if needed:
                        special_clause = self._create_special_clause(
                            clause_type=clause_type,
                            variables={}  # 使用默认变量
                        )
                        if special_clause:
                            contract['special_clauses'].append(special_clause)

            return contract

        except Exception as e:
            print(f"生成合同时出错: {str(e)}")
            return None

    def modify_contract(self, contract: Dict, modifications: List[Dict]) -> Dict:
        """修改现有合同
        
        Args:
            contract: 现有合同
            modifications: 修改列表
        """
        for mod in modifications:
            if not isinstance(mod, dict):
                continue
                
            mod_type = mod.get('type')
            action = mod.get('action')
            target = mod.get('target')
            value = mod.get('value')
            
            if not all(x is not None for x in [mod_type, action, target, value]):
                continue
            
            if mod_type == 'basic_info':
                if isinstance(target, dict):
                    section = target.get('section')
                    field = target.get('field')
                    
                    if section and field:
                        if 'sections' not in contract:
                            contract['sections'] = {}
                        if section not in contract['sections']:
                            contract['sections'][section] = {}
                        contract['sections'][section][field] = value
            
            elif mod_type == 'clause':
                if not isinstance(target, str):
                    continue
                    
                if action == 'add':
                    # 获取条款模板
                    template = self.session.query(SpecialClause).filter_by(
                        clause_type=target
                    ).first()
                    
                    if template:
                        # 获取变量
                        variables = value.get('variables', {}) if isinstance(value, dict) else {}
                        self.add_special_clause(contract, target, variables)
                            
                elif action == 'remove':
                    if 'special_clauses' in contract:
                        contract['special_clauses'] = [
                            c for c in contract['special_clauses']
                            if c.get('type') != target
                        ]
                            
                elif action == 'modify':
                    if 'special_clauses' in contract:
                        for clause in contract['special_clauses']:
                            if clause.get('type') == target:
                                if isinstance(value, dict):
                                    variables = value.get('variables', {})
                                    clause['variables'].update(variables)
                                    
                                    # 重新格式化内容
                                    template = self.session.query(SpecialClause).filter_by(
                                        clause_type=target
                                    ).first()
                                    
                                    if template:
                                        content = template.content
                                        if isinstance(content, str):
                                            content = content.format(**clause['variables'])
                                        elif isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
                                            if isinstance(content, str):
                                                content = json.loads(content)
                                            content = json.loads(json.dumps(content).format(**clause['variables']))
                                        clause['content'] = content
                                        clause['modified_at'] = datetime.now().isoformat()
        
        # 记录修改历史
        if 'modification_history' not in contract:
            contract['modification_history'] = []
            
        contract['modification_history'].append({
            'timestamp': datetime.now().isoformat(),
            'modifications': modifications
        })
        
        return contract
            
    def add_special_clause(self, contract: Dict, clause_type: str, variables: Dict = None) -> Dict:
        """添加特殊条款到合同"""
        # 获取条款模板
        template = self.session.query(SpecialClause).filter_by(
            clause_type=clause_type
        ).first()
        
        if not template:
            print(f"Warning: Clause template not found: {clause_type}")
            return contract
        
        # 验证必需变量
        required_vars = (json.loads(template.variables) 
                       if isinstance(template.variables, str) 
                       else template.variables or [])
        
        if variables is None:
            variables = {}
            
        missing_vars = set(required_vars) - set(variables.keys())
        if missing_vars:
            print(f"Warning: Missing required variables for clause {clause_type}: {missing_vars}")
            return contract
        
        # 初始化特殊条款列表
        if 'special_clauses' not in contract:
            contract['special_clauses'] = []
        
        # 处理条款内容
        content = template.content
        if isinstance(content, str):
            content = content.format(**variables)
        elif isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
            if isinstance(content, str):
                content = json.loads(content)
            content = json.loads(json.dumps(content).format(**variables))
        
        # 添加条款
        contract['special_clauses'].append({
            'type': clause_type,
            'display_name': template.title or self.format_clause_name(clause_type),
            'content': content,
            'variables': variables,
            'added_at': datetime.now().isoformat()
        })
        
        return contract

    def _select_relevant_clauses(self, requirements: Dict) -> List[Dict]:
        """Select relevant clauses based on requirements"""
        relevant_clauses = []
        
        # Query relevant clauses based on different aspects of requirements
        if requirements.get('special_requirements', {}).get('pets', {}).get('allowed'):
            pet_clauses = self.session.query(SpecialClause).filter(
                SpecialClause.category == 'pets',
                SpecialClause.province == requirements['location']['province']
            ).all()
            relevant_clauses.extend(pet_clauses)
        
        # Query clauses based on other special requirements
        for feature in requirements.get('property', {}).get('preferences', []):
            feature_clauses = self.session.query(SpecialClause).filter(
                SpecialClause.category == feature,
                SpecialClause.province == requirements['location']['province']
            ).all()
            relevant_clauses.extend(feature_clauses)
        
        # Convert to dictionary format
        return [{
            'id': clause.id,
            'category': clause.category,
            'content': clause.clause_text,
            'variables': clause.variables if clause.variables else {},
            'prerequisites': clause.prerequisites if clause.prerequisites else {}
        } for clause in relevant_clauses]

    
    def _select_base_template(self, requirements: Dict) -> Dict:
        """Select base template based on requirements"""
        # Get all possible templates
        templates = self.session.query(ContractTemplate).filter(
            ContractTemplate.province == requirements['location']['province']
        ).all()
        
        if not templates:
            raise Exception("No matching contract template found")
            
        # Property type mapping
        property_type_map = {
            'apartment': 'rental',
            'house': 'rental',
            'condo': 'rental',
            'room': 'rental'
        }
        
        # Prepare template list for AI evaluation
        template_details = []
        for template in templates:
            try:
                version = int(float(template.version)) if template.version else 1
            except (ValueError, TypeError):
                version = 1
                
            template_details.append({
                'id': template.id,
                'type': template.type,
                'version': version,
                'description': template.template_json.get('description', ''),
                'sections': [s.get('title') for s in template.template_json.get('sections', [])],
                'blank_fields': self._extract_blank_fields(template.template_json),
                'special_features': template.template_json.get('special_features', []),
                'score': 0
            })
            
        # Print all available templates for selection
        print("\nAvailable contract templates:")
        for i, template in enumerate(template_details, 1):
            print(f"\nTemplate {i}:")
            print(f"ID: {template['id']}")
            print(f"Type: {template['type']}")
            print(f"Version: {template['version']}")
            print(f"Description: {template['description']}")
            print("Includes sections:", ", ".join(template['sections']))
            print("Special features:", ", ".join(template['special_features']))
            
        # Scoring criteria
        scoring_criteria = {
            'property_type_match': 10,
            'special_requirements_match': 5,
            'completeness': 3,
            'version': 2,
            'field_coverage': 4,
            'feature_match': 6
        }
        
        # Score each template
        for template in template_details:
            # 1. Property type match
            required_type = property_type_map.get(
                requirements.get('property', {}).get('type', ''),
                'rental'
            )
            if template['type'] == required_type:
                template['score'] += scoring_criteria['property_type_match']
                
            # 2. Special requirement match
            special_reqs = requirements.get('special_requirements', {})
            for feature in template['special_features']:
                if feature in special_reqs:
                    template['score'] += scoring_criteria['special_requirements_match']
                    
            # 3. Template completeness score
            template['score'] += len(template['sections']) * scoring_criteria['completeness']
            
            # 4. Version score
            template['score'] += template['version'] * scoring_criteria['version']
            
            # 5. Field coverage score
            required_fields = self._get_required_fields(requirements)
            available_fields = set(field['name'] for field in template['blank_fields'])
            coverage = len(required_fields.intersection(available_fields)) / len(required_fields) if required_fields else 0
            template['score'] += coverage * scoring_criteria['field_coverage']
            
            # 6. Feature match
            for pref in requirements.get('property', {}).get('preferences', []):
                if pref in template['special_features']:
                    template['score'] += scoring_criteria['feature_match']
        
        # Sort templates by score
        template_details.sort(key=lambda x: x['score'], reverse=True)
        
        # Get the highest scoring template
        selected_template = self.session.query(ContractTemplate).get(template_details[0]['id'])
        
        # Debug output
        print("\nSelected template details:")
        print(f"ID: {selected_template.id}")
        print(f"Type: {selected_template.type}")
        print(f"Version: {selected_template.version} (converted: {template_details[0]['version']})")
        print(f"Score: {template_details[0]['score']}")
        print("Match reasons:")
        print(f"- Property type match: {template['type'] == required_type}")
        print(f"- Special feature match: {set(template_details[0]['special_features']) & set(requirements.get('property', {}).get('preferences', []))}")
        print(f"- Section count: {len(template_details[0]['sections'])}")
        
        return selected_template.template_json

    def _get_required_fields(self, requirements: Dict) -> set:
        """Determine required fields based on requirements"""
        required_fields = set()
        
        # Basic fields
        if 'location' in requirements:
            required_fields.update({'city', 'province', 'country'})
            
        if 'financial' in requirements:
            required_fields.update({'rent_amount', 'currency'})
            if 'deposit' in requirements['financial']:
                required_fields.update({'deposit_amount', 'deposit_unit'})
                
        if 'timeline' in requirements:
            required_fields.update({'start_date', 'duration_amount', 'duration_unit'})
            
        if 'special_requirements' in requirements:
            if 'pets' in requirements['special_requirements']:
                required_fields.update({'pets_allowed', 'pet_types'})
            
        return required_fields

    def _extract_blank_fields(self, template_json: Dict) -> List[Dict]:
        """Extract all blank fields from template"""
        blank_fields = []
        
        # Iterate through all sections
        for section in template_json.get('sections', []):
            for field in section.get('fields', []):
                if field.get('type') in ['text', 'number', 'date', 'select']:
                    blank_fields.append({
                        'section': section['title'],
                        'name': field['name'],
                        'type': field['type'],
                        'required': field.get('required', False),
                        'validation': field.get('validation', {})
                    })
                    
        return blank_fields

    def _create_contract(self, template: Dict, requirements: Dict, special_clauses: List[Dict]) -> Dict:
        """Create new contract"""
        try:
            # Create basic contract structure
            contract = {
                'version': template.get('version', '1.0'),
                'type': template.get('type', 'rental'),
                'sections': {
                    'property': requirements.get('property', {}),
                    'landlord': requirements.get('landlord', {}),
                    'tenant': requirements.get('tenant', {}),
                    'term': requirements.get('term', {}),
                    'rent': requirements.get('rent', {})
                },
                'special_clauses': [],
                'custom_clauses': []
            }
            
            # Add special clauses
            if special_clauses:
                for clause in special_clauses:
                    # Check clause compatibility
                    if self._check_clause_compatibility(contract, clause):
                        contract['special_clauses'].append(clause)
            
            # Validate contract completeness
            validation_messages = self._validate_contract(contract, requirements)
            if validation_messages:
                print("\nContract validation results:")
                for msg in validation_messages:
                    print(msg)
            
            return contract
            
        except Exception as e:
            print(f"Error creating contract: {str(e)}")
            raise

    def _check_clause_compatibility(self, contract: Dict, new_clause: Dict) -> bool:
        """Check clause compatibility"""
        # Get existing clause types
        existing_types = {clause['type'] for clause in contract.get('special_clauses', [])}
        
        # Define incompatible clause combinations
        incompatible_combinations = {
            'pets': {'no_pets'},  # Pet clause and no pet clause are incompatible
            'parking': {'no_parking'},  # Parking clause and no parking clause are incompatible
            'balcony': {'no_balcony'},  # Balcony clause and no balcony clause are incompatible
            'gas_appliance': {'no_gas'}  # Gas appliance clause and no gas clause are incompatible
        }
        
        # Check if new clause conflicts with existing clauses
        incompatible = incompatible_combinations.get(new_clause['type'], set())
        return not (incompatible & existing_types)

    def _find_field_by_name(self, contract: Dict, field_name: str) -> Optional[Dict]:
        """Find field by name in contract"""
        if not contract or not field_name:
            return None
            
        # Search in sections
        sections = contract.get('sections', {})
        for section_name, section_data in sections.items():
            if field_name in section_data:
                return section_data[field_name]
        
        # Search in special clauses
        special_clauses = contract.get('special_clauses', [])
        for clause in special_clauses:
            if clause.get('name') == field_name:
                return clause
        
        return None

    def _fill_basic_info(self, contract: Dict, requirements: Dict):
        """Fill in basic contract information"""
        # Basic information mapping
        basic_info = {
            'property_location': f"{requirements['location']['city']}, {requirements['location']['province']}",
            'property_type': requirements['property']['type'],
            'rent_amount': requirements['financial']['rent_amount'],
            'start_date': requirements['timeline']['start_date'],
            'end_date': self._calculate_end_date(
                requirements['timeline']['start_date'],
                requirements['timeline']['duration']
            ),
            'deposit_amount': requirements['financial']['rent_amount'] * 
                            requirements['financial']['deposit']['amount']
        }
        
        # Iterate through all sections and fill in corresponding fields
        for section in contract['sections']:
            for field in section['fields']:
                field_name = field['name']
                if field_name in basic_info:
                    field['value'] = basic_info[field_name]
                    field['display_value'] = str(basic_info[field_name])  # Add display value

    def _calculate_end_date(self, start_date: str, duration: Dict) -> str:
        """Calculate end date"""
        if not duration:
            # Default one-year term
            start_date = datetime.now().replace(day=1) + relativedelta(months=1)
            end_date = start_date + relativedelta(years=1, days=-1)
            return end_date.strftime('%Y-%m-%d')
        
        # If end date is already specified, use it
        if duration.get('end_date'):
            return duration['end_date']
        
        # Get start date
        start_date_str = start_date
        if not start_date_str:
            start_date = datetime.now().replace(day=1) + relativedelta(months=1)
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                # If date format is incorrect, use next month's first day as start date
                start_date = datetime.now().replace(day=1) + relativedelta(months=1)
        
        # Get duration information
        years = duration.get('years', 0)
        months = duration.get('months', 0)
        days = duration.get('days', 0)
        
        # Calculate end date
        end_date = start_date + relativedelta(years=years, months=months, days=days - 1)
        return end_date.strftime('%Y-%m-%d')

    def _handle_special_requirements(self, contract: Dict, requirements: Dict):
        """Handle special requirements"""
        special_reqs = requirements['special_requirements']
        
        # Track added clause categories
        added_categories = set()
        
        # If contract doesn't have special_clauses field, initialize it
        if 'special_clauses' not in contract:
            contract['special_clauses'] = []
        
        # Handle special requirements
        for category, details in special_reqs.items():
            if isinstance(details, dict) and details.get('allowed'):
                # If this category is already added, skip
                if category in added_categories:
                    continue
                    
                # Query relevant clauses
                clauses = self.session.query(SpecialClause).filter(
                    SpecialClause.category == category
                ).all()
                
                # Add found clauses
                for clause in clauses:
                    # Replace clause variables
                    clause_content = clause.clause_text
                    for var_name, var_value in details.items():
                        if isinstance(var_value, list):
                            var_value = ', '.join(var_value)
                        placeholder = f"{{{var_name}}}"
                        if placeholder in clause_content:
                            clause_content = clause_content.replace(placeholder, str(var_value))
                    
                    contract['special_clauses'].append({
                        'id': clause.id,
                        'category': clause.category,
                        'content': clause_content
                    })
                    added_categories.add(category)
        
        # Handle preferences
        preferences = requirements['property'].get('preferences', [])
        for pref in preferences:
            # If this preference is already added, skip
            if pref in added_categories:
                continue
                
            # Query relevant clauses
            pref_clauses = self.session.query(SpecialClause).filter(
                SpecialClause.category == pref
            ).all()
            
            # Add found clauses
            for clause in pref_clauses:
                contract['special_clauses'].append({
                    'id': clause.id,
                    'category': clause.category,
                    'content': clause.clause_text
                })
                added_categories.add(pref)
                
        # Remove duplicates from special_clauses
        contract['special_clauses'] = list({
            clause['category']: clause
            for clause in contract['special_clauses']
        }.values())
        
        # Handle preferences
        preferences = requirements['property'].get('preferences', [])
        if preferences:
            # Query relevant clauses
            for pref in preferences:
                pref_clauses = self.session.query(SpecialClause).filter(
                    SpecialClause.category == pref
                ).all()
                
                # Add found clauses
                for clause in pref_clauses:
                    if 'special_clauses' not in contract:
                        contract['special_clauses'] = []
                    contract['special_clauses'].append({
                        'id': clause.id,
                        'category': clause.category,
                        'content': clause.clause_text
                    })
    
    def _analyze_modification_needs(self, request: Dict, current_contract: Dict) -> Tuple[List[str], List[str]]:
        """Analyze modifications needed"""
        additions = []
        removals = []
        
        # Analyze each modification request
        for req in request['requirements']:
            if req['action'] == 'add':
                # Check if similar clause already exists
                if not self._has_similar_clause(current_contract, req['category']):
                    additions.append(req['category'])
            elif req['action'] == 'remove':
                removals.append(req['category'])
        
        return additions, removals

    def _fetch_required_clauses(self, categories: List[str]) -> List[Dict]:
        """Fetch required clauses from database"""
        clauses = []
        for category in categories:
            db_clauses = self.session.query(SpecialClause).filter(
                SpecialClause.category == category
            ).all()
            clauses.extend([clause.to_dict() for clause in db_clauses])
        return clauses

    def _has_similar_clause(self, contract: Dict, category: str) -> bool:
        """Check if contract already has similar clause"""
        for section in contract['sections']:
            for clause in section.get('clauses', []):
                if clause['category'].lower() == category.lower():
                    return True
        return False

    def _find_appropriate_section(self, contract: Dict, category: str) -> Dict:
        """Find suitable section for clause"""
        category_section_mapping = {
            'pets': 'Special Terms',
            'maintenance': 'Responsibilities',
            'payment': 'Financial Details',
            'utilities': 'Services and Utilities'
        }
        
        target_section = category_section_mapping.get(category.lower(), 'General Terms')
        
        # Find or create target section
        for section in contract['sections']:
            if section['title'] == target_section:
                return section
                
        # If no suitable section is found, create a new one
        new_section = {
            'title': target_section,
            'clauses': []
        }
        contract['sections'].append(new_section)
        return new_section

    def _get_special_clauses(self, requirements: Dict) -> List[Dict]:
        """获取特殊条款"""
        special_clauses = []
        
        # 处理必需的特殊条款
        if 'special_clauses' in requirements:
            for clause_req in requirements['special_clauses']:
                clause_type = clause_req.get('type')
                if clause_type:
                    clause = self.session.query(SpecialClause).filter_by(clause_type=clause_type).first()
                    if clause:
                        # 处理变量
                        content = clause.content
                        variables = clause_req.get('variables', {})
                        
                        special_clauses.append({
                            'type': clause_type,
                            'content': content,
                            'title': clause.title,
                            'variables': variables
                        })
                    else:
                        print(f"Warning: Required special clause '{clause_type}' not found")
        
        # 处理特殊要求
        if 'special_requirements' in requirements:
            for req_type, req_value in requirements['special_requirements'].items():
                if req_value and not any(clause['type'] == req_type for clause in special_clauses):
                    clause = self.session.query(SpecialClause).filter_by(clause_type=req_type).first()
                    if clause:
                        # 处理变量
                        content = clause.content
                        variables = {}  # 这里可以根据需要设置变量
                        
                        special_clauses.append({
                            'type': req_type,
                            'content': content,
                            'title': clause.title,
                            'variables': variables
                        })
                    else:
                        print(f"Warning: Special requirement clause '{req_type}' not found")
        
        return special_clauses

    def _create_special_clause(self, clause_type: str, variables: Dict = None) -> Dict:
        """创建特殊条款"""
        try:
            # 从数据库获取条款模板
            clause_template = self.session.query(SpecialClause).filter_by(
                clause_type=clause_type
            ).first()
            
            if not clause_template:
                print(f"Warning: Clause template '{clause_type}' not found in database")
                return "Clause template not found."
            
            # 获取条款内容
            content = clause_template.content
            
            # 填充变量
            if variables:
                for var_name, var_value in variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in content:
                        content = content.replace(placeholder, str(var_value))
                    else:
                        print(f"Warning: Variable placeholder '{var_name}' not found in template")
            
            return {
                'type': clause_type,
                'content': content
            }
            
        except Exception as e:
            print(f"创建特殊条款时出错: {str(e)}")
            return None

    def _format_clause_content(self, clause_type: str, variables: Dict) -> str:
        """格式化条款内容"""
        try:
            # 从数据库获取条款模板
            clause_template = self.session.query(SpecialClause).filter_by(
                clause_type=clause_type
            ).first()
            
            if not clause_template:
                print(f"Warning: Clause template '{clause_type}' not found in database")
                return "Clause template not found."
            
            # 获取条款内容
            content = clause_template.content
            
            # 填充变量
            if variables:
                for var_name, var_value in variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in content:
                        content = content.replace(placeholder, str(var_value))
                    else:
                        print(f"Warning: Variable placeholder '{var_name}' not found in template")
            
            return content
            
        except Exception as e:
            print(f"Error formatting clause content: {str(e)}")
            return "Error formatting clause content."

    def _evaluate_condition(self, condition: Dict, value: any) -> bool:
        """Evaluate condition"""
        if not condition or not isinstance(condition, dict):
            return True
            
        op = condition.get('operator')
        target = condition.get('value')
        
        if not op or target is None:
            return True
        
        try:
            if op == 'equals':
                return str(value).lower() == str(target).lower()
            elif op == 'not_equals':
                return str(value).lower() != str(target).lower()
            elif op == 'greater_than':
                return float(value) > float(target)
            elif op == 'less_than':
                return float(value) < float(target)
            elif op == 'contains':
                return str(target).lower() in str(value).lower()
            elif op == 'not_contains':
                return str(target).lower() not in str(value).lower()
        except (ValueError, TypeError):
            return False
        
        return True

    def _extract_field_values(self, requirements: Dict) -> Dict:
        """Extract field values from requirements"""
        field_values = {}
        
        # Extract tenant information
        if 'tenant' in requirements:
            tenant = requirements['tenant']
            field_values.update({
                'tenant_name': tenant.get('name'),
                'tenant_contact': tenant.get('contact')
            })
        
        # Extract landlord information
        if 'landlord' in requirements:
            landlord = requirements['landlord']
            field_values.update({
                'landlord_name': landlord.get('name'),
                'landlord_contact': landlord.get('contact')
            })
        
        # Extract property information
        if 'property' in requirements:
            property_info = requirements['property']
            field_values.update({
                'property_type': property_info.get('type'),
                'property_address': property_info.get('address'),
                'unit_number': property_info.get('unit')
            })
        
        # Extract term information
        if 'term' in requirements:
            term = requirements['term']
            field_values.update({
                'start_date': term.get('start_date'),
                'end_date': term.get('end_date'),
                'term_type': term.get('type', 'fixed')
            })
        
        # Extract rent information
        if 'rent' in requirements:
            rent = requirements['rent']
            field_values.update({
                'rent_amount': rent.get('amount'),
                'rent_payment_frequency': rent.get('frequency', 'monthly'),
                'rent_due_date': rent.get('due_date', 1)
            })
        
        # Remove all None values
        field_values = {k: v for k, v in field_values.items() if v is not None}
        
        return field_values

    def _validate_field_values(self, field_values: Dict) -> List[str]:
        """Validate field values"""
        errors = []
        
        # Validate dates
        if 'start_date' in field_values:
            try:
                start_date = datetime.strptime(field_values['start_date'], '%Y-%m-%d')
                if start_date < datetime.now():
                    errors.append('Start date cannot be earlier than today')
            except ValueError:
                errors.append('Invalid start date format')
                
        # Validate amounts
        if 'rent_amount' in field_values:
            try:
                rent = float(field_values['rent_amount'])
                if rent <= 0:
                    errors.append('Rent amount must be greater than 0')
            except ValueError:
                errors.append('Invalid rent amount format')
                
        if 'deposit_amount' in field_values:
            try:
                deposit = float(field_values['deposit_amount'])
                if deposit <= 0:
                    errors.append('Deposit amount must be greater than 0')
            except ValueError:
                errors.append('Invalid deposit amount format')
                
        # Validate required fields
        required_fields = {
            'city': 'City',
            'province': 'Province',
            'rent_amount': 'Rent amount',
            'start_date': 'Start date',
            'duration_amount': 'Duration'
        }
        
        for field, label in required_fields.items():
            if field not in field_values or not field_values[field]:
                errors.append(f'{label} cannot be empty')
                
        return errors

    def _process_clause_variables(self, clause: Dict, field_values: Dict) -> Dict:
        """Process clause variables"""
        processed_clause = clause.copy()
        
        # Ensure basic fields exist
        if 'type' not in processed_clause:
            processed_clause['type'] = 'general'
        if 'title' not in processed_clause:
            processed_clause['title'] = processed_clause['type'].capitalize()
        
        # Get clause variables
        variables = processed_clause.get('variables', {})
        
        # Replace variables
        content = processed_clause['content']
        for var_name, var_info in variables.items():
            if var_name in field_values:
                placeholder = f"{{{var_name}}}"
                value = field_values[var_name]
                
                # Format value based on variable type
                if var_info.get('type') == 'currency':
                    value = f"{value:,.2f}"
                elif var_info.get('type') == 'date':
                    value = datetime.strptime(value, '%Y-%m-%d').strftime('%B %d, %Y')
                
                content = content.replace(placeholder, str(value))
        
        processed_clause['content'] = content
        processed_clause['filled'] = all(
            var_name in field_values 
            for var_name in variables.keys()
        )
        
        return processed_clause

    def _localize_clause(self, clause: Dict) -> Dict:
        """Localize special clause content"""
        # Get localized content from database
        localized = self.session.query(ClauseTranslation).filter_by(
            clause_id=clause['id'],
            language='en_US'  # Can be changed based on user preference
        ).first()
        
        if localized:
            clause['title'] = localized.title
            clause['content'] = localized.content
            
        return clause

    def _create_special_clause(self, clause_type: str, content: str = None, variables: Dict = None) -> Dict:
        """Create special clause"""
        try:
            # Get special clause from database
            clause = self.session.query(SpecialClause).filter_by(clause_type=clause_type).first()
            if not clause:
                return None
            
            # Use provided content or template content
            clause_content = content if content else clause.content
            
            # Handle variables
            if variables and clause.variables:
                try:
                    default_variables = json.loads(clause.variables)
                    # Merge default variables and provided variables
                    final_variables = {**default_variables, **variables}
                    # Replace variables
                    for var_name, value in final_variables.items():
                        if value is None:
                            value = ''
                        clause_content = clause_content.replace('{' + var_name + '}', str(value))
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON in clause variables for {clause_type}")
            
            return {
                'type': clause_type,
                'title': clause.title,
                'content': clause_content.strip()  # Remove extra whitespace
            }
            
        except Exception as e:
            print(f"Error creating special clause: {str(e)}")
            return None
            
    def _generate_contract(self) -> bool:
        """生成合同"""
        try:
            # 1. 初始化合同结构
            self.contract = {
                'version': self.template.get('version', '1.0'),
                'type': self.template.get('type'),
                'sections': []
            }
            
            # 2. 添加基本部分
            self._add_basic_sections()
            
            # 3. 处理特殊需求，转换为特殊条款需求
            if 'special_requirements' in self.requirements:
                if 'special_clauses' not in self.requirements:
                    self.requirements['special_clauses'] = []
                
                for req_type, req_value in self.requirements['special_requirements'].items():
                    if req_value and not any(clause['type'] == req_type for clause in self.requirements['special_clauses']):
                        # 获取默认变量值
                        clause = self.session.query(SpecialClause).filter_by(
                            clause_type=req_type
                        ).first()
                        
                        if clause and clause.variables:
                            default_variables = json.loads(clause.variables)
                            self.requirements['special_clauses'].append({
                                'type': req_type,
                                'variables': default_variables
                            })
            
            # 4. 添加特殊条款
            special_clauses = self._get_special_clauses(self.requirements)
            if special_clauses:
                self.contract['special_clauses'] = special_clauses
            
            return True
            
        except Exception as e:
            print(f"生成合同时出错: {str(e)}")
            return False

    def _generate_contract_text(self, contract: Dict) -> str:
        """生成合同文本"""
        try:
            sections = []
            
            # 添加标题
            sections.append("【租赁合同】")
            sections.append(f"合同版本: {contract.get('version', '1.0')}")
            sections.append(f"合同类型: {contract.get('type', 'residential_lease')}\n")
            
            # 添加基本章节
            for section_name in ['Parties', 'Rental Unit', 'Term', 'Rent']:
                sections.append(f"【{section_name}】")
                if section_name.lower() in contract:
                    section_data = contract[section_name.lower()]
                    for key, value in section_data.items():
                        # 格式化字段名称，例如将 start_date 转换为 Start Date
                        formatted_key = ' '.join(word.capitalize() for word in key.split('_'))
                        sections.append(f"{formatted_key}: {value}")
                sections.append("")
            
            # 添加特殊条款
            if contract.get('special_clauses'):
                sections.append("【特殊条款】\n")
                for clause in contract['special_clauses']:
                    if isinstance(clause, dict):
                        # Add title if available
                        if 'title' in clause:
                            sections.append(f"{clause['title']}:")
                        else:
                            sections.append(f"{clause['type']}类条款:")
                        
                        # Format content with proper indentation
                        if 'content' in clause:
                            content = clause['content'].strip()
                            # Add indentation to each line
                            content = '\n'.join('                ' + line for line in content.split('\n'))
                            sections.append(content)
                            sections.append("")  # Add empty line for readability
            
            # 添加自定义条款
            if contract.get('custom_clauses'):
                sections.append("【自定义条款】\n")
                for i, clause in enumerate(contract['custom_clauses'], 1):
                    sections.append(f"自定义条款 {i}:")
                    sections.append(clause['content'])
                    sections.append("")
            
            # 生成最终文本
            return "\n".join(sections)
            
        except Exception as e:
            print(f"生成合同文本时出错: {str(e)}")
            return ""

    def _get_contract_template(self, requirements: Dict) -> Dict:
        """获取最合适的合同模板"""
        try:
            # 获取所有可用模板
            templates = self.get_available_templates(requirements)
            if not templates:
                return None
            
            # 选择最合适的模板
            best_match = None
            best_score = -1
            
            for template in templates:
                score = 0
                
                # 检查省份匹配
                if requirements.get('property', {}).get('city') == template.get('province'):
                    score += 3
                
                # 检查合同类型匹配
                if requirements.get('property', {}).get('type') == template.get('type'):
                    score += 2
                
                # 检查特殊要求匹配
                template_features = json.loads(template.get('features', '[]'))
                special_requirements = requirements.get('special_requirements', {})
                for feature in template_features:
                    if feature in special_requirements and special_requirements[feature]:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = template
            
            return best_match
            
        except Exception as e:
            print(f"获取合同模板时出错: {str(e)}")
            return None

    def validate_template(self, template: ContractTemplate) -> List[str]:
        """验证合同模板的完整性和有效性
        
        Args:
            template: 合同模板
            
        Returns:
            问题列表，如果没有问题则为空列表
        """
        issues = []
        
        # 检查必需字段
        required_fields = ['type', 'version', 'sections', 'province']
        for field in required_fields:
            if not hasattr(template, field) or getattr(template, field) is None:
                issues.append(f"Missing required field: {field}")
        
        # 检查sections结构
        if hasattr(template, 'sections'):
            required_sections = ['landlord', 'tenant', 'property', 'term', 'financial']
            for section in required_sections:
                if section not in template.sections:
                    issues.append(f"Missing required section: {section}")
        
        return issues
    
    def format_clause_name(self, clause_type: str) -> str:
        """将条款类型转换为友好的显示名称
        
        Args:
            clause_type: 条款类型标识符
            
        Returns:
            友好的显示名称
        """
        # 从数据库获取显示名称
        clause = self.session.query(SpecialClause).filter_by(clause_type=clause_type).first()
        if clause and clause.display_name:
            return clause.display_name
            
        # 如果没有预设的显示名称，美化标识符
        return clause_type.replace('_', ' ').title()
    
    def add_special_clause(self, contract: Dict, clause_type: str, variables: Dict) -> Dict:
        """添加特殊条款到合同
        
        Args:
            contract: 当前合同
            clause_type: 条款类型
            variables: 条款变量
            
        Returns:
            更新后的合同
        """
        # 获取条款模板
        template = self.session.query(SpecialClause).filter_by(
            clause_type=clause_type
        ).first()
        
        if not template:
            print(f"Warning: Clause template not found: {clause_type}")
            return contract
        
        # 验证必需变量
        required_vars = (json.loads(template.variables) 
                       if isinstance(template.variables, str) 
                       else template.variables or [])
        
        if variables is None:
            variables = {}
            
        missing_vars = set(required_vars) - set(variables.keys())
        if missing_vars:
            print(f"Warning: Missing required variables for clause {clause_type}: {missing_vars}")
            return contract
        
        # 初始化特殊条款列表
        if 'special_clauses' not in contract:
            contract['special_clauses'] = []
        
        # 处理条款内容
        content = template.content
        if isinstance(content, str):
            content = content.format(**variables)
        elif isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
            if isinstance(content, str):
                content = json.loads(content)
            content = json.loads(json.dumps(content).format(**variables))
        
        # 添加条款
        contract['special_clauses'].append({
            'type': clause_type,
            'display_name': template.title or self.format_clause_name(clause_type),
            'content': content,
            'variables': variables,
            'added_at': datetime.now().isoformat()
        })
        
        return contract
    
    def generate_contract(self, template_type: str, basic_info: Dict, special_clauses: List[str]) -> Dict:
        """生成新合同
        
        Args:
            template_type: 合同模板类型
            basic_info: 基本信息
            special_clauses: 特殊条款列表
        
        Returns:
            Dict: 生成的合同数据
            
        Raises:
            ValueError: 当无法确定省份或找不到合适的模板时
            Exception: 其他错误
        """
        try:
            # 从地址中提取省份信息
            province = None
            if 'property' in basic_info and 'address' in basic_info['property']:
                address = basic_info['property']['address']
                # 提取省份缩写
                province_matches = {
                    'ON': ['Ontario', 'ON', 'Toronto', 'Ottawa', 'Hamilton'],
                    'BC': ['British Columbia', 'BC', 'Vancouver', 'Victoria'],
                    'AB': ['Alberta', 'AB', 'Calgary', 'Edmonton'],
                    'QC': ['Quebec', 'QC', 'Montreal', 'Quebec City'],
                }
                
                for prov_code, patterns in province_matches.items():
                    if any(pattern.lower() in address.lower() for pattern in patterns):
                        province = prov_code
                        break
            
            if not province:
                raise ValueError(f"无法从地址确定省份: {basic_info.get('property', {}).get('address')}")
            
            # 使用省份信息查询模板
            template = self.session.query(ContractTemplate).filter_by(
                type=template_type,
                province=province
            ).first()
            
            if not template:
                raise ValueError(f"找不到合同模板: {template_type} (省份: {province})")
            
            # 创建合同基本结构
            contract = {
                'version': template.version,
                'type': template.type,
                'province': province,
                'sections': {},
                'special_clauses': [],
                'creation_time': datetime.now().isoformat(),
                'modification_history': []
            }
            
            # 填充基本信息
            template_sections = json.loads(template.sections) if isinstance(template.sections, str) else template.sections
            if not template_sections:
                print(f"警告: 模板 {template_type} 没有定义任何章节")
                template_sections = {}
            
            # 处理每个部分
            for section_name, section_data in template_sections.items():
                contract['sections'][section_name] = {}
                if section_name in basic_info:
                    # 如果基本信息中有对应的部分，复制所有字段
                    contract['sections'][section_name] = basic_info[section_name]
                    # 确保所有必填字段都有值
                    if 'fields' in section_data:
                        for field_name, field_info in section_data['fields'].items():
                            if field_name not in contract['sections'][section_name]:
                                print(f"警告: 缺少必填字段 {section_name}.{field_name}")
                                contract['sections'][section_name][field_name] = ""
            
            # 添加特殊条款
            if isinstance(special_clauses, list):
                for clause_info in special_clauses:
                    if isinstance(clause_info, dict):
                        clause_type = clause_info.get('clause_type')
                        variables = clause_info.get('variables', {})
                    else:
                        clause_type = clause_info
                        # 从基本信息中提取相关变量
                        variables = self._extract_variables_from_basic_info(basic_info)
                        
                    if clause_type:
                        try:
                            # 添加条款
                            contract = self.add_special_clause(contract, clause_type, variables)
                        except Exception as e:
                            print(f"警告: 添加条款 {clause_type} 失败: {str(e)}")
                            traceback.print_exc()
            
            return contract
            
        except Exception as e:
            print(f"生成合同时出错: {str(e)}")
            traceback.print_exc()
            raise
            
    def _extract_variables_from_basic_info(self, basic_info: Dict) -> Dict:
        """从基本信息中提取变量
        
        Args:
            basic_info: 基本信息字典
            
        Returns:
            Dict: 提取的变量
        """
        variables = {}
        # 遍历基本信息的每个部分
        for section_name, section_data in basic_info.items():
            if isinstance(section_data, dict):
                # 对于字典类型的部分，将其扁平化
                for key, value in section_data.items():
                    if isinstance(value, (str, int, float, bool)):
                        variables[f"{section_name}_{key}"] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool)):
                                variables[f"{section_name}_{key}_{sub_key}"] = sub_value
        return variables

    def modify_contract(self, contract: Dict, modifications: List[Dict]) -> Dict:
        """修改现有合同
        
        Args:
            contract: 现有合同
            modifications: 修改列表
        """
        for mod in modifications:
            if mod['type'] == 'basic_info':
                self._modify_basic_info(contract, mod)
            elif mod['type'] == 'clause':
                self._modify_clauses(contract, mod)
            
            # 记录修改历史
            contract['modification_history'].append({
                'timestamp': datetime.now().isoformat(),
                'modification': mod
            })
        
        return contract

    def _modify_basic_info(self, contract: Dict, mod: Dict) -> None:
        """修改合同基本信息"""
        target = mod.get('target')
        value = mod.get('value')
        
        if not isinstance(target, dict):
            return
            
        section = target.get('section')
        field = target.get('field')
        
        if not section or not field:
            return
            
        if 'sections' not in contract:
            contract['sections'] = {}
        if section not in contract['sections']:
            contract['sections'][section] = {}
            
        contract['sections'][section][field] = value

    def _modify_clauses(self, contract: Dict, mod: Dict) -> None:
        """修改特殊条款"""
        action = mod.get('action')
        target = mod.get('target')
        clause_type = mod.get('clause_type', target)  # 支持两种方式指定条款类型
        
        if not action or not (target or clause_type):
            return
        
        if action == 'add':
            # 获取条款模板
            template = self.session.query(SpecialClause).filter_by(
                clause_type=clause_type
            ).first()
            
            if template:
                # 获取变量
                variables = mod.get('value', {}).get('variables', {})
                
                # 处理条款内容
                content = template.content
                if isinstance(content, str):
                    content = content.format(**variables)
                elif isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
                    if isinstance(content, str):
                        content = json.loads(content)
                    content = json.loads(json.dumps(content).format(**variables))
                
                # 初始化特殊条款列表
                if 'special_clauses' not in contract:
                    contract['special_clauses'] = []
                    
                # 添加条款
                contract['special_clauses'].append({
                    'type': clause_type,
                    'title': template.title,
                    'content': content,
                    'variables': variables,
                    'added_at': datetime.now().isoformat()
                })
                
        elif action == 'remove':
            if 'special_clauses' in contract:
                contract['special_clauses'] = [
                    c for c in contract['special_clauses']
                    if c.get('type') != clause_type
                ]
                
        elif action == 'modify':
            if 'special_clauses' in contract:
                for clause in contract['special_clauses']:
                    if clause.get('type') == clause_type:
                        # 更新变量
                        new_variables = mod.get('value', {}).get('variables', {})
                        if 'variables' not in clause:
                            clause['variables'] = {}
                        clause['variables'].update(new_variables)
                        
                        # 重新格式化内容
                        template = self.session.query(SpecialClause).filter_by(
                            clause_type=clause_type
                        ).first()
                        
                        if template:
                            content = template.content
                            if isinstance(content, str):
                                content = content.format(**clause['variables'])
                            elif isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
                                if isinstance(content, str):
                                    content = json.loads(content)
                                content = json.loads(json.dumps(content).format(**clause['variables']))
                            clause['content'] = content
                            clause['modified_at'] = datetime.now().isoformat()