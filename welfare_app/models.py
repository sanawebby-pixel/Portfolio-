from django.db import models


class Employee(models.Model):
    pl_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    father_name = models.CharField(max_length=120, blank=True, null=True)
    department = models.CharField(max_length=120)
    designation = models.CharField(max_length=120, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_medical_expense(self):
        total = self.medical_records.aggregate(total=models.Sum('total_expense'))['total']
        return total or 0

    def __str__(self):
        return f"{self.pl_number} - {self.name}"


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
