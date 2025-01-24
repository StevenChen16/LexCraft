# tools/contract_diagnostics.py

from typing import Dict, List, Set
import json
from sqlalchemy.orm import Session
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.orm import ContractTemplate, SpecialClause, get_db_session

class ContractDiagnostics:
    """合同数据库诊断工具"""
    
    def __init__(self):
        """初始化诊断工具"""
        self.session, _ = get_db_session()
        self.required_sections = {
            'rental': {
                'common': [
                    'Parties',
                    'Rental Unit',
                    'Term',
                    'Rent',
                    'Security Deposit',
                    'Utilities',
                    'Maintenance'
                ],
                'British Columbia': [
                    'Application of the Residential Tenancy Act',
                    'Security Deposit and Pet Damage Deposit'
                ],
                'Ontario': [
                    'Additional Terms',
                    'Rights and Responsibilities'
                ]
            }
        }
        
        self.required_clauses = {
            'British Columbia': ['pet', 'balcony', 'parking', 'smoking'],
            'Ontario': ['pet', 'balcony', 'maintenance', 'insurance']
        }
    
    def run_diagnostics(self) -> Dict:
        """运行完整的诊断检查"""
        try:
            results = {
                'templates': self._check_templates(),
                'special_clauses': self._check_special_clauses(),
                'integrity': self._check_data_integrity(),
                'recommendations': []
            }
            
            # 生成建议
            self._generate_recommendations(results)
            
            return results
            
        finally:
            self.session.close()
    
    def _check_templates(self) -> Dict:
        """检查合同模板"""
        templates = self.session.query(ContractTemplate).all()
        results = {
            'total_count': len(templates),
            'by_province': {},
            'issues': []
        }
        
        for template in templates:
            province = template.province
            
            if province not in results['by_province']:
                results['by_province'][province] = {
                    'count': 0,
                    'versions': set(),
                    'missing_sections': set(),
                    'incomplete_sections': []
                }
            
            prov_result = results['by_province'][province]
            prov_result['count'] += 1
            prov_result['versions'].add(template.version)
            
            # 检查模板结构
            template_sections = template.sections if template.sections else {}
            if isinstance(template_sections, str):
                try:
                    template_sections = json.loads(template_sections)
                except json.JSONDecodeError:
                    template_sections = {}
            
            sections = set()
            if isinstance(template_sections, dict) and 'sections' in template_sections:
                sections = {s.get('title') for s in template_sections['sections'] if isinstance(s, dict) and 'title' in s}
            elif isinstance(template_sections, list):
                sections = {s.get('title') for s in template_sections if isinstance(s, dict) and 'title' in s}
            
            # 检查必需章节
            required = (self.required_sections['rental']['common'] + 
                      self.required_sections['rental'].get(province, []))
            missing = set(required) - sections
            prov_result['missing_sections'].update(missing)
            
            # 检查章节完整性
            section_list = template_sections.get('sections', []) if isinstance(template_sections, dict) else template_sections
            for section in section_list:
                if isinstance(section, dict) and not section.get('fields'):
                    prov_result['incomplete_sections'].append(section.get('title'))
            
        # 转换集合为列表以便JSON序列化
        for prov_data in results['by_province'].values():
            prov_data['versions'] = list(prov_data['versions'])
            prov_data['missing_sections'] = list(prov_data['missing_sections'])
        
        return results
    
    def _check_special_clauses(self) -> Dict:
        """检查特殊条款"""
        clauses = self.session.query(SpecialClause).all()
        results = {
            'total_count': len(clauses),
            'by_province': {},
            'missing_clauses': {}
        }
        
        for clause in clauses:
            province = clause.province
            
            if province not in results['by_province']:
                results['by_province'][province] = {
                    'count': 0,
                    'categories': set()
                }
            
            prov_result = results['by_province'][province]
            prov_result['count'] += 1
            prov_result['categories'].add(clause.category)
        
        # 检查缺失的必需条款
        for province, required in self.required_clauses.items():
            if province not in results['by_province']:
                results['missing_clauses'][province] = required
            else:
                existing = results['by_province'][province]['categories']
                missing = set(required) - existing
                if missing:
                    results['missing_clauses'][province] = list(missing)
        
        # 转换集合为列表
        for prov_data in results['by_province'].values():
            prov_data['categories'] = list(prov_data['categories'])
            
        return results
    
    def _check_data_integrity(self) -> Dict:
        """检查数据完整性"""
        results = {
            'invalid_templates': [],
            'invalid_clauses': [],
            'orphaned_fields': []
        }
        
        # 检查模板JSON结构
        templates = self.session.query(ContractTemplate).all()
        for template in templates:
            try:
                if not isinstance(template.sections, dict):
                    results['invalid_templates'].append({
                        'id': template.id,
                        'province': template.province,
                        'issue': 'Invalid JSON structure'
                    })
            except Exception as e:
                results['invalid_templates'].append({
                    'id': template.id,
                    'province': template.province,
                    'issue': str(e)
                })
        
        # 检查特殊条款
        clauses = self.session.query(SpecialClause).all()
        for clause in clauses:
            if not clause.content or not clause.content.strip():
                results['invalid_clauses'].append({
                    'id': clause.id,
                    'province': clause.province,
                    'category': clause.category,
                    'issue': 'Empty clause text'
                })
        
        return results
    
    def _generate_recommendations(self, results: Dict):
        """根据诊断结果生成建议"""
        recommendations = results['recommendations']
        
        # 模板相关建议
        for province, prov_data in results['templates']['by_province'].items():
            if prov_data['missing_sections']:
                recommendations.append({
                    'priority': 'high',
                    'type': 'template',
                    'province': province,
                    'action': f"Add missing sections for {province}: " + 
                             ", ".join(prov_data['missing_sections'])
                })
            
            if prov_data['incomplete_sections']:
                recommendations.append({
                    'priority': 'medium',
                    'type': 'template',
                    'province': province,
                    'action': f"Complete empty sections in {province} template: " +
                             ", ".join(prov_data['incomplete_sections'])
                })
        
        # 特殊条款建议
        for province, missing in results['special_clauses']['missing_clauses'].items():
            if missing:
                recommendations.append({
                    'priority': 'high',
                    'type': 'clause',
                    'province': province,
                    'action': f"Add missing special clauses for {province}: " +
                             ", ".join(missing)
                })
        
        # 数据完整性建议
        if results['integrity']['invalid_templates']:
            recommendations.append({
                'priority': 'critical',
                'type': 'integrity',
                'action': "Fix invalid template structures: " +
                         str(len(results['integrity']['invalid_templates'])) +
                         " templates affected"
            })
        
        if results['integrity']['invalid_clauses']:
            recommendations.append({
                'priority': 'high',
                'type': 'integrity',
                'action': "Fix invalid special clauses: " +
                         str(len(results['integrity']['invalid_clauses'])) +
                         " clauses affected"
            })

if __name__ == "__main__":
    diagnostics = ContractDiagnostics()
    results = diagnostics.run_diagnostics()
    
    print("\n=== Contract Database Diagnostics Report ===\n")
    
    print("Templates Summary:")
    print(f"Total templates: {results['templates']['total_count']}")
    for province, data in results['templates']['by_province'].items():
        print(f"\n{province}:")
        print(f"  Count: {data['count']}")
        print(f"  Versions: {', '.join(data['versions'])}")
        if data['missing_sections']:
            print(f"  Missing sections: {', '.join(data['missing_sections'])}")
        if data['incomplete_sections']:
            print(f"  Incomplete sections: {', '.join(data['incomplete_sections'])}")
    
    print("\nSpecial Clauses Summary:")
    print(f"Total clauses: {results['special_clauses']['total_count']}")
    for province, data in results['special_clauses']['by_province'].items():
        print(f"\n{province}:")
        print(f"  Count: {data['count']}")
        print(f"  Categories: {', '.join(data['categories'])}")
    
    if results['special_clauses']['missing_clauses']:
        print("\nMissing Required Clauses:")
        for province, missing in results['special_clauses']['missing_clauses'].items():
            print(f"  {province}: {', '.join(missing)}")
    
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"[{rec['priority'].upper()}] {rec['action']}")