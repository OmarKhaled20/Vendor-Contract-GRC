import datetime, json

def calculate_vendor_risk(vendor, contracts):
    score = 30.0
    today = datetime.date.today()
    try:
        certs = json.loads(vendor.certifications_json or '{}')
    except Exception:
        certs = {}
    for name, expiry in certs.items():
        try:
            exp = datetime.datetime.strptime(expiry, '%Y-%m-%d').date()
            days = (exp - today).days
            if days < 0:
                score += 20.0
            elif days < 30:
                score += 10.0
            elif days < 90:
                score += 5.0
        except Exception:
            score += 5.0
    score += (vendor.past_incidents or 0) * 6.0
    fs = max(1, min(10, vendor.financial_stability or 5))
    score += (5 - fs) * 2.5
    for c in contracts:
        if not c.is_compliant:
            score += 8.0
        try:
            if c.expiry_date:
                expc = datetime.datetime.strptime(c.expiry_date, '%Y-%m-%d').date()
                days = (expc - today).days
                if days < 0:
                    score += 5.0
                elif days < 30:
                    score += 2.5
        except Exception:
            pass
        if not c.has_sla:
            score += 2.0
        if not c.has_nda:
            score += 3.0
        if not c.has_data_protection:
            score += 5.0
        if not c.has_compliance_requirement:
            score += 4.0
        if c.has_auto_renewal:
            score += 2.0
        if not c.has_termination_for_breach:
            score += 3.0
        if not c.has_penalty_clause:
            score += 2.0
        if not c.has_audit_rights:
            score += 3.0
    score = max(0.0, min(100.0, round(score,1)))
    classification = 'Low' if score <= 30 else ('Medium' if score <= 60 else 'High')
    return score, classification
