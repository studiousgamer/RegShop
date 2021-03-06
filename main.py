from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint, Google
from dotenv import load_dotenv

from databases import Database

import os

if os.path.exists('.env'):
    load_dotenv('.env')

app = Flask(__name__)
app.config.from_mapping(dict(os.environ))

oauth = OAuth(app)

backends = [Google]
database = Database(os.getenv('MONGO_URL'))

@app.route('/')
def index():
    if 'user' not in session:
        return render_template('index.html')
    shops = database.getUserShops(session['user']['_id'])
    return render_template('user.html', user=session['user'], shops=shops)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/new', methods=['GET', 'POST'])
def new():
    if 'user' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        if name.strip() == '' or name==None:
            return render_template('new.html')
        database.addShop(name, description, session['user'])
        return redirect(url_for('index'))
    return render_template('new.html')

@app.route('/shop/<id>')
def shop(id):
    if 'user' not in session:
        return redirect(url_for('index'))
    shop = database.getShop(id)
    if shop is None:
        return redirect(url_for('index'))
    elif shop['owner'] != session['user']['_id']:
        return redirect(url_for('index'))
    return render_template('shop.html', shop=shop, receipts=shop['receipts'][:4])

@app.route('/shop/<id>/items', methods=['GET', 'POST'])
def shop_items(id):
    if 'user' not in session:
        return redirect(url_for('index'))
    shop = database.getShop(id)
    if shop is None:
        return redirect(url_for('index'))
    elif shop['owner'] != session['user']['_id']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        if name.strip() == '' or name==None or price.strip() == '' or price==None:
            return render_template('shop_items.html', shop=shop)
        try:
            price = float(price)
        except ValueError:
            return render_template('shop_items.html', shop=shop)
        database.addItem(shop, name, price)
        return redirect(url_for('shop_items', id=id))
    if 'json' in request.args:
        return jsonify(shop['items'])
    return render_template('shop_items.html', shop=shop)

@app.route('/shop/<id>/items/delete')
def shop_item_delete(id):
    if 'item_id' not in request.args:
        print('no item id')
        return redirect(url_for('shop_items', id=id))
    item_id = request.args.get('item_id')
    shop = database.getShop(id)
    database.deleteItem(shop, item_id)
    return redirect(url_for('shop_items', id=id))

@app.route('/shop/<id>/receipt/new', methods=['GET', 'POST'])
def shop_receipt_new(id):
    if 'user' not in session:
        return redirect(url_for('index'))
    shop = database.getShop(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        database.createReceipt(shop, data)
        return redirect(url_for('shop_receipt_new', id=id))
    if shop is None:
        return redirect(url_for('index'))
    elif shop['owner'] != session['user']['_id']:
        return redirect(url_for('index'))
    return render_template('new_receipt.html', shop=shop)

@app.route('/shop/<id>/receipts')
def shop_receipts(id):
    if 'user' not in session:
        return redirect(url_for('index'))
    shop = database.getShop(id)
    if shop is None:
        return redirect(url_for('index'))
    elif shop['owner'] != session['user']['_id']:
        return redirect(url_for('index'))
    return render_template('receipts.html', shop=shop, receipts=shop['receipts'])

def handle_authorize(remote, token, user_info):
    if not database.userExists(user_info['email']):
        database.addUser(user_info)
    session['user'] = database.getUser(user_info['email'])
    return redirect(url_for('index'))

bp = create_flask_blueprint(backends, oauth, handle_authorize)
app.register_blueprint(bp, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True)