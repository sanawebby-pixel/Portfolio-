import os
import shutil
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from welfare_app.models import (
    Department, BenefitRule, Employee, Dependent, Hospital, Doctor,
    HospitalVisit, VisitExpenseItem, MedicalRecord, MedicalClaim,
    ClaimExpenseItem, ApprovalWorkflow, ClaimPayment, Bill, Budget,
    FinanceTransaction, Medicine, MedicineTransaction, Supplier,
    PurchaseRequest, PurchaseOrder, Document, Notification, AuditLog,
    UserProfile
)


class Command(BaseCommand):
    help = 'Cleans all operational and sample data from the database, leaving a clean system with an Admin login'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Cleaning all operational records and data...'))

        # 1. Delete dependent & child transactional records first
        VisitExpenseItem.objects.all().delete()
        HospitalVisit.objects.all().delete()
        ClaimExpenseItem.objects.all().delete()
        ApprovalWorkflow.objects.all().delete()
        ClaimPayment.objects.all().delete()
        MedicalClaim.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Dependent.objects.all().delete()
        Employee.objects.all().delete()

        # 2. Delete clinical facilities & staff
        Doctor.objects.all().delete()
        Hospital.objects.all().delete()

        # 3. Delete finance & billing
        Bill.objects.all().delete()
        Budget.objects.all().delete()
        FinanceTransaction.objects.all().delete()

        # 4. Delete inventory & procurement
        MedicineTransaction.objects.all().delete()
        Medicine.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        PurchaseRequest.objects.all().delete()
        Supplier.objects.all().delete()

        # 5. Delete documents, notifications, logs & rules
        Document.objects.all().delete()
        Notification.objects.all().delete()
        AuditLog.objects.all().delete()
        BenefitRule.objects.all().delete()
        Department.objects.all().delete()

        # 6. Clean users except superuser 'admin'
        User.objects.filter(is_superuser=False).delete()

        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@welfare.org',
                'first_name': 'Welfare',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password('admin123')
        admin_user.save()

        profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        profile.role = 'Admin'
        profile.employee = None
        profile.save()

        # 7. Clean media upload files
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root and os.path.exists(media_root):
            for item in os.listdir(media_root):
                item_path = os.path.join(media_root, item)
                if item == '.gitkeep':
                    continue
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    try:
                        os.remove(item_path)
                    except OSError:
                        pass

            # Re-create empty media subfolders with .gitkeep
            for folder in ['employees/photos', 'visits/expenses', 'visits/consultation', 'bills', 'claims', 'finance', 'payments']:
                folder_path = os.path.join(media_root, folder)
                os.makedirs(folder_path, exist_ok=True)
                gitkeep_file = os.path.join(folder_path, '.gitkeep')
                if not os.path.exists(gitkeep_file):
                    with open(gitkeep_file, 'w') as f:
                        f.write('')

        self.stdout.write(self.style.SUCCESS('Database and media successfully cleaned! Ready for fresh data entry.'))
