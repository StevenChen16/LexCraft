# in main.py

from core.assistance import ContractAssistant
from core.ContractGenerator import ContractGenerator
from typing import Dict, List
import json

def display_contract(contract: Dict):
    """显示合同内容"""
    print("\n当前合同内容:")
    print("-" * 50 + "\n")
    
    # 显示合同基本信息
    print("【合同信息】")
    print(f"版本: {contract.get('version', 'N/A')}")
    print(f"类型: {contract.get('type', 'N/A')}\n")
    
    # 显示各个部分
    for section, content in contract.get('sections', {}).items():
        if content:  # 只显示非空部分
            print(f"【{section}】")
            if isinstance(content, dict):
                for key, value in content.items():
                    print(f"{key}: {value}")
            else:
                print(content)
            print()
    
    # 显示特殊条款
    special_clauses = contract.get('special_clauses', [])
    if special_clauses:
        print("【特殊条款】")
        for clause in special_clauses:
            print(f"\n{clause.get('title', '未命名条款')}:")
            print(f"{clause.get('content', '条款内容未指定')}")

def main():
    """主函数，处理用户交互"""
    assistant = ContractAssistant()
    generator = ContractGenerator()
    
    print("欢迎使用LexCraft智能合同系统！")
    print("请描述您的需求，我们将为您生成合适的合同。")
    print("例如：我想在温哥华租一套公寓，预算2000加币每月，需要允许养猫...")
    
    # 第一轮对话：理解初始需求
    initial_input = input("\n请描述您的需求: ")
    
    # 获取AI分析结果
    requirements = assistant.interact_with_ai(initial_input, interaction_type="initial")
    print("\n我已理解您的需求，正在生成初始合同...")
    print("\nAI的分析结果:")
    print(json.dumps(requirements, ensure_ascii=False, indent=2))
    
    # 生成初始合同
    contract = generator.generate_contract(
        requirements['template_type'],
        requirements['basic_info'],
        [clause['clause_type'] for clause in requirements.get('suggested_clauses', [])]
    )
    
    if contract:
        print("\n合同生成成功！")
        print("\n合同详情:")
        print(json.dumps(contract, ensure_ascii=False, indent=2))
        # 显示当前合同
        display_contract(contract)
        
        # 进入修改循环
        while True:
            print("\n您可以：")
            print("1. 修改合同内容")
            print("2. 完成并退出")
            
            choice = input("\n请选择 (1/2): ")
            
            if choice == '2':
                print("\n感谢使用LexCraft！您的合同已经准备就绪。")
                break
            
            # 获取修改请求
            modification_input = input("\n请描述您想要的修改: ")
            
            # 获取AI分析结果
            modifications = assistant.interact_with_ai(modification_input)
            print("\nAI分析结果:")
            print(json.dumps(modifications, ensure_ascii=False, indent=2))
            
            # 应用修改
            contract = generator.modify_contract(contract, modifications.get('modifications', []))
            
            # 显示更新后的合同
            print("\n已应用您的修改:")
            display_contract(contract)

if __name__ == "__main__":
    main()