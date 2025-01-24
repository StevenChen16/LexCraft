from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import text
from datetime import datetime

Base = declarative_base()

class ContractTemplate(Base):
    """合同模板表"""
    __tablename__ = 'contract_templates'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    version = Column(String(10), nullable=False)
    description = Column(Text)
    sections = Column(JSON)  # 章节定义
    features = Column(JSON)  # 特殊功能
    property_types = Column(JSON)  # 适用的物业类型
    province = Column(String(50))  # 适用的省份
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContractTemplate(id={self.id}, type='{self.type}', version='{self.version}')>"

    # 关联
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")
    structure = relationship("ContractStructure", back_populates="template", uselist=False)

class TemplateField(Base):
    """字段定义表"""
    __tablename__ = 'template_fields'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('contract_templates.id'))
    field_name = Column(String, nullable=False)    # 字段名称
    field_type = Column(String, nullable=False)    # 字段类型
    section = Column(String, nullable=False)       # 所属章节
    is_required = Column(Boolean)                  # 是否必填
    validation_rules = Column(JSON)                # JSON格式的验证规则
    default_value = Column(String)                 # 默认值
    description = Column(Text)                     # 字段描述
    
    # 关联
    template = relationship("ContractTemplate", back_populates="fields")
    options = relationship("FieldOption", back_populates="field", cascade="all, delete-orphan")
    explanations = relationship("LegalExplanation", back_populates="field", cascade="all, delete-orphan")

class FieldOption(Base):
    """选项值表"""
    __tablename__ = 'field_options'
    
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('template_fields.id'))
    option_value = Column(String, nullable=False)  # 选项值
    option_label = Column(String, nullable=False)  # 选项标签
    is_default = Column(Boolean, default=False)    # 是否默认选项
    
    # 关联
    field = relationship("TemplateField", back_populates="options")

class ContractStructure(Base):
    """合同结构表"""
    __tablename__ = 'contract_structures'

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('contract_templates.id'), nullable=False, unique=True)
    sections = Column(JSONB, nullable=False, server_default='[]')
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    # 关联
    template = relationship("ContractTemplate", back_populates="structure")

    def __repr__(self):
        return f"<ContractStructure(id={self.id}, template_id={self.template_id})>"

class SpecialClause(Base):
    """特殊条款表"""
    __tablename__ = 'special_clauses'

    id = Column(Integer, primary_key=True)
    clause_type = Column(String(50), unique=True, nullable=False)  # 添加unique=True
    category = Column(String(50))
    title = Column(String(100))
    content = Column(Text)
    variables = Column(JSON)
    compatibility = Column(JSON)
    requirements = Column(JSON)
    validation = Column(JSON)
    property_types = Column(JSON)
    features = Column(JSON)
    province = Column(String(50))

class ClauseTranslation(Base):
    """条款翻译表"""
    __tablename__ = 'clause_translations'

    id = Column(Integer, primary_key=True)
    clause_id = Column(Integer, ForeignKey('special_clauses.id'))
    language = Column(String(10))  # 语言代码，如 'zh_CN'
    title = Column(String(100))
    content = Column(Text)

class ClauseKeywordMapping(Base):
    """条款关键词映射表"""
    __tablename__ = 'clause_keyword_mappings'
    
    id = Column(Integer, primary_key=True)
    clause_type = Column(String(50), ForeignKey('special_clauses.clause_type'))
    keywords = Column(JSON)  # 存储关键词列表
    variables_template = Column(JSON)  # 存储变量模板
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    clause = relationship("SpecialClause", backref="keyword_mappings")

    def __repr__(self):
        return f"<ClauseKeywordMapping(clause_type='{self.clause_type}')>"

class LegalExplanation(Base):
    """法律解释表"""
    __tablename__ = 'legal_explanations'
    
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('template_fields.id'))
    province = Column(String, nullable=False)      # 适用省份
    explanation = Column(Text, nullable=False)     # 解释内容
    legal_reference = Column(Text)                 # 法律依据
    
    # 关联
    field = relationship("TemplateField", back_populates="explanations")

# 数据库连接和会话管理
def get_db_session():
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import DB_CONFIG
    
    db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session(), engine
