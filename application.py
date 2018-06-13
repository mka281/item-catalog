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


# ------------ #
# -- Routes -- #
# ------------ #
# Show all categories - Home page
@app.route('/')
@app.route('/categories')
def showCategories():
    return "All categories"


# Add a category
@app.route('/categories/new', methods=['GET', 'POST'])
def addCategory():
    return "New category"


# Edit an existing category
@app.route('/categories/<category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name):
    return "Edit %s category" % category_name


# Delete a category
@app.route('/categories/<category_name>/delete', methods=['GET', 'POST'])
def deleteCategory(category_name):
    return "Delete %s category" % category_name


# Show all items of a category
@app.route('/categories/<category_name>')
@app.route('/categories/<category_name>/items')
def showItemList(category_name):
    return "Show items of %s category" % category_name


# Add item to category
@app.route('/categories/<category_name>/items/new', methods=['GET', 'POST'])
def addItem(category_name):
    return "New item for %s category" % item_name


# Show item details
@app.route('/categories/<category_name>/items/<item_name>')
def showItem(category_name, item_name):
    return "Show %s" % item_name


# Edit an existing item
@app.route('/categories/<category_name>/items/<item_name>/edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    return "Edit %s" % item_name


# Delete an item
@app.route('/categories/<category_name>/items/<item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    return "Delete %s" % item_name


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
