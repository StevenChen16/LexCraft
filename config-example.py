# config-example.py
# This is a configuration template file. Replace the placeholders with your actual values.

# Database configuration
DB_CONFIG = {
    'host': 'localhost',  # Database host address
    'database': 'your_database_name',  # Database name
    'user': 'your_username',  # Database username
    'password': 'your_password',  # Database password
    'port': 5432  # Database port number
}

# Initial database configuration (used for creating or initializing the database)
INITIAL_DB_CONFIG = {
    'host': 'localhost',  # Database host address
    'database': 'postgres',  # Connect to the default 'postgres' database
    'user': 'your_username',  # Database username
    'password': 'your_password',  # Database password
    'port': 5432  # Database port number
}

# DeepSeek API configuration
DEEPSEEK_CONFIG = {
    'api_key': 'your_api_key_here',  # Replace with your DeepSeek API key
    'base_url': 'https://api.deepseek.com',  # DeepSeek API base URL
    'model': 'deepseek-chat'  # Model name to use
}

# Prompt templates
PROMPT_TEMPLATES = {
    "understand_requirements": """
    Extract rental requirements from the following conversation.
    Focus on key information like location, property type, special requirements, etc.
    
    User input: {input}
    
    Output the information in the following format:
    {format_instructions}
    """
}