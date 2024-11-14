import os
import subprocess

# Define the main Python file and additional folders
main_script = "app.py"
folders_to_add = [
    "web",
    "gfpgan",
    "LongVideos",
    "Utilities",
    "SadTalker"
]  # Add folder paths as needed

# Prepare the PyInstaller command without --onefile to test if it resolves the issue
pyinstaller_command = [
    "pyinstaller",
    "--noconfirm",
    "--noconsole",
    "--onedir",  # Use --onedir instead of --onefile to avoid packing into a single executable
    "--log-level=DEBUG",  # Enable detailed logging for debugging
]

# Add each folder to the PyInstaller command
for folder in folders_to_add:
    # Using Windows path separator syntax for adding data
    pyinstaller_command.extend(["--add-data", f"{folder};{folder}"])

# Add the main Python script to the command
pyinstaller_command.append(main_script)

# Run the command
try:
    subprocess.run(pyinstaller_command, check=True)
    print("Build completed successfully.")
except subprocess.CalledProcessError as e:
    print("Error occurred during the build process:", e)
