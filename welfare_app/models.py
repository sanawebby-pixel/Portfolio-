import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone


# 1. Department
class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# 2. Benefit / Welfare Rule Setting
class BenefitRule(models.Model):
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    grade_scale = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. All Scales, Scale-16+, etc.")
    annual_medical_limit = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    opd_consultation_limit = models.DecimalField(max_digits=12, decimal_places=2, default=3000.00)
    lab_coverage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="Percentage covered (0-100)")
    medicine_coverage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="Percentage covered (0-100)")
    room_per_day_limit = models.DecimalField(max_digits=12, decimal_places=2, default=6000.00)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Limit: Rs. {self.annual_medical_limit:,.0f})"


# 3. Employee (Extended)
class Employee(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Retired', 'Retired'),
        ('Terminated', 'Terminated'),
        ('Suspended', 'Suspended'),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ('Permanent', 'Permanent'),
        ('Contract', 'Contract'),
        ('Probation', 'Probation'),
        ('Temporary', 'Temporary'),
        ('Daily Wage', 'Daily Wage'),
        ('Intern', 'Intern'),
        ('Trainee / Apprentice', 'Trainee / Apprentice'),
        ('Other', 'Other'),
    ]

    # Existing Core Fields
    pl_number = models.CharField(max_length=50, unique=True, verbose_name="Employee ID / PL#")
    name = models.CharField(max_length=120, verbose_name="Full Name")
    father_name = models.CharField(max_length=120, blank=True, null=True, verbose_name="Father/Guardian Name")
    department = models.CharField(max_length=120)
    designation = models.CharField(max_length=120, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Extended ERP Fields
    cnic = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="CNIC")
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    grade_scale = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pay Grade / Scale")
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default='Permanent')
    employment_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    bank_name = models.CharField(max_length=120, blank=True, null=True)
    bank_account = models.CharField(max_length=100, blank=True, null=True)
    bank_iban = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def total_medical_expense(self):
        records_total = self.medical_records.aggregate(total=models.Sum('total_expense'))['total'] or 0
        claims_total = self.medical_claims.aggregate(total=models.Sum('total_bill_amount'))['total'] or 0
        return max(float(records_total), float(claims_total))

    def paid_medical_expense(self):
        records_paid = self.medical_records.filter(status='Paid').aggregate(total=models.Sum('total_expense'))['total'] or 0
        claims_paid = self.medical_claims.filter(payment_status='Paid').aggregate(total=models.Sum('approved_amount'))['total'] or 0
        return max(float(records_paid), float(claims_paid))

    def pending_claim_amount(self):
        return float(self.medical_claims.filter(claim_status__in=['New', 'Pending', 'Under Review']).aggregate(total=models.Sum('total_bill_amount'))['total'] or 0)

    def approved_claim_amount(self):
        return float(self.medical_claims.filter(claim_status__in=['Approved', 'Partially Approved', 'Paid']).aggregate(total=models.Sum('approved_amount'))['total'] or 0)

    def rejected_claim_amount(self):
        return float(self.medical_claims.filter(claim_status='Rejected').aggregate(total=models.Sum('total_bill_amount'))['total'] or 0)

    def __str__(self):
        return f"{self.pl_number} - {self.name}"


# 4. Existing MedicalRecord (Preserved for backward compatibility)
class MedicalRecord(models.Model):
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Processed', 'Processed'),
        ('Pending', 'Pending'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='medical_records')
    treatment_date = models.DateField()
    hospital = models.CharField(max_length=200)
    doctor = models.CharField(max_length=120, blank=True, null=True)
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    doctor_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lab_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medicine_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    admission_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bill_no = models.CharField(max_length=80, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Paid')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_expense = (
            self.doctor_fee + self.lab_fee + self.medicine_fee +
            self.admission_fee + self.other_fee
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bill_no or 'No Bill'} - {self.employee.name}"


# 5. Dependent / Family Members
class Dependent(models.Model):
    RELATION_CHOICES = [
        ('Spouse', 'Spouse'),
        ('Son', 'Son'),
        ('Daughter', 'Daughter'),
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=50, choices=RELATION_CHOICES)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    cnic_bform = models.CharField(max_length=20, blank=True, null=True)
    contact = models.CharField(max_length=50, blank=True, null=True)
    medical_eligible = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.relationship} of {self.employee.name})"


# 6. Hospital / Clinic Master Data
class Hospital(models.Model):
    TYPE_CHOICES = [
        ('Government', 'Government Hospital'),
        ('Private', 'Private Hospital'),
        ('Semi-Government', 'Semi-Government'),
        ('Military', 'Military / Armed Forces'),
        ('Clinic', 'Clinic / Diagnostic Center'),
    ]
    PANEL_CHOICES = [
        ('Panel', 'Panel Hospital (Contracted)'),
        ('Non-Panel', 'Non-Panel Hospital'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]

    hospital_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    name = models.CharField(max_length=255)
    hospital_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Private')
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    contact_person = models.CharField(max_length=120, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    panel_status = models.CharField(max_length=50, choices=PANEL_CHOICES, default='Panel')
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def is_contract_active(self):
        if self.contract_start_date and self.contract_end_date:
            today = timezone.now().date()
            return self.contract_start_date <= today <= self.contract_end_date
        return True

    def save(self, *args, **kwargs):
        if not self.hospital_code:
            last = Hospital.objects.order_by('-id').first()
            self.hospital_code = f"HOSP-{((last.id if last else 0) + 1):03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.city or 'General'})"


# 7. Doctor Master Data
class Doctor(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=120)
    specialization = models.CharField(max_length=150, blank=True, null=True, help_text="e.g. Cardiology, Orthopedics, General Physician")
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name='doctors', blank=True, null=True)
    contact = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="PMC / PMDC Reg #")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.specialization or 'General'} ({self.hospital.name if self.hospital else 'Independent'})"


# 8. Hospital Visit / Medical Consultation Log
class HospitalVisit(models.Model):
    VISIT_TYPE_CHOICES = [
        ('OPD', 'OPD / Outpatient'),
        ('Emergency', 'Emergency Room'),
        ('Admission', 'Hospital Admission / Inpatient'),
        ('Follow-up', 'Follow-up Consultation'),
        ('Lab Test', 'Laboratory & Diagnostics'),
        ('Consultation', 'Specialist Consultation'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Completed', 'Completed'),
        ('Follow-up Required', 'Follow-up Required'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='hospital_visits')
    dependent = models.ForeignKey(Dependent, on_delete=models.SET_NULL, blank=True, null=True, related_name='hospital_visits')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, blank=True, null=True, related_name='visits')
    hospital_name = models.CharField(max_length=200, blank=True, null=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, related_name='visits')
    doctor_name = models.CharField(max_length=120, blank=True, null=True)
    department_specialization = models.CharField(max_length=120, blank=True, null=True)
    visit_date = models.DateField(default=timezone.now)
    visit_type = models.CharField(max_length=50, choices=VISIT_TYPE_CHOICES, default='OPD')
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    lab_tests = models.TextField(blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True)
    total_visit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    attached_document = models.FileField(upload_to='visits/', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    admission_date = models.DateField(blank=True, null=True)
    discharge_date = models.DateField(blank=True, null=True)
    room_ward = models.CharField(max_length=100, blank=True, null=True)
    followup_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']

    @property
    def duration_days(self):
        if self.admission_date and self.discharge_date:
            return max(1, (self.discharge_date - self.admission_date).days)
        return 0

    def __str__(self):
        patient = self.dependent.name if self.dependent else self.employee.name
        return f"Visit ({self.visit_date}) - {patient}"


# 9. Medical Claim (Main Core Module)
class MedicalClaim(models.Model):
    CLAIM_STATUS_CHOICES = [
        ('New', 'New'),
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
        ('Paid', 'Paid'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
    ]
    CLAIM_TYPE_CHOICES = [
        ('OPD Consultation', 'OPD Consultation'),
        ('Emergency Treatment', 'Emergency Treatment'),
        ('Hospitalization / Surgery', 'Hospitalization / Surgery'),
        ('Diagnostic / Lab Tests', 'Diagnostic / Lab Tests'),
        ('Prescription Medicine', 'Prescription Medicine'),
        ('Maternity / Dental / Optical', 'Maternity / Dental / Optical'),
        ('Other Medical Claim', 'Other Medical Claim'),
    ]

    claim_number = models.CharField(max_length=50, unique=True, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='medical_claims')
    dependent = models.ForeignKey(Dependent, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    hospital_visit = models.ForeignKey(HospitalVisit, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    claim_type = models.CharField(max_length=100, choices=CLAIM_TYPE_CHOICES, default='OPD Consultation')
    claim_date = models.DateField(default=timezone.now)
    treatment_date = models.DateField(default=timezone.now)
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    bill_number = models.CharField(max_length=100, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)

    # Detailed Itemized Fee Breakdown Fields
    doctor_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    doctor_dues = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    lab_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    medicine_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    admission_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    procedure_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    other_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Auto-calculated Totals
    total_bill_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    claimable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    employee_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    welfare_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    rejected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Status Workflow (Default is Pending / Unpaid - MUST NEVER default to Paid)
    claim_status = models.CharField(max_length=50, choices=CLAIM_STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')

    supporting_documents = models.FileField(upload_to='claims/', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_claims')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_claims')

    class Meta:
        ordering = ['-claim_date', '-created_at']

    def calculate_totals(self):
        self.total_bill_amount = (
            (self.doctor_fee or 0) +
            (self.doctor_dues or 0) +
            (self.lab_fee or 0) +
            (self.medicine_fee or 0) +
            (self.admission_fee or 0) +
            (self.procedure_fee or 0) +
            (self.other_fee or 0)
        )
        if not self.claimable_amount or self.claimable_amount == 0:
            self.claimable_amount = self.total_bill_amount - (self.employee_contribution or 0)
        if not self.welfare_contribution or self.welfare_contribution == 0:
            self.welfare_contribution = self.claimable_amount

    @property
    def remaining_payable_amount(self):
        return max(0.0, float(self.approved_amount) - float(self.paid_amount))

    def save(self, *args, **kwargs):
        if not self.claim_number:
            last_claim = MedicalClaim.objects.order_by('-id').first()
            last_id = last_claim.id if last_claim else 0
            self.claim_number = f"CLM-{last_id + 1:04d}"
        self.calculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.claim_number} - {self.employee.name} (Rs. {self.total_bill_amount:,.0f})"


# 10. Claim Expense Items
class ClaimExpenseItem(models.Model):
    CATEGORY_CHOICES = [
        ('Doctor Fee', 'Doctor Fee'),
        ('Doctor Dues', 'Doctor Dues'),
        ('Laboratory', 'Laboratory / Diagnostic'),
        ('Medicine', 'Medicine & Pharmacy'),
        ('Admission', 'Admission / Hospital Stay'),
        ('Surgery', 'Surgery / Procedure'),
        ('Other', 'Other Expense'),
    ]

    claim = models.ForeignKey(MedicalClaim, on_delete=models.CASCADE, related_name='expense_items')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: Rs. {self.amount:,.0f} for {self.claim.claim_number}"


# 11. Centralized Approval Workflow Log
class ApprovalWorkflow(models.Model):
    STAGE_CHOICES = [
        ('Submitted', 'Submitted for Review'),
        ('Welfare Review', 'Welfare Officer Review'),
        ('Manager Approval', 'Factory Manager Approval'),
        ('Finance Verification', 'Finance & Treasury Verification'),
        ('Payment', 'Payment Processing'),
        ('Completed', 'Completed / Disbursed'),
        ('Rejected', 'Rejected'),
        ('Returned', 'Returned for Correction'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Returned', 'Returned for Correction'),
    ]

    claim = models.ForeignKey(MedicalClaim, on_delete=models.CASCADE, related_name='approvals')
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    action_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['action_date']

    def __str__(self):
        return f"{self.stage} ({self.status}) for {self.claim.claim_number}"


# 12. Claim Payment Record
class ClaimPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer / Online'),
        ('Cheque', 'Bank Cheque'),
        ('Cash', 'Cash Disbursement'),
        ('Payroll Credit', 'Payroll Allowance Addition'),
    ]

    payment_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    claim = models.ForeignKey(MedicalClaim, on_delete=models.CASCADE, related_name='payments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payments')
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Bank Transfer')
    account = models.CharField(max_length=120, blank=True, null=True, help_text="e.g. Welfare Treasury HBL A/C 0042")
    transaction_reference = models.CharField(max_length=120, blank=True, null=True, verbose_name="Tx / Cheque #")
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    receipt_attachment = models.FileField(upload_to='payments/', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.payment_number:
            last = ClaimPayment.objects.order_by('-id').first()
            self.payment_number = f"PAY-{((last.id if last else 0) + 1):04d}"
        super().save(*args, **kwargs)

        # Update claim paid amount and payment status
        claim = self.claim
        total_paid = claim.payments.aggregate(total=models.Sum('payment_amount'))['total'] or 0
        claim.paid_amount = total_paid
        if total_paid >= claim.approved_amount and claim.approved_amount > 0:
            claim.payment_status = 'Paid'
            claim.claim_status = 'Paid'
        elif total_paid > 0:
            claim.payment_status = 'Partially Paid'
        else:
            claim.payment_status = 'Unpaid'
        claim.save()

    def __str__(self):
        return f"{self.payment_number} - Rs. {self.payment_amount:,.0f} to {self.employee.name}"


# 13. Bills & General Expenses
class Bill(models.Model):
    CATEGORY_CHOICES = [
        ('Doctor Fee', 'Doctor Fee'),
        ('Doctor Dues', 'Doctor Dues'),
        ('Lab Test', 'Lab Test & Diagnostics'),
        ('Medicine', 'Medicine & Pharmacy Supply'),
        ('Admission', 'Admission & Hospitalization'),
        ('Procedure', 'Surgical / Medical Procedure'),
        ('Hospital Bill', 'Hospital Panel Monthly Bill'),
        ('Other Medical Expense', 'Other Medical Expense'),
        ('Administrative Welfare Expense', 'Administrative Welfare Expense'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Cash', 'Cash'),
        ('Online', 'Online'),
    ]

    bill_number = models.CharField(max_length=100, unique=True, verbose_name="Invoice / Bill #")
    bill_date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Hospital Bill')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Bank Transfer')
    attachment = models.FileField(upload_to='bills/', blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bills')

    class Meta:
        ordering = ['-bill_date', '-created_at']

    def __str__(self):
        return f"{self.bill_number} - Rs. {self.amount:,.0f} ({self.category})"


# 14. Departmental Budgets
class Budget(models.Model):
    CATEGORY_CHOICES = [
        ('Medical', 'Medical Welfare Fund'),
        ('Operational', 'Operational Welfare'),
        ('Emergency', 'Emergency / Critical Health Fund'),
        ('Pharmacy', 'Pharmacy & Medicine Fund'),
        ('Other', 'Other Welfare Allocation'),
    ]

    year = models.IntegerField(default=2026)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Medical')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'department', 'category')
        ordering = ['-year', 'department__name']

    @property
    def used_amount(self):
        if self.department:
            emp_ids = Employee.objects.filter(department__iexact=self.department.name).values_list('id', flat=True)
            claims_sum = MedicalClaim.objects.filter(
                employee_id__in=emp_ids,
                claim_date__year=self.year,
                claim_status__in=['Approved', 'Partially Approved', 'Paid']
            ).aggregate(total=models.Sum('approved_amount'))['total'] or 0
            return float(claims_sum)
        else:
            all_claims = MedicalClaim.objects.filter(
                claim_date__year=self.year,
                claim_status__in=['Approved', 'Partially Approved', 'Paid']
            ).aggregate(total=models.Sum('approved_amount'))['total'] or 0
            return float(all_claims)

    @property
    def remaining_amount(self):
        return max(0.0, float(self.allocated_amount) - self.used_amount)

    @property
    def utilization_percentage(self):
        if self.allocated_amount > 0:
            return min(100.0, (self.used_amount / float(self.allocated_amount)) * 100)
        return 0.0

    def __str__(self):
        dept_name = self.department.name if self.department else 'General Welfare'
        return f"{dept_name} {self.category} Budget {self.year}: Rs. {self.allocated_amount:,.0f}"


# 15. Finance & Treasury Transactions
class FinanceTransaction(models.Model):
    TYPE_CHOICES = [
        ('Income', 'Receipt / Allocation (Income)'),
        ('Expense', 'Disbursement / Expense'),
        ('Payment', 'Medical Claim Payment'),
        ('Refund', 'Refund / Credit Note'),
    ]
    METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Cash', 'Cash'),
        ('Online', 'Online Banking / RTGS'),
    ]

    transaction_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=METHOD_CHOICES, default='Bank Transfer')
    account = models.CharField(max_length=120, blank=True, null=True, default="Welfare Main Account (HBL)")
    related_claim = models.ForeignKey(MedicalClaim, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    attachment = models.FileField(upload_to='finance/', blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            last = FinanceTransaction.objects.order_by('-id').first()
            self.transaction_id = f"TRX-{((last.id if last else 0) + 1):05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id}: {self.transaction_type} of Rs. {self.amount:,.0f}"


# 16. Supplier Master Data
class Supplier(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    supplier_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    ntn_registration = models.CharField(max_length=100, blank=True, null=True, verbose_name="NTN / STRN #")
    payment_terms = models.CharField(max_length=100, blank=True, null=True, default="Net 30 Days")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.supplier_id:
            last = Supplier.objects.order_by('-id').first()
            self.supplier_id = f"SUP-{((last.id if last else 0) + 1):03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# 17. Medicine & Pharmacy Inventory
class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Syrup', 'Syrup / Suspension'),
        ('Injection', 'Injection / IV Infusion'),
        ('Cream / Ointment', 'Cream / Ointment'),
        ('Eye/Ear Drops', 'Eye/Ear Drops'),
        ('Inhaler', 'Inhaler / Spray'),
        ('Surgical Supply', 'Surgical Supply / Bandage'),
        ('Other', 'Other Pharmacy Item'),
    ]
    UNIT_CHOICES = [
        ('Pack', 'Pack / Box'),
        ('Bottle', 'Bottle'),
        ('Strip', 'Strip'),
        ('Tablet', 'Tablet'),
        ('Vial', 'Vial / Ampoule'),
        ('Tube', 'Tube'),
        ('Piece', 'Piece'),
    ]

    medicine_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Tablet')
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='Pack')
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Unit Cost (Rs.)")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def stock_value(self):
        cost = self.unit_cost if self.unit_cost > 0 else self.purchase_price
        return float(self.quantity) * float(cost)

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            today = timezone.now().date()
            return today <= self.expiry_date <= today + datetime.timedelta(days=90)
        return False

    def save(self, *args, **kwargs):
        if not self.medicine_id:
            last = Medicine.objects.order_by('-id').first()
            self.medicine_id = f"MED-{((last.id if last else 0) + 1):04d}"
        if not self.unit_cost and self.purchase_price:
            self.unit_cost = self.purchase_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit} in stock)"


# 18. Medicine Stock Transactions
class MedicineTransaction(models.Model):
    TYPE_CHOICES = [
        ('Stock In', 'Stock In (Purchase/Receipt)'),
        ('Stock Out', 'Stock Out (Dispensed/Issued)'),
        ('Adjustment', 'Stock Adjustment'),
        ('Return', 'Return to Supplier'),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="PO / Invoice / Rx #")
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.transaction_type == 'Stock In':
                self.medicine.quantity += self.quantity
            elif self.transaction_type in ['Stock Out', 'Return']:
                self.medicine.quantity = max(0, self.medicine.quantity - self.quantity)
            elif self.transaction_type == 'Adjustment':
                self.medicine.quantity = max(0, self.quantity)
            self.medicine.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} of {self.quantity} {self.medicine.name}"


# 19. Purchase Requests
class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Ordered', 'Ordered'),
        ('Completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent / Priority'),
        ('Emergency', 'Emergency'),
    ]

    request_number = models.CharField(max_length=50, unique=True, editable=False)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchase_requests')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=100, default='Medicines & Medical Consumables')
    item_name = models.CharField(max_length=200, default='Medical Consumables')
    quantity = models.IntegerField(default=1)
    items_description = models.TextField()
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Normal')
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending Approval')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_date = models.DateField(blank=True, null=True)
    invoice_attachment = models.FileField(upload_to='procurement/', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.request_number:
            last_pr = PurchaseRequest.objects.order_by('-id').first()
            self.request_number = f"PR-{((last_pr.id if last_pr else 0) + 1):04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_number} - {self.item_name} (Rs. {self.estimated_amount:,.0f})"


# 20. Purchase Orders
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Ordered', 'Ordered / Issued'),
        ('Acknowledged', 'Acknowledged by Vendor'),
        ('Received', 'Received & Stocked'),
        ('Cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True)
    items_description = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Ordered')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    expected_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            self.order_number = f"PO-{((last_po.id if last_po else 0) + 1):04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} to {self.supplier.name} (Rs. {self.total_amount:,.0f})"


# 21. General Documents & Attachments
class Document(models.Model):
    TYPE_CHOICES = [
        ('CNIC', 'CNIC / National Identity Card'),
        ('Medical Report', 'Medical Report / Discharge Summary'),
        ('Bill / Invoice', 'Bill / Invoice / Receipt'),
        ('Prescription', 'Doctor Prescription'),
        ('Hospital Contract', 'Hospital Panel Contract'),
        ('Welfare Policy', 'Welfare Policy Document'),
        ('Other', 'Other Attachment'),
    ]

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Other')
    content_type_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# 22. System Notifications
class Notification(models.Model):
    TYPE_CHOICES = [
        ('Info', 'Info'),
        ('Success', 'Success'),
        ('Warning', 'Warning'),
        ('Error', 'Error'),
        ('Approval', 'Approval Request'),
        ('Claim', 'Medical Claim'),
        ('Payment', 'Payment Disbursed'),
        ('Stock', 'Low Stock Warning'),
        ('Budget', 'Budget Alert'),
        ('Contract', 'Hospital Contract Notice'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Info')
    is_read = models.BooleanField(default=False)
    related_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


# 23. Audit Logs
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('Created', 'Created'),
        ('Updated', 'Updated'),
        ('Deleted', 'Deleted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Submitted', 'Submitted'),
        ('Paid', 'Payment Recorded'),
        ('Login', 'Login'),
        ('Logout', 'Logout'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    record_repr = models.CharField(max_length=255, blank=True, null=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    @classmethod
    def log(cls, user, action, module, record_id='', record_repr='', old_values=None, new_values=None, ip_address=None):
        return cls.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            module=module,
            record_id=record_id,
            record_repr=record_repr,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address
        )

    def __str__(self):
        return f"{self.action} on {self.module} by {self.user}"


# 24. Extended User Profile & Roles
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin (Full Access)'),
        ('Welfare Officer', 'Welfare Officer (Claims, Visits, Hospitals, Reports)'),
        ('HR Staff', 'HR Staff (Employees & HR Reports)'),
        ('Finance Officer', 'Finance Officer (Payments, Budgets, Treasury, Bills)'),
        ('Approver', 'Approver (Approvals & Claim Review)'),
        ('Viewer', 'Viewer (Read-only Access)'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Welfare Officer')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_admin(self):
        return self.role == 'Admin' or self.user.is_superuser

    def __str__(self):
        return f"{self.user.username} ({self.role})"
