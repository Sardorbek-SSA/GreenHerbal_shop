from django.db import models

class Herbal(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(
        upload_to='herbals/', 
        blank=True, 
        null=True,
        default='herbals/default.jpg'
    )
    is_home = models.BooleanField(default=False)

    def image_url(self):
        """Rasm URL ni qaytarish"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/static/images/default-herbal.jpg' 

    def __str__(self):
        return self.name


class PickupPoint(models.Model):
    """Olib ketish punktlari"""
    name = models.CharField(max_length=200, verbose_name="Punkt nomi")
    address = models.TextField(verbose_name="Manzil")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    working_hours = models.CharField(max_length=100, verbose_name="Ish vaqtlari")
    description = models.TextField(blank=True, verbose_name="Qo'shimcha ma'lumot")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Olib ketish punkti"
        verbose_name_plural = "Olib ketish punktlari"

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', "Kutilmoqda"),
        ('confirmed', "Tasdiqlandi"),
        ('ready', "Tayyor"),
        ('picked_up', "Olib ketildi"),
        ('cancelled', "Bekor qilindi"),
    ]
    
    PAYMENT_METHODS = [
        ('cash_pickup', "Naqd (Olib ketishda)"),
        ('click', "Click"),
        ('payme', "Payme"),
        ('uzum', "Uzum"),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Buyurtma raqami")
    full_name = models.CharField(max_length=100, verbose_name="To'liq ism")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    # Pickup point
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, 
                                     null=True, verbose_name="Olib ketish punkti")
    
    # Payment info
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, 
                                      default='cash_pickup', verbose_name="To'lov usuli")
    payment_status = models.BooleanField(default=False, verbose_name="To'lov holati")
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Jami summa")
    # shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Yetkazib berish")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Umumiy summa")
    
    # Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name="Holati")
    
    # Dates
    pickup_date = models.DateField(null=True, blank=True, verbose_name="Olib ketish sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")
    
    # Notes
    notes = models.TextField(blank=True, verbose_name="Qo'shimcha eslatmalar")
    
    def __str__(self):
        return f"Buyurtma #{self.order_number} - {self.full_name}"
    
    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Buyurtma")
    product_name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi")
    quantity = models.IntegerField(verbose_name="Miqdori")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy narx")
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"