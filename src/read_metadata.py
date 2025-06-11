from PIL import Image, ExifTags

img = Image.open('03_loop/DJI_20250513135456_0106_D.JPG')
exif_data = img._getexif()

for tag_id, value in exif_data.items():
    tag = ExifTags.TAGS.get(tag_id, tag_id)
    print(f"{tag} : {value}")
