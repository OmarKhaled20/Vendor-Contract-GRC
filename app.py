from flask import Flask, render_template, request, redirect, url_for, send_file, flash, abort
from models import db, Vendor, Contract
from risk_engine import calculate_vendor_risk
import os, datetime, json
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXT = {'pdf','png','jpg','jpeg','docx','doc'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grc_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'change-me'

db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

@app.route('/')
def index():
    vendors = Vendor.query.order_by(Vendor.id.desc()).all()
    contracts = Contract.query.order_by(Contract.id.desc()).limit(8).all()
    metrics = {'total_vendors': len(vendors), 'total_contracts': Contract.query.count()}
    return render_template('index.html', vendors=vendors, contracts=contracts, metrics=metrics)

@app.route('/vendor/add', methods=['GET','POST'])
def add_vendor():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        past_incidents = int(request.form.get('past_incidents') or 0)
        financial_stability = int(request.form.get('financial_stability') or 5)
        certs = {}
        iso = request.form.get('iso_expiry')
        pci = request.form.get('pci_expiry')
        if iso: certs['ISO27001'] = iso
        if pci: certs['PCI-DSS'] = pci
        cert_file = request.files.get('cert_file')
        cert_file_name = ''
        if cert_file and cert_file.filename and allowed_file(cert_file.filename):
            filename = secure_filename(f"cert_{int(datetime.datetime.datetime.utcnow().timestamp())}_" + cert_file.filename)
            cert_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cert_file_name = filename
        v = Vendor(name=name, contact=contact, certifications_json=json.dumps(certs), past_incidents=past_incidents, financial_stability=financial_stability, created_at=datetime.datetime.utcnow().isoformat())
        db.session.add(v); db.session.commit()
        if cert_file_name:
            meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"vendor_{v.id}_files.json")
            with open(meta_path,'w',encoding='utf-8') as f: json.dump({'cert_file': cert_file_name}, f)
        flash('Vendor added','success')
        return redirect(url_for('index'))
    return render_template('add_vendor.html')

@app.route('/contract/add', methods=['GET','POST'])
def add_contract():
    vendors = Vendor.query.order_by(Vendor.name).all()
    if request.method == 'POST':
        vendor_id = int(request.form.get('vendor_id'))
        title = request.form.get('title')
        expiry = request.form.get('expiry')
        is_compliant = True if request.form.get('is_compliant')=='on' else False
        has_sla = True if request.form.get('has_sla')=='on' else False
        has_nda = True if request.form.get('has_nda')=='on' else False
        has_data_protection = True if request.form.get('has_data_protection')=='on' else False
        has_compliance_requirement = True if request.form.get('has_compliance_requirement')=='on' else False
        has_auto_renewal = True if request.form.get('has_auto_renewal')=='on' else False
        has_termination_for_breach = True if request.form.get('has_termination_for_breach')=='on' else False
        has_penalty_clause = True if request.form.get('has_penalty_clause')=='on' else False
        has_audit_rights = True if request.form.get('has_audit_rights')=='on' else False
        contract_file = request.files.get('contract_file')
        contract_file_name = ''
        if contract_file and contract_file.filename and allowed_file(contract_file.filename):
            filename = secure_filename(f"contract_{int(datetime.datetime.datetime.utcnow().timestamp())}_" + contract_file.filename)
            contract_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            contract_file_name = filename
        c = Contract(vendor_id=vendor_id, title=title, expiry_date=expiry, is_compliant=is_compliant,
                     has_sla=has_sla, has_nda=has_nda, has_data_protection=has_data_protection,
                     has_compliance_requirement=has_compliance_requirement, has_auto_renewal=has_auto_renewal,
                     has_termination_for_breach=has_termination_for_breach, has_penalty_clause=has_penalty_clause,
                     has_audit_rights=has_audit_rights, contract_file=contract_file_name, created_at=datetime.datetime.utcnow().isoformat())
        db.session.add(c); db.session.commit()
        flash('Contract added','success')
        return redirect(url_for('index'))
    return render_template('add_contract.html', vendors=vendors)

@app.route('/vendor/<int:vid>')
def vendor_detail(vid):
    v = Vendor.query.get_or_404(vid)
    contracts = Contract.query.filter_by(vendor_id=vid).order_by(Contract.id.desc()).all()
    score, classification = calculate_vendor_risk(v, contracts)
    meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"vendor_{v.id}_files.json")
    files_meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path,'r',encoding='utf-8') as f: files_meta = json.load(f)
        except Exception:
            files_meta = {}
    return render_template('vendor_detail.html', vendor=v, contracts=contracts, score=score, classification=classification, files_meta=files_meta)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)

@app.route('/export')
def export():
    path = 'audit_export_v3.csv'
    with open(path, 'w', newline='', encoding='utf-8') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['Vendor Name','Certifications','Past Incidents','Financial Stability','Contract Title','Compliant','Expiry','Clauses','Contract File'])
        contracts = Contract.query.order_by(Contract.id.desc()).all()
        for c in contracts:
            v = Vendor.query.get(c.vendor_id)
            clauses = {
                'SLA': c.has_sla, 'NDA': c.has_nda, 'DataProtection': c.has_data_protection,
                'Compliance': c.has_compliance_requirement, 'AutoRenew': c.has_auto_renewal,
                'TerminationForBreach': c.has_termination_for_breach, 'Penalty': c.has_penalty_clause,
                'AuditRights': c.has_audit_rights
            }
            writer.writerow([v.name, v.certifications_json, v.past_incidents, v.financial_stability, c.title, c.is_compliant, c.expiry_date, json.dumps(clauses), c.contract_file])
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
