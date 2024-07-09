from flask import after_this_request, render_template, request, redirect, send_file, url_for, flash, jsonify
from dotenv import load_dotenv
from app import app, db
from app.models import Person, Property, RentalContract, Payment
from datetime import datetime,timedelta,date
import calendar,subprocess, os,tempfile,shlex
from sqlalchemy import func,case,and_,or_
from sqlalchemy.orm import aliased

load_dotenv()

def format_date(date:str):
    fecha_obj = datetime.strptime(date, '%Y-%m-%d')
    fecha_formateada = fecha_obj.strftime('%d/%m/%Y')

    return fecha_formateada

def string_to_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("El formato de fecha debe ser YYYY-MM-DD")

def update_available_property(id:int,valor:bool):
    update_properties = Property.query.get_or_404(id)
    update_properties.available = valor
    db.session.commit()

def add_months_to_date(current_date, months_to_add:int):
    if not isinstance(months_to_add, int) or months_to_add < 0 or months_to_add > 60:
        raise ValueError("months_to_add debe ser un entero entre 0 y 60")

    year = current_date.year
    month = current_date.month
    day = current_date.day

    total_months = month + months_to_add
    new_year = year + (total_months - 1) // 12
    new_month = ((total_months - 1) % 12) + 1

    _, last_day = calendar.monthrange(new_year, new_month)
    new_day = min(day, last_day)

    return date(new_year, new_month, new_day)

def get_payment_notification():
    current_date = datetime.now().date()
    seven_days_from_now = current_date + timedelta(days=15)

    expired_payments = Payment.query.filter(
        and_(
            Payment.status == 'pending',
            Payment.date < current_date
        )
    ).update({'status': 'expired'}, synchronize_session='fetch')

    if expired_payments > 0:
        db.session.commit()

    payments = db.session.query(
        Payment, 
        RentalContract, 
        Property,
        case(
            (Payment.date < current_date, 'red'),
            else_='green'
        ).label('alert')
    ).join(RentalContract, Payment.contract_id == RentalContract.id)\
     .join(Property, RentalContract.property_id == Property.id)\
     .filter(and_(
         Payment.status.in_(['pending', 'expired']),
         Payment.date <= seven_days_from_now
     ))\
     .order_by(Payment.date.asc())
    return payments

@app.route('/')
def index():
    return redirect(url_for('list_persons', type='propietario', start='True'))

## persons
@app.route('/persons')
@app.route('/persons/<string:type>')
def list_persons(type:str=None,start:str=None):
    start = request.args.get('start', 'False')
    if type:
        persons = Person.query.filter(Person.type_person ==type).order_by(Person.id.asc())
    else:
        persons = Person.query.all()

    if start == 'True':
        payments = get_payment_notification()
        return render_template('notification/notification.html', persons=persons,type=type,payments=payments)
    else:
        return render_template('persons/list.html', persons=persons,type=type)

@app.route('/persons/add', methods=['GET', 'POST'])
@app.route('/persons/add/<string:type>', methods=['GET', 'POST'])
def add_person(type:str=None):
    if request.method == 'POST':
        try:
            new_person = Person(
                dni=request.form['dni'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                phone_number=request.form['phone_number'],
                address=request.form['address'],
                nationality=request.form['nationality'],
                type_person=request.form['type_person']
            )
            db.session.add(new_person)
            db.session.commit()
            flash('Person added successfully', 'success')
            return redirect(url_for('list_persons',type=type))
        except Exception as error:
            flash(f'Error al agregar - msg: {error}', 'danger')
    return render_template('persons/add.html',type=type)

@app.route('/persons/edit/<int:id>', methods=['GET', 'POST'])
def edit_person(id):
    person = Person.query.get_or_404(id)
    if request.method == 'POST':
        person.dni = request.form['dni']
        person.first_name = request.form['first_name']
        person.last_name = request.form['last_name']
        person.phone_number = request.form['phone_number']
        person.address = request.form['address']
        person.nationality = request.form['nationality']
        person.type_person = request.form['type_person']
        person.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Person updated successfully', 'success')
        return redirect(url_for('list_persons',type=person.type_person))
    return render_template('persons/edit.html', person=person)

@app.route('/persons/delete/<int:id>', methods=['POST'])
def delete_person(id):
    try:
        person = Person.query.get_or_404(id)
        db.session.delete(person)
        db.session.commit()
        flash('Persona eliminada satisfactoriamente', 'success')
    except Exception as error:
        flash(f'Error al eliminar la persona - msg: {error}', 'danger')
    
    return redirect(url_for('list_persons'))

## routs of properties
@app.route('/properties')
@app.route('/properties/<int:id>')
def list_properties(id:int=None):
    if id:
        person= Person.query.get_or_404(id)
        properties = Property.query.join(Person, Property.owner_id == Person.id).add_columns(
            Property.id,
            Property.name,
            Property.address,
            Property.property_type,
            Property.area,
            Property.available,
            Person.first_name.label('owner_first_name'),
            Person.last_name.label('owner_last_name'),
            Person.id.label('owner_id')
        ).filter(Person.id==id)
    else:
        properties = Property.query.join(Person, Property.owner_id == Person.id).add_columns(
            Property.id,
            Property.name,
            Property.address,
            Property.property_type,
            Property.area,
            Property.available,
            Person.first_name.label('owner_first_name'),
            Person.last_name.label('owner_last_name')
        ).all()
    return render_template('properties/list.html', properties=properties,person=person)

@app.route('/properties/add', methods=['GET', 'POST'])
@app.route('/properties/add/<int:id>', methods=['GET', 'POST'])
def add_property(id:int=None):
    if id:
        persons = Person.query.get_or_404(id)
    else:
        persons = Person.query.all()
    if request.method == 'POST':
        new_property = Property(
            name=request.form['name'],
            address=request.form['address'],
            property_type=request.form['property_type'],
            area=float(request.form['area']),
            description=request.form['description'],
            available=request.form.get('available') == 'on',
            owner_id=int(request.form['owner_id'])
        )
        db.session.add(new_property)
        db.session.commit()
        flash('Property added successfully', 'success')
        return redirect(url_for('list_properties',id=int(request.form['owner_id'])))
    return render_template('properties/add.html', persons=persons)

@app.route('/properties/edit/<int:id>', methods=['GET', 'POST'])
def edit_property(id):
    property = Property.query.get_or_404(id)
    persons = Person.query.all()
    if request.method == 'POST':
        property.name = request.form['name']
        property.address = request.form['address']
        property.property_type = request.form['property_type']
        property.area = float(request.form['area'])
        property.description = request.form['description']
        property.available = request.form.get('available') == 'on'
        property.owner_id = int(request.form['owner_id'])
        property.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Property updated successfully', 'success')
        return redirect(url_for('list_properties',id=int(request.form['owner_id'])))
    return render_template('properties/edit.html', property=property, persons=persons)

@app.route('/properties/delete/<int:id>', methods=['POST'])
def delete_property(id):
    try:
        property = Property.query.get_or_404(id)
        owner_id = property.owner_id
        db.session.delete(property)
        db.session.commit()
        flash('Propiedad eliminado correctamente', 'success')
    except Exception as error:
        flash(f'Error a eliminar propiedad, msg {error}', 'danger')

    return redirect(url_for('list_properties',id=owner_id))

## routes rental_contract
@app.route('/rental_contracts')
@app.route('/rental_contracts/<int:id>')
def list_rental_contracts(id:int=None):
    current_date = datetime.now().date()
    seven_days_from_now = current_date + timedelta(days=7)
    if id:
        expired_rentalcontract = RentalContract.query.filter(
            and_(
                RentalContract.end_date < current_date
            )
        ).update({'status': 'expired','count':True}, synchronize_session='fetch')

        if expired_rentalcontract > 0:
            db.session.commit()

        update_properties = RentalContract.query.filter(
        and_(
            RentalContract.status == 'expired',
            Payment.date < current_date,
            RentalContract.count == False
        )).all()

        if len(update_properties) > 0:
            for upade in update_properties:
                update_available_property(upade.property_id,True)

        person = Person.query.get_or_404(id)
        Tenant = aliased(Person)
        Owner = aliased(Person)
        rental_contracts = (
            RentalContract.query
            .join(Property, RentalContract.property_id == Property.id)
            .join(Tenant, RentalContract.tenant_id == Tenant.id)
            .join(Owner, Property.owner_id == Owner.id)
            .add_columns(
                RentalContract.id,
                RentalContract.rent_amount,
                RentalContract.deposit_amount,
                RentalContract.status,
                RentalContract.payment_date,
                RentalContract.start_date,
                RentalContract.end_date,
                func.concat(Tenant.first_name, ' ', Tenant.last_name).label('tenant'),
                Property.name.label('property_name'),
                case(
                    (RentalContract.end_date < current_date, 'red'),
                    (RentalContract.end_date < seven_days_from_now,'yellow'),
                    else_='green'
                ).label('alert')
            )
            .filter(Owner.id == id).order_by(RentalContract.status.asc(),RentalContract.start_date.asc())
            # .order_by(RentalContract.start_date.desc())
        )
        return render_template('rental_contracts/list.html', rental_contracts=rental_contracts,person=person)
    else:
        rental_contracts = RentalContract.query.join(Person, RentalContract.tenant_id == Person.id)\
        .join(Property, RentalContract.property_id == Property.id)\
        .add_columns(
            RentalContract.id,
            RentalContract.rent_amount,
            RentalContract.deposit_amount,
            RentalContract.status,
            RentalContract.payment_date,
            RentalContract.start_date,
            RentalContract.end_date,
            Person.first_name.label('tenant_first_name'),
            Person.last_name.label('tenant_last_name'),
            Property.name.label('property_name')
        ).all()
    return render_template('rental_contracts/list.html', rental_contracts=rental_contracts)

@app.route('/rental_contracts/add', methods=['GET', 'POST'])
@app.route('/rental_contracts/add/<int:id>', methods=['GET', 'POST'])
def add_rental_contract(id:int=None):
    person = Person.query.get_or_404(id)
    tenants = Person.query.filter(Person.type_person =='inquilino')
    properties = Property.query.filter_by(available=True,owner_id=id).all()
    
    if request.method == 'POST':
        person_id = int(request.form['person_id'])
        new_contract = RentalContract(
            tenant_id=int(request.form['tenant_id']),
            property_id=int(request.form['property_id']),
            rent_amount=float(request.form['rent_amount']),
            deposit_amount=float(request.form['deposit_amount']),
            status=request.form['status'],
            payment_date=format_date(request.form['payment_date']),
            start_date=format_date(request.form['start_date']),
            end_date= add_months_to_date(string_to_date(request.form['start_date']),int(request.form['end_date'])) if request.form['end_date'] else None
        )
        db.session.add(new_contract)
        db.session.commit()
        
        # Update property availability
        property = Property.query.get(new_contract.property_id)
        property.available = False
        db.session.commit()
        
        flash('Rental contract added successfully', 'success')
        return redirect(url_for('list_rental_contracts',id=person_id))
    
    return render_template('rental_contracts/add.html', tenants=tenants, properties=properties,person=person)

@app.route('/rental_contracts/edit/<int:id>', methods=['GET', 'POST'])
def edit_rental_contract(id):
    contract = RentalContract.query.get_or_404(id)
    tenants = Person.query.all()
    properties = Property.query.all()
    properties_person=Property.query.get_or_404(contract.property_id)
    person=Person.query.get_or_404(properties_person.owner_id)
    
    if request.method == 'POST':
        person_id = int(request.form['person_id'])
        contract.tenant_id = int(request.form['tenant_id'])
        contract.property_id = int(request.form['property_id'])
        contract.rent_amount = float(request.form['rent_amount'])
        contract.deposit_amount = float(request.form['deposit_amount'])
        contract.status = request.form['status']
        contract.payment_date = format_date(request.form['payment_date'])
        contract.start_date = format_date(request.form['start_date'])
        contract.end_date = add_months_to_date(string_to_date(request.form['start_date']),int(request.form['end_date'])) if request.form['end_date'] else None
        contract.updated_at = datetime.utcnow()
        
        flash('Rental contract updated successfully', 'success')

        if contract.status == 'inactive':
            update_properties = Property.query.get_or_404(contract.property_id)
            update_properties.available = True

        db.session.commit()
        return redirect(url_for('list_rental_contracts',id=person_id))
    
    return render_template('rental_contracts/edit.html', contract=contract, tenants=tenants, properties=properties, person=person)

@app.route('/rental_contracts/delete/<int:id>', methods=['POST'])
def delete_rental_contract(id):
    try:
        contract = RentalContract.query.get_or_404(id)
        property = Property.query.get(contract.property_id)
        property.available = True

        payments_to_delete = Payment.query.filter_by(contract_id=id).all()
        for payment in payments_to_delete:
            db.session.delete(payment)
            
        db.session.delete(contract)
        db.session.commit()
        flash('Rental contract deleted successfully', 'success')
    except Exception as error:
        flash(f'Error al eliminar el contrato - msg: {error}', 'danger')
    
    return redirect(url_for('list_rental_contracts',id=property.owner_id))

## routes payments
@app.route('/payments')
def list_payments():
    current_date = datetime.now().date()
    start_of_month = current_date.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    expired_payments = Payment.query.filter(
        and_(
            Payment.status == 'pending',
            Payment.date < current_date
        )
    ).update({'status': 'expired'}, synchronize_session='fetch')

    if expired_payments > 0:
        db.session.commit()

    payments = db.session.query(
        Payment, 
        RentalContract, 
        Property,
        func.concat(Person.first_name, ' ',Person.last_name,).label('tenant'),
        Person.phone_number.label('phone'),
        case(
            (Payment.status == 'expired', 'red'),
            (and_(Payment.status == 'pending', Payment.date < current_date), 'red'),
            else_='green'
        ).label('alert')
    ).join(RentalContract, Payment.contract_id == RentalContract.id)\
    .join(Property, RentalContract.property_id == Property.id)\
    .join(Person, RentalContract.tenant_id == Person.id)\
    .filter(
        or_(
            and_(Payment.date >= start_of_month, Payment.date <= end_of_month, Payment.status.in_(['pending'])),
            Payment.status == 'expired'
        )
    )\
    .order_by(Payment.date.asc())

    return render_template('payments/list.html', payments=payments)

def get_next_payment_date(current_date):
    year = current_date.year
    month = current_date.month
    day = current_date.day
    month += 1
    if month > 12:
        month = 1
        year += 1
    _, last_day = calendar.monthrange(year, month)
    next_day = min(day, last_day)
    return datetime(year, month, next_day)

@app.route('/payments/<int:id>/pay', methods=['POST'])
def pay_rent(id):
    payment = Payment.query.get_or_404(id)
    payment.status = 'paid'
    contract= RentalContract.query.get_or_404(payment.contract_id)
    
    if contract.status == 'active':
        next_payment_date = get_next_payment_date(payment.date)
        next_payment = Payment(
            contract_id=payment.contract_id,
            date=next_payment_date,
            amount=payment.amount,
            status='pending'
        )
        
        db.session.add(next_payment)
        flash('Payment processed successfully and next payment scheduled.', 'success')
    else:
        flash('Payment processed successfully. No new payment scheduled as the contract is not active.', 'info')
    
    db.session.commit()
    
    return redirect(url_for('list_payments'))

@app.route('/download_backup')
def download_backup():
    pg_dump_path = os.getenv("PG_DUMP_PATH")
    db_name = os.getenv("PG_DB_NAME")
    db_user = os.getenv("PG_DB_USER")
    db_password = os.getenv("PG_DB_PASSWORD")
    backup_directory = os.getenv("BACKUP_DIRECTORY")
    
    if not db_password:
        return "Error: La contraseña de la base de datos no está configurada", 500
    
    os.makedirs(backup_directory, exist_ok=True)
    
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    backup_file = os.path.join(backup_directory, backup_filename)
    
    pgpass_path = os.path.join(os.path.dirname(__file__), '.pgpass')
    with open(pgpass_path, 'w') as pgpass_file:
        pgpass_file.write(f"*:*:*:{db_user}:{db_password}")
    os.chmod(pgpass_path, 0o600)
    
    try:
        os.environ['PGPASSFILE'] = pgpass_path

        command = f'"{pg_dump_path}" -U {db_user} -d {db_name} -f "{backup_file}"'
        
        result=subprocess.run(command, shell=True, check=True)
        if result:
            file_size = os.path.getsize(backup_file)
            if file_size > 0:
                return jsonify({
                    "message": "Backup creado exitosamente",
                    "file": backup_filename,
                    "size": file_size
                }), 200
            else:
                return jsonify({"error": "El archivo de backup está vacío"}), 500
        else:
            return jsonify({"error": "No se pudo crear el archivo de backup"}), 500
    except subprocess.CalledProcessError as e:
        return f"Error al ejecutar pg_dump: {str(e)}", 500
    except Exception as e:
        return f"Error al crear el respaldo: {str(e)}", 500
    finally:
        if os.path.exists(pgpass_path):
            os.remove(pgpass_path)

@app.route('/get_backup/<filename>')
def get_backup(filename):
    backup_directory = r"C:\ruta\donde\guardar\backups"  # Debe ser la misma ruta que en download_backup
    file_path = os.path.join(backup_directory, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "Archivo no encontrado"}), 404