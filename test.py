from PIL import Image
import os

def convert_jpg_to_png(folder_path, initial_value=1, target_size=(768, 1368)):
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        print(f"The specified folder '{folder_path}' does not exist.")
        return
    
    # Get all JPG files in the folder
    jpg_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
    
    if not jpg_files:
        print("No JPG images found in the folder.")
        return
    
    # Sort files to maintain a specific order (optional)
    jpg_files.sort()
    
    # Convert each JPG to resized PNG and rename
    for index, jpg_file in enumerate(jpg_files, start=initial_value):
        # Define input and output paths
        input_path = os.path.join(folder_path, jpg_file)
        output_path = os.path.join(folder_path, f"{index}.png")
        
        # Open, resize, and convert image
        with Image.open(input_path) as img:
            resized_img = img.resize(target_size)  # Resize to target dimensions
            resized_img.save(output_path, "PNG")
        
        print(f"Converted '{jpg_file}' to '{output_path}' with size {target_size}")

# Example usage:
convert_jpg_to_png("C:\\Users\\catch\\OneDrive\\Desktop\\New folder", initial_value=14)
