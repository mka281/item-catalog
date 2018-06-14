from flask import Flask, request, render_template, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategoryItem


app = Flask(__name__)

# Connect to DB
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

# Create DB session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# ------------ #
# -- Routes -- #
# ------------ #
# Show all categories - Home page
@app.route('/')
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)


# Add a category
@app.route('/categories/new', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# Edit an existing category
@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete)


# Show all items of a category
@app.route('/categories/<int:category_id>')
@app.route('/categories/<int:category_id>/items')
def showItemList(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(category_id=category_id).all()
    return render_template('items.html', category=category, items=items)


# Add item to category
@app.route('/categories/<int:category_id>/items/new', methods=['GET', 'POST'])
def addItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = CategoryItem(name=request.form['name'],
                               description=request.form['description'],
                               category_id=category_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', restaurant_id=restaurant_id))
    else:
        return render_template('newItem.html', category=category)


# Show details of a specific item
@app.route('/categories/<int:category_id>/items/<int:item_id>')
def showItem(category_id, item_id):
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('showItem.html', item=item, category=category)


# Edit an existing item
@app.route('/categories/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if (request.form['name'] and request.form['description']):
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('editItem.html',
                               item=editedItem, category_id=category_id)


# Delete an item
@app.route('/categories/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete, category_id=category_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
