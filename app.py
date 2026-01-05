from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# database stored in factory.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///factory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# define product detail table
class Style(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    unit_weight = db.Column(db.Float)

# define hengji record table
class HengjiRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    style_name = db.Column(db.String(50))
    pieces = db.Column(db.Integer)
    total_weight = db.Column(db.Float) # compute by unit_weight * pieces 

# init database and add sample rows
with app.app_context():
    db.create_all()
    if not Style.query.first():
        db.session.add_all([
            Style(name="0528", unit_weight=0.365),
            Style(name="0529", unit_weight=0.730),
            Style(name="0530", unit_weight=0.630),
        ])
        db.session.commit()

@app.route('/')
def index():
    styles = Style.query.all()
    records = HengjiRecord.query.order_by(HengjiRecord.id.desc()).all()
    return render_template("index.html", styles=styles, records=records)

@app.route('/add', methods=['POST'])
def add():
    style_name = request.form.get('style_name')
    pieces = float(request.form.get('pieces'))

    # use unit_weight from database and compute total_weight
    style = Style.query.filter_by(name=style_name).first()
    total_weight = pieces * style.unit_weight

    new_rec = HengjiRecord(
        date = datetime.now().strftime('%Y-%m-%d'),
        style_name = style_name,
        pieces = int(pieces),
        total_weight = total_weight
    )
    db.session.add(new_rec)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    print("local server running on: http://127.0.0.1:5000")
    app.run(debug=True)
