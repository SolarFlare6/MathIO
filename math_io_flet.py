import flet
from flet import IconButton, Page, Row, TextField, icons, AppBar, Text, PopupMenuButton, PopupMenuItem, Switch, Container, Column, ElevatedButton, Radio, RadioGroup, Image, FilePicker, SnackBar, ProgressRing
import cv2
import threading
from io import BytesIO
import base64
import time
import os

# TODO : implement equation image to latex conversion

# import mathplot lib without gui backend
import matplotlib
matplotlib.use("Agg")  # (no GUI backend)

import matplotlib.pyplot as plt

# note flet version 0.24.0

# global variables 
global_selected_image_path = ""
global_image_selected = False

# temp img vars
global_temp_equation_file_name = "equ_temp.png"
global_temp_equation_path = ""

# global thread vars
stop_event = threading.Event()
last_points = None

def main(page: Page):
    page.title = "Math I/O"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.theme_mode = "light"

    # define functions

    def latex_to_png_file(latex_str,output_path=global_temp_equation_file_name):
        print("Running latex to base64 fn !!!")
        
        fig = plt.figure(figsize=(2, 1))
        fig.patch.set_alpha(0)
        
        plt.text(
            0.5,
            0.5,
            rf"${latex_str}$",
            fontsize=30,
            ha="center",
            va="center",
            color="black"
        )
        
        plt.axis("off")
        
        plt.savefig(
            output_path,
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
            transparent=True,
            dpi=300
        )
        
        plt.close(fig)
        
        return output_path

    # delete the temp img fn
    def delete_rendered_equation():
        print("Called the function to delete the temporary file")

        try:

            latex_render_img.src = "render_place_holder.png"
            page.update()

            if (os.path.exists(global_temp_equation_path)):
                os.remove(global_temp_equation_path)
                print("deleted temporary file.")
        
        except Exception as e:
            print(e)
    
    # fn for cropping new (has better scaling and can morph with right click)
    def get_4_crop_points(image_path, stop_event):
        
        img = cv2.imread(image_path)
        
        if img is None:
            print("Failed to load image")
            return None
        
        h, w = img.shape[:2]
        
        # scale to fit screen
        max_w, max_h = 1000, 700
        scale = min(max_w / w, max_h / h, 1.0)
        
        view_x, view_y = 0, 0
        dragging = False
        last_mouse = (0, 0)
        
        points = []
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal dragging, last_mouse, view_x, view_y
            
            if event == cv2.EVENT_LBUTTONDOWN:
                # convert to original coords
                real_x = int((x + view_x) / scale)
                real_y = int((y + view_y) / scale)
                
                if len(points) < 4:
                    points.append((real_x, real_y))
                    print(f"Point {len(points)}: {(real_x, real_y)}")
            
            elif event == cv2.EVENT_RBUTTONDOWN:
                dragging = True
                last_mouse = (x, y)
            
            elif event == cv2.EVENT_MOUSEMOVE and dragging:
                dx = x - last_mouse[0]
                dy = y - last_mouse[1]
                
                view_x = max(0, min(view_x - dx, int(w * scale)))
                view_y = max(0, min(view_y - dy, int(h * scale)))
                
                last_mouse = (x, y)
            
            elif event == cv2.EVENT_RBUTTONUP:
                dragging = False
        
        cv2.namedWindow("Cropper", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Cropper", mouse_callback)
        
        while not stop_event.is_set():
            
            # crop visible area
            resized = cv2.resize(img, None, fx=scale, fy=scale)
            vh, vw = resized.shape[:2]
            
            x2 = min(view_x + max_w, vw)
            y2 = min(view_y + max_h, vh)
            
            view = resized[view_y:y2, view_x:x2].copy()
            
            # draw selected points
            for i, (px, py) in enumerate(points):
                sx = int(px * scale) - view_x
                sy = int(py * scale) - view_y
                
                if 0 <= sx < view.shape[1] and 0 <= sy < view.shape[0]:
                    cv2.circle(view, (sx, sy), 5, (225, 110, 91), -1)
                    cv2.putText(view, str(i+1), (sx+5, sy-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225,110,91), 1)
            
            cv2.imshow("Cropper", view)
            
            key = cv2.waitKey(1)
            
            if key == 27:  # ESC
                break
            
            if len(points) == 4:
                break
        
        cv2.destroyAllWindows()
        
        if len(points) != 4:
            print("Not enough points selected")
            return None
        
        return points

    # funtion for cropping (opens the window) [currently unused]
    def get_4_crop_points_old(image_path, stop_event):
        
        img = cv2.imread(image_path)
        
        if img is None:
            print("Failed to load image")
            return None
        
        
        clone = img.copy()
        points = []
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
                points.append((x, y))
                print(f"Point {len(points)}: {(x, y)}")
        
        cv2.namedWindow("Cropper")
        cv2.setMouseCallback("Cropper", mouse_callback)
        
        while not stop_event.is_set():
            
            display = clone.copy()
            
            # draw points - define the color and the size of the points (color is in BGR)
            for i, (x, y) in enumerate(points):
                cv2.circle(display, (x, y), 5, (225, 110, 91), -1)
                cv2.putText(display, str(i+1), (x+5, y-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (225,110,91), 1)
            
            cv2.imshow("Cropper", display)
            
            key = cv2.waitKey(1)
            
            if key == 27:  # ESC
                break
            
            if len(points) == 4:
                break
        
        cv2.destroyAllWindows()
        
        if len(points) != 4:
            print("Not enough points selected")
            return None
        
        return points  # [TL, TR, BR, BL]

    
    # funtion to run cropper
    def run_cropper(image_path):
        
        global last_points
        
        print("Running cropper...")
        
        pts = get_4_crop_points(image_path, stop_event)
        last_points = pts
        
        print("Selected points:", pts)
        stop_cropper()
    
    # fn to start cropper thread
    def run_cropper_start_thread(image_path):
        
        print("Called function to start cropper...")
        
        if image_path != "":
            stop_event.clear()
            
            cropper_thread = threading.Thread(
                target=run_cropper,
                args=(image_path,),
            )
            
            cropper_thread.start()
            
            print("Started cropper thread")
        else:
            print("No image selected!!!")
    
    # to stop the thread
    def stop_cropper():
        print("Stopping cropper...")
        stop_event.set()
        cv2.destroyAllWindows()
    
    # cropp button fn
    def cropper_btn_fn(e):
        print("Cropper button fn called !!!")
        run_cropper_start_thread(global_selected_image_path)

    
    # simply opens the snackbar with its default content
    def open_snackbar():
        print("Open snackbar function called !!")

        # modify bgcolor
        if (page.theme_mode == "light"):
            print("Adjusting for light mode")
            info_snackbar.bgcolor = "#F8F7FF"
        else:
            print("Adjusting for dark mode")
            info_snackbar.bgcolor = "#202429"

        info_snackbar.open = True
        page.update()

    # close the snackbar
    def close_snackbar():
        print("Close snackbar function called !!")
        info_snackbar.open = False
        page.update()
    
    # show snackbar with parametars - define the text that will be displayed, does it have a progress ring and the color of the ring
    def set_snackbar(txt,show_progress_ring, ring_color):
        print("Called Set snackbar function !!!")
        snackbar_text.value = txt
        snackbar_progress_ring.visible = show_progress_ring
        if (ring_color != None):
            print("Changing the color or the progress ring")
            snackbar_progress_ring.color = ring_color
        open_snackbar()
    
    def file_btn_fn(e):
        print("File button pressed fn called !!")
        open_file_dialog_fn()

    def change_theme_fn(e):
        print("Called change theme fn!!!")
        if (page.theme_mode == "light"):
            page.theme_mode = "dark"
        else:
            page.theme_mode = "light"
        page.update()

    # fn for radio group
    def radio_group_changed_fn(e):
        print("Radio group fn called !!")
    
    # close eqation layout btn fn
    def close_eqation_layout_btn_fn(e):
        print("Close eqation layout btn pressed fn called !!")
        
        delete_rendered_equation()
        
        equation_processing_layout.visible = False
        input_layout.visible = True
        # implement full logic when implementing
        page.update()
    
    def close_txt_processing_layout_fn(e):
        print("Close txt processing layout fn called !!")
        text_processing_layout.visible = False
        input_layout.visible = True
        page.update()

    def copy_text_btn_fn(e):
        print("Copy text btn fn called !!")
    
    def save_text_btn_fn(e):
        print("Save text btn fn called !!")
    
    # start btn fn
    def start_btn_fn(e):
        print("Start btn pressed fn called !!")

        # implement logic fully later
        if (int(radio_group.value) == 1 and global_image_selected):
            print("Showing text processing layout")
            
            # set visibility of layouts
            input_layout.visible = False
            text_processing_layout.visible = True
            
            # set image source
            text_img.src = global_selected_image_path
            
            # update the ui
            page.update()

            # show snackbar
            set_snackbar("Text processing",True,None)
        
        if (int(radio_group.value) == 2 and global_image_selected):
            print("Showing eqation processing layout")
            
            # visibility
            input_layout.visible = False
            equation_processing_layout.visible = True
            
            # set source for eqation image
            eqation_img.src = global_selected_image_path

            # update the ui
            page.update()

            # show snacbar
            set_snackbar("Equation processing",True,"#F53D37")
    
    
    # render latex btn fn
    def render_latex_btn_fn(e):
        
        global global_temp_equation_path
        
        print("Render latex btn function called !!!")

        # get the path for the image
        if (extracted_eqation_latex_field.value != ""):
            
            img_path = latex_to_png_file(extracted_eqation_latex_field.value)
            
            latex_render_img.src = img_path
            global_temp_equation_path = img_path

        page.update()
    
    # eqation calculate btn fn
    def eqation_calculate_btn_fn(e):
        print("Equation calculate btn fn called !!")
    
    
    # fn to handle file picker result
    def on_file_selected(e: flet.FilePickerResultEvent):

        global global_selected_image_path
        global global_image_selected

        if e.files:
            selected_file = e.files[0].path
            print("Selected : ", selected_file)

            # update the image path
            global_selected_image_path = selected_file
            print("global selected image path is : " + global_selected_image_path)
            
            # set values
            select_file_btn.text = "File selected!"
            path_lable.value = global_selected_image_path
            cropper_button.visible = True

            # update the elements
            select_file_btn.update()
            path_lable.update()
            cropper_button.update()

            # set flag true
            global_image_selected = True
    
    # fn to open file dialog
    def open_file_dialog_fn():
        print("Called open file dialog fn !!!")
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"]
        )
    
    # define vars

    # define appbar

    # define widgets

    # define app bar
    page.appbar = AppBar(
        title=Row(
            [
                Text("Math", size=22,font_family="Roboto",weight=flet.FontWeight.BOLD),
                Container(width=10),
                Text("I", size=22,font_family="Roboto",weight=flet.FontWeight.BOLD,color="#0D96FF"),
                Text("/", size=22,font_family="Roboto",weight=flet.FontWeight.BOLD),
                Text("O", size=22,font_family="Roboto",weight=flet.FontWeight.BOLD,color="#F53D37"),
            ],
            alignment=flet.alignment.center_left,
            spacing=1
        ),
        actions=[
            PopupMenuButton(
                
                # items in the popupmenu
                items=[
                    PopupMenuItem(icon=flet.icons.DARK_MODE,text="Change theme",on_click=change_theme_fn),
                    PopupMenuItem(text="Version : 1.0v"),
                ]

            )
        ],
    )

    # define snacbar content

    # the text for the snackbar
    snackbar_text = Text("...", size=20,font_family="Roboto",weight=flet.FontWeight.W_500,color=flet.colors.ON_SURFACE)

    # progress ring for snackbar
    snackbar_progress_ring = ProgressRing(width=16,height=16,stroke_width=3,color="#0D96FF")

    # progress ring

    snackbar_content = Row(
        [
            snackbar_text,
            snackbar_progress_ring
        ],
    )

    # define snackbar
    info_snackbar = SnackBar(
        content=snackbar_content,
    )
    
    
    # define other layouts

    # define input layout widgets

    select_file_btn = ElevatedButton(
        text="Open file",
        #bgcolor="transparent",
        color="#0D96FF", # text color
        width=500,
        height=80,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=30),
            
            side=flet.BorderSide(
                width=2,
                color="#0D96FF"
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=file_btn_fn,
    )

    # to show the imagepath
    path_lable = Text("", size=10,font_family="Roboto",weight=flet.FontWeight.BOLD,color="#0D96FF")

    # mini cropper button
    cropper_button = IconButton(
        icon=icons.CROP,
        icon_color="#0D96FF",
        tooltip="Crop image",
        on_click=cropper_btn_fn
    )
    cropper_button.visible = False

    radio_group = RadioGroup(
        content=Row(
            [
                Radio(
                    value=1,
                    label="text",
                    label_style=flet.TextStyle(
                        size=25,
                        weight=flet.FontWeight.W_700,
                        font_family="Roboto",
                    )
                ),
                Radio(
                    value=2,
                    label="equation",
                    label_style=flet.TextStyle(
                        size=25,
                        weight=flet.FontWeight.W_700,
                        font_family="Roboto"
                    )
                ),
            ],
            alignment=flet.MainAxisAlignment.CENTER,
        ),
        on_change=radio_group_changed_fn,
    )
    radio_group.value = 1 # set default selection to text

    start_btn = ElevatedButton(
        text="Start",
        #bgcolor="transparent",
        color=flet.colors.ON_SURFACE, # text color
        width=250,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color=flet.colors.ON_SURFACE # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=start_btn_fn,
    )

    # input layout
    input_layout = Column(
        [
            # widgets inside the input layout
            
            # define big title
            Column(
                [
                    Text("For processing select an", size=40,font_family="Roboto",weight=flet.FontWeight.BOLD),
                    Text("image", size=40,font_family="Roboto",weight=flet.FontWeight.BOLD,color="#0D96FF"),
                ],
                alignment=flet.MainAxisAlignment.CENTER,
                horizontal_alignment=flet.CrossAxisAlignment.CENTER
            ),

            # spacer
            Container(height=20),

            # Elevated button and path lable
            Column(
                [
                    select_file_btn,
                    Row(
                        [
                            path_lable,
                            Container(width=1),
                            cropper_button,
                        ],
                        alignment=flet.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=flet.MainAxisAlignment.CENTER,
                horizontal_alignment=flet.CrossAxisAlignment.CENTER
            ),

            # space
            Container(height=20),

            # title for process method
            Text("Process :", size=30,font_family="Roboto",weight=flet.FontWeight.BOLD),
            Container(height=3),
            radio_group,

            # spacer
            Container(height=10),

            # start btn
            start_btn,
        ],
        alignment=flet.MainAxisAlignment.CENTER,
        horizontal_alignment=flet.CrossAxisAlignment.CENTER
    )
    input_layout.visible = True

    # define equation processing layout widgets
    
    eqation_img = Image(
        src="eqation.png", # path to image
        fit=flet.ImageFit.COVER,
        border_radius=20,
    )
    
    image_container_for_eqation = Container(
        width=370,
        height=370,
        content=eqation_img,
        padding=5,
        bgcolor="#F53D37",
        border_radius=flet.border_radius.all(20),
    )

    extracted_eqation_latex_field = TextField("...",expand=True,border_width=0,hint_text="latex formula here")

    render_latex_btn = IconButton(
        icon=icons.ARROW_CIRCLE_DOWN_ROUNDED,
        icon_size=35,
        tooltip="render latex",
        icon_color="#AA5959",
        on_click=render_latex_btn_fn
    )

    latex_render_img = Image(
        src="render_place_holder.png",
        border_radius=20,
        fit=flet.ImageFit.CONTAIN,       
    )

    latex_render_conatainer = Container(
        width=500,
        height=150,
        content=latex_render_img,
        padding=10,
        bgcolor=flet.colors.SURFACE_VARIANT,
        border_radius=flet.border_radius.all(20)
    )

    eqation_caluclate_btn = ElevatedButton(
        text="Calculate",
        #bgcolor="transparent",
        color="#F53D37", # text color
        width=250,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color="#F53D37" # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=eqation_calculate_btn_fn,
    )

    close_eqation_layout_btn = ElevatedButton(
        text="Close",
        #bgcolor="transparent",
        color=flet.colors.ON_SURFACE, # text color
        width=250,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color=flet.colors.ON_SURFACE # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=close_eqation_layout_btn_fn,
    )

    # define equation processing layout
    equation_processing_layout = Row(
        [
            image_container_for_eqation,
            Container(width=10),
            Column(
                [
                    # title for extracted eqation layout
                    Text("Latex form :", size=25,font_family="Roboto",weight=flet.FontWeight.BOLD),
                    
                    # spacer
                    Container(height=5),
                    
                    # row for latex field and render button
                    Row(
                        [
                            # container for the extacted eqation
                            Container(
                                width=500,
                                height=70,
                                content=extracted_eqation_latex_field,
                                padding=10,
                                bgcolor=flet.colors.SURFACE_VARIANT,
                                border_radius=flet.border_radius.all(20)
                            ),

                            # render latex button
                            render_latex_btn,
                        ],
                        alignment=flet.MainAxisAlignment.CENTER,
                    ),

                    # spacer
                    Container(height=10),

                    # rendered latex output in image form
                    
                    # label for rendered eqation
                    Text("Rendered equation :", size=25,font_family="Roboto",weight=flet.FontWeight.BOLD),

                    # render latex conatiner
                    latex_render_conatainer,

                    # spacer
                    Container(height=10),

                    # button row
                    Row(
                        [
                            eqation_caluclate_btn,
                            close_eqation_layout_btn,
                        ],
                        alignment=flet.MainAxisAlignment.CENTER,
                    ),
                ],
            ),
        ],
        alignment=flet.MainAxisAlignment.CENTER
    )
    equation_processing_layout.visible = False

    # define widgets for text processing layout

    text_img = Image(
        src="txt.png", # path to image
        fit=flet.ImageFit.COVER,
        border_radius=20,
    )
    
    image_container_for_text = Container(
        width=320,
        height=320,
        content=text_img,
        padding=5,
        bgcolor="#0D96FF",
        border_radius=flet.border_radius.all(20),
    )

    extracted_text_field = TextField("...",expand=True,border_width=0,multiline=True,hint_text="extracted text",read_only=True)

    copy_txt_btn = ElevatedButton(
        text="Copy",
        #bgcolor="transparent",
        color="#0D96FF", # text color
        width=150,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color="#0D96FF" # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=copy_text_btn_fn,
    )

    save_txt_btn = ElevatedButton(
        text="Save text",
        #bgcolor="transparent",
        color="#F53D37", # text color
        width=150,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color="#F53D37" # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=save_text_btn_fn,
    )

    close_text_processing_layout_btn = ElevatedButton(
        text="Close",
        #bgcolor="transparent",
        color=flet.colors.ON_SURFACE, # text color
        width=150,
        height=60,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
            
            side=flet.BorderSide(
                width=2,
                color=flet.colors.ON_SURFACE # border color
            ),
            
            text_style=flet.TextStyle(
                size=20,
                weight=flet.FontWeight.W_700,
                font_family="Roboto"
            ),

        ),
        on_click=close_txt_processing_layout_fn,
    )

    
    # define text processing layout
    text_processing_layout = Row(
        [
            image_container_for_text,
            Container(width=10),
            Column(
                [
                    # title for extracted text layout
                    Text("Extracted text :", size=25,font_family="Roboto",weight=flet.FontWeight.BOLD),
                    
                    # spacer
                    Container(height=5),
                    
                    # container for the extacted text
                    Container(
                        width=500,
                        height=150,
                        content=extracted_text_field,
                        padding=10,
                        bgcolor=flet.colors.SURFACE_VARIANT,
                        border_radius=flet.border_radius.all(20)
                    ),

                    # spacer
                    Container(height=10),

                    # button row
                    Row(
                        [
                            copy_txt_btn,
                            save_txt_btn,
                            close_text_processing_layout_btn
                        ],
                        alignment=flet.MainAxisAlignment.CENTER,
                    ),
                ],
            ),
        ],
        alignment=flet.MainAxisAlignment.CENTER
    )
    text_processing_layout.visible = False

    # cropping layout
    cropping_layout = Column(
        [

        ],
        alignment=flet.MainAxisAlignment.CENTER
    )



    # define the main column
    main_column = Column(
        [
            # add layouts here
            input_layout,
            equation_processing_layout,
            text_processing_layout
        ],
        expand=True,
        alignment=flet.MainAxisAlignment.CENTER
    )

    # def file picker
    file_picker = flet.FilePicker(on_result=on_file_selected)

    # append snackbar
    page.snack_bar = info_snackbar

    # append to page
    page.overlay.append(file_picker)

    # add to the page - this area shows the inserted widgets
    page.add(
        main_column
    )

#flet.app(target=main)
#flet.app(target=main, view=flet.WEB_BROWSER, assets_dir="assets") # you can comment the line above and uncomment this line to run it in a browser
flet.app(target=main, assets_dir="assets") # when assets are used