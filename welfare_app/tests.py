import datetime
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse

from welfare_app.models import (
    Department, Employee, Dependent, Hospital, Doctor, HospitalVisit,
    MedicalClaim, ClaimExpenseItem, ClaimPayment, ApprovalWorkflow,
    Bill, Budget, Medicine, Supplier, UserProfile
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
        # 1. Test Form Render
        res_form = self.client.get(reverse('visit_create'))
        self.assertEqual(res_form.status_code, 200)
        self.assertContains(res_form, 'id_doctor_fee')
        self.assertContains(res_form, 'id_medicine_cost')
        self.assertContains(res_form, 'id_diagnostic_cost')
        self.assertContains(res_form, 'id_other_charges')
        self.assertContains(res_form, 'id_total_visit_cost')
        self.assertContains(res_form, 'Consultation Fee / Doctor Fee')
        self.assertContains(res_form, 'Medicine Cost')
        self.assertContains(res_form, 'Diagnostic & Lab Tests Cost', html=False)
        self.assertContains(res_form, 'Other Hospital Charges / Miscellaneous')
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



