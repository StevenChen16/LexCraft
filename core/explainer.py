class ContractExplainer:
    """Generate explanations for contract terms and modifications"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def explain_changes(self, original: str, modified: str) -> str:
        """Explain changes made to the contract"""
        prompt = PromptTemplate(
            template="""Compare the original and modified contracts and explain:
            1. What changes were made
            2. Why each change was made
            3. Any potential implications
            
            Original Contract:
            {original}
            
            Modified Contract:
            {modified}
            
            Provide a clear, non-technical explanation suitable for the client.
            """,
            input_variables=["original", "modified"]
        )
        
        return self.llm(prompt.format(original=original, modified=modified))
        
    def explain_clause(self, clause: str) -> str:
        """Provide simple explanation of a specific clause"""
        prompt = PromptTemplate(
            template="""Explain this contract clause in simple terms:
            
            Clause:
            {clause}
            
            Explain:
            1. What it means
            2. Why it's important
            3. Any obligations or rights it creates
            """,
            input_variables=["clause"]
        )
        
        return self.llm(prompt.format(clause=clause))
