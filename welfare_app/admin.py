from django.contrib import admin
from .models import (
    Department, Employee, Dependent, Hospital, Doctor, HospitalVisit,
    MedicalRecord, MedicalClaim, ClaimExpenseItem, ApprovalWorkflow,
    Bill, Budget, FinanceTransaction, Medicine, MedicineTransaction,
    Supplier, PurchaseRequest, PurchaseOrder, Document, Notification,
    AuditLog, UserProfile
)


class ClaimExpenseItemInline(admin.TabularInline):
    model = ClaimExpenseItem
    extra = 1


class DependentInline(admin.TabularInline):
    model = Dependent
    extra = 1


class ApprovalWorkflowInline(admin.TabularInline):
    model = ApprovalWorkflow
    extra = 0
    readonly_fields = ('action_date',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('pl_number', 'name', 'department', 'designation', 'employment_status', 'joined_date')
    search_fields = ('pl_number', 'name', 'cnic', 'email', 'contact_number')
    list_filter = ('department', 'employment_status')
    inlines = [DependentInline]


@admin.register(Dependent)
class DependentAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee', 'relationship', 'date_of_birth', 'medical_eligible', 'status')
    search_fields = ('name', 'employee__name', 'employee__pl_number', 'cnic_bform')
    list_filter = ('relationship', 'medical_eligible', 'status')


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital_type', 'city', 'contact_number', 'panel_status', 'status')
    search_fields = ('name', 'city', 'contact_number', 'email')
    list_filter = ('hospital_type', 'panel_status', 'status')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'hospital', 'contact', 'status')
    search_fields = ('name', 'specialization', 'registration_number', 'contact')
    list_filter = ('hospital', 'status')


@admin.register(HospitalVisit)
class HospitalVisitAdmin(admin.ModelAdmin):
    list_display = ('employee', 'dependent', 'hospital', 'doctor', 'visit_date', 'visit_type', 'status')
    search_fields = ('employee__name', 'employee__pl_number', 'diagnosis', 'hospital__name', 'doctor__name')
    list_filter = ('visit_type', 'status', 'visit_date')
    date_hierarchy = 'visit_date'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'employee', 'hospital', 'doctor', 'treatment_date', 'total_expense', 'status')
    search_fields = ('bill_no', 'employee__name', 'employee__pl_number', 'hospital', 'doctor', 'diagnosis')
    list_filter = ('status', 'treatment_date')
    date_hierarchy = 'treatment_date'


@admin.register(MedicalClaim)
class MedicalClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_number', 'employee', 'claim_date', 'total_bill_amount', 'eligible_amount', 'approved_amount', 'claim_status', 'payment_status')
    search_fields = ('claim_number', 'employee__name', 'employee__pl_number', 'bill_number')
    list_filter = ('claim_status', 'payment_status', 'claim_date')
    date_hierarchy = 'claim_date'
    inlines = [ClaimExpenseItemInline, ApprovalWorkflowInline]
    readonly_fields = ('claim_number', 'created_at', 'updated_at')


@admin.register(ClaimExpenseItem)
class ClaimExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('claim', 'category', 'description', 'amount', 'eligible_amount', 'approved_amount')
    search_fields = ('claim__claim_number', 'description')
    list_filter = ('category',)


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ('claim', 'stage', 'approver', 'status', 'action_date')
    search_fields = ('claim__claim_number', 'approver__username', 'remarks')
    list_filter = ('stage', 'status', 'action_date')
    date_hierarchy = 'action_date'


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'bill_date', 'hospital', 'vendor_name', 'employee', 'amount', 'status', 'payment_status')
    search_fields = ('bill_number', 'vendor_name', 'employee__name')
    list_filter = ('status', 'payment_status', 'bill_date')
    date_hierarchy = 'bill_date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('year', 'department', 'category', 'allocated_amount', 'is_active')
    search_fields = ('year', 'department__name', 'category')
    list_filter = ('year', 'category', 'is_active')


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'category', 'reference_number', 'payment_method', 'date', 'created_by')
    search_fields = ('reference_number', 'category', 'description')
    list_filter = ('transaction_type', 'payment_method', 'date')
    date_hierarchy = 'date'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'contact_number', 'email', 'category', 'status')
    search_fields = ('name', 'contact_person', 'email', 'contact_number')
    list_filter = ('status', 'category')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'category', 'batch_number', 'quantity', 'min_stock_level', 'selling_price', 'expiry_date', 'is_active')
    search_fields = ('name', 'generic_name', 'batch_number', 'manufacturer')
    list_filter = ('category', 'is_active', 'expiry_date')


@admin.register(MedicineTransaction)
class MedicineTransactionAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'transaction_type', 'quantity', 'reference', 'date', 'created_by')
    search_fields = ('medicine__name', 'reference')
    list_filter = ('transaction_type', 'date')
    date_hierarchy = 'date'


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'requester', 'department', 'estimated_amount', 'status', 'approved_by', 'created_at')
    search_fields = ('request_number', 'requester__username')
    list_filter = ('status', 'created_at')
    readonly_fields = ('request_number',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'total_amount', 'status', 'payment_status', 'expected_delivery', 'created_at')
    search_fields = ('order_number', 'supplier__name')
    list_filter = ('status', 'payment_status', 'created_at')
    readonly_fields = ('order_number',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_type', 'content_type_name', 'object_id', 'uploaded_by', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('document_type', 'content_type_name', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    list_filter = ('notification_type', 'is_read', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'module', 'record_id', 'record_repr', 'ip_address', 'timestamp')
    search_fields = ('module', 'record_id', 'record_repr', 'user__username')
    list_filter = ('action', 'module', 'timestamp')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'employee', 'phone')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('role',)
