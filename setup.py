from database.orm import Base, get_db_session
import sys
import os

def setup_database():
    """初始化数据库结构"""
    # 创建所有表
    engine = get_db_session()[1]
    Base.metadata.create_all(engine)
    print("数据库表已创建")

if __name__ == "__main__":
    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    setup_database()
