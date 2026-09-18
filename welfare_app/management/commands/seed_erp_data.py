import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from welfare_app.models import (
    Department, Employee, Dependent, Hospital, Doctor, HospitalVisit,
    MedicalRecord, MedicalClaim, ClaimExpenseItem, ApprovalWorkflow,
    Bill, Budget, FinanceTransaction, Medicine, MedicineTransaction,
    Supplier, PurchaseRequest, PurchaseOrder, Notification, UserProfile
)


class Command(BaseCommand):
    help = 'Seeds initial ERP data including admin user, departments, hospitals, doctors, medicines, and budgets'

    def handle(self, *args, **options):
        self.stdout.write('Seeding ERP data...')

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@welfare.org',
                'first_name': 'Welfare',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created (username: admin, password: admin123)'))
        else:
            self.stdout.write('Admin user already exists.')

        profile, _ = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'Admin', 'phone': '+92-300-1234567'}
        )
        profile.role = 'Admin'
        profile.save()

        # 2. Departments
        departments_data = [
            ('Mechanical Assembly', 'MECH-01', 'Mechanical plant production and assembly operations'),
            ('Electrical Engineering', 'ELEC-02', 'Electrical installation, power and electronics engineering'),
            ('Quality Assurance', 'QA-03', 'Quality control, inspection and compliance'),
            ('Human Resources', 'HR-04', 'Talent management, welfare and personnel affairs'),
            ('Logistics & Stores', 'LOG-05', 'Inventory warehousing, shipping and material supply'),
            ('Medical & Welfare', 'MED-06', 'Employee health services, welfare benefits and claims'),
            ('Finance & Accounts', 'FIN-07', 'Treasury, payroll, billing, budgets and financial audits'),
        ]
        dept_objs = {}
        for name, code, desc in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={'code': code, 'description': desc, 'is_active': True}
            )
            dept_objs[name] = dept
        self.stdout.write(self.style.SUCCESS(f'Departments seeded: {len(dept_objs)}'))

        # 3. Hospitals
        hospitals_data = [
            ('Al-Shifa Hospital', 'Private', 'Rawalpindi / Islamabad Highway', 'Islamabad', '+92-51-5487821', 'info@alshifa.org', 'Panel', timezone.now().date() - datetime.timedelta(days=180), timezone.now().date() + datetime.timedelta(days=185)),
            ('City General Hospital', 'Government', 'Jinnah Avenue, Sector G-8', 'Islamabad', '+92-51-9261170', 'contact@citygeneral.gov.pk', 'Panel', timezone.now().date() - datetime.timedelta(days=365), timezone.now().date() + datetime.timedelta(days=365)),
            ('National Medical Complex', 'Semi-Government', 'Main Boulevard, Gulberg', 'Lahore', '+92-42-35750000', 'care@nmc.edu.pk', 'Panel', timezone.now().date() - datetime.timedelta(days=90), timezone.now().date() + datetime.timedelta(days=275)),
            ('Medix Specialty Clinic', 'Clinic', 'Commercial Area, Phase 4', 'Rawalpindi', '+92-51-5123456', 'info@medixclinic.com', 'Non-Panel', None, None),
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
        self.stdout.write(self.style.SUCCESS(f'Hospitals seeded: {len(hosp_objs)}'))

        # 4. Doctors
        doctors_data = [
            ('Dr. Tariq Mahmood Khan', 'Cardiology', hosp_objs.get('Al-Shifa Hospital'), '+92-301-5551234', 'dr.tariq@alshifa.org', 'PMC-45892-C'),
            ('Dr. Ayesha Siddiqa', 'General Medicine', hosp_objs.get('Al-Shifa Hospital'), '+92-302-5552345', 'dr.ayesha@alshifa.org', 'PMC-51203-M'),
            ('Dr. Muhammad Usman', 'Orthopedic Surgery', hosp_objs.get('City General Hospital'), '+92-303-5553456', 'dr.usman@citygeneral.gov.pk', 'PMC-38914-O'),
            ('Dr. Zainab Fatima', 'Pediatrics & Family Medicine', hosp_objs.get('National Medical Complex'), '+92-304-5554567', 'dr.zainab@nmc.edu.pk', 'PMC-62341-P'),
        ]
        doc_objs = []
        for name, spec, hosp, contact, email, reg in doctors_data:
            doc, _ = Doctor.objects.get_or_create(
                name=name,
                defaults={
                    'specialization': spec,
                    'hospital': hosp,
                    'contact': contact,
                    'email': email,
                    'registration_number': reg,
                    'status': 'Active',
                }
            )
            doc_objs.append(doc)
        self.stdout.write(self.style.SUCCESS(f'Doctors seeded: {len(doc_objs)}'))

        # 5. Update existing employees with sample metadata if empty
        employees = Employee.objects.all()
        for idx, emp in enumerate(employees):
            if not emp.cnic:
                emp.cnic = f"37405-{1000000 + emp.id:07d}-1"
            if not emp.gender:
                emp.gender = 'Male'
            if not emp.contact_number:
                emp.contact_number = f"+92-300-{4000000 + emp.id:07d}"
            if not emp.email:
                emp.email = f"emp{emp.pl_number.lower().replace('-', '')}@factory.org"
            if not emp.basic_salary:
                emp.basic_salary = 65000 + (emp.id * 8500)
            if not emp.employment_status:
                emp.employment_status = 'Active'
            emp.save()

            # Add sample dependent if none exist
            if not emp.dependents.exists():
                Dependent.objects.create(
                    employee=emp,
                    name=f"Family Member of {emp.name.split()[0]}",
                    relationship='Spouse' if idx % 2 == 0 else 'Son',
                    gender='Female' if idx % 2 == 0 else 'Male',
                    date_of_birth=datetime.date(1995, 4, 15),
                    cnic_bform=f"37405-{2000000 + emp.id:07d}-2",
                    medical_eligible=True,
                    status='Active'
                )

        # 6. Suppliers
        suppliers_data = [
            ('Pharmatec Healthcare Supplies', 'Hassan Raza', '+92-51-4433221', 'sales@pharmatec.pk', 'I-9 Industrial Area, Islamabad', 'Pharmaceuticals'),
            ('National Medilab Instruments', 'Khurram Shehzad', '+92-42-3665544', 'orders@medilab.com.pk', 'Circular Road, Lahore', 'Lab & Diagnostic Equipment'),
            ('Premier Surgical Supplies', 'Bilal Ahmed', '+92-21-3445566', 'premier@surgical.pk', 'Korangi Industrial Zone, Karachi', 'Surgical Disposables'),
        ]
        sup_objs = {}
        for name, contact_p, phone, email, addr, cat in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact_p,
                    'contact_number': phone,
                    'email': email,
                    'address': addr,
                    'category': cat,
                    'status': 'Active',
                }
            )
            sup_objs[name] = sup

        # 7. Medicines & Stock
        medicines_data = [
            ('Panadol Extra 500mg', 'Paracetamol + Caffeine', 'Tablet', 'GSK Pakistan', 'BATCH-8890', timezone.now().date() + datetime.timedelta(days=450), 3.50, 4.50, 450, 50, sup_objs.get('Pharmatec Healthcare Supplies')),
            ('Augmentin 625mg', 'Amoxicillin + Clavulanic Acid', 'Tablet', 'GSK Pakistan', 'BATCH-7741', timezone.now().date() + datetime.timedelta(days=320), 28.00, 35.00, 180, 30, sup_objs.get('Pharmatec Healthcare Supplies')),
            ('Brufen 400mg', 'Ibuprofen', 'Tablet', 'Abbott Laboratories', 'BATCH-6623', timezone.now().date() + datetime.timedelta(days=500), 4.20, 5.50, 300, 40, sup_objs.get('Pharmatec Healthcare Supplies')),
            ('Cac-1000 Plus', 'Calcium + Vitamin C + D3', 'Tablet', 'GSK Pakistan', 'BATCH-4412', timezone.now().date() + datetime.timedelta(days=280), 32.00, 40.00, 85, 20, sup_objs.get('Pharmatec Healthcare Supplies')),
            ('Ceftriaxone 1g IV', 'Ceftriaxone Sodium', 'Injection', 'Sami Pharma', 'BATCH-9932', timezone.now().date() + datetime.timedelta(days=600), 220.00, 280.00, 45, 15, sup_objs.get('Pharmatec Healthcare Supplies')),
            ('Risek 40mg IV', 'Omeprazole', 'Injection', 'Getz Pharma', 'BATCH-3310', timezone.now().date() + datetime.timedelta(days=360), 160.00, 200.00, 8, 15, sup_objs.get('Pharmatec Healthcare Supplies')), # Low stock alert sample
        ]
        for name, gen, cat, mfg, batch, exp, p_price, s_price, qty, min_l, sup in medicines_data:
            med, _ = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'generic_name': gen,
                    'category': cat,
                    'manufacturer': mfg,
                    'batch_number': batch,
                    'expiry_date': exp,
                    'purchase_price': p_price,
                    'selling_price': s_price,
                    'quantity': qty,
                    'min_stock_level': min_l,
                    'supplier': sup,
                    'is_active': True,
                }
            )

        # 8. Budgets for Current Year
        current_year = timezone.now().year
        budgets_data = [
            (dept_objs.get('Mechanical Assembly'), 'Medical', 1500000),
            (dept_objs.get('Electrical Engineering'), 'Medical', 1200000),
            (dept_objs.get('Quality Assurance'), 'Medical', 800000),
            (dept_objs.get('Human Resources'), 'Medical', 600000),
            (dept_objs.get('Logistics & Stores'), 'Medical', 900000),
            (None, 'Emergency', 2000000),
        ]
        for dept, cat, alloc in budgets_data:
            Budget.objects.get_or_create(
                year=current_year,
                department=dept,
                category=cat,
                defaults={
                    'allocated_amount': alloc,
                    'description': f'{cat} welfare budget allocation for fiscal year {current_year}',
                    'is_active': True,
                }
            )

        # 9. Sample Claims & Visits
        if employees.exists():
            first_emp = employees.first()
            alshifa = hosp_objs.get('Al-Shifa Hospital')
            doc = doc_objs[0] if doc_objs else None

            # Create sample visit
            visit, _ = HospitalVisit.objects.get_or_create(
                employee=first_emp,
                visit_date=timezone.now().date() - datetime.timedelta(days=5),
                defaults={
                    'hospital': alshifa,
                    'doctor': doc,
                    'visit_type': 'OPD',
                    'diagnosis': 'Seasonal allergic rhinitis & bronchial congestion',
                    'symptoms': 'Persistent dry cough, mild fever, throat irritation for 4 days',
                    'treatment': 'Oral antibiotics course and antihistamine therapy prescribed',
                    'prescription': 'Augmentin 625mg 1 tab BD x 5 days\nPanadol Extra 1 tab TDS\nCac-1000 Plus 1 tab OD',
                    'medical_notes': 'Patient advised 2 days bed rest. Vitals stable.',
                    'status': 'Completed',
                }
            )

            # Create sample claim
            claim, claim_created = MedicalClaim.objects.get_or_create(
                employee=first_emp,
                bill_number='BILL-2026-001',
                defaults={
                    'hospital': alshifa,
                    'doctor': doc,
                    'hospital_visit': visit,
                    'claim_date': timezone.now().date() - datetime.timedelta(days=4),
                    'bill_date': timezone.now().date() - datetime.timedelta(days=5),
                    'total_bill_amount': 8500.00,
                    'eligible_amount': 8500.00,
                    'employee_contribution': 0.00,
                    'welfare_contribution': 8500.00,
                    'approved_amount': 8500.00,
                    'claim_status': 'Approved',
                    'payment_status': 'Paid',
                    'remarks': 'Regular medical reimbursement approved per policy scale.',
                    'created_by': admin_user,
                }
            )
            if claim_created:
                ClaimExpenseItem.objects.create(claim=claim, category='Consultation', description='Specialist doctor consultation fee', amount=2500, eligible_amount=2500, approved_amount=2500)
                ClaimExpenseItem.objects.create(claim=claim, category='Medicine', description='Prescribed antibiotic & supportive medication', amount=3500, eligible_amount=3500, approved_amount=3500)
                ClaimExpenseItem.objects.create(claim=claim, category='Laboratory', description='CBC + ESR Blood Work', amount=2500, eligible_amount=2500, approved_amount=2500)

                ApprovalWorkflow.objects.create(claim=claim, stage='Submitted', approver=admin_user, status='Approved', remarks='Claim submitted with receipts')
                ApprovalWorkflow.objects.create(claim=claim, stage='Welfare Review', approver=admin_user, status='Approved', remarks='Verified against policy')
                ApprovalWorkflow.objects.create(claim=claim, stage='Manager Approval', approver=admin_user, status='Approved', remarks='Budget available, approved')
                ApprovalWorkflow.objects.create(claim=claim, stage='Payment', approver=admin_user, status='Approved', remarks='Disbursed via bank transfer')

        # 10. Sample Notifications
        notifications_data = [
            ('Welcome to Welfare & Hospital ERP', 'Your enterprise welfare management system is online and ready.', 'Info'),
            ('Low Medicine Stock Alert', 'Risek 40mg IV is currently below minimum safety stock level (8 units remaining).', 'Warning'),
            ('Panel Hospital Contract Notice', 'Al-Shifa Hospital panel contract is active until Q4 2026.', 'Contract'),
        ]
        for title, msg, n_type in notifications_data:
            Notification.objects.get_or_create(
                user=admin_user,
                title=title,
                defaults={'message': msg, 'notification_type': n_type, 'is_read': False}
            )

        self.stdout.write(self.style.SUCCESS('ERP seed data loaded successfully!'))
