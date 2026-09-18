import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone


# 1. Department
class Department(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 2. Employee (Extended)
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

    # Existing Fields
    pl_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    father_name = models.CharField(max_length=120, blank=True, null=True)
    department = models.CharField(max_length=120)
    designation = models.CharField(max_length=120, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # New Fields
    cnic = models.CharField(max_length=15, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    grade_scale = models.CharField(max_length=10, blank=True, null=True)
    employment_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    bank_name = models.CharField(max_length=120, blank=True, null=True)
    bank_account = models.CharField(max_length=100, blank=True, null=True)
    bank_iban = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def total_medical_expense(self):
        total = self.medical_records.aggregate(total=models.Sum('total_expense'))['total']
        return total or 0

    def __str__(self):
        return f"{self.pl_number} - {self.name}"


# Existing MedicalRecord
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


# 3. Dependent
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


# 4. Hospital
class Hospital(models.Model):
    TYPE_CHOICES = [
        ('Government', 'Government'),
        ('Private', 'Private'),
        ('Semi-Government', 'Semi-Government'),
        ('Military', 'Military'),
        ('Clinic', 'Clinic'),
    ]
    PANEL_CHOICES = [
        ('Panel', 'Panel'),
        ('Non-Panel', 'Non-Panel'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=255)
    hospital_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    panel_status = models.CharField(max_length=50, choices=PANEL_CHOICES, default='Non-Panel')
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_contract_active(self):
        if self.contract_start_date and self.contract_end_date:
            today = timezone.now().date()
            return self.contract_start_date <= today <= self.contract_end_date
        return False

    def __str__(self):
        return self.name


# 5. Doctor
class Doctor(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=120)
    specialization = models.CharField(max_length=150, blank=True, null=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name='doctors', blank=True, null=True)
    contact = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.specialization or 'General'}"


# 6. HospitalVisit
class HospitalVisit(models.Model):
    VISIT_TYPE_CHOICES = [
        ('OPD', 'OPD'),
        ('Emergency', 'Emergency'),
        ('Admission', 'Admission'),
        ('Follow-up', 'Follow-up'),
        ('Lab', 'Lab'),
        ('Consultation', 'Consultation'),
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
    visit_date = models.DateField()
    visit_type = models.CharField(max_length=50, choices=VISIT_TYPE_CHOICES, default='OPD')
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    lab_tests = models.TextField(blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True)
    admission_date = models.DateField(blank=True, null=True)
    discharge_date = models.DateField(blank=True, null=True)
    room_ward = models.CharField(max_length=100, blank=True, null=True)
    followup_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def duration_days(self):
        if self.admission_date and self.discharge_date:
            return (self.discharge_date - self.admission_date).days
        return 0

    def __str__(self):
        return f"Visit on {self.visit_date} for {self.dependent.name if self.dependent else self.employee.name}"


# 7. MedicalClaim
class MedicalClaim(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
    ]
    CLAIM_STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
        ('Paid', 'Paid'),
    ]

    claim_number = models.CharField(max_length=50, unique=True, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='medical_claims')
    dependent = models.ForeignKey(Dependent, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    hospital_visit = models.ForeignKey(HospitalVisit, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, related_name='medical_claims')
    claim_date = models.DateField(default=timezone.now)
    bill_number = models.CharField(max_length=100, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    total_bill_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employee_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    welfare_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    claim_status = models.CharField(max_length=50, choices=CLAIM_STATUS_CHOICES, default='Draft')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_claims')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_claims')

    def save(self, *args, **kwargs):
        if not self.claim_number:
            last_claim = MedicalClaim.objects.order_by('-id').first()
            if last_claim:
                last_id = last_claim.id
                self.claim_number = f"CLM-{last_id + 1:04d}"
            else:
                self.claim_number = "CLM-0001"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.claim_number} - {self.employee.name}"


# 8. ClaimExpenseItem
class ClaimExpenseItem(models.Model):
    CATEGORY_CHOICES = [
        ('Consultation', 'Consultation'),
        ('Medicine', 'Medicine'),
        ('Laboratory', 'Laboratory'),
        ('X-Ray', 'X-Ray'),
        ('Ultrasound', 'Ultrasound'),
        ('Surgery', 'Surgery'),
        ('Room Charges', 'Room Charges'),
        ('Emergency', 'Emergency'),
        ('Other', 'Other'),
    ]

    claim = models.ForeignKey(MedicalClaim, on_delete=models.CASCADE, related_name='expense_items')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} for {self.claim.claim_number}"


# 9. ApprovalWorkflow
class ApprovalWorkflow(models.Model):
    STAGE_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Welfare Review', 'Welfare Review'),
        ('Manager Approval', 'Manager Approval'),
        ('Finance Verification', 'Finance Verification'),
        ('Payment', 'Payment'),
        ('Completed', 'Completed'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Returned', 'Returned'),
    ]

    claim = models.ForeignKey(MedicalClaim, on_delete=models.CASCADE, related_name='approvals')
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    action_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['action_date']

    def __str__(self):
        return f"{self.stage} - {self.status} for {self.claim.claim_number}"


# 10. Bill
class Bill(models.Model):
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

    bill_number = models.CharField(max_length=100, unique=True)
    bill_date = models.DateField()
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    attachment = models.FileField(upload_to='bills/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.bill_number


# 11. Budget
class Budget(models.Model):
    CATEGORY_CHOICES = [
        ('Medical', 'Medical'),
        ('Operational', 'Operational'),
        ('Emergency', 'Emergency'),
        ('Other', 'Other'),
    ]

    year = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'department', 'category')

    @property
    def used_amount(self):
        # Implementation for sum of approved claims logic would typically go here
        return 0

    @property
    def remaining_amount(self):
        return self.allocated_amount - self.used_amount

    @property
    def utilization_percentage(self):
        if self.allocated_amount > 0:
            return (self.used_amount / self.allocated_amount) * 100
        return 0

    def __str__(self):
        return f"{self.category} Budget {self.year}"


# 12. FinanceTransaction
class FinanceTransaction(models.Model):
    TYPE_CHOICES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
        ('Payment', 'Payment'),
        ('Refund', 'Refund'),
    ]
    METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Online', 'Online'),
    ]

    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=METHOD_CHOICES, default='Bank Transfer')
    related_claim = models.ForeignKey(MedicalClaim, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


# 15. Supplier (Defined before Medicine to resolve FK)
class Supplier(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 13. Medicine
class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Syrup', 'Syrup'),
        ('Injection', 'Injection'),
        ('Cream', 'Cream'),
        ('Drops', 'Drops'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
            return timezone.now().date() <= self.expiry_date <= timezone.now().date() + datetime.timedelta(days=90)
        return False

    def __str__(self):
        return self.name


# 14. MedicineTransaction
class MedicineTransaction(models.Model):
    TYPE_CHOICES = [
        ('Stock In', 'Stock In'),
        ('Stock Out', 'Stock Out'),
        ('Adjustment', 'Adjustment'),
        ('Issue', 'Issue'),
        ('Return', 'Return'),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk: # Only on creation
            if self.transaction_type in ['Stock In', 'Return']:
                self.medicine.quantity += self.quantity
            elif self.transaction_type in ['Stock Out', 'Issue']:
                self.medicine.quantity -= self.quantity
            # For adjustment, logic might differ based on exact requirements, ignoring for basic implementation
            self.medicine.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} of {self.quantity} {self.medicine.name}"


# 16. PurchaseRequest
class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Ordered', 'Ordered'),
        ('Completed', 'Completed'),
    ]

    request_number = models.CharField(max_length=50, unique=True, editable=False)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchase_requests')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    items_description = models.TextField()
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.request_number:
            last_pr = PurchaseRequest.objects.order_by('-id').first()
            if last_pr:
                self.request_number = f"PR-{last_pr.id + 1:04d}"
            else:
                self.request_number = "PR-0001"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.request_number


# 17. PurchaseOrder
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Acknowledged', 'Acknowledged'),
        ('Received', 'Received'),
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
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    expected_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            if last_po:
                self.order_number = f"PO-{last_po.id + 1:04d}"
            else:
                self.order_number = "PO-0001"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


# 18. Document
class Document(models.Model):
    TYPE_CHOICES = [
        ('CNIC', 'CNIC'),
        ('Medical Report', 'Medical Report'),
        ('Bill', 'Bill'),
        ('Receipt', 'Receipt'),
        ('Prescription', 'Prescription'),
        ('Contract', 'Contract'),
        ('Certificate', 'Certificate'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Other')
    content_type_name = models.CharField(max_length=100)  # e.g., 'employee', 'claim'
    object_id = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 19. Notification
class Notification(models.Model):
    TYPE_CHOICES = [
        ('Info', 'Info'),
        ('Success', 'Success'),
        ('Warning', 'Warning'),
        ('Error', 'Error'),
        ('Approval', 'Approval'),
        ('Claim', 'Claim'),
        ('Payment', 'Payment'),
        ('Stock', 'Stock'),
        ('Budget', 'Budget'),
        ('Contract', 'Contract'),
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


# 20. AuditLog
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('Created', 'Created'),
        ('Updated', 'Updated'),
        ('Deleted', 'Deleted'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Submitted', 'Submitted'),
        ('Paid', 'Paid'),
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
            user=user,
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


# 21. UserProfile
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('HR Officer', 'HR Officer'),
        ('Welfare Officer', 'Welfare Officer'),
        ('Medical Officer', 'Medical Officer'),
        ('Finance Officer', 'Finance Officer'),
        ('Manager', 'Manager'),
        ('Inventory Officer', 'Inventory Officer'),
        ('Employee', 'Employee'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Employee')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_admin(self):
        return self.role == 'Admin'

    def has_module_access(self, module_name):
        # Implement specific access logic based on role here
        if self.is_admin:
            return True
        return False

    def __str__(self):
        return f"{self.user.username} Profile"
