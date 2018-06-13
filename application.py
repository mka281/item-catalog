from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategoryItem


app = Flask(__name__)

# Connect to DB
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

# Create DB session
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
def HelloWorld():
    return "Hello World"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
