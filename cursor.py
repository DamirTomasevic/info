import pyautogui
import tkinter as tk
from tkinter import filedialog, Menu
from PIL import Image, ImageTk

# Initialize global variables
points = []
boundaries_set = False
img = None
photo_img = None
marker_radius = 5  # Radius for the marker points

# Function to scale the click coordinates to a 1920x1080 resolution
def scale_to_viewport(x, y, top_left, bottom_right):
    viewport_width = bottom_right[0] - top_left[0]
    viewport_height = bottom_right[1] - top_left[1]
    scaled_x = int((x - top_left[0]) * 1920 / viewport_width)
    scaled_y = int((y - top_left[1]) * 1080 / viewport_height)
    return scaled_x, scaled_y

# Click event handler
def click_handler(event):
    global points, boundaries_set

    if not boundaries_set:
        # Collect two points for defining the viewport
        if len(points) < 2:
            # Save the point and display a green marker
            points.append((event.x, event.y))
            draw_marker(event.x, event.y)
            print(f"Point {len(points)} set at: {event.x}, {event.y}")

            # Once two points are set, draw the rectangle and enable boundary setting
            if len(points) == 2:
                boundaries_set = True
                draw_rectangle(points[0], points[1])
                print(f"Viewport set from {points[0]} to {points[1]}")
    else:
        # Calculate and display scaled coordinates
        scaled_x, scaled_y = scale_to_viewport(event.x, event.y, points[0], points[1])
        display_position(event.x, event.y, scaled_x, scaled_y)

# Function to draw a green marker at a specific point
def draw_marker(x, y):
    canvas.create_oval(x - marker_radius, y - marker_radius, 
                       x + marker_radius, y + marker_radius,
                       outline="green", fill="green")

# Function to draw a rectangle based on two points
def draw_rectangle(top_left, bottom_right):
    canvas.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1], outline="green")

# Display the position in a label at the clicked location
def display_position(screen_x, screen_y, scaled_x, scaled_y):
    overlay_text = f"{scaled_x} * {scaled_y}"
    label = tk.Label(root, text=overlay_text, fg="red", bg="white", font=("Arial", 12, "bold"))
    label.place(x=screen_x, y=screen_y)
    label.after(2000, label.destroy)

# Function to load an image, resize it, and display it on the canvas
def load_image():
    global img, photo_img, boundaries_set, points

    # Reset viewport boundaries and clear markers
    boundaries_set = False
    points.clear()
    canvas.delete("all")  # Clear canvas including previous markers and rectangle

    # Open file dialog to select an image file
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
    if not file_path:
        print("No image selected.")
        return

    # Load the image
    img = Image.open(file_path)

    # Resize the image to fit within 1500x900 while keeping aspect ratio
    img.thumbnail((1500, 900), Image.LANCZOS)
    photo_img = ImageTk.PhotoImage(img)

    # Display the new image
    canvas.create_image(0, 0, anchor="nw", image=photo_img)

# Main Tkinter setup
root = tk.Tk()
root.title("Dynamic Image Import and Scaled Position Display")
root.geometry("1500x900")  # Set window size to 1500x900

# Canvas to display the image, set to fill the Tkinter window
canvas = tk.Canvas(root, width=1500, height=900)
canvas.pack(fill="both", expand=True)

# Menu to load a new image
menubar = Menu(root)
file_menu = Menu(menubar, tearoff=0)
file_menu.add_command(label="Import Image", command=load_image)
menubar.add_cascade(label="File", menu=file_menu)
root.config(menu=menubar)

# Bind left-click mouse button to click_handler function
root.bind("<Button-1>", click_handler)

root.mainloop()
