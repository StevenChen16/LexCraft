import streamlit as st
import json
from datetime import datetime
from core.assistance import ContractAssistant
from core.ContractGenerator import ContractGenerator
from typing import Dict, List
import os

# 初始化 Session State
if 'contract' not in st.session_state:
    st.session_state.contract = None
if 'generator' not in st.session_state:
    st.session_state.generator = ContractGenerator()
if 'assistant' not in st.session_state:
    st.session_state.assistant = ContractAssistant()
if 'modification_input' not in st.session_state:
    st.session_state.modification_input = ""

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

def export_contract(contract: Dict):
    """Export contract to file"""
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

def display_contract(contract: Dict):
    """Display contract in Streamlit"""
    st.subheader("Contract Content")
    
    # Display contract basic information
    with st.expander("Contract Information", expanded=True):
        st.write(f"Version: {contract.get('version', 'N/A')}")
        st.write(f"Type: {contract.get('type', 'N/A')}")
    
    # Display sections
    for section, content in contract.get('sections', {}).items():
        if content:  # Only display non-empty sections
            with st.expander(f"{section.title()}", expanded=True):
                if isinstance(content, dict):
                    for key, value in content.items():
                        st.write(f"**{key}**: {value}")
                else:
                    st.write(content)
    
    # Display special clauses
    special_clauses = contract.get('special_clauses', [])
    if special_clauses:
        with st.expander("Special Clauses", expanded=True):
            for clause in special_clauses:
                st.markdown(f"**{clause.get('title', 'Untitled Clause')}**")
                st.write(clause.get('content', 'Clause content not specified'))
                st.write("---")

def main():
    """Main function for user interaction"""
    st.title("LexCraft Smart Contract System")
    
    # Create two-column layout with adjusted ratio
    left_col, right_col = st.columns([2, 3])  
    
    with left_col:
        if not st.session_state.contract:
            st.write("Welcome to LexCraft Smart Contract System!")
            st.write("Please describe your requirements, and we'll generate a suitable contract for you.")
            st.write("Example: I want to rent an apartment in Vancouver for 2000 CAD per month, and I need to be allowed to have a cat...")
            
            # First round: Understanding initial requirements
            initial_input = st.text_area("Describe your requirements:", height=200)
            
            if st.button("Generate Contract"):
                with st.spinner("Analyzing your requirements..."):
                    # Get AI analysis results
                    requirements = st.session_state.assistant.interact_with_ai(initial_input, interaction_type="initial")
                    
                    # Display AI analysis results
                    with st.expander("AI Analysis Results", expanded=False):
                        st.json(requirements)
                    
                    # Generate initial contract
                    st.session_state.contract = st.session_state.generator.generate_contract(
                        requirements['template_type'],
                        requirements['basic_info'],
                        [clause['clause_type'] for clause in requirements.get('suggested_clauses', [])]
                    )
                    
                    st.success("Contract generated successfully!")
                    st.rerun()
        
        else:
            # Modification section
            st.subheader("Contract Modification")
            
            # Modification input box
            modification_input = st.text_area(
                "Describe your modifications:",
                height=200,
                key="modification_area",
                value=st.session_state.modification_input
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Apply Changes"):
                    with st.spinner("Processing modification request..."):
                        # Get AI analysis results
                        modifications = st.session_state.assistant.interact_with_ai(modification_input)
                        
                        # Display AI analysis results
                        with st.expander("AI Analysis Results", expanded=False):
                            st.json(modifications)
                        
                        # Apply modifications
                        st.session_state.contract = st.session_state.generator.modify_contract(
                            st.session_state.contract,
                            modifications.get('modifications', [])
                        )
                        
                        # Clear modification input
                        st.session_state.modification_input = ""
                        
                        st.success("Changes applied successfully!")
                        st.rerun()
            
            with col2:
                if st.button("Export Contract"):
                    filename = export_contract(st.session_state.contract)
                    st.success(f"Contract exported to: {filename}")
                    
                    # Provide download link
                    with open(filename, 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="Download Contract",
                            data=f.read(),
                            file_name=os.path.basename(filename),
                            mime="text/markdown"
                        )
            
            if st.button("Create New Contract"):
                st.session_state.contract = None
                st.rerun()
    
    # Right side contract display
    with right_col:
        if st.session_state.contract:
            display_contract(st.session_state.contract)

if __name__ == "__main__":
    main()
