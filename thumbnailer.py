import os
from PIL import Image

THUMBNAIL_SIZE = (200, 200)

# Keep this path inside the project so thumbnails always go to the right place
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
THUMBNAIL_FOLDER = os.path.join(BASE_DIR, 'static', 'thumbnails')


def generate_thumbnail(file_id, file_path, file_type):
    if file_type != 'Photos':
        return False

    try:
        img = Image.open(file_path)
        img.thumbnail(THUMBNAIL_SIZE)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        thumb_path = os.path.join(THUMBNAIL_FOLDER, str(file_id) + '.jpg')
        img.save(thumb_path, 'JPEG')
        return True

    except Exception as e:
        print('Thumbnail failed for', file_path, ':', e)
        return False
