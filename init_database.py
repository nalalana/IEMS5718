from database import Base, engine
import database  # 确保包含了 User 类定义

# 创建所有模型对应的表
Base.metadata.create_all(bind=engine)
