from django.contrib import admin
from .models import (
    Department, BenefitRule, Employee, Dependent, Hospital, Doctor, HospitalVisit, VisitExpenseItem,
    MedicalRecord, MedicalClaim, ClaimExpenseItem, ApprovalWorkflow, ClaimPayment,
    Bill, BillDocument, Budget, FinanceTransaction, Document, Notification,
    AuditLog, UserProfile
)



class VisitExpenseItemInline(admin.TabularInline):
    model = VisitExpenseItem
    extra = 1
    fields = ('title', 'cost', 'document')


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


class ClaimPaymentInline(admin.TabularInline):
    model = ClaimPayment
    extra = 0
    readonly_fields = ('payment_number', 'created_at')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(BenefitRule)
class BenefitRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'grade_scale', 'annual_medical_limit', 'opd_consultation_limit', 'lab_coverage_percent', 'is_active')
    search_fields = ('name', 'grade_scale')
    list_filter = ('is_active', 'department')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('pl_number', 'name', 'department', 'designation', 'employment_type', 'employment_status', 'joined_date')
    search_fields = ('pl_number', 'name', 'cnic', 'email', 'contact_number')
    list_filter = ('department', 'employment_status', 'employment_type')
    inlines = [DependentInline]


@admin.register(Dependent)
class DependentAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee', 'relationship', 'date_of_birth', 'medical_eligible', 'status')
    search_fields = ('name', 'employee__name', 'employee__pl_number', 'cnic_bform')
    list_filter = ('relationship', 'medical_eligible', 'status')


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('hospital_code', 'name', 'hospital_type', 'city', 'contact_person', 'contact_number', 'panel_status', 'status')
    search_fields = ('hospital_code', 'name', 'city', 'contact_number', 'email')
    list_filter = ('hospital_type', 'panel_status', 'status')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'hospital', 'consultation_fee', 'contact', 'status')
    search_fields = ('name', 'specialization', 'registration_number', 'contact')
    list_filter = ('hospital', 'status')


@admin.register(HospitalVisit)
class HospitalVisitAdmin(admin.ModelAdmin):
    list_display = ('employee', 'dependent', 'hospital', 'doctor', 'visit_date', 'visit_type', 'doctor_fee', 'medicine_cost', 'diagnostic_cost', 'other_charges', 'total_visit_cost', 'status')
    search_fields = ('employee__name', 'employee__pl_number', 'diagnosis', 'hospital__name', 'doctor__name')
    list_filter = ('visit_type', 'status', 'visit_date')
    date_hierarchy = 'visit_date'
    fieldsets = (
        ('Encounter Information', {
            'fields': ('employee', 'dependent', 'hospital', 'hospital_name', 'doctor', 'doctor_name', 'department_specialization', 'visit_date', 'visit_type', 'status')
        }),
        ('Clinical Findings', {
            'fields': ('diagnosis', 'symptoms', 'treatment', 'prescription', 'lab_tests', 'medical_notes')
        }),
        ('Itemized Financials & Document Scans', {
            'fields': (
                ('doctor_fee', 'doctor_fee_doc'),
                ('medicine_cost', 'medicine_doc'),
                ('diagnostic_cost', 'diagnostic_doc'),
                ('other_charges', 'other_charges_doc'),
                ('total_visit_cost', 'attached_document'),
            )
        }),
        ('Inpatient & Follow-up', {
            'fields': ('admission_date', 'discharge_date', 'room_ward', 'followup_date', 'remarks'),
            'classes': ('collapse',)
        }),
    )
    inlines = [VisitExpenseItemInline]


@admin.register(VisitExpenseItem)
class VisitExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'cost', 'visit', 'document', 'created_at')
    search_fields = ('title', 'visit__employee__name', 'visit__employee__pl_number')
    list_filter = ('created_at',)


@admin.register(MedicalRecord)

class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'employee', 'hospital', 'doctor', 'treatment_date', 'total_expense', 'status')
    search_fields = ('bill_no', 'employee__name', 'employee__pl_number', 'hospital', 'doctor', 'diagnosis')
    list_filter = ('status', 'treatment_date')
    date_hierarchy = 'treatment_date'


@admin.register(MedicalClaim)
class MedicalClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_number', 'employee', 'claim_type', 'claim_date', 'total_bill_amount', 'claimable_amount', 'approved_amount', 'paid_amount', 'claim_status', 'payment_status')
    search_fields = ('claim_number', 'employee__name', 'employee__pl_number', 'bill_number', 'diagnosis')
    list_filter = ('claim_status', 'payment_status', 'claim_type', 'claim_date')
    date_hierarchy = 'claim_date'
    inlines = [ClaimExpenseItemInline, ApprovalWorkflowInline, ClaimPaymentInline]
    readonly_fields = ('claim_number', 'created_at', 'updated_at')


@admin.register(ClaimPayment)
class ClaimPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'claim', 'employee', 'payment_amount', 'payment_date', 'payment_method', 'account', 'transaction_reference')
    search_fields = ('payment_number', 'claim__claim_number', 'employee__name', 'transaction_reference')
    list_filter = ('payment_method', 'payment_date')
    date_hierarchy = 'payment_date'


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


class BillDocumentInline(admin.TabularInline):
    model = BillDocument
    extra = 1
    fields = ('description', 'document')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'bill_date', 'category', 'hospital', 'vendor_name', 'employee', 'amount', 'status', 'payment_status')
    search_fields = ('bill_number', 'vendor_name', 'employee__name')
    list_filter = ('status', 'payment_status', 'category', 'bill_date')
    date_hierarchy = 'bill_date'
    inlines = [BillDocumentInline]


@admin.register(BillDocument)
class BillDocumentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'description', 'document', 'created_at')
    search_fields = ('bill__bill_number', 'description')



@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('year', 'department', 'category', 'allocated_amount', 'is_active')
    search_fields = ('year', 'department__name', 'category')
    list_filter = ('year', 'category', 'is_active')


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'transaction_type', 'amount', 'category', 'payment_method', 'date', 'created_by')
    search_fields = ('transaction_id', 'reference_number', 'category', 'description')
    list_filter = ('transaction_type', 'payment_method', 'date')
    date_hierarchy = 'date'




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
