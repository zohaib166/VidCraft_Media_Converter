from PIL import Image

# Open your high-res logo PNG (or favicon.ico image)
img = Image.open("logo.png")  # or "logo.png"

# Convert and save as a proper multi-size Windows icon
img.save(
    "app_icon.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print("app_icon.ico created successfully!")