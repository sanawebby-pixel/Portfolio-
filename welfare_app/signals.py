from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, MedicalClaim, Notification, FinanceTransaction, Budget, MedicineTransaction, Medicine

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=MedicalClaim)
def claim_status_changed(sender, instance, **kwargs):
    # Depending on implementation, you might want to check if status actually changed.
    # Simplified check.
    if hasattr(instance.employee, 'user') and instance.employee.user:
        Notification.objects.create(
            user=instance.employee.user,
            title="Claim Status Updated",
            message=f"Your claim {instance.claim_number} status is now {instance.status}."
        )

@receiver(post_save, sender=FinanceTransaction)
def budget_threshold_check(sender, instance, created, **kwargs):
    if created and instance.transaction_type == 'Expense' and instance.budget:
        budget = instance.budget
        spent_amount = sum(t.amount for t in budget.financetransaction_set.filter(transaction_type='Expense')) if hasattr(budget, 'financetransaction_set') else 0
        if spent_amount > (budget.allocated_amount * 0.8):
            finance_users = UserProfile.objects.filter(role__in=['Admin', 'HR Manager', 'Super Admin'])
            for profile in finance_users:
                Notification.objects.create(
                    user=profile.user,
                    title="Budget Warning",
                    message=f"Budget {budget.name} has exceeded 80% of its allocation."
                )

@receiver(post_save, sender=MedicineTransaction)
def medicine_stock_alert(sender, instance, created, **kwargs):
    medicine = instance.medicine
    if medicine.quantity_in_stock < medicine.min_stock_level:
        admin_users = UserProfile.objects.filter(role__in=['Admin', 'Inventory Manager', 'Super Admin'])
        for profile in admin_users:
            Notification.objects.create(
                user=profile.user,
                title="Low Stock Alert",
                message=f"Medicine {medicine.name} is running low on stock ({medicine.quantity_in_stock})."
            )
