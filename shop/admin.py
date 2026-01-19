from django.contrib import admin
from .models import Herbal, PickupPoint, Order, OrderItem
from django.utils.html import format_html

class HerbalAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'image_preview', 'is_home', 'created_at']
    list_filter = ['is_home', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_home']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'description', 'price', 'is_home')
        }),
        ('Rasm', {
            'fields': ('image', 'image_preview', 'image_name'),
            'description': 'Yangi rasm yuklang yoki eski rasm nomini kiriting'
        }),
    )
    
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            img_url = obj.image.url
            return format_html('<img src="{}" style="max-height: 150px; max-width: 150px; border-radius: 8px;" />', img_url)
        return "-"
    
    image_preview.short_description = "Rasm ko'rinishi"
    
    class Media:
        css = {
            'all': ('admin/css/herbal_admin.css',)
        }


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total_price']
    can_delete = False


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'total', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'full_name', 'phone']
    readonly_fields = ['order_number', 'subtotal', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order_number', 'full_name', 'phone', 'email', 'pickup_point', 'pickup_date')
        }),
        ('To\'lov ma\'lumotlari', {
            'fields': ('payment_method', 'payment_status', 'subtotal', 'total')
        }),
        ('Holat', {
            'fields': ('status', 'notes')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )


admin.site.register(Herbal, HerbalAdmin)
admin.site.register(PickupPoint)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)