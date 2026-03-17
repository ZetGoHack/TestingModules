from PIL import Image
Image.MAX_IMAGE_PIXELS = None
img = Image.open("mask.png").convert('L')

img.save("res.png")
print(img.getbbox())
