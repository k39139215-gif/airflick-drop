from PIL import Image, ImageDraw

# Create a sleek 512x512 app icon
size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Rounded rectangle background with indigo gradient-like color
draw.rounded_rectangle([16, 16, size-16, size-16], radius=110, fill=(99, 102, 241, 255))

# Draw an upward flight arrow / paper plane / flick icon
# Inner polygon
draw.polygon([(256, 110), (390, 360), (256, 305), (122, 360)], fill=(255, 255, 255, 255))
draw.polygon([(256, 110), (256, 305), (390, 360)], fill=(224, 231, 255, 255))

img.save(r"C:\Users\kartik\.gemini\antigravity\scratch\airflick-drop\web\icon.png")
print("icon.png generated")
