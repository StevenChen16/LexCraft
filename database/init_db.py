import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from database.orm import Base, ContractTemplate, SpecialClause, get_db_session
import json

def init_database():
    """初始化数据库"""
    session, engine = get_db_session()
    
    try:
        # 1. 删除所有表
        Base.metadata.drop_all(engine)
        print("所有表已删除")
        
        # 2. 创建所有表
        Base.metadata.create_all(engine)
        print("所有表已创建")
        
        # 3. 添加基础合同模板
        ontario_template = ContractTemplate(
            type='residential_lease',
            province='ON',
            version='2024-01',
            description='Standard residential lease agreement for Ontario',
            sections=json.dumps({
                "parties": {
                    "title": "1. Parties to the Agreement",
                    "fields": {
                        "landlord": {
                            "name": "",
                            "type": "landlord",
                            "contact": ""
                        },
                        "tenant": {
                            "name": "",
                            "type": "tenant",
                            "contact": ""
                        }
                    }
                },
                "property": {
                    "title": "2. Rental Unit",
                    "fields": {
                        "type": "",
                        "address": "",
                        "features": []
                    }
                },
                "term": {
                    "title": "3. Term of Tenancy",
                    "fields": {
                        "start_date": "",
                        "duration": {
                            "amount": "",
                            "unit": ""
                        }
                    }
                },
                "financial_terms": {
                    "title": "4. Rent and Financial Terms",
                    "fields": {
                        "rent": 0,
                        "currency": "CAD",
                        "payment_frequency": "monthly",
                        "payment_method": []
                    }
                }
            }),
            features=json.dumps(['standard_terms', 'customizable']),
            property_types=json.dumps(['apartment', 'house', 'townhouse'])
        )
        
        bc_template = ContractTemplate(
            type='residential_lease',
            province='BC',
            version='2024-01',
            description='Standard residential lease agreement for British Columbia',
            features=json.dumps(['standard_terms', 'customizable']),
            property_types=json.dumps(['apartment', 'house', 'townhouse'])
        )
        
        # 添加特殊条款
        clauses = [
            SpecialClause(
                clause_type='snow_removal',
                category='maintenance',
                title='Snow Removal Agreement',
                content='Regarding winter snow removal responsibilities, both parties agree to the following:\n1. Responsible Party: {responsibility}\n2. Professional Service Delegation: {delegation_allowed}\n3. Tenant Responsibility: {tenant_responsibility}\n4. The landlord shall ensure timely snow removal to maintain safe access.',
                variables=json.dumps(['responsibility', 'delegation_allowed', 'tenant_responsibility'])
            ),
            SpecialClause(
                clause_type='pet_permission',
                category='permissions',
                title='Pet Agreement',
                content='The tenant is permitted to keep pets in the rental property under the following conditions:\n1. Pet Type: {pet_type}\n2. Number Limit: {pet_count}\n3. Size Restriction: {size_limit}\n4. The tenant is responsible for any damage caused by pets.',
                variables=json.dumps(['pet_type', 'pet_count', 'size_limit'])
            ),
            SpecialClause(
                clause_type='parking_space',
                category='facilities',
                title='Parking Space Agreement',
                content='The tenant is granted use of a designated parking space as follows:\n1. Space Number: {space_number}\n2. Location: {location}\n3. Monthly Fee: {monthly_fee}',
                variables=json.dumps(['space_number', 'location', 'monthly_fee'])
            ),
            SpecialClause(
                clause_type='internet_usage',
                category='utilities',
                title='Internet Usage Agreement',
                content='Regarding internet usage in the rental property, both parties agree to the following:\n1. Service Provider: {provider}\n2. Bandwidth: {bandwidth}\n3. Cost Responsibility: {cost_responsibility} is responsible for internet costs\n4. The tenant must comply with Canadian laws and regulations regarding internet usage.',
                variables=json.dumps(['provider', 'bandwidth', 'cost_responsibility'])
            ),
            SpecialClause(
                clause_type='appliances',
                category='facilities',
                title='Appliances Usage Agreement',
                content='Regarding the use of appliances in the rental property, both parties agree to the following:\n1. Included Appliances: {included_appliances}\n2. Maintenance Responsibility: {maintenance_responsibility}\n3. Usage Restrictions: {usage_restrictions}',
                variables=json.dumps(['included_appliances', 'maintenance_responsibility', 'usage_restrictions'])
            ),

            SpecialClause(
                clause_type='renovation',
                category='permissions',
                title='Renovation and Modification Agreement',
                content="""
                Regarding modifications to the rental property:
                1. Permitted Modifications: {permitted_modifications}
                2. Professional Requirements: {professional_requirements}
                3. Prior Notice: Tenant must provide {notice_period} days written notice
                4. Documentation Required: {documentation_requirements}
                5. Restoration Requirements: {restoration_requirements}
                6. Security Deposit: Additional deposit of {modification_deposit} may be required
                """,
                variables=json.dumps([
                    'permitted_modifications',
                    'professional_requirements',
                    'notice_period',
                    'documentation_requirements', 
                    'restoration_requirements',
                    'modification_deposit'
                ])
            ),
            
            SpecialClause(
                clause_type='guest_policy',
                category='permissions',
                title='Guest Policy Agreement', 
                content="""
                Regarding guests in the rental property:
                1. Maximum Stay Duration: {max_stay_duration} consecutive days
                2. Maximum Frequency: {max_frequency} visits per month
                3. Guest Registration: Required for stays over {registration_threshold} days
                4. Overnight Guest Limits: Maximum {overnight_limit} guests per night
                5. Common Area Usage: {common_area_rules}
                6. Tenant Responsibility: Tenant is liable for all guest conduct
                """,
                variables=json.dumps([
                    'max_stay_duration',
                    'max_frequency', 
                    'registration_threshold',
                    'overnight_limit',
                    'common_area_rules'
                ])
            ),

            SpecialClause(
                clause_type='pest_control',
                category='maintenance',
                title='Pest Control Agreement',
                content="""
                Regarding pest control in the rental property:
                1. Routine Inspections: {inspection_frequency}
                2. Reporting Requirements: {reporting_procedure}
                3. Access Requirements: {access_requirements}
                4. Treatment Protocol: {treatment_protocol}
                5. Cost Responsibility: {cost_responsibility}
                6. Preventive Measures: {preventive_measures}
                """,
                variables=json.dumps([
                    'inspection_frequency',
                    'reporting_procedure',
                    'access_requirements',
                    'treatment_protocol',
                    'cost_responsibility',
                    'preventive_measures'
                ])
            ),

            SpecialClause(
                clause_type='security_access',
                category='security',
                title='Security and Access Agreement',
                content="""
                Regarding property security and access:
                1. Keys/Fobs Provided: {access_devices}
                2. Replacement Cost: {replacement_cost} per item
                3. Security System: {security_system_details}
                4. Access Restrictions: {access_restrictions}
                5. Emergency Contact Protocol: {emergency_protocol}
                6. Lock Changes: {lock_change_policy}
                """,
                variables=json.dumps([
                    'access_devices',
                    'replacement_cost',
                    'security_system_details',
                    'access_restrictions',
                    'emergency_protocol',
                    'lock_change_policy'
                ])
            )
        ]
        
        # 添加到会话
        session.add_all([ontario_template, bc_template])
        session.add_all(clauses)
        
        # 提交会话
        session.commit()
        print("基础合同模板已添加")
        print("基础特殊条款已添加")
        
        print("\n数据库初始化完成!")
        
    except Exception as e:
        session.rollback()
        print(f"初始化数据库时出错: {str(e)}")
        raise
        
    finally:
        session.close()

if __name__ == "__main__":
    init_database()
