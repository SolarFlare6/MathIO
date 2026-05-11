import flet
from flet import IconButton, Page, Row, TextField, icons, AppBar, Text, PopupMenuButton, PopupMenuItem, Switch, Container, Column, ElevatedButton, Radio, RadioGroup, Image, FilePicker, SnackBar, ProgressRing, Dropdown, Divider, ExpansionTile, AlertDialog
import cv2
import threading
from io import BytesIO
import base64
import time
import os
import PIL
import platform
from image_proccesing import process_image, warp_perspective_image
from ai_engine import image_to_string, latex_to_expr_and_answer, explain_solution_with_ollama, verifyConnection, verify_tesseract_connection

# latex ocr import
from pix2tex.cli import LatexOCR

# Note add if when there are points in last points call function warped perspective, if no points are unavailable call image processing
# TODO : fix the cacheing of the prev. img in verify menu
# TODO : fix cropper function on mac os to run without thread
# TODO : add checks for tesaract and ollama
# TODO : find a fix for latex rendering on mac os



# import mathplot lib without gui backend
import matplotlib
matplotlib.use("Agg")  # (no GUI backend)

import matplotlib.pyplot as plt

# note flet version 0.24.0

# init device
global_device_platform = platform.system()

# init latex orc model
global_latex_ocr_model = LatexOCR()

# global variables 
global_selected_image_path = ""
global_image_selected = False

# temp img vars
global_temp_equation_path = ""
global_temp_img_index = 0
global_temp_equation_file_name = f"equ_temp{global_temp_img_index}.png"
global_verify_path = ""

# global thread vars
stop_event = threading.Event()
last_points = None
global_graywarp = None
global_warped_perp_obj = None
global_verify_cropping = False

def main(page: Page):
    page.title = "Math I/O"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.theme_mode = "light"

    # define functions

    # turn image input into latex
    def img_to_latex(image_path):
        print("Running image to latex function !!!")
        try:

            # open image
            img = PIL.Image.open(image_path)

            # extract latex
            latex = global_latex_ocr_model(img)

            print("Detected Latex : ", latex)
            
            return latex
        except Exception as e:
            print("Latex OCR Error : ", e)
            return None

    def run_verifiy():

        global global_verify_path

        print("Running verify function !!!")
        try:
            if (verify_switch.value):

                # delete the previous images
                delete_verify_img()

                # get verification image
                path_verify, points = process_image(global_selected_image_path,debug=debug_switch.value,verify=verify_switch.value)

                global_verify_path = path_verify

                verify_img.src = global_verify_path
                #verify_img.update()

                open_verify_menu()
            else:
                run_text_processing_new(mode="cont")
        
        except Exception as e:
            print("Error while running verify : ",e)

    
    def run_text_processing_new(mode):
        print("Running new text processing")

        def continue_process():

            global global_graywarp

            try:
                
                graywarp = process_image(global_selected_image_path, lang=lang_dropdown.value, debug=debug_switch.value, verify=False)
                print(type(graywarp))
                global_graywarp = graywarp

                extracted_text_field.value = image_to_string(global_graywarp)
                print("Running image to str with global_graywarp")
                show_text_processing_layout()
            
            except Exception as e:
                print("Error while processing with graywarp : ", e)
                set_snackbar("Error while processing : " + str(e),False,None)

        def crop_process():

            try:
                if (global_warped_perp_obj is not None):
                    extracted_text_field.value = image_to_string(global_warped_perp_obj)
                    print("Running image to str with global_warped_perp_obj")
                    show_text_processing_layout()
            
            except Exception as e:
                print("Error while processing with global_warped_perp_obj : ",e)
                set_snackbar("Error while processing : " + str(e),False,None)
        
        if (mode == "cont"):
            thread_cont = threading.Thread(target=continue_process, daemon=True)
            thread_cont.start()
        if (mode == "crop"):
            thread_crop = threading.Thread(target=crop_process, daemon=True)
            thread_crop.start()


    """def run_text_processing():
        def background_task():
            global global_graywarp  # ADD THIS LINE
            print("Running text processing ...")
            try:
                if global_warped_perp_obj is None:
                    graywarp = process_image(global_selected_image_path, debug=debug_switch.value, verify=verify_switch.value)
                    print(type(graywarp))
                    global_graywarp = graywarp

                    #path_verify,points = process_image(global_selected_image_path, debug=debug_switch.value, verify=verify_switch.value)
                    #global global_verify_path
                    #global_verify_path = path_verify
                    
            except Exception as e:
                print("Error from processing task : ", e)
                set_snackbar(e, False, None)
                return

            # image to str
            try:
                if global_warped_perp_obj is not None:
                    extracted_text_field.value = image_to_string(global_warped_perp_obj)
                    print("Running image to str with global_warped_perp_obj")
                else:
                    extracted_text_field.value = image_to_string(global_graywarp)
                    print("Running image to str with global_graywarp")
                print("Value set to text field...")
                show_text_processing_layout()
                page.update()
            except Exception as e:
                print("Exception : ", e)
                set_snackbar(e, False, None)

        thread = threading.Thread(target=background_task, daemon=True)
        thread.start()"""
    
    """def run_text_processing_old():
        print("Running text processing ...")
        def processing_task():

            global global_graywarp

            print("running task :")
            try:
                if (global_warped_perp_obj is None):
                    graywarp = process_image(global_selected_image_path,debug=debug_switch.value,verify=False)
                    print(type(graywarp))
                    global_graywarp = graywarp
            except Exception as e:
                print("Error from processing task : ", e)
                set_snackbar(e,False,None)
        
        processing_task()

        # image to str
        try:
            if (global_warped_perp_obj is not None):
                extracted_text_field.value = image_to_string(global_warped_perp_obj,lang=lang_dropdown.value)
                print("Running image to str with global_warped_perp_obj")
            else:
                 extracted_text_field.value = image_to_string(global_graywarp)
                 print("Running image to str with global_graywarp")
            print("Value set to text field...")
            show_text_processing_layout()
        except Exception as e:
            print("Exception : ",e)
            set_snackbar(e,False,None)

        page.update()"""

    
    def run_ocr_thread(img_path):
        def task():

            result_latex = img_to_latex(img_path)

            if (result_latex):
                extracted_eqation_latex_field.value = result_latex
                page.update()
                render_latex_to_image()
        
        threading.Thread(target=task,daemon=True).start()
    
    # turn latex input into png
    def latex_to_png_file(latex_str,output_path=global_temp_equation_file_name):
        print("Running latex to png !!!")
        
        try:
            
            fig = plt.figure(figsize=(2, 1))
            fig.patch.set_alpha(0)
            
            
            if (page.theme_mode == "light"):
                print("Setting text as black for light mode.")
                plt.text(
                    0.5,
                    0.5,
                    rf"${latex_str}$",
                    fontsize=30,
                    ha="center",
                    va="center",
                    color="black"
                )
            if (page.theme_mode == "dark"):
                print("Setting text as white for dark mode.")
                plt.text(
                    0.5,
                    0.5,
                    rf"${latex_str}$",
                    fontsize=30,
                    ha="center",
                    va="center",
                    color="white"
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
        
        except Exception as e:
            print("Error while converting latex to png : ", e)
            set_snackbar("Error : " + str(e),False,None)

    # delete temp verify img fn
    def delete_verify_img():
        print("Called delete verify img fn after use !!!")
        try:
            image_path = global_verify_path

            verify_img.src = None
            verify_img.update()

            print("Verify path img to be deletet is : ", image_path)

            if (os.path.exists(image_path)):
                os.remove(image_path)
                print("Deleted verify img.")
        
        except Exception as e:
            print("Error in deleteing verify img : ",e)
    
    # delete the temp img fn
    def delete_rendered_equation():
        print("Called the function to delete the temporary file")

        try:

            image_path = global_temp_equation_path

            print("Image path to be deleted : ", image_path)

            latex_render_img.src = "render_place_holder.png"
            page.update()

            if (os.path.exists(image_path)):
                os.remove(image_path)
                print("deleted temporary file.")
        
        except Exception as e:
            print(e)
    
    # fn for cropping new (has better scaling and can morph with right click)
    def get_4_crop_points(image_path, stop_event):
        try:
            
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
        
        except Exception as e:
            print("get 4 crop points error : ", e)
            set_snackbar("Crop error : "+str(e),False,None)
            return None

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
        
        print("Selected points:", last_points)
        stop_cropper()
    
    # fn to start cropper thread
    def run_cropper_start_thread(image_path):
        
        print("Called function to start cropper...")
        
        if image_path != "":
            stop_event.clear()
            
            if (global_device_platform != "Darwin"):
                
                # When other os run with thread
                print("Not running on Mac OS run with thread !!!")
                
                cropper_thread = threading.Thread(
                    target=run_cropper,
                    args=(image_path,),
                )
                cropper_thread.start()
                print("Started cropper thread")
            else:
                # when running on mac call the window without thread
                print("Running on mac run without thread")
                run_cropper(image_path)
        
        else:
            print("No image selected!!!")
    
    # to stop the thread
    def stop_cropper():
        
        global global_warped_perp_obj
        
        print("Stopping cropper...")

        global global_verify_cropping

        stop_event.set()
        cv2.destroyAllWindows()
        # warp_perspective_image(selected_image_path, points) call
        if (last_points != None):
            print("running warped perspective with coords "+ str(last_points))
            global_warped_perp_obj = warp_perspective_image(global_selected_image_path,last_points)
            set_snackbar("Saved cropping",False,None)
        else:
            global_warped_perp_obj = None
            print("No points from cropper function selected")
            set_snackbar("Cropping canceled",False,None)
        
        if (global_verify_cropping and last_points != None):
            print("Running after cropping...")
            global_verify_cropping = False
            close_verify_menu()
            run_text_processing_new(mode="crop")

    
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

    def check_model_connection(e):
        print("Called check model connection !!!")
        set_snackbar("Checking model ...",True,None)
        try:
            verifyConnection()
            print("Model is configured and Ollama is running.")
            set_snackbar("MathI/O is connected to model.",False,None)
        except Exception as e:
            print("Connection not present, start ollama or configure it.")
            set_snackbar("No connection to model, please start Ollama!",False,None)
    
    def check_tessaract_conf(e):
        print("Called function to check tessaract conf !!!")
        if verify_tesseract_connection():
            print("Tesseract is pressent.")
            set_snackbar("Tesseract is pressent.",False,None)
        else:
            print("Please install tesseract !!")
            set_snackbar("Please install tesseract !!",False,None)

    
    # fn for radio group
    def radio_group_changed_fn(e):
        print("Radio group fn called !!")
        print(radio_group.value)

        radio_val = int(radio_group.value)

        if (radio_val == 1):
            print("Choese text processing.")
            lang_dropdown.visible = True
            page.update()
        
        if (radio_val == 2):
            print("Choese equation processing.")
            lang_dropdown.visible = False
            page.update()
    
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
        copy_to_clipboard(extracted_text_field.value)
    
    def save_text_btn_fn(e):
        print("Save text btn fn called !!")
        open_save_dialog()
    
    # start btn fn
    def start_btn_fn(e):
        print("Start btn pressed fn called !!")

        # implement logic fully later
        if (int(radio_group.value) == 1 and global_image_selected):
            print("Showing text processing layout")
            
            # show snackbar
            #set_snackbar("Text processing",True,None)
            
            # set image source
            text_img.src = global_selected_image_path

            run_verifiy()
            
            # update the ui
            page.update()
        
        if (int(radio_group.value) == 2 and global_image_selected):
            print("Showing eqation processing layout")

            run_ocr_thread(global_selected_image_path)
            
            # visibility
            input_layout.visible = False
            equation_processing_layout.visible = True
            
            # set source for eqation image
            eqation_img.src = global_selected_image_path

            # update the ui
            page.update()

            # show snacbar
            set_snackbar("Equation processing",True,"#F53D37")
    
    
    # render the latex fn universal
    def render_latex_to_image():
        delete_rendered_equation()
        print("Running universal render latex to png fn ...")
        print(extracted_eqation_latex_field.value)
        
        global global_temp_equation_path
        global global_temp_img_index

        # get the path for the image
        if (extracted_eqation_latex_field.value != ""):
            
            global_temp_img_index = global_temp_img_index + 1
            global_temp_equation_file_name = f"equ_temp{global_temp_img_index}.png"
            
            print("global temp image index : ", global_temp_img_index)
            print("global temp image filename : ", global_temp_equation_file_name)
            print("global temp image path : ", global_temp_equation_path)

            img_path = latex_to_png_file(extracted_eqation_latex_field.value,global_temp_equation_file_name)
            
            latex_render_img.src = img_path
            global_temp_equation_path = img_path

        page.update()
    
    # render latex btn fn
    def render_latex_btn_fn(e):
        render_latex_to_image()
    
    # eqation calculate btn fn
    def eqation_calculate_btn_fn(e):
        print("Equation calculate btn fn called !!")
        set_snackbar("Calculating equation...",True,"#F53D37")
        delete_rendered_equation()
        run_solution_thread()
        show_solution_layout()
    
    
    def close_solution_layout_fn(e):
        print("Called close solution layout btn fn !!!")
        show_input_layout()
        destroy_solution_ui()
    
    # fn to handle save file dialog result
    def save_file_result(e: flet.FilePickerResultEvent):
        print("Called save file dialog result fn !!!")
        if e.path:
            with open(e.path, "w", encoding="utf-8") as file:
                file.write(extracted_text_field.value)
            
            print("Saved file : ", e.path)
            set_snackbar("Saved text file",False,None)
        else:
            print("Did not save.")
    
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
    
    # open save dialog
    def open_save_dialog():
        print("Running function to open save dialog !!!")
        save_file_dialog.save_file(
            dialog_title="Save extracted text",
            file_name="extracted_text.txt",
            allowed_extensions=["txt"]
        )
    
    # fn to open file dialog
    def open_file_dialog_fn():
        print("Called open file dialog fn !!!")
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"]
        )
    
    # copy to clipboard fn
    def copy_to_clipboard(txt):
        print("Running copy to clipboard fn with str : " + txt)
        page.set_clipboard(txt)
        set_snackbar("Copied to clipboard",False,None)
    
    def verify_menu_item_fn(e):
        print("Called verify menu item fn !!!")
        if (verify_switch.value):
            verify_switch.value = False
        else:
            verify_switch.value = True
        print("Verifiy switch value : ", verify_switch.value)
        verify_switch.update()
    
    def debug_menu_item_fn(e):
        print("Called debug menu item fn !!!")

        if (debug_switch.value):
            debug_switch.value = False
        else:
            debug_switch.value = True
        print("Debug switch value : ", debug_switch.value)
        
        debug_switch.update()
    
    def show_solution_layout():
        print("Show solution layout fn called !!")
        
        equation_solution_layout.visible = True
        input_layout.visible = False
        equation_processing_layout.visible = False
        text_processing_layout.visible = False

        page.update()

    def show_input_layout():
        print("Show input layout fn called !!")
        
        equation_solution_layout.visible = False
        input_layout.visible = True
        equation_processing_layout.visible = False
        text_processing_layout.visible = False

        page.update()

    def show_eqation_processing_layout():
        print("Show equation processing layout fn called !!")
        
        equation_solution_layout.visible = False
        input_layout.visible = False
        equation_processing_layout.visible = True
        text_processing_layout.visible = False

        page.update()
    
    def show_text_processing_layout():
        print("Show text processing layout fn called !!")
        
        equation_solution_layout.visible = False
        input_layout.visible = False
        equation_processing_layout.visible = False
        text_processing_layout.visible = True

        page.update()
     
    # open verify menu fn
    def open_verify_menu():
        print("Open verify menu fn called !!!")
        page.dialog = verify_alert_dialog
        verify_alert_dialog.open = True
        page.update()
    
    # close verify menu fn
    def close_verify_menu():
        print("Called close verify menu fn !!!")
        verify_alert_dialog.open = False
        page.update()
    
    # continue verify btn fn
    def verify_continue_btn_fn(e):
        print("Called verify continue btn fn !!!")
        close_verify_menu()
        run_text_processing_new(mode="cont")
    
    # verify crop btn fn
    def verify_crop_btn_fn(e):
        print("Called verify crop btn fn !!!")
        global global_verify_cropping

        global_verify_cropping = True

        # run the cropper function
        run_cropper_start_thread(global_selected_image_path)

        

    def ver_menu_item_fn(e):
        print("Running version menu item fn !!!")
    
    # destroy solution ui
    def destroy_solution_ui():
        print("Destroying the solution widgets inside steps_column !!!")
        steps_column.controls.clear()
        page.update()
    
    # fn to add in steps dynamicly
    def build_solution_ui(step_count,step_eqation,desc):
        print("Adding ui component with : " + str(step_count) + "," + step_eqation + "," + desc)
        steps_column.controls.append(
            Column(
                [
                    # Step label
                    Text("Step "+str(step_count+1)+" :", size=20,font_family="Roboto",weight=flet.FontWeight.BOLD),
                    
                    # spacer
                    Container(height=10),
                    
                    # Expansion tile
                    Container(
                        width=780,
                        bgcolor=flet.colors.SURFACE_VARIANT,
                        border_radius=10,
                        padding=15,
                        content=ExpansionTile(
                            width=400,
                            title=Text(step_eqation, size=20,font_family="Roboto",weight=flet.FontWeight.BOLD),
                            affinity=flet.TileAffinity.TRAILING,
                            collapsed_text_color="#B45B5B",
                            text_color="#B45B5B",
                            shape=flet.StadiumBorder(),
                            #expand=False,
                            controls=[
                                Text(desc, size=17,font_family="Roboto",weight=flet.FontWeight.W_700),
                            ],
                        ),
                    ),
                    
                    
                    
                    # spacer
                    Container(height=5),
                    
                    # devider
                    Divider(height=5,color=flet.colors.ON_SURFACE),
                    
                    # spacer
                    Container(height=2),
                ],
                alignment=flet.MainAxisAlignment.CENTER,
                horizontal_alignment=flet.CrossAxisAlignment.CENTER,
            )
        )
        page.update()
    
    def load_solution_in_ui(expression, answer):
        try:
            if verifyConnection():
                response = explain_solution_with_ollama(expression, answer, solution_type = "JSON")
                expression = response["expression"]
                answer = response["answer"]
                steps = response["steps"]
                print(len(response["steps"]))
                for i in range(len(steps)):
                    build_solution_ui(i,steps[i]["situation"],steps[i]["explanation"])
            else:
                print("Could not connect to model.")
                set_snackbar("Could not connect to model",False,None)
        except Exception as e:
            # TODO: Handle The Exception
            print(e)
            set_snackbar("Error while establishing connection with model : "+str(e),False,None)
            show_input_layout()
    
    def run_solution_thread():
        print("Running solution task...")

        def task():
            print("Running the ai thread to get the answer ")
            destroy_solution_ui()
            expression, answer = latex_to_expr_and_answer(extracted_eqation_latex_field.value)
            load_solution_in_ui(expression, answer)
        
        thread_ai = threading.Thread(target=task, daemon=True)
        thread_ai.start()

    # define vars

    # define appbar

    # define widgets

    # define verify dialog image
    verify_img = Image(
        fit=flet.ImageFit.FILL,
        border_radius=30,
    )

    verify_img_container = Container(
        width=250,
        height=250,
        content=verify_img,
        padding=10,
        bgcolor=flet.colors.SURFACE_VARIANT,
        border_radius=flet.border_radius.all(20)
    )

    # define verify dialog buttons
    verify_continue_btn = ElevatedButton(
        text="Continue",
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
        on_click=verify_continue_btn_fn,
    )

    verify_crop_btn = ElevatedButton(
        text="Crop",
        #bgcolor="transparent",
        color=flet.colors.ON_SURFACE, # text color
        width=120,
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
        on_click=verify_crop_btn_fn,
    )


    # Alert dialog
    verify_alert_dialog = AlertDialog(
        title=Column(
            [
                Text("Verify", size=20,font_family="Roboto",weight=flet.FontWeight.BOLD),
            ],
            alignment=flet.MainAxisAlignment.CENTER,
            horizontal_alignment=flet.CrossAxisAlignment.CENTER,
        ),
        content=Column(
            [
                # explanation text
                Text("Check if the points are good if not manually crop them", size=15,font_family="Roboto",weight=flet.FontWeight.W_600),

                # spacer
                Container(height=10),

                # image to display
                verify_img_container,

                # spacer
                Container(height=5),

                # buttons layout
                Row(
                    [
                        verify_continue_btn,
                        Container(height=3),
                        verify_crop_btn,
                    ],
                    alignment=flet.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=flet.MainAxisAlignment.CENTER,
            horizontal_alignment=flet.CrossAxisAlignment.CENTER,
        ),
        #on_dismiss=verify_continue_btn_fn,
    )

    # widgets for popup menu items
    verify_switch = Switch()
    debug_switch = Switch()

    verify_switch.value = True

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
                    PopupMenuItem(icon=flet.icons.ROCKET,text="Check model",on_click=check_model_connection),
                    PopupMenuItem(icon=flet.icons.TEXT_FORMAT,text="Check tessaract",on_click=check_tessaract_conf),
                    PopupMenuItem(
                        content=Row(
                            [
                                Text("Verify"),
                                verify_switch,
                            ],
                        ),
                        on_click=verify_menu_item_fn,
                    ),
                    PopupMenuItem(
                        content=Row(
                            [
                                Text("Debug"),
                                debug_switch,
                            ],
                        ),
                        on_click=debug_menu_item_fn,
                    ),
                    PopupMenuItem(), # devider
                    PopupMenuItem(text="Version : 1.0v",on_click=ver_menu_item_fn),
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
        width=230,
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

    lang_dropdown = Dropdown(
        label="Language",
        hint_text="choose OCR support",
        #border_color=flet.colors.ON_SURFACE,
        #border_color="#0D96FF",
        border_color=flet.colors.ON_SURFACE,
        text_style=flet.TextStyle(
            color=flet.colors.ON_SURFACE,
            font_family="Roboto",
            weight=flet.FontWeight.W_600,
        ),
        border_width=2,
        border_radius=10,
        width=210,
        height=60,
        options=[
            flet.dropdown.Option("eng"),
            flet.dropdown.Option("mkd"),
        ],
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

            # lang support section
            lang_dropdown,

            # spacer
            Container(height=10),
            
            # start btn
            start_btn,

            # spacer
            Container(height=10),

        ],
        alignment=flet.MainAxisAlignment.CENTER,
        horizontal_alignment=flet.CrossAxisAlignment.CENTER
    )
    input_layout.visible = True

    # define equation processing layout widgets
    
    eqation_img = Image(
        src="eqation.png", # path to image
        fit=flet.ImageFit.FILL,
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

    extracted_eqation_latex_field = TextField("...",expand=True,border_width=0,hint_text="latex formula here",on_submit=render_latex_btn_fn)

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

    # define widgets for eqation layout

    # solution steps column
    
    steps_column = Column(
        [
            
        ],
        spacing=5,
        scroll=flet.ScrollMode.AUTO,
        expand=True,
    )

    # solution conatiner

    solution_container = Container(
        width=1100,
        height=400,
        border_radius=10,
        padding=20,
        border=flet.border.all(
            width=3,
            color=flet.colors.ON_SURFACE,
        ),
        content=steps_column,
    )

    close_solution_layout_btn = ElevatedButton(
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
        on_click=close_solution_layout_fn,
    )
    
    # equation solution layout
    equation_solution_layout = Column(
        [

            # Solution label
            Text("Solution", size=25,font_family="Roboto",weight=flet.FontWeight.BOLD),

            # spacer
            Container(height=10),

            # solution container
            solution_container,

            # spacer
            Container(height=10),

            # close btn
            close_solution_layout_btn,

            # spacer
            Container(height=10),

        ],
        alignment=flet.MainAxisAlignment.CENTER,
        horizontal_alignment=flet.CrossAxisAlignment.CENTER,
    )
    equation_solution_layout.visible = False



    # define the main column
    main_column = Column(
        [
            # add layouts here
            input_layout,
            equation_processing_layout,
            text_processing_layout,
            equation_solution_layout,
        ],
        expand=True,
        alignment=flet.MainAxisAlignment.CENTER
    )

    # def file picker
    file_picker = flet.FilePicker(on_result=on_file_selected)

    # def save file dialog
    save_file_dialog = flet.FilePicker(on_result=save_file_result)

    # append snackbar
    page.snack_bar = info_snackbar

    # append to page
    page.overlay.append(file_picker)
    page.overlay.append(save_file_dialog)

    # add to the page - this area shows the inserted widgets
    page.add(
        main_column
    )

#flet.app(target=main)
#flet.app(target=main, view=flet.WEB_BROWSER, assets_dir="assets") # you can comment the line above and uncomment this line to run it in a browser
flet.app(target=main, assets_dir="assets") # when assets are used