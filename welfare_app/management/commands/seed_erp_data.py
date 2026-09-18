import datetime
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from welfare_app.models import (
    Department, Employee, Dependent, Hospital, Doctor, HospitalVisit,
    MedicalRecord, MedicalClaim, ClaimExpenseItem, ApprovalWorkflow, ClaimPayment,
    Bill, Budget, FinanceTransaction, Medicine, MedicineTransaction,
    Supplier, PurchaseRequest, PurchaseOrder, Notification, UserProfile,
    BenefitRule, AuditLog
)


class Command(BaseCommand):
    help = 'Seeds complete, realistic Factory Welfare Department ERP data'

    def handle(self, *args, **options):
        self.stdout.write('Starting Factory Welfare ERP Data Seeder...')

        # 1. Admin User
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@factory-welfare.com',
                'first_name': 'Factory',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        profile, _ = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'Admin', 'phone': '+92-300-1234567'}
        )
        profile.role = 'Admin'
        profile.save()

        # 2. Departments
        departments_data = [
            ('Mechanical Assembly', 'MECH', 'Heavy machinery assembly, stamping, fabrication and plant operations'),
            ('Electrical & Automation', 'ELEC', 'Power systems, robotics, CNC electronics and motor controls'),
            ('Quality Assurance & Testing', 'QA', 'Standards compliance, laboratory materials testing, ISO audits'),
            ('Human Resources & Welfare', 'HR', 'Workforce administration, industrial welfare and employee health'),
            ('Supply Chain & Logistics', 'SCM', 'Warehousing, raw materials sourcing and finished goods distribution'),
            ('Finance & Treasury', 'FIN', 'Corporate accounts, factory budget allocations and audit management'),
            ('Plant Maintenance & Safety', 'MAINT', 'Facility utilities, HSE environmental safety and emergency response'),
        ]
        dept_objs = {}
        for name, code, desc in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={'code': code, 'description': desc, 'is_active': True}
            )
            dept_objs[name] = dept

        # 3. Benefit / Welfare Rules
        benefit_rules_data = [
            ('Executive & Management Healthcare Policy', None, 'Scale 17+', 250000.00, 5000.00, 100.0, 100.0, 10000.00, 'Comprehensive coverage for executive staff and dependents.'),
            ('Senior Technical & Supervisory Policy', None, 'Scale 11-16', 150000.00, 3500.00, 90.0, 90.0, 6000.00, 'Standard policy for supervisory and senior engineering staff.'),
            ('Factory Plant Worker Welfare Policy', None, 'Scale 1-10', 100000.00, 2500.00, 100.0, 100.0, 4000.00, 'Full coverage under Factory Welfare Fund with panel hospital access.'),
        ]
        for name, dept, grade, limit, opd, lab_p, med_p, room, desc in benefit_rules_data:
            BenefitRule.objects.get_or_create(
                name=name,
                defaults={
                    'department': dept,
                    'grade_scale': grade,
                    'annual_medical_limit': limit,
                    'opd_consultation_limit': opd,
                    'lab_coverage_percent': lab_p,
                    'medicine_coverage_percent': med_p,
                    'room_per_day_limit': room,
                    'description': desc,
                    'is_active': True,
                }
            )

        # 4. Panel Hospitals
        today = timezone.now().date()
        hospitals_data = [
            ('Al-Shifa Trust Medical Center', 'Private', 'GT Road, Rawalpindi / Islamabad', 'Islamabad', '+92-51-5487821', 'panel@alshifa.org', 'Panel', today - datetime.timedelta(days=180), today + datetime.timedelta(days=185)),
            ('Shifa International Hospital', 'Private', 'Pitras Bukhari Road, H-8/4', 'Islamabad', '+92-51-8463000', 'corporate@shifa.com.pk', 'Panel', today - datetime.timedelta(days=200), today + datetime.timedelta(days=165)),
            ('City General District Hospital', 'Government', 'Jinnah Avenue, Sector G-8', 'Islamabad', '+92-51-9261170', 'medical@citygeneral.gov.pk', 'Panel', today - datetime.timedelta(days=365), today + datetime.timedelta(days=365)),
            ('National Hospital & Medical Center', 'Private', 'L-Block, DHA Phase 1', 'Lahore', '+92-42-111171819', 'welfare@nationalhospital.pk', 'Panel', today - datetime.timedelta(days=90), today + datetime.timedelta(days=275)),
            ('Indus Health Network Hospital', 'Semi-Government', 'Korangi Crossing', 'Karachi', '+92-21-35112709', 'corporate@indushospital.org.pk', 'Panel', today - datetime.timedelta(days=120), today + datetime.timedelta(days=245)),
            ('Medix Specialty Diagnostic Clinic', 'Clinic', 'Commercial Market, Satellite Town', 'Rawalpindi', '+92-51-4412389', 'info@medixclinic.com', 'Non-Panel', None, None),
        ]
        hosp_objs = {}
        for name, h_type, addr, city, contact, email, panel, start, end in hospitals_data:
            hosp, _ = Hospital.objects.get_or_create(
                name=name,
                defaults={
                    'hospital_type': h_type,
                    'address': addr,
                    'city': city,
                    'contact_number': contact,
                    'email': email,
                    'panel_status': panel,
                    'contract_start_date': start,
                    'contract_end_date': end,
                    'status': 'Active',
                }
            )
            hosp_objs[name] = hosp

        # 5. Master Doctors
        doctors_data = [
            ('Dr. Tariq Mahmood Khan', 'Cardiology & Heart Disease', hosp_objs['Al-Shifa Trust Medical Center'], '+92-301-5551234', 'dr.tariq@alshifa.org', 'PMC-45892-C', 3500.00),
            ('Dr. Ayesha Siddiqa', 'General Internal Medicine', hosp_objs['Al-Shifa Trust Medical Center'], '+92-302-5552345', 'dr.ayesha@alshifa.org', 'PMC-51203-M', 2500.00),
            ('Dr. Muhammad Usman', 'Orthopedic Surgery & Trauma', hosp_objs['City General District Hospital'], '+92-303-5553456', 'dr.usman@citygeneral.gov.pk', 'PMC-38914-O', 2000.00),
            ('Dr. Zainab Fatima', 'Pediatrics & Family Health', hosp_objs['Shifa International Hospital'], '+92-304-5554567', 'dr.zainab@shifa.com.pk', 'PMC-62341-P', 3000.00),
            ('Dr. Farooq Azam', 'Pulmonology & Chest Diseases', hosp_objs['National Hospital & Medical Center'], '+92-305-5556789', 'dr.farooq@nationalhospital.pk', 'PMC-41908-U', 3200.00),
            ('Dr. Rabia Noreen', 'Ophthalmology & Eye Specialist', hosp_objs['Al-Shifa Trust Medical Center'], '+92-306-5557890', 'dr.rabia@alshifa.org', 'PMC-77123-E', 2500.00),
            ('Dr. Salman Qureshi', 'ENT & Head Neck Surgery', hosp_objs['Indus Health Network Hospital'], '+92-307-5558901', 'dr.salman@indushospital.org.pk', 'PMC-59812-N', 2800.00),
        ]
        doc_objs = []
        for name, spec, hosp, contact, email, reg, fee in doctors_data:
            doc, _ = Doctor.objects.get_or_create(
                name=name,
                defaults={
                    'specialization': spec,
                    'hospital': hosp,
                    'contact': contact,
                    'email': email,
                    'registration_number': reg,
                    'consultation_fee': fee,
                    'status': 'Active',
                }
            )
            doc_objs.append(doc)

        # 6. Realistic Employees
        sample_employees = [
            ('PL-101', 'Muhammad Ali Khan', 'Sardar Khan', 'Mechanical Assembly', 'Senior Plant Machinist', '1985-03-12', '37405-1234567-1', 'Male', '+92-300-9812345', 'Scale-12', 78000.00, 'Habib Bank Limited', '00427901234503'),
            ('PL-102', 'Kamran Bashir', 'Bashir Ahmed', 'Mechanical Assembly', 'Welding Specialist', '1990-07-22', '37405-2345678-1', 'Male', '+92-301-8723456', 'Scale-09', 58000.00, 'United Bank Limited', '01928374650192'),
            ('PL-103', 'Rashid Mehmood', 'Mehmood Ul Hassan', 'Electrical & Automation', 'Senior Electrical Engineer', '1982-11-05', '37405-3456789-1', 'Male', '+92-302-7634567', 'Scale-17', 125000.00, 'Meezan Bank', '02819283746501'),
            ('PL-104', 'Fatima Zahra', 'Syed Anwar Hussain', 'Quality Assurance & Testing', 'Quality Control Inspector', '1992-04-18', '37405-4567890-2', 'Female', '+92-303-6545678', 'Scale-11', 72000.00, 'Allied Bank Limited', '09182736450192'),
            ('PL-105', 'Tahir Imran', 'Imran Nazir', 'Supply Chain & Logistics', 'Warehouse Supervisor', '1988-09-30', '37405-5678901-1', 'Male', '+92-304-5456789', 'Scale-10', 64000.00, 'National Bank of Pakistan', '00192837465019'),
            ('PL-106', 'Zahid Hussain', 'Ghulam Hussain', 'Plant Maintenance & Safety', 'HSE Safety Officer', '1986-01-15', '37405-6789012-1', 'Male', '+92-305-4367890', 'Scale-14', 92000.00, 'MCB Bank Limited', '03829182736450'),
            ('PL-107', 'Noreen Akhtar', 'Akhtar Rasool', 'Human Resources & Welfare', 'Welfare Officer', '1991-06-25', '37405-7890123-2', 'Female', '+92-306-3278901', 'Scale-14', 88000.00, 'Bank Alfalah', '01928374650283'),
            ('PL-108', 'Bilal Ahmed Siddiqui', 'Ahmed Siddiqui', 'Finance & Treasury', 'Accounts Officer', '1989-12-10', '37405-8901234-1', 'Male', '+92-307-2189012', 'Scale-15', 96000.00, 'Faysal Bank', '04829182736451'),
            ('PL-109', 'Naveed Iqbal', 'Iqbal Masood', 'Mechanical Assembly', 'CNC Machine Operator', '1994-08-14', '37405-9012345-1', 'Male', '+92-308-1090123', 'Scale-07', 48000.00, 'Habib Bank Limited', '00427901827364'),
            ('PL-110', 'Shazia Parveen', 'Muhammad Din', 'Quality Assurance & Testing', 'Lab Chemist', '1993-02-28', '37405-0123456-2', 'Female', '+92-309-0981234', 'Scale-12', 75000.00, 'Meezan Bank', '02819283746599'),
        ]

        emp_objs = []
        for pl, name, fname, dept_name, desig, dob, cnic, gender, phone, scale, salary, b_name, b_acc in sample_employees:
            emp, _ = Employee.objects.get_or_create(
                pl_number=pl,
                defaults={
                    'name': name,
                    'father_name': fname,
                    'department': dept_name,
                    'designation': desig,
                    'date_of_birth': dob,
                    'cnic': cnic,
                    'gender': gender,
                    'contact_number': phone,
                    'email': f"{pl.lower().replace('-', '')}@factory.org",
                    'grade_scale': scale,
                    'basic_salary': salary,
                    'bank_name': b_name,
                    'bank_account': b_acc,
                    'joined_date': today - datetime.timedelta(days=random.randint(400, 3000)),
                    'employment_status': 'Active',
                    'emergency_contact_name': f"Family of {name.split()[0]}",
                    'emergency_contact_phone': phone,
                    'emergency_contact_relation': 'Spouse / Parent',
                }
            )
            emp_objs.append(emp)

            # Dependent
            Dependent.objects.get_or_create(
                employee=emp,
                name=f"Sultana Bibi ({name.split()[0]})" if gender == 'Male' else f"Tariq Khan ({name.split()[0]})",
                defaults={
                    'relationship': 'Spouse',
                    'gender': 'Female' if gender == 'Male' else 'Male',
                    'date_of_birth': today - datetime.timedelta(days=12000),
                    'cnic_bform': f"37405-{random.randint(1000000, 9999999)}-{1 if gender == 'Female' else 2}",
                    'contact': phone,
                    'medical_eligible': True,
                    'status': 'Active',
                }
            )

        # 7. Suppliers
        suppliers_data = [
            ('Pharmatec Healthcare Supplies', 'Hassan Raza', '+92-51-4433221', 'sales@pharmatec.pk', 'I-9 Industrial Area, Islamabad', 'Pharmaceuticals & OTC'),
            ('National Medilab Instruments', 'Khurram Shehzad', '+92-42-3665544', 'orders@medilab.com.pk', 'Circular Road, Lahore', 'Diagnostic Reagents & Equipment'),
            ('Premier Surgical Supplies', 'Bilal Ahmed', '+92-21-3445566', 'premier@surgical.pk', 'Korangi Industrial Zone, Karachi', 'Surgical Disposables & First Aid'),
        ]
        sup_objs = {}
        for s_name, cp, phone, email, addr, cat in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(
                name=s_name,
                defaults={
                    'contact_person': cp,
                    'contact_number': phone,
                    'email': email,
                    'address': addr,
                    'category': cat,
                    'status': 'Active',
                }
            )
            sup_objs[s_name] = sup

        # 8. Medicines
        medicines_data = [
            ('Panadol Extra 500mg', 'Paracetamol + Caffeine', 'Tablet', 'GSK Pakistan', 'BATCH-8890', today + datetime.timedelta(days=450), 3.50, 4.50, 650, 100, sup_objs['Pharmatec Healthcare Supplies']),
            ('Augmentin 625mg', 'Amoxicillin + Clavulanic Acid', 'Tablet', 'GSK Pakistan', 'BATCH-7741', today + datetime.timedelta(days=320), 28.00, 35.00, 220, 40, sup_objs['Pharmatec Healthcare Supplies']),
            ('Brufen 400mg', 'Ibuprofen', 'Tablet', 'Abbott Laboratories', 'BATCH-6623', today + datetime.timedelta(days=500), 4.20, 5.50, 380, 50, sup_objs['Pharmatec Healthcare Supplies']),
            ('Cac-1000 Plus', 'Calcium + Vitamin C + D3', 'Tablet', 'GSK Pakistan', 'BATCH-4412', today + datetime.timedelta(days=280), 32.00, 40.00, 120, 25, sup_objs['Pharmatec Healthcare Supplies']),
            ('Ceftriaxone 1g IV', 'Ceftriaxone Sodium', 'Injection', 'Sami Pharma', 'BATCH-9932', today + datetime.timedelta(days=600), 220.00, 280.00, 65, 20, sup_objs['Pharmatec Healthcare Supplies']),
            ('Risek 40mg IV', 'Omeprazole', 'Injection', 'Getz Pharma', 'BATCH-3310', today + datetime.timedelta(days=45), 160.00, 200.00, 8, 20, sup_objs['Pharmatec Healthcare Supplies']),
            ('Flagyl 400mg', 'Metronidazole', 'Tablet', 'Sanofi Aventis', 'BATCH-5519', today + datetime.timedelta(days=410), 5.10, 6.80, 410, 50, sup_objs['Pharmatec Healthcare Supplies']),
            ('Surbex Z', 'High Potency B-Complex + Zinc', 'Tablet', 'Abbott Laboratories', 'BATCH-1189', today + datetime.timedelta(days=360), 18.00, 24.00, 190, 30, sup_objs['Pharmatec Healthcare Supplies']),
        ]
        for m_name, gen, cat, mfg, batch, exp, pp, sp, qty, min_l, sup in medicines_data:
            Medicine.objects.get_or_create(
                name=m_name,
                defaults={
                    'generic_name': gen,
                    'category': cat,
                    'manufacturer': mfg,
                    'batch_number': batch,
                    'expiry_date': exp,
                    'purchase_price': pp,
                    'unit_cost': pp,
                    'selling_price': sp,
                    'quantity': qty,
                    'min_stock_level': min_l,
                    'supplier': sup,
                    'is_active': True,
                }
            )

        # 9. Budgets
        current_year = today.year
        budget_amounts = {
            'Mechanical Assembly': 2500000.00,
            'Electrical & Automation': 1800000.00,
            'Quality Assurance & Testing': 1200000.00,
            'Human Resources & Welfare': 900000.00,
            'Supply Chain & Logistics': 1400000.00,
            'Finance & Treasury': 800000.00,
            'Plant Maintenance & Safety': 1600000.00,
        }
        for d_name, amount in budget_amounts.items():
            dept = dept_objs.get(d_name)
            Budget.objects.get_or_create(
                year=current_year,
                department=dept,
                category='Medical',
                defaults={
                    'allocated_amount': amount,
                    'description': f'Medical Welfare Fund Allocation for {d_name} - FY {current_year}',
                    'is_active': True,
                }
            )

        # 10. Diverse Claims with Itemized Breakdown and Payments
        claims_scenario = [
            (emp_objs[0], hosp_objs['Al-Shifa Trust Medical Center'], doc_objs[0], 'OPD Consultation', 'Hypertensive Episode with Angina Symptoms', 3500, 0, 4500, 3200, 0, 0, 0, 0, 'Approved', 'Paid', 11200),
            (emp_objs[1], hosp_objs['City General District Hospital'], doc_objs[2], 'Emergency Treatment', 'Industrial Hand Laceration & Tendon Repair', 2000, 1500, 2200, 1800, 3500, 4500, 800, 0, 'Approved', 'Paid', 16300),
            (emp_objs[2], hosp_objs['Shifa International Hospital'], doc_objs[3], 'Prescription Medicine', 'Acute Bronchial Infection with Fever', 3000, 0, 1500, 6800, 0, 0, 0, 500, 'Approved', 'Unpaid', 10800),
            (emp_objs[3], hosp_objs['Al-Shifa Trust Medical Center'], doc_objs[1], 'Diagnostic / Lab Tests', 'Gastroenteritis & Comprehensive Blood Panel', 2500, 0, 5800, 2400, 0, 0, 0, 0, 'Under Review', 'Unpaid', 10700),
            (emp_objs[4], hosp_objs['National Hospital & Medical Center'], doc_objs[4], 'OPD Consultation', 'Severe Chronic Asthma with Wheezing', 3200, 0, 3100, 4200, 0, 0, 0, 0, 'Pending', 'Unpaid', 10500),
            (emp_objs[5], hosp_objs['Al-Shifa Trust Medical Center'], doc_objs[5], 'Maternity / Dental / Optical', 'Cataract Eye Examination & Lens Assessment', 2500, 0, 1800, 1200, 0, 0, 0, 0, 'Approved', 'Partially Paid', 5500),
            (emp_objs[6], hosp_objs['Indus Health Network Hospital'], doc_objs[6], 'Hospitalization / Surgery', 'Acute Appendicitis Laparoscopic Appendectomy', 2800, 5000, 6500, 8500, 18000, 22000, 1500, 0, 'Approved', 'Paid', 64300),
            (emp_objs[7], hosp_objs['City General District Hospital'], doc_objs[2], 'OPD Consultation', 'Lumbar Spine Strain & Sciatica', 2000, 0, 4200, 2800, 0, 0, 0, 0, 'Rejected', 'Unpaid', 9000),
        ]

        for i, (emp, hosp, doc, c_type, diag, d_fee, d_dues, l_fee, m_fee, a_fee, p_fee, o_fee, emp_contrib, c_status, p_status, app_amt) in enumerate(claims_scenario):
            c_date = today - datetime.timedelta(days=random.randint(2, 45))
            claim, created = MedicalClaim.objects.get_or_create(
                bill_number=f"INV-2026-{1000 + i}",
                defaults={
                    'employee': emp,
                    'hospital': hosp,
                    'doctor': doc,
                    'claim_type': c_type,
                    'diagnosis': diag,
                    'claim_date': c_date,
                    'treatment_date': c_date - datetime.timedelta(days=1),
                    'bill_date': c_date - datetime.timedelta(days=1),
                    'doctor_fee': d_fee,
                    'doctor_dues': d_dues,
                    'lab_fee': l_fee,
                    'medicine_fee': m_fee,
                    'admission_fee': a_fee,
                    'procedure_fee': p_fee,
                    'other_fee': o_fee,
                    'employee_contribution': emp_contrib,
                    'approved_amount': app_amt if c_status in ['Approved', 'Partially Approved', 'Paid'] else 0.00,
                    'claim_status': c_status,
                    'payment_status': p_status,
                    'remarks': f'Medical assistance sanctioned per policy rules for {emp.name}.',
                    'created_by': admin_user,
                }
            )

            if created:
                # Workflow steps
                ApprovalWorkflow.objects.create(claim=claim, stage='Submitted', approver=admin_user, status='Approved', remarks='Claim submitted with invoices')
                if c_status in ['Under Review', 'Approved', 'Partially Approved', 'Paid', 'Rejected']:
                    ApprovalWorkflow.objects.create(claim=claim, stage='Welfare Review', approver=admin_user, status='Approved' if c_status != 'Rejected' else 'Rejected', remarks='Policy limits verified')
                if c_status in ['Approved', 'Partially Approved', 'Paid']:
                    ApprovalWorkflow.objects.create(claim=claim, stage='Manager Approval', approver=admin_user, status='Approved', approved_amount=app_amt, remarks='Approved for disbursement')

                # If Paid or Partially Paid, record ClaimPayment & FinanceTransaction
                if p_status in ['Paid', 'Partially Paid']:
                    pay_amt = app_amt if p_status == 'Paid' else (app_amt / 2)
                    pay = ClaimPayment.objects.create(
                        claim=claim,
                        employee=emp,
                        approved_amount=app_amt,
                        payment_amount=pay_amt,
                        payment_date=c_date + datetime.timedelta(days=2),
                        payment_method='Bank Transfer',
                        account='Welfare Main Account (HBL A/C 0042-7901)',
                        transaction_reference=f"FT-2026-{5000 + i}",
                        paid_by=admin_user,
                        remarks=f'Direct payroll bank disbursement for Claim {claim.claim_number}'
                    )

                    FinanceTransaction.objects.create(
                        transaction_type='Payment',
                        amount=pay_amt,
                        category='Medical Claim Disbursement',
                        description=f'Disbursement for {claim.claim_number} ({emp.name})',
                        reference_number=pay.payment_number,
                        payment_method='Bank Transfer',
                        account='Welfare Main Account (HBL)',
                        related_claim=claim,
                        date=pay.payment_date,
                        created_by=admin_user,
                    )

        # 11. Direct Bills
        Bill.objects.get_or_create(
            bill_number='HOSP-INV-001',
            defaults={
                'hospital': hosp_objs['Al-Shifa Trust Medical Center'],
                'category': 'Hospital Bill',
                'amount': 45000.00,
                'bill_date': today - datetime.timedelta(days=10),
                'due_date': today + datetime.timedelta(days=20),
                'description': 'Monthly panel hospital consolidated OPD retainer and billing',
                'status': 'Approved',
                'payment_status': 'Paid',
                'payment_method': 'Bank Transfer',
                'paid_date': today - datetime.timedelta(days=5),
                'created_by': admin_user,
            }
        )

        # 12. Notifications
        Notification.objects.get_or_create(
            user=admin_user,
            title='Welfare ERP System Online',
            defaults={'message': 'Factory Welfare & Hospital Management ERP is live with all modules active.', 'notification_type': 'Success', 'is_read': False}
        )

        self.stdout.write(self.style.SUCCESS('Factory Welfare ERP data successfully seeded!'))
