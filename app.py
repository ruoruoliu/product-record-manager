from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect, func
from datetime import datetime, timedelta
import os

app = Flask(__name__)
# database stored in factory.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///factory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev_secret_key_change_this_production_random_string'
db = SQLAlchemy(app)

# define product detail table
class Style(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    unit_weight = db.Column(db.Float, nullable=False)

class ProcessingUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# define hengji record table
class HengjiRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    style_name = db.Column(db.String(50))
    processing_unit = db.Column(db.String(50))
    pieces = db.Column(db.Integer)
    total_weight = db.Column(db.Float) # compute by unit_weight * pieces 

# define taokou record table
class TaokouRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    style_name = db.Column(db.String(50))
    processing_unit = db.Column(db.String(50))
    pieces = db.Column(db.Integer)

# init database and migrations
with app.app_context():
    db.create_all()
    
    # Init default styles if empty
    if not Style.query.first():
        db.session.add_all([
            Style(name="0528", unit_weight=0.365),
            Style(name="0529", unit_weight=0.730),
            Style(name="0530", unit_weight=0.630),
        ])
        db.session.commit()
    
    # Init default processing units if empty
    if not ProcessingUnit.query.first():
        db.session.add_all([
            ProcessingUnit(name="张三"),
            ProcessingUnit(name="李四"),
            ProcessingUnit(name="王五"),
        ])
        db.session.commit()
    
    # Simple migration for adding processing_unit column if it doesn't exist
    try:
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('hengji_record')]
        if 'processing_unit' not in columns:
            print("Migrating: Adding processing_unit column to hengji_record table")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE hengji_record ADD COLUMN processing_unit VARCHAR(50)"))
                conn.commit()
    except Exception as e:
        print(f"Migration warning: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Store filters in session and Redirect to GET
        session['date_range'] = request.form.get('date_range', '')
        session['unit_filter'] = request.form.getlist('unit_filter')
        session['style_filter'] = request.form.getlist('style_filter')
        
        action = request.form.get('action')
        if action == 'toggle_aggregate':
             session['show_aggregate'] = not (request.form.get('current_show_aggregate') == 'True')
        else:
             session['show_aggregate'] = request.form.get('current_show_aggregate') == 'True'

        return redirect(url_for('index'))
    
    # GET request: Consume session filters (Flash pattern)
    # Pop them so they don't persist on next refresh
    date_range = session.pop('date_range', '')
    unit_filters = session.pop('unit_filter', [])
    style_filters = session.pop('style_filter', [])
    show_aggregate = session.pop('show_aggregate', False)
    
    # Also support getting from args (legacy support for simple links if any, though session is preferred now)
    # But usually args will not be used in this "Flash Session" pattern unless we explicitly redirect with them.
    # We will rely on session populated by Add/Edit/Delete actions before they redirect.
        
    query = HengjiRecord.query
    
    # Apply filters (Multi-select support)
    if unit_filters and '' not in unit_filters:
         query = query.filter(HengjiRecord.processing_unit.in_(unit_filters))
        
    if style_filters and '' not in style_filters:
         query = query.filter(HengjiRecord.style_name.in_(style_filters))
    
    # Date Range logic
    if date_range:
        if " to " in date_range:
            start_date, end_date = date_range.split(" to ")
            query = query.filter(HengjiRecord.date >= start_date)
            query = query.filter(HengjiRecord.date <= end_date)
        elif " 至 " in date_range:
            start_date, end_date = date_range.split(" 至 ")
            query = query.filter(HengjiRecord.date >= start_date)
            query = query.filter(HengjiRecord.date <= end_date)
        else:
            # Single date selected
            # Try to handle potential single date format if it contains Chinese characters?
            # Normally flatpickr value is standard Y-m-d unless specified otherwise.
            # But if range logic failed, we assume it's a single date string.
            query = query.filter(HengjiRecord.date == date_range)
    else:
        # Default behavior: show all
        pass
        
    if show_aggregate:
        records = query.with_entities(
            HengjiRecord.date,
            HengjiRecord.processing_unit,
            HengjiRecord.style_name,
            func.sum(HengjiRecord.pieces).label('pieces'),
            func.sum(HengjiRecord.total_weight).label('total_weight')
        ).group_by(
            HengjiRecord.date,
            HengjiRecord.processing_unit,
            HengjiRecord.style_name
        ).order_by(HengjiRecord.date.desc()).all()
    else:
        records = query.order_by(HengjiRecord.id.desc()).all()
    
    # Calculate summary
    total_weight = sum(r.total_weight for r in records)
    total_pieces = sum(r.pieces for r in records)
    
    styles = Style.query.order_by(Style.name).all()
    units = ProcessingUnit.query.order_by(ProcessingUnit.name).all()
    
    return render_template("hengji.html", 
        styles=styles, 
        units=units,
        records=records, 
        total_weight=round(total_weight, 3), 
        total_pieces=total_pieces,
        show_aggregate=show_aggregate,
        current_filters={
            'date_range': date_range,
            'unit': unit_filters,
            'style': style_filters
        }
    )

@app.route('/add', methods=['POST'])
def add():
    # Capture filters to persist them
    session['date_range'] = request.form.get('filter_date_range', '')
    session['style_filter'] = request.form.getlist('filter_style')
    session['unit_filter'] = request.form.getlist('filter_unit')
    session['show_aggregate'] = request.form.get('filter_show_aggregate') == 'True'
    
    style_name = request.form.get('style_name')
    processing_unit = request.form.get('processing_unit')
    try:
        pieces = int(request.form.get('pieces'))
    except ValueError:
        flash('件数必须是整数', 'danger')
        return redirect(url_for('index'))

    style = Style.query.filter_by(name=style_name).first()
    if not style:
        flash('款式不存在', 'danger')
        return redirect(url_for('index'))
        
    total_weight = pieces * style.unit_weight

    new_rec = HengjiRecord(
        date = datetime.now().strftime('%Y-%m-%d'),
        style_name = style_name,
        processing_unit = processing_unit,
        pieces = pieces,
        total_weight = round(total_weight, 4)
    )
    db.session.add(new_rec)
    db.session.commit()
    flash('添加成功', 'success')
    return redirect(url_for('index'))


@app.route('/basic_info')
def basic_info():
    styles = Style.query.order_by(Style.name).all()
    units = ProcessingUnit.query.order_by(ProcessingUnit.name).all()
    return render_template('basic_info.html', styles=styles, units=units)

@app.route('/style/add', methods=['POST'])
def add_style():
    name = request.form.get('name')
    unit_weight = request.form.get('unit_weight')
    
    # Handle optional unit_weight (default to 0.0)
    if not unit_weight:
        weight_val = 0.0
    else:
        try:
            weight_val = float(unit_weight)
        except ValueError:
            weight_val = 0.0

    if Style.query.filter_by(name=name).first():
        flash('该款式已存在', 'danger')
    else:
        new_style = Style(name=name, unit_weight=weight_val)
        db.session.add(new_style)
        db.session.commit()
        flash('款式添加成功', 'success')
        
    # Redirect back to the referrer page
    return redirect(request.referrer or url_for('index'))

@app.route('/style/edit', methods=['POST'])
def edit_style():
    style_id = request.form.get('id')
    name = request.form.get('name')
    unit_weight = request.form.get('unit_weight')
    
    style = Style.query.get(style_id)
    if style:
        style.name = name
        # Only update weight if provided
        if unit_weight is not None:
             try:
                style.unit_weight = float(unit_weight)
             except ValueError:
                pass # keep original if invalid? or set to 0?
        db.session.commit()
        flash('款式修改成功', 'success')
    else:
        flash('款式不存在', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/style/delete/<int:id>', methods=['POST'])
def delete_style(id):
    style = Style.query.get(id)
    if style:
        db.session.delete(style)
        db.session.commit()
        flash('款式删除成功', 'success')
    else:
        flash('款式不存在', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/unit/add', methods=['POST'])
def add_unit():
    name = request.form.get('name')
    if ProcessingUnit.query.filter_by(name=name).first():
        flash('该加工单位已存在', 'danger')
    else:
        new_unit = ProcessingUnit(name=name)
        db.session.add(new_unit)
        db.session.commit()
        flash('加工单位添加成功', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/unit/edit', methods=['POST'])
def edit_unit():
    unit_id = request.form.get('id')
    name = request.form.get('name')
    
    unit = ProcessingUnit.query.get(unit_id)
    if unit:
        unit.name = name
        db.session.commit()
        flash('加工单位修改成功', 'success')
    else:
        flash('加工单位不存在', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/unit/delete/<int:id>', methods=['POST'])
def delete_unit(id):
    unit = ProcessingUnit.query.get(id)
    if unit:
        db.session.delete(unit)
        db.session.commit()
        flash('加工单位删除成功', 'success')
    else:
        flash('加工单位不存在', 'danger')
    return redirect(request.referrer or url_for('index'))
    return redirect(url_for('index'))

@app.route('/record/delete/<int:id>', methods=['POST'])
def delete_record(id):
    # Retrieve filters to persist context
    session['date_range'] = request.form.get('date_range', '')
    session['style_filter'] = request.form.getlist('style_filter')
    session['unit_filter'] = request.form.getlist('unit_filter')
    session['show_aggregate'] = request.form.get('show_aggregate') == 'True'

    record = HengjiRecord.query.get(id)
    if record:
        db.session.delete(record)
        db.session.commit()
        flash('记录删除成功', 'success')
    else:
        flash('记录不存在', 'danger')
    return redirect(url_for('index'))

@app.route('/record/edit', methods=['POST'])
def edit_record():
    # Retrieve filters
    session['date_range'] = request.form.get('filter_date_range', '')
    session['style_filter'] = request.form.getlist('filter_style')
    session['unit_filter'] = request.form.getlist('filter_unit')
    session['show_aggregate'] = request.form.get('filter_show_aggregate') == 'True'

    record_id = request.form.get('id')
    date = request.form.get('date')
    style_name = request.form.get('style_name')
    processing_unit = request.form.get('processing_unit')
    try:
        pieces = int(request.form.get('pieces'))
    except ValueError:
        flash('件数必须是整数', 'danger')
        return redirect(url_for('index'))

    record = HengjiRecord.query.get(record_id)
    if record:
        style = Style.query.filter_by(name=style_name).first()
        if not style:
             flash('款式不存在', 'danger') 
             return redirect(url_for('index'))
        
        record.date = date
        record.style_name = style_name
        record.processing_unit = processing_unit
        record.pieces = pieces
        record.total_weight = round(pieces * style.unit_weight, 4)
        
        db.session.commit()
        flash('记录修改成功', 'success')
    else:
        flash('记录不存在', 'danger')
    return redirect(url_for('index'))

@app.route('/taokou', methods=['GET', 'POST'])
def taokou_index():
    if request.method == 'POST':
        session['taokou_date_range'] = request.form.get('date_range', '')
        session['taokou_unit_filter'] = request.form.getlist('unit_filter')
        session['taokou_style_filter'] = request.form.getlist('style_filter')
        
        action = request.form.get('action')
        if action == 'toggle_aggregate':
             session['taokou_show_aggregate'] = not (request.form.get('current_show_aggregate') == 'True')
        else:
             session['taokou_show_aggregate'] = request.form.get('current_show_aggregate') == 'True'

        return redirect(url_for('taokou_index'))
    
    date_range = session.pop('taokou_date_range', '')
    unit_filters = session.pop('taokou_unit_filter', [])
    style_filters = session.pop('taokou_style_filter', [])
    show_aggregate = session.pop('taokou_show_aggregate', False)
    
    query = TaokouRecord.query
    
    if unit_filters and '' not in unit_filters:
         query = query.filter(TaokouRecord.processing_unit.in_(unit_filters))
        
    if style_filters and '' not in style_filters:
         query = query.filter(TaokouRecord.style_name.in_(style_filters))
    
    if date_range:
        if " to " in date_range:
            start_date, end_date = date_range.split(" to ")
            query = query.filter(TaokouRecord.date >= start_date)
            query = query.filter(TaokouRecord.date <= end_date)
        elif " 至 " in date_range:
            start_date, end_date = date_range.split(" 至 ")
            query = query.filter(TaokouRecord.date >= start_date)
            query = query.filter(TaokouRecord.date <= end_date)
        else:
            query = query.filter(TaokouRecord.date == date_range)
    
    if show_aggregate:
        records = query.with_entities(
            TaokouRecord.date,
            TaokouRecord.processing_unit,
            TaokouRecord.style_name,
            func.sum(TaokouRecord.pieces).label('pieces')
        ).group_by(
            TaokouRecord.date,
            TaokouRecord.processing_unit,
            TaokouRecord.style_name
        ).order_by(TaokouRecord.date.desc()).all()
    else:
        records = query.order_by(TaokouRecord.id.desc()).all()
    
    total_pieces = sum(r.pieces for r in records)
    
    styles = Style.query.order_by(Style.name).all()
    units = ProcessingUnit.query.order_by(ProcessingUnit.name).all()
    
    return render_template("taokou.html", 
        styles=styles, 
        units=units,
        records=records, 
        total_pieces=total_pieces,
        show_aggregate=show_aggregate,
        current_filters={
            'date_range': date_range,
            'unit': unit_filters,
            'style': style_filters
        }
    )

@app.route('/taokou/add', methods=['POST'])
def taokou_add():
    session['taokou_date_range'] = request.form.get('filter_date_range', '')
    session['taokou_style_filter'] = request.form.getlist('filter_style')
    session['taokou_unit_filter'] = request.form.getlist('filter_unit')
    session['taokou_show_aggregate'] = request.form.get('filter_show_aggregate') == 'True'
    
    style_name = request.form.get('style_name')
    processing_unit = request.form.get('processing_unit')
    try:
        pieces = int(request.form.get('pieces'))
    except ValueError:
        flash('件数必须是整数', 'danger')
        return redirect(url_for('taokou_index'))

    style = Style.query.filter_by(name=style_name).first()
    if not style:
        flash('款式不存在', 'danger')
        return redirect(url_for('taokou_index'))

    new_rec = TaokouRecord(
        date = datetime.now().strftime('%Y-%m-%d'),
        style_name = style_name,
        processing_unit = processing_unit,
        pieces = pieces
    )
    db.session.add(new_rec)
    db.session.commit()
    flash('添加成功', 'success')
    return redirect(url_for('taokou_index'))

@app.route('/taokou/delete_record/<int:id>', methods=['POST'])
def taokou_delete_record(id):
    session['taokou_date_range'] = request.form.get('date_range', '')
    session['taokou_style_filter'] = request.form.getlist('style_filter')
    session['taokou_unit_filter'] = request.form.getlist('unit_filter')
    session['taokou_show_aggregate'] = request.form.get('show_aggregate') == 'True'

    record = TaokouRecord.query.get(id)
    if record:
        db.session.delete(record)
        db.session.commit()
        flash('记录删除成功', 'success')
    else:
        flash('记录不存在', 'danger')
    return redirect(url_for('taokou_index'))

@app.route('/taokou/edit_record', methods=['POST'])
def taokou_edit_record():
    session['taokou_date_range'] = request.form.get('filter_date_range', '')
    session['taokou_style_filter'] = request.form.getlist('filter_style')
    session['taokou_unit_filter'] = request.form.getlist('filter_unit')
    session['taokou_show_aggregate'] = request.form.get('filter_show_aggregate') == 'True'

    record_id = request.form.get('id')
    date = request.form.get('date')
    style_name = request.form.get('style_name')
    processing_unit = request.form.get('processing_unit')
    try:
        pieces = int(request.form.get('pieces'))
    except ValueError:
        flash('件数必须是整数', 'danger')
        return redirect(url_for('taokou_index'))

    record = TaokouRecord.query.get(record_id)
    if record:
        record.date = date
        record.style_name = style_name
        record.processing_unit = processing_unit
        record.pieces = pieces
        db.session.commit()
        flash('记录修改成功', 'success')
    else:
        flash('记录不存在', 'danger')
    return redirect(url_for('taokou_index'))

if __name__ == '__main__':
    print("local server running on: http://127.0.0.1:5000")
    app.run(debug=True)
