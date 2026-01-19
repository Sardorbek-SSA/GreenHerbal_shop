from django.db import models
import os

class Herbal(models.Model):
    name = models.CharField(max_length=255, verbose_name="Mahsulot nomi")
    description = models.TextField(verbose_name="Tavsif")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narx")
    image = models.ImageField(
        upload_to='herbals/',
        verbose_name="Mahsulot rasmi",
        help_text="Rasmni yuklang (JPG, PNG formatida)",
        blank=True,
        null=True
    )
    
    image_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Eski rasm nomi",
        help_text="Avvalgi rasmlar uchun"
    )
    
    is_home = models.BooleanField(default=False, verbose_name="Bosh sahifada ko'rsatish")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    
    def get_image_url(self):
        """Rasm URL qaytarish"""
        if self.image:
            return self.image.url
        elif self.image_name:
            from django.templatetags.static import static
            return static(f'herbals/{self.image_name}')
        else:
            from django.templatetags.static import static
            return static('images/default-product.jpg')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dorivor o'simlik"
        verbose_name_plural = "Dorivor o'simliklar"
        ordering = ['-created_at']


class PickupPoint(models.Model):
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
    ]
    
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Buyurtma raqami")
    full_name = models.CharField(max_length=100, verbose_name="To'liq ism")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, 
                                     null=True, verbose_name="Olib ketish punkti")
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, 
                                      default='cash_pickup', verbose_name="To'lov usuli")
    payment_status = models.BooleanField(default=False, verbose_name="To'lov holati")
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Jami summa")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Umumiy summa")
    
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name="Holati")
    
    pickup_date = models.DateField(null=True, blank=True, verbose_name="Olib ketish sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")
    
    notes = models.TextField(blank=True, verbose_name="Qo'shimcha eslatmalar")
    
    def __str__(self):
        return f"Buyurtma #{self.order_number} - {self.full_name}"
    
    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Buyurtma")
    herbal = models.ForeignKey(Herbal, on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi")
    quantity = models.IntegerField(verbose_name="Miqdori")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy narx")
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"