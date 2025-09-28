from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(200))
    certifications_json = db.Column(db.Text, default='{}')
    past_incidents = db.Column(db.Integer, default=0)
    financial_stability = db.Column(db.Integer, default=5)
    created_at = db.Column(db.String(50))

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    title = db.Column(db.String(300))
    expiry_date = db.Column(db.String(20))
    is_compliant = db.Column(db.Boolean, default=True)
    has_sla = db.Column(db.Boolean, default=False)
    has_nda = db.Column(db.Boolean, default=False)
    has_data_protection = db.Column(db.Boolean, default=False)
    has_compliance_requirement = db.Column(db.Boolean, default=False)
    has_auto_renewal = db.Column(db.Boolean, default=False)
    has_termination_for_breach = db.Column(db.Boolean, default=False)
    has_penalty_clause = db.Column(db.Boolean, default=False)
    has_audit_rights = db.Column(db.Boolean, default=False)
    contract_file = db.Column(db.String(300))
    created_at = db.Column(db.String(50))

    vendor = db.relationship('Vendor', backref='contracts')
