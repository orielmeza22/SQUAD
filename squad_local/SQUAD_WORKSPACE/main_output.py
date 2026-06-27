from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ServerModel(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(250))

    def __repr__(self):
        return f"Server(id={self.id}, name='{self.name}', description='{self.description}')"

# Create the database engine and metadata
engine = create_engine("sqlite:///servers.db")
Base.metadata.create_all(engine)