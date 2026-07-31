from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Shoe, Category

class Command(BaseCommand):
    help = 'Add sample shoe products'

    def handle(self, *args, **options):
        # Create or get default category
        category, created = Category.objects.get_or_create(
            name='Footwear',
            defaults={
                'slug': 'footwear',
                'description': 'All footwear products'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created default category'))

        products = [
            {'name': 'Air Max Elite', 'price': 149.99, 'description': 'Premium running shoes', 'sizes': '7,8,9,10,11,12', 'stock': 25},
            {'name': 'Urban Sneaker Pro', 'price': 89.99, 'description': 'Versatile sneakers', 'sizes': '8,9,10,11', 'stock': 30},
            {'name': 'Classic Leather Oxford', 'price': 199.99, 'description': 'Timeless leather oxford', 'sizes': '8,9,10,11,12', 'stock': 15},
            {'name': 'Trail Runner X', 'price': 129.99, 'description': 'Durable trail running', 'sizes': '7,8,9,10,11', 'stock': 20},
            {'name': 'Minimalist Loafers', 'price': 79.99, 'description': 'Elegant casual loafers', 'sizes': '8,9,10', 'stock': 18},
            {'name': 'Sport Court Classic', 'price': 109.99, 'description': 'Retro basketball style', 'sizes': '9,10,11,12', 'stock': 22},
            {'name': 'Eco-Friendly Runners', 'price': 159.99, 'description': 'Sustainable materials', 'sizes': '7,8,9,10', 'stock': 12},
            {'name': 'Luxury Chelsea Boots', 'price': 249.99, 'description': 'Premium full-grain leather', 'sizes': '8,9,10,11', 'stock': 10},
            {'name': 'Performance Training Shoe', 'price': 119.99, 'description': 'High-performance training', 'sizes': '7,8,9,10,11,12', 'stock': 28},
            {'name': 'Summer Slide Sandals', 'price': 59.99, 'description': 'Comfortable summer sandals', 'sizes': '8,9,10,11', 'stock': 35},
            {'name': 'Premium Leather Derby', 'price': 189.99, 'description': 'Classic derby shoes', 'sizes': '8,9,10,11,12', 'stock': 14},
            {'name': 'Lightweight Mesh Runners', 'price': 99.99, 'description': 'Ultra-lightweight mesh', 'sizes': '7,8,9,10', 'stock': 32},
        ]

        added = 0
        for p in products:
            # Generate a unique slug from the name
            base_slug = slugify(p['name'])
            slug = base_slug
            counter = 1
            
            # Check if slug exists and make it unique
            while Shoe.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            obj, created = Shoe.objects.get_or_create(
                name=p['name'],
                defaults={
                    'price': p['price'],
                    'description': p['description'],
                    'sizes': p['sizes'],
                    'stock': p['stock'],
                    'category': category,
                    'slug': slug,  # Add the slug!
                }
            )
            if created:
                added += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Added: {obj.name} (slug: {obj.slug})'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Skipped: {obj.name} (already exists)'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Added {added} new products! Total: {Shoe.objects.count()}'))
