import datetime
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse

from welfare_app.models import (
    Department, Employee, Dependent, Hospital, Doctor, HospitalVisit,
    MedicalClaim, ClaimExpenseItem, ClaimPayment, ApprovalWorkflow,
    Bill, BillDocument, Budget, Medicine, Supplier, UserProfile
)


class CoreMedicalOperationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@welfare.org',
            password='password123'
        )
        self.profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'Admin'}
        )
        self.client.force_login(self.user)

        # Department
        self.dept = Department.objects.create(
            name='Engineering',
            code='ENG-01',
            is_active=True
        )

        # Employee
        self.emp = Employee.objects.create(
            pl_number='PL-101',
            name='Muhammad Ahmed',
            department='Engineering',
            employment_status='Active'
        )

        # Dependent
        self.dep = Dependent.objects.create(
            employee=self.emp,
            name='Fatima Ahmed',
            relationship='Spouse',
            medical_eligible=True,
            status='Active'
        )

        # Hospital
        self.hospital = Hospital.objects.create(
            name='Al-Shifa Trust Hospital',
            hospital_code='HOSP-001',
            hospital_type='Private',
            city='Islamabad',
            panel_status='Panel',
            status='Active'
        )

        # Doctor
        self.doctor = Doctor.objects.create(
            name='Dr. Tariq Mahmood',
            specialization='Cardiology',
            hospital=self.hospital,
            consultation_fee=2500.00,
            status='Active'
        )

        # Hospital Visit
        self.visit = HospitalVisit.objects.create(
            employee=self.emp,
            dependent=self.dep,
            hospital=self.hospital,
            doctor=self.doctor,
            visit_type='OPD',
            diagnosis='Hypertension & Chest Discomfort',
            total_visit_cost=3500.00,
            status='Completed'
        )

        # Medical Claim
        self.claim = MedicalClaim.objects.create(
            employee=self.emp,
            dependent=self.dep,
            hospital=self.hospital,
            doctor=self.doctor,
            hospital_visit=self.visit,
            claim_type='OPD Consultation',
            doctor_fee=2500.00,
            lab_fee=1500.00,
            medicine_fee=1000.00,
            total_bill_amount=5000.00,
            claimable_amount=5000.00,
            approved_amount=5000.00,
            claim_status='Pending',
            payment_status='Unpaid'
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'welfare_app/dashboard.html')
        
        # Test 12 KPIs presence
        self.assertIn('total_claims_count', response.context)
        self.assertIn('total_claims_amount', response.context)
        self.assertIn('approved_claims_amount', response.context)
        self.assertIn('disbursed_amount', response.context)
        self.assertIn('pending_claims_count', response.context)
        self.assertIn('pending_claims_amount', response.context)
        self.assertIn('active_employees_count', response.context)
        self.assertIn('total_dependents_count', response.context)
        self.assertIn('panel_hospitals_count', response.context)
        self.assertIn('total_doctors_count', response.context)
        self.assertIn('hospital_visits_count', response.context)
        self.assertIn('low_stock_count', response.context)

        # Test 6 Chart datasets presence
        self.assertIn('monthly_chart_labels', response.context)
        self.assertIn('status_labels', response.context)
        self.assertIn('dept_labels', response.context)
        self.assertIn('hospital_labels', response.context)
        self.assertIn('type_labels', response.context)
        self.assertIn('fee_labels', response.context)

    def test_hospital_views(self):
        # List
        res_list = self.client.get(reverse('hospital_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, 'welfare_app/hospitals/list.html')
        self.assertContains(res_list, 'Al-Shifa Trust Hospital')

        # Detail
        res_det = self.client.get(reverse('hospital_detail', args=[self.hospital.pk]))
        self.assertEqual(res_det.status_code, 200)
        self.assertTemplateUsed(res_det, 'welfare_app/hospitals/detail.html')
        self.assertContains(res_det, 'HOSP-001')

        # Create
        res_create = self.client.post(reverse('hospital_create'), {
            'name': 'City Care Clinic',
            'hospital_type': 'Clinic',
            'city': 'Rawalpindi',
            'panel_status': 'Panel',
            'status': 'Active'
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Hospital.objects.filter(name='City Care Clinic').exists())

    def test_doctor_views(self):
        # List
        res_list = self.client.get(reverse('doctor_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, 'welfare_app/doctors/list.html')
        self.assertContains(res_list, 'Dr. Tariq Mahmood')

        # Create
        res_create = self.client.post(reverse('doctor_create'), {
            'name': 'Dr. Ayesha Malik',
            'specialization': 'Pediatrics',
            'hospital': self.hospital.pk,
            'consultation_fee': 2000,
            'status': 'Active'
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Doctor.objects.filter(name='Dr. Ayesha Malik').exists())

    def test_visit_views(self):
        # List
        res_list = self.client.get(reverse('visit_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, 'welfare_app/visits/list.html')
        self.assertContains(res_list, 'Muhammad Ahmed')

        # Detail
        res_det = self.client.get(reverse('visit_detail', args=[self.visit.pk]))
        self.assertEqual(res_det.status_code, 200)
        self.assertTemplateUsed(res_det, 'welfare_app/visits/detail.html')

        # Dependent API endpoint
        res_api = self.client.get(reverse('employee_dependents_api', args=[self.emp.pk]))
        self.assertEqual(res_api.status_code, 200)
        self.assertIn('Fatima Ahmed', res_api.content.decode())

    def test_claim_views_and_voucher(self):
        # Detail
        res_det = self.client.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertEqual(res_det.status_code, 200)
        self.assertTemplateUsed(res_det, 'welfare_app/claims/detail.html')
        self.assertContains(res_det, self.claim.claim_number)

        # Approve
        res_app = self.client.post(reverse('claim_approve', args=[self.claim.pk]), {
            'action': 'Approved',
            'approved_amount': '5000',
            'remarks': 'Sanctioned per policy.'
        })
        self.assertEqual(res_app.status_code, 302)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.claim_status, 'Approved')

        # Disburse Payment
        res_pay = self.client.post(reverse('claim_payment_create', args=[self.claim.pk]), {
            'payment_amount': '5000',
            'payment_date': datetime.date.today().strftime('%Y-%m-%d'),
            'payment_method': 'Bank Transfer',
            'account': 'Welfare Main Account (HBL)',
            'transaction_reference': 'FT-99881',
            'remarks': 'Online transfer complete'
        })
        self.assertEqual(res_pay.status_code, 302)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.payment_status, 'Paid')

        # Print Voucher
        res_print = self.client.get(reverse('claim_print', args=[self.claim.pk]))
        self.assertEqual(res_print.status_code, 200)
        self.assertTemplateUsed(res_print, 'welfare_app/claims/print_voucher.html')
        self.assertContains(res_print, 'Medical Expense Reimbursement Voucher')
        self.assertContains(res_print, self.claim.claim_number)

    def test_visit_itemized_financials_and_calculation(self):
        # 1. Test Form Render with dynamic expense rows
        res_form = self.client.get(reverse('visit_create'))
        self.assertEqual(res_form.status_code, 200)
        self.assertContains(res_form, 'id="expense-rows-container"', html=False)
        self.assertContains(res_form, '+ Add Expense', html=False)
        self.assertContains(res_form, 'id_total_visit_cost')
        self.assertContains(res_form, '5. Financials & Document Scans', html=False)

        # 2. Test Create with itemized expenses & dummy file upload
        doc_receipt = SimpleUploadedFile("consultation_receipt.pdf", b"Dummy consultation receipt content", content_type="application/pdf")
        med_slip = SimpleUploadedFile("pharmacy_bill.pdf", b"Dummy pharmacy bill content", content_type="application/pdf")

        post_data = {
            'employee': self.emp.pk,
            'hospital': self.hospital.pk,
            'doctor': self.doctor.pk,
            'visit_date': datetime.date.today().strftime('%Y-%m-%d'),
            'visit_type': 'OPD',
            'diagnosis': 'Seasonal Flu & Allergy',
            'doctor_fee': '2000.00',
            'doctor_fee_doc': doc_receipt,
            'medicine_cost': '1500.00',
            'medicine_doc': med_slip,
            'diagnostic_cost': '800.00',
            'other_charges': '200.00',
            'status': 'Completed'
        }

        res_post = self.client.post(reverse('visit_create'), post_data)
        self.assertEqual(res_post.status_code, 302)

        # 3. Verify saved record & auto-calculated total (2000 + 1500 + 800 + 200 = 4500)
        created_visit = HospitalVisit.objects.filter(diagnosis='Seasonal Flu & Allergy').first()
        self.assertIsNotNone(created_visit)
        self.assertEqual(float(created_visit.doctor_fee), 2000.00)
        self.assertEqual(float(created_visit.medicine_cost), 1500.00)
        self.assertEqual(float(created_visit.diagnostic_cost), 800.00)
        self.assertEqual(float(created_visit.other_charges), 200.00)
        self.assertEqual(float(created_visit.total_visit_cost), 4500.00)
        self.assertTrue(bool(created_visit.doctor_fee_doc))
        self.assertTrue(bool(created_visit.medicine_doc))

        # 4. Verify Detail View displays all expenses & file links
        res_detail = self.client.get(reverse('visit_detail', args=[created_visit.pk]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, '2000.00')
        self.assertContains(res_detail, '1500.00')
        self.assertContains(res_detail, '800.00')
        self.assertContains(res_detail, '200.00')
        self.assertContains(res_detail, '4500.00')

        # 5. Verify Update preserves uploaded file without re-uploading
        update_data = {
            'employee': self.emp.pk,
            'hospital': self.hospital.pk,
            'doctor': self.doctor.pk,
            'visit_date': datetime.date.today().strftime('%Y-%m-%d'),
            'visit_type': 'OPD',
            'diagnosis': 'Seasonal Flu & Allergy - Followup',
            'doctor_fee': '2500.00',
            'medicine_cost': '1500.00',
            'diagnostic_cost': '800.00',
            'other_charges': '200.00',
            'status': 'Completed'
        }
        res_update = self.client.post(reverse('visit_update', args=[created_visit.pk]), update_data)
        self.assertEqual(res_update.status_code, 302)

        created_visit.refresh_from_db()
        self.assertEqual(float(created_visit.doctor_fee), 2500.00)
        self.assertEqual(float(created_visit.total_visit_cost), 5000.00)
        # Previous file still persisted!
        self.assertTrue(bool(created_visit.doctor_fee_doc))

    def test_visit_dynamic_repeatable_expenses(self):
        # 1. Create visit with 3 dynamic repeatable rows
        doc_receipt = SimpleUploadedFile("doctor_bill.pdf", b"Doctor fee bill content", content_type="application/pdf")
        lab_report = SimpleUploadedFile("lab_report.pdf", b"Lab diagnostic report content", content_type="application/pdf")

        post_data = {
            'employee': self.emp.pk,
            'hospital': self.hospital.pk,
            'doctor': self.doctor.pk,
            'visit_date': datetime.date.today().strftime('%Y-%m-%d'),
            'visit_type': 'Emergency',
            'diagnosis': 'Acute Abdominal Colic',
            'status': 'Completed',
            # Dynamic rows indices
            'expense_row_index': ['1', '2', '3'],
            'expense_title_1': 'Specialist Surgeon Fee',
            'expense_cost_1': '2500.00',
            'expense_doc_1': doc_receipt,
            'expense_title_2': 'Abdominal Ultrasound & Diagnostics',
            'expense_cost_2': '3500.00',
            'expense_doc_2': lab_report,
            'expense_title_3': 'Emergency Bed Charges',
            'expense_cost_3': '4000.00',
        }

        res_create = self.client.post(reverse('visit_create'), post_data)
        self.assertEqual(res_create.status_code, 302)

        # 2. Verify visit created and total auto-calculated (2500 + 3500 + 4000 = 10000)
        visit = HospitalVisit.objects.filter(diagnosis='Acute Abdominal Colic').first()
        self.assertIsNotNone(visit)
        self.assertEqual(float(visit.total_visit_cost), 10000.00)

        # 3. Verify VisitExpenseItem child records
        items = visit.expense_items.all()
        self.assertEqual(items.count(), 3)
        self.assertEqual(items[0].title, 'Specialist Surgeon Fee')
        self.assertEqual(float(items[0].cost), 2500.00)
        self.assertTrue(bool(items[0].document))
        self.assertEqual(items[1].title, 'Abdominal Ultrasound & Diagnostics')
        self.assertEqual(float(items[1].cost), 3500.00)
        self.assertTrue(bool(items[1].document))
        self.assertEqual(items[2].title, 'Emergency Bed Charges')
        self.assertEqual(float(items[2].cost), 4000.00)

        # 4. Verify Detail page renders dynamic items & receipts
        res_detail = self.client.get(reverse('visit_detail', args=[visit.pk]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'Specialist Surgeon Fee')
        self.assertContains(res_detail, '2500.00')
        self.assertContains(res_detail, 'Abdominal Ultrasound &amp; Diagnostics')
        self.assertContains(res_detail, '3500.00')
        self.assertContains(res_detail, 'Emergency Bed Charges')
        self.assertContains(res_detail, '4000.00')
        self.assertContains(res_detail, '10000.00')
        self.assertContains(res_detail, '3 Items')

        # 5. Test Update: remove row 3, update cost of row 1, add new row 4
        item1 = items[0]
        item2 = items[1]
        update_data = {
            'employee': self.emp.pk,
            'hospital': self.hospital.pk,
            'doctor': self.doctor.pk,
            'visit_date': datetime.date.today().strftime('%Y-%m-%d'),
            'visit_type': 'Emergency',
            'diagnosis': 'Acute Abdominal Colic - Discharged',
            'status': 'Completed',
            'expense_row_index': ['1', '2', '4'],
            # Row 1 updated
            'expense_existing_id_1': item1.pk,
            'expense_title_1': 'Specialist Surgeon Fee - Discounted',
            'expense_cost_1': '2000.00',
            # Row 2 kept as-is (file preserved)
            'expense_existing_id_2': item2.pk,
            'expense_title_2': item2.title,
            'expense_cost_2': '3500.00',
            # Row 3 omitted (deleted by user)
            # Row 4 newly added
            'expense_title_4': 'Post-Op Antibiotics & Pharmacy',
            'expense_cost_4': '1500.00',
        }
        res_update = self.client.post(reverse('visit_update', args=[visit.pk]), update_data)
        self.assertEqual(res_update.status_code, 302)

        visit.refresh_from_db()
        # New total: 2000 + 3500 + 1500 = 7000
        self.assertEqual(float(visit.total_visit_cost), 7000.00)
        updated_items = visit.expense_items.all()
        self.assertEqual(updated_items.count(), 3)
        # Verify item 1 updated
        updated_item1 = updated_items.filter(pk=item1.pk).first()
        self.assertEqual(updated_item1.title, 'Specialist Surgeon Fee - Discounted')
        self.assertEqual(float(updated_item1.cost), 2000.00)
        self.assertTrue(bool(updated_item1.document))  # Preserved!
        # Verify row 3 was deleted
        self.assertFalse(visit.expense_items.filter(title='Emergency Bed Charges').exists())
        # Verify row 4 was created
        self.assertTrue(visit.expense_items.filter(title='Post-Op Antibiotics & Pharmacy').exists())

    def test_employee_mandatory_validation(self):
        from welfare_app.forms.employee_forms import FullEmployeeForm

        # 1. Empty Form must be invalid
        empty_form = FullEmployeeForm(data={})
        self.assertFalse(empty_form.is_valid())
        mandatory_fields = [
            'pl_number', 'name', 'father_name', 'cnic', 'date_of_birth',
            'gender', 'department', 'designation', 'joined_date',
            'employment_type', 'employment_status', 'basic_salary',
            'contact_number', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation'
        ]
        for field in mandatory_fields:
            self.assertIn(field, empty_form.errors, f"Field '{field}' should have validation error when empty")

        # 2. Invalid CNIC format (< 13 digits)
        invalid_data = {
            'pl_number': 'PL-99999',
            'name': 'Test User',
            'father_name': 'Test Father',
            'cnic': '12345',  # invalid
            'date_of_birth': '1990-01-01',
            'gender': 'Male',
            'department': 'Mechanical Assembly',
            'designation': 'Technician',
            'joined_date': '2023-01-01',
            'employment_type': 'Permanent',
            'employment_status': 'Active',
            'basic_salary': '50000',
            'contact_number': '03001234567',
            'address': 'Street 1, Islamabad',
            'emergency_contact_name': 'Father',
            'emergency_contact_phone': '03007654321',
            'emergency_contact_relation': 'Father'
        }
        form_invalid_cnic = FullEmployeeForm(data=invalid_data)
        self.assertFalse(form_invalid_cnic.is_valid())
        self.assertIn('cnic', form_invalid_cnic.errors)

        # 3. Valid submission succeeds
        valid_data = invalid_data.copy()
        valid_data['cnic'] = '37405-1234567-9'
        form_valid = FullEmployeeForm(data=valid_data)
        self.assertTrue(form_valid.is_valid(), form_valid.errors.as_text())
        saved_emp = form_valid.save()
        self.assertEqual(saved_emp.pl_number, 'PL-99999')
        self.assertEqual(saved_emp.cnic, '37405-1234567-9')

    def test_dependent_relationships_include_brother_and_sister(self):
        # 1. Verify choices in model
        relation_keys = [c[0] for c in Dependent.RELATION_CHOICES]
        self.assertIn('Brother', relation_keys)
        self.assertIn('Sister', relation_keys)

        # 2. Create Brother dependent
        brother = Dependent.objects.create(
            employee=self.emp,
            name='Ali Ahmed',
            relationship='Brother',
            gender='Male',
            date_of_birth='2005-06-15',
            status='Active'
        )
        self.assertEqual(brother.relationship, 'Brother')

        # 3. Create Sister dependent
        sister = Dependent.objects.create(
            employee=self.emp,
            name='Zainab Ahmed',
            relationship='Sister',
            gender='Female',
            date_of_birth='2008-09-20',
            status='Active'
        )
        self.assertEqual(sister.relationship, 'Sister')

    def test_inventory_and_supply_module_removed(self):
        # 1. Base navigation should not have Inventory & Supply
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('Inventory & Supply', content)
        self.assertNotIn('href="/inventory/', content)
        self.assertNotIn('href="/procurement/', content)

    def test_bill_dynamic_documentation_and_remarks(self):
        # 1. Test Bill Create Page renders + buttons and dynamic container
        res_form = self.client.get(reverse('bill_create'))
        self.assertEqual(res_form.status_code, 200)
        self.assertContains(res_form, 'id="add-bill-doc-btn"', html=False)
        self.assertContains(res_form, 'id="dynamic-docs-container"', html=False)
        self.assertContains(res_form, '4. Documentation & Voucher Remarks', html=False)


        # 2. Test Bill Creation with primary attachment and 2 dynamic entries
        primary_file = SimpleUploadedFile("hospital_invoice.pdf", b"Primary Hospital Consolidated Invoice", content_type="application/pdf")
        doc1 = SimpleUploadedFile("lab_slip.pdf", b"Diagnostic Lab Slip Receipt", content_type="application/pdf")
        doc2 = SimpleUploadedFile("pharmacy_receipt.png", b"Pharmacy medicine receipt image data", content_type="image/png")

        post_data = {
            'bill_number': 'INV-2026-9901',
            'bill_date': datetime.date.today().strftime('%Y-%m-%d'),
            'category': 'Hospital Bill',
            'hospital': self.hospital.pk,
            'amount': '12500.00',
            'status': 'Pending',
            'payment_status': 'Unpaid',
            'payment_method': 'Bank Transfer',
            'description': 'Consolidated March Panel Hospital Invoice',
            'attachment': primary_file,
            # Dynamic documentation rows
            'bill_doc_index': ['1', '2'],
            'bill_doc_remark_1': 'Detailed Diagnostic Lab Tests Breakdown',
            'bill_doc_file_1': doc1,
            'bill_doc_remark_2': 'Post-Op Pharmacy Disbursed Medication Receipt',
            'bill_doc_file_2': doc2,
        }

        res_create = self.client.post(reverse('bill_create'), post_data)
        self.assertEqual(res_create.status_code, 302)

        # 3. Verify bill created and child BillDocument objects persisted
        bill = Bill.objects.filter(bill_number='INV-2026-9901').first()
        self.assertIsNotNone(bill)
        self.assertEqual(float(bill.amount), 12500.00)
        self.assertTrue(bool(bill.attachment))

        attachments = bill.attachments.all()
        self.assertEqual(attachments.count(), 2)
        self.assertEqual(attachments[0].description, 'Detailed Diagnostic Lab Tests Breakdown')
        self.assertTrue(bool(attachments[0].document))
        self.assertEqual(attachments[1].description, 'Post-Op Pharmacy Disbursed Medication Receipt')
        self.assertTrue(bool(attachments[1].document))

        # 4. Verify Bill List renders dynamic attachments count badge
        res_list = self.client.get(reverse('bill_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'INV-2026-9901')
        self.assertContains(res_list, '+2')

        # 5. Test Bill Edit: update remark 1, remove remark 2, add remark 3
        att1 = attachments[0]
        doc3 = SimpleUploadedFile("consultant_fee_slip.pdf", b"Surgeon fee slip receipt", content_type="application/pdf")

        update_data = {
            'bill_number': 'INV-2026-9901',
            'bill_date': datetime.date.today().strftime('%Y-%m-%d'),
            'category': 'Hospital Bill',
            'hospital': self.hospital.pk,
            'amount': '15000.00',
            'status': 'Approved',
            'payment_status': 'Unpaid',
            'payment_method': 'Bank Transfer',
            'description': 'Consolidated March Panel Hospital Invoice - Verified',
            # Row 1 updated (file preserved)
            'bill_doc_index': ['1', '3'],
            'bill_doc_existing_id_1': att1.pk,
            'bill_doc_remark_1': 'Detailed Diagnostic Lab Tests Breakdown - Audited',
            # Row 2 omitted (deleted)
            # Row 3 newly added
            'bill_doc_remark_3': 'Surgeon Specialist Fee Voucher',
            'bill_doc_file_3': doc3,
        }

        res_update = self.client.post(reverse('bill_update', args=[bill.pk]), update_data)
        self.assertEqual(res_update.status_code, 302)

        bill.refresh_from_db()
        self.assertEqual(float(bill.amount), 15000.00)
        self.assertEqual(bill.status, 'Approved')

        updated_attachments = bill.attachments.all()
        self.assertEqual(updated_attachments.count(), 2)
        # Verify att1 updated and file preserved
        updated_att1 = updated_attachments.filter(pk=att1.pk).first()
        self.assertIsNotNone(updated_att1)
        self.assertEqual(updated_att1.description, 'Detailed Diagnostic Lab Tests Breakdown - Audited')
        self.assertTrue(bool(updated_att1.document))
        # Verify row 2 was removed
        self.assertFalse(bill.attachments.filter(description='Post-Op Pharmacy Disbursed Medication Receipt').exists())
        # Verify row 3 was added
        self.assertTrue(bill.attachments.filter(description='Surgeon Specialist Fee Voucher').exists())






