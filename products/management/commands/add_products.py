import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from products.models import Shoe, Category
from urllib.parse import urlparse
import os

class Command(BaseCommand):
    help = 'Add sample shoe products'

    def handle(self, *args, **options):
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
            {
                'name': 'Air Max Elite',
                'price': 149.99,
                'description': 'Premium running shoes with maximum comfort and style. Features responsive cushioning and breathable mesh upper.',
                'sizes': '7,8,9,10,11,12',
                'stock': 25,
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500'
            },
            {
                'name': 'Urban Sneaker Pro',
                'price': 89.99,
                'description': 'Versatile sneakers perfect for everyday wear. Classic design with modern comfort technology.',
                'sizes': '8,9,10,11',
                'stock': 30,
                'image_url': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500'
            },
            {
                'name': 'Classic Leather Oxford',
                'price': 199.99,
                'description': 'Timeless leather oxford shoes for formal occasions. Handcrafted with premium Italian leather.',
                'sizes': '8,9,10,11,12',
                'stock': 15,
                'image_url': 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=500'
            },
            {
                'name': 'Trail Runner X',
                'price': 129.99,
                'description': 'Durable trail running shoes designed for off-road adventures. Excellent grip and stability.',
                'sizes': '7,8,9,10,11',
                'stock': 20,
                'image_url': 'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=500'
            },
            {
                'name': 'Minimalist Loafers',
                'price': 79.99,
                'description': 'Elegant loafers for a sophisticated casual look. Crafted with soft suede and leather lining.',
                'sizes': '8,9,10',
                'stock': 18,
                'image_url': 'https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=500'
            },
            {
                'name': 'Sport Court Classic',
                'price': 109.99,
                'description': 'Retro basketball sneakers with modern comfort. Iconic design with responsive cushioning.',
                'sizes': '9,10,11,12',
                'stock': 22,
                'image_url': 'https://images.unsplash.com/photo-1516478177764-9fe0bd749e18?w=500'
            },
            {
                'name': 'Eco-Friendly Runners',
                'price': 159.99,
                'description': 'Sustainable running shoes made from recycled materials. Lightweight and eco-conscious.',
                'sizes': '7,8,9,10',
                'stock': 12,
                'image_url': 'https://images.unsplash.com/photo-1575408264798-b50b252663e6?w=500'
            },
            {
                'name': 'Luxury Chelsea Boots',
                'price': 249.99,
                'description': 'Premium Chelsea boots crafted from full-grain leather. Versatile and timeless design.',
                'sizes': '8,9,10,11',
                'stock': 10,
                'image_url': 'https://images.unsplash.com/photo-1638247025967-b4e38c3b7c2b?w=500'
            },
            {
                'name': 'Performance Training Shoe',
                'price': 119.99,
                'description': 'High-performance training shoes with superior support and stability for intense workouts.',
                'sizes': '7,8,9,10,11,12',
                'stock': 28,
                'image_url': 'https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=500'
            },
            {
                'name': 'Summer Slide Sandals',
                'price': 59.99,
                'description': 'Comfortable slide sandals perfect for summer. Soft footbed with durable construction.',
                'sizes': '8,9,10,11',
                'stock': 35,
                'image_url': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500'
            },
            {
                'name': 'Premium Leather Derby',
                'price': 189.99,
                'description': 'Classic derby shoes with a modern twist. Made with premium calfskin leather.',
                'sizes': '8,9,10,11,12',
                'stock': 14,
                'image_url': 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=500'
            },
            {
                'name': 'Lightweight Mesh Runners',
                'price': 99.99,
                'description': 'Ultra-lightweight running shoes with breathable mesh upper and responsive foam.',
                'sizes': '7,8,9,10',
                'stock': 32,
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500'
            }
        ]


        added = 0
        for p in products:
            base_slug = slugify(p['name'])
            slug = base_slug
            counter = 1
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
                    'slug': slug,
                }
            )

            if created:
                added += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Added: {obj.name} (slug: {obj.slug})'))

                image_url = p.get('image_url')
                if image_url:
                    try:
                        response = requests.get(p['image_url'], timeout=10)
                        response.raise_for_status()
                        path = urlparse(p['image_url']).path
                        ext = os.path.splitext(path)[1] or '.jpg'
                        filename = f'{slug}{ext}'
                        obj.image.save(filename, ContentFile(response.content), save=True)
                        self.stdout.write(self.style.SUCCESS(f'   ↳ image saved for {obj.name}'))
                    except requests.RequestException as e:
                        self.stdout.write(self.style.WARNING(f'   ⚠️ could not fetch image for {obj.name}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Skipped: {obj.name} (already exists)'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Added {added} new products! Total: {Shoe.objects.count()}'))
        
        
        
        
        
        
        


        
        