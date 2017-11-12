from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#from database_setup import Restaurant, Base, MenuItem
from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalogitemwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

#Create all Catagories
# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

category1 = Category(user_id = 1, name = "Soccer")
category2 = Category(user_id = 1, name = "Basketball")
category3 = Category(user_id = 1, name = "Baseball")
category4 = Category(user_id = 1, name = "Frisbee")
category5 = Category(user_id = 1, name = "Snowboarding")
category6 = Category(user_id = 1, name = "Rock Climbing")
category7 = Category(user_id = 1, name = "Boosball")
category8 = Category(user_id = 1, name = "Skating")
category9 = Category(user_id = 1, name = "Hockey")

session.add(category1)
session.add(category2)
session.add(category3)
session.add(category4)
session.add(category5)
session.add(category6)
session.add(category7)
session.add(category8)
session.add(category9)
session.commit()


item1 = Item(user_id = 1, title="Stick", description="Hockey Stick", category = category1)
session.add(item1)
session.commit()

item2 = Item(user_id = 1, title="Googles", description="Google", category = category5)
session.add(item2)
session.commit()

item3 = Item(user_id = 1, title="Snowboard", description="Snowbaord", category = category5)
session.add(item3)
session.commit()

item4 = Item(user_id = 1, title="Two shinguards", description="Two shinguards", category = category1)
session.add(item4)
session.commit()

item5 = Item(user_id = 1, title="Shinguards", description="Shinguards", category = category1)
session.add(item5)
session.commit()

item6 = Item(user_id = 1, title="Frisbee", description="Frisbee", category = category4)
session.add(item6)
session.commit()

item7 = Item(user_id = 1, title="Bat", description="Bat", category = category3)
session.add(item7)
session.commit()

item8 = Item(user_id = 1, title="Jersy", description="Jersy", category = category1)
session.add(item8)
session.commit()

item9 = Item(user_id = 1, title="Soccer Cleats", description="Soccer Cleats", category = category1)
session.add(item9)
session.commit()

print ("added items!")