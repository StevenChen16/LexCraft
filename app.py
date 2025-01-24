import gradio as gr
import json
from datetime import datetime
from core.assistance import ContractAssistant
from core.ContractGenerator import ContractGenerator
from typing import Dict, List
import os

# 初始化全局变量
generator = ContractGenerator()
assistant = ContractAssistant()
current_contract = None

def convert_contract_to_markdown(contract: Dict) -> str:
    """Convert contract to Markdown format"""
    md_content = []
    
    # Title
    md_content.append("# Lease Agreement")
    md_content.append(f"*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Basic Information
    md_content.append("## Contract Information")
    md_content.append(f"- Version: {contract.get('version', 'N/A')}")
    md_content.append(f"- Type: {contract.get('type', 'N/A')}\n")
    
    # Sections
    for section, content in contract.get('sections', {}).items():
        if content:
            md_content.append(f"## {section.title()}")
            if isinstance(content, dict):
                for key, value in content.items():
                    md_content.append(f"- **{key}**: {value}")
            else:
                md_content.append(str(content))
            md_content.append("")
    
    # Special Clauses
    special_clauses = contract.get('special_clauses', [])
    if special_clauses:
        md_content.append("## Special Clauses")
        for clause in special_clauses:
            md_content.append(f"### {clause.get('title', 'Untitled Clause')}")
            md_content.append(clause.get('content', 'Clause content not specified'))
            md_content.append("")
    
    return "\n".join(md_content)

def export_contract(contract: Dict) -> str:
    """Export contract to file and return the filename"""
    if not os.path.exists("exports"):
        os.makedirs("exports")
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"exports/contract_{timestamp}.md"
    
    # Convert and save as Markdown
    md_content = convert_contract_to_markdown(contract)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return filename

def generate_contract(requirements: str) -> tuple[str, str]:
    """Generate contract based on user requirements"""
    global current_contract
    
    # Get AI analysis results
    analysis = assistant.interact_with_ai(requirements, interaction_type="initial")
    
    # Generate initial contract
    current_contract = generator.generate_contract(
        analysis['template_type'],
        analysis['basic_info'],
        [clause['clause_type'] for clause in analysis.get('suggested_clauses', [])]
    )
    
    # Convert contract to markdown for display
    contract_md = convert_contract_to_markdown(current_contract)
    
    return json.dumps(analysis, indent=2), contract_md

def modify_contract(modifications: str) -> tuple[str, str]:
    """Modify existing contract based on user input"""
    global current_contract
    
    if not current_contract:
        return "No contract to modify", "Please generate a contract first"
    
    # Get AI analysis results
    analysis = assistant.interact_with_ai(modifications)
    
    # Apply modifications
    current_contract = generator.modify_contract(
        current_contract,
        analysis.get('modifications', [])
    )
    
    # Convert updated contract to markdown
    contract_md = convert_contract_to_markdown(current_contract)
    
    return json.dumps(analysis, indent=2), contract_md

def export_current_contract() -> str:
    """Export current contract and return the file path"""
    if not current_contract:
        return "No contract to export"
    
    filename = export_contract(current_contract)
    return f"Contract exported to: {filename}"

def reset_contract() -> tuple[str, str]:
    """Reset the current contract"""
    global current_contract
    current_contract = None
    return "", "Contract cleared. Ready to generate new contract."

# 创建 Gradio 界面
with gr.Blocks(title="LexCraft Smart Contract System") as demo:
    gr.Markdown("# LexCraft Smart Contract System")
    
    with gr.Row():
        # 左侧控制面板
        with gr.Column(scale=2):
            with gr.Tab("Generate Contract"):
                requirements_input = gr.Textbox(
                    label="Describe your requirements",
                    placeholder="Example: I want to rent an apartment in Vancouver for 2000 CAD per month, and I need to be allowed to have a cat...",
                    lines=10
                )
                generate_btn = gr.Button("Generate Contract")
            
            with gr.Tab("Modify Contract"):
                modifications_input = gr.Textbox(
                    label="Describe your modifications",
                    lines=10
                )
                modify_btn = gr.Button("Apply Changes")
                export_btn = gr.Button("Export Contract")
                reset_btn = gr.Button("Create New Contract")
            
            analysis_output = gr.JSON(label="AI Analysis Results")
        
        # 右侧合同显示
        contract_display = gr.Markdown(label="Contract Content")
    
    # 事件处理
    generate_btn.click(
        generate_contract,
        inputs=[requirements_input],
        outputs=[analysis_output, contract_display]
    )
    
    modify_btn.click(
        modify_contract,
        inputs=[modifications_input],
        outputs=[analysis_output, contract_display]
    )
    
    export_btn.click(
        export_current_contract,
        inputs=[],
        outputs=[analysis_output]
    )
    
    reset_btn.click(
        reset_contract,
        inputs=[],
        outputs=[analysis_output, contract_display]
    )

if __name__ == "__main__":
    demo.launch()
