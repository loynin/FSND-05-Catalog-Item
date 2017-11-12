import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


# class Restaurant(Base):
#     __tablename__ = 'restaurant'
# 
#     id = Column(Integer, primary_key=True)
#     name = Column(String(250), nullable=False)
# 
# 
# class MenuItem(Base):
#     __tablename__ = 'menu_item'
# 
#     name = Column(String(80), nullable=False)
#     id = Column(Integer, primary_key=True)
#     description = Column(String(250))
#     price = Column(String(8))
#     course = Column(String(250))
#     restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
#     restaurant = relationship(Restaurant) 

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key = True)
    name = Column(String(250),nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))
    admin = Column(Boolean, unique= False, default = False)
    
class Category(Base):
    __tablename__ = 'category'
    
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    
    @property
    def serialize(self):
        return{
            'name' : self.name,
            'id' : self.id,
            }

class Item(Base):
    __tablename__ = 'item'
    
    cat_id = Column(Integer, ForeignKey('category.id'))
    description = Column(String(250), nullable = True)
    id = Column(Integer, primary_key = True)
    title = Column(String(80),nullable = False)
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    
    @property
    def serialize(self):
        return{
            'title' : self.title,
            'description' : self.description,
            'id' : self.id,
            'cat_id': self.cat_id,
            }


         
# class Object:
#     def toJSON(self)
#         return json.dumps(self,default=lambda o: o.__dic__,
#             sort_keys=True, indent=4)
    

engine = create_engine('sqlite:///catalogitemwithusers.db')

#User.__table__.drop(engine)

Base.metadata.create_all(engine)
