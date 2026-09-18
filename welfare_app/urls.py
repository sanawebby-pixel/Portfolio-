from django.urls import path

from . import views

urlpatterns = [
    # ============================================================
    # Authentication
    # ============================================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),

    # ============================================================
    # Dashboard (existing - preserved)
    # ============================================================
    path('', views.dashboard, name='dashboard'),

    # ============================================================
    # Legacy Employee URLs (preserved for backward compatibility)
    # ============================================================
    path('employee/add/', views.add_employee, name='add_employee'),
    path('employee/edit/<int:pk>/', views.edit_employee, name='edit_employee'),
    path('employee/delete/<int:pk>/', views.delete_employee, name='delete_employee'),

    # ============================================================
    # Legacy Medical Record URLs (preserved for backward compatibility)
    # ============================================================
    path('record/add/', views.add_record, name='add_record'),
    path('record/edit/<int:pk>/', views.edit_record, name='edit_record'),
    path('record/delete/<int:pk>/', views.delete_record, name='delete_record'),

    # ============================================================
    # Employee Management (new full CRUD)
    # ============================================================
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    # Dependents
    path('employees/<int:employee_pk>/dependents/add/', views.dependent_create, name='dependent_create'),
    path('dependents/<int:pk>/edit/', views.dependent_update, name='dependent_update'),
    path('dependents/<int:pk>/delete/', views.dependent_delete, name='dependent_delete'),

    # ============================================================
    # Hospital Management
    # ============================================================
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/create/', views.hospital_create, name='hospital_create'),
    path('hospitals/<int:pk>/', views.hospital_detail, name='hospital_detail'),
    path('hospitals/<int:pk>/edit/', views.hospital_update, name='hospital_update'),
    path('hospitals/<int:pk>/delete/', views.hospital_delete, name='hospital_delete'),

    # ============================================================
    # Doctor Management
    # ============================================================
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/create/', views.doctor_create, name='doctor_create'),
    path('doctors/<int:pk>/edit/', views.doctor_update, name='doctor_update'),
    path('doctors/<int:pk>/delete/', views.doctor_delete, name='doctor_delete'),

    # ============================================================
    # Hospital Visits
    # ============================================================
    path('visits/', views.visit_list, name='visit_list'),
    path('visits/create/', views.visit_create, name='visit_create'),
    path('visits/<int:pk>/', views.visit_detail, name='visit_detail'),
    path('visits/<int:pk>/edit/', views.visit_update, name='visit_update'),
    path('visits/<int:pk>/delete/', views.visit_delete, name='visit_delete'),

    # ============================================================
    # Medical Claims
    # ============================================================
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/create/', views.claim_create, name='claim_create'),
    path('claims/<int:pk>/', views.claim_detail, name='claim_detail'),
    path('claims/<int:pk>/edit/', views.claim_update, name='claim_update'),
    path('claims/<int:pk>/delete/', views.claim_delete, name='claim_delete'),
    path('claims/<int:pk>/submit/', views.claim_submit, name='claim_submit'),
    path('claims/<int:pk>/approve/', views.claim_approve, name='claim_approve'),
    path('claims/<int:pk>/reject/', views.claim_reject, name='claim_reject'),

    # ============================================================
    # Bills & Expenses
    # ============================================================
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/create/', views.bill_create, name='bill_create'),
    path('bills/<int:pk>/edit/', views.bill_update, name='bill_update'),
    path('bills/<int:pk>/delete/', views.bill_delete, name='bill_delete'),
    path('bills/<int:pk>/approve/', views.bill_approve, name='bill_approve'),

    # ============================================================
    # Finance & Budgets
    # ============================================================
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/budgets/', views.budget_list, name='budget_list'),
    path('finance/budgets/create/', views.budget_create, name='budget_create'),
    path('finance/budgets/<int:pk>/edit/', views.budget_update, name='budget_update'),
    path('finance/transactions/', views.transaction_list, name='transaction_list'),
    path('finance/transactions/create/', views.transaction_create, name='transaction_create'),

    # ============================================================
    # Approvals
    # ============================================================
    path('approvals/', views.claim_list, name='approval_list'),

    # ============================================================
    # Inventory / Medicines
    # ============================================================
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/create/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_update, name='medicine_update'),
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),
    path('stock/', views.stock_transactions, name='stock_transactions'),
    path('stock/in/', views.stock_in, name='stock_in'),
    path('stock/out/', views.stock_out, name='stock_out'),

    # ============================================================
    # Procurement
    # ============================================================
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('purchase-requests/', views.purchase_request_list, name='purchase_request_list'),
    path('purchase-requests/create/', views.purchase_request_create, name='purchase_request_create'),
    path('purchase-requests/<int:pk>/approve/', views.purchase_request_approve, name='purchase_request_approve'),
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),

    # ============================================================
    # Reports
    # ============================================================
    path('reports/', views.report_index, name='report_index'),
    path('reports/employees/', views.employee_report, name='employee_report'),
    path('reports/expenses/', views.expense_report, name='expense_report'),
    path('reports/hospitals/', views.hospital_report, name='hospital_report'),
    path('reports/claims/', views.claim_report, name='claim_report'),
    path('reports/budget/', views.budget_report, name='budget_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),

    # ============================================================
    # Global Search
    # ============================================================
    path('search/', views.global_search, name='global_search'),

    # ============================================================
    # User Management
    # ============================================================
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('users/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),

    # ============================================================
    # Notifications
    # ============================================================
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),

    # ============================================================
    # Audit Log
    # ============================================================
    path('audit-log/', views.audit_log, name='audit_log'),
]
