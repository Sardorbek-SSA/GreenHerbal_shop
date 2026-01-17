from django.contrib import admin
from .models import Herbal, PickupPoint, Order, OrderItem

@admin.register(Herbal)
class HerbalAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'pickup_point', 
                    'total', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'full_name', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Asosiy maʼlumotlar', {
            'fields': ('order_number', 'full_name', 'phone', 'email')
        }),
        ('Olib ketish', {
            'fields': ('pickup_point', 'pickup_date', 'notes')
        }),
        ('Toʻlov', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Summalar', {
            'fields': ('subtotal', 'total')
        }),
        ('Holat', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'working_hours', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'address']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'product_price', 'total_price']
    list_filter = ['order__status']