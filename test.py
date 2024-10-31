from PIL import Image
import os

def shorts_images_png_conversion(folder_path, initial_value=1, target_size=(768, 1368)):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print(f"The specified folder '{folder_path}' does not exist.")
        return
    
    # Get all JPG and PNG files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".png"))]
    
    if not image_files:
        print("No JPG or PNG images found in the folder.")
        return
    
    # Sort files to maintain a specific order (optional)
    image_files.sort()
    
    # Convert each image to resized PNG and rename
    for index, image_file in enumerate(image_files, start=initial_value):
        # Define input and output paths
        input_path = os.path.join(folder_path, image_file)
        output_path = os.path.join(folder_path, f"{index}.png")
        
        # Open, resize, and convert image
        with Image.open(input_path) as img:
            resized_img = img.resize(target_size)
            resized_img.save(output_path, "PNG")
        
        print(f"Converted '{image_file}' to '{output_path}' with size {target_size}")

def convert_and_replace_png(folder_path, target_size=(1472, 832)):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print(f"The specified folder '{folder_path}' does not exist.")
        return
    
    # Get all JPG and PNG files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".png"))]
    
    if not image_files:
        print("No JPG or PNG images found in the folder.")
        return
    
    # Sort files to maintain a specific order (optional)
    image_files.sort()
    
    # Convert each image to resized PNG, replacing original file
    for image_file in image_files:
        input_path = os.path.join(folder_path, image_file)
        output_path = os.path.splitext(input_path)[0] + ".png"  # Replace original extension with .png
        
        # Open, resize, and convert image
        with Image.open(input_path) as img:
            resized_img = img.resize(target_size)
            resized_img.save(output_path, "PNG")
        
        # Remove the original file if it was a .jpg
        if image_file.lower().endswith(".jpg"):
            os.remove(input_path)
        
        print(f"Replaced '{image_file}' with '{output_path}' in size {target_size}")

# Example usage:
shorts_images_png_conversion("C:\\Users\\catch\\OneDrive\\Desktop\\New folder", initial_value=14)
#convert_and_replace_png("Web\\assets\\images\\vendor")
