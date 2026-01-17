# Build Command yoki build.sh
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Default rasm fayllarini static papkaga nusxalash
mkdir -p static/images
cp -r media/herbals/* static/images/ 2>/dev/null || echo "No media files to copy"