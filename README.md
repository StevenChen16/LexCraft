# LexCraft: Intelligent Contract Generation System

LexCraft is an AI-powered contract generation system that helps create, customize, and manage residential lease agreements. It provides an intelligent interface for generating legally compliant contracts while allowing for flexible modifications through AI interaction.

## Features

- **Smart Contract Generation**: Automatically generates residential lease agreements based on user requirements
- **Province-Specific Templates**: Supports multiple Canadian provinces (ON, BC, AB, QC) with province-specific legal requirements
- **Dynamic Special Clauses**: Includes customizable clauses for:
  - Pet agreements
  - Parking space allocation
  - Internet usage terms
  - Appliance usage
  - Snow removal responsibilities
  - Renovation permissions
  - Guest policies
  - Pest control
  - Security and access management
- **AI-Assisted Modifications**: Natural language interface for contract modifications
- **Template Management**: Database-driven template system for easy updates and maintenance
- **Modern Web Interface**: Streamlit-based UI with:
  - Split-panel layout for easy interaction
  - Real-time contract preview
  - Markdown export functionality
  - Interactive contract modification
  - Progress indicators and notifications

## Project Structure

```
LexCraft/
├── core/
│   ├── ContractGenerator.py   # Main contract generation logic
│   ├── assistance.py          # AI assistance integration
│   └── contract.py           # Contract data structures
├── database/
│   ├── init_db.py            # Database initialization
│   ├── contract_diagnostics.py # Diagnostic tools
│   ├── orm.py                # Database models
│   └── seed.py               # Sample data seeding
├── app.py                    # Streamlit web interface
├── main.py                   # CLI application entry point
└── exports/                  # Generated contract exports
```

## Setup

1. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Initialization**
   ```bash
   cd database
   python init_db.py
   ```

3. **Environment Variables**
   Create a `.env` file with:
   ```
   DATABASE_URL=your_database_url
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

### Web Interface (Recommended)

1. **Starting the Web Application**
   ```bash
   streamlit run app.py
   ```

2. **Using the Web Interface**
   - Left Panel:
     - Input your contract requirements
     - View AI analysis results
     - Modify existing contracts
     - Export contracts to Markdown
   - Right Panel:
     - Real-time contract preview
     - Expandable sections for easy reading
     - Special clauses review

3. **Contract Generation Process**
   - Enter your requirements in natural language
   - Review AI-generated contract in the right panel
   - Make modifications as needed
   - Export the final contract

### Command Line Interface

1. **Starting the CLI Application**
   ```bash
   python main.py
   ```

2. **Creating a New Contract**
   - Provide basic information (parties, property details, term)
   - Select desired special clauses
   - Review and modify generated contract

3. **Modifying Existing Contracts**
   - Use natural language to describe desired changes
   - AI will interpret and apply modifications appropriately

## Database Schema

### Core Tables
- `contract_templates`: Base contract templates by province
- `special_clauses`: Customizable contract clauses
- `template_fields`: Field definitions for templates
- `contract_structures`: Template section organization

## Development

### Adding New Features
1. Define new special clauses in `database/init_db.py`
2. Update ORM models in `database/orm.py` if needed
3. Add corresponding handling in `core/ContractGenerator.py`
4. Update UI components in `app.py` if needed

### Testing
Run tests with:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with SQLAlchemy for database management
- Powered by OpenAI's GPT for AI assistance
- Designed for the Canadian real estate market
