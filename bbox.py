from PIL import Image
img = Image.open("mask.png").convert('L')

img.save("res.png")
print(img.getbbox())
