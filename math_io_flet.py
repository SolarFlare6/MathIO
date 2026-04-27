import flet
from flet import IconButton, Page, Row, TextField, icons, AppBar, Text, PopupMenuButton, PopupMenuItem, Switch, Container, Column, ElevatedButton, Radio, RadioGroup, Image, FilePicker

# global variables 
global_selected_image_path = ""
global_image_selected = False

def main(page: Page):
    page.title = "Math I/O"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.theme_mode = "light"

    # define functions

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
        
        if (int(radio_group.value) == 2 and global_image_selected):
            print("Showing eqation processing layout")
            
            # visibility
            input_layout.visible = False
            equation_processing_layout.visible = True
            
            # set source for eqation image
            eqation_img.src = global_selected_image_path

            # update the ui
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
            select_file_btn.text = "File selected!"
            path_lable.value = global_selected_image_path
            select_file_btn.update()
            path_lable.update()

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

    # define other layouts

    # define input layout widgets

    select_file_btn = ElevatedButton(
        text="File",
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

    path_lable = Text("", size=10,font_family="Roboto",weight=flet.FontWeight.BOLD,color="#0D96FF")

    radio_group = RadioGroup(
        content=Row(
            [
                Radio(
                    value=1,
                    label="text",
                    label_style=flet.TextStyle(
                        size=25,
                        weight=flet.FontWeight.W_700,
                        font_family="Roboto"
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
                    Text("Select or drag and drop an", size=40,font_family="Roboto",weight=flet.FontWeight.BOLD),
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
                    path_lable
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

    extracted_eqation_label = Text("...", size=20,font_family="Roboto",weight=flet.FontWeight.W_600)

    eqation_caluclate_btn = ElevatedButton(
        text="Calculate",
        #bgcolor="transparent",
        color="#F53D37", # text color
        width=500,
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
        width=500,
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
                    Text("Extracted equation :", size=25,font_family="Roboto",weight=flet.FontWeight.BOLD),
                    
                    # spacer
                    Container(height=5),
                    
                    # container for the extacted eqation
                    Container(
                        width=500,
                        height=150,
                        content=extracted_eqation_label,
                        padding=10,
                        bgcolor=flet.colors.SURFACE_VARIANT,
                        border_radius=flet.border_radius.all(20)
                    ),

                    # spacer
                    Container(height=10),

                    # button column
                    Column(
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

    extracted_text_label = Text("...", size=20,font_family="Roboto",weight=flet.FontWeight.W_600)

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
                        content=extracted_text_label,
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

    # append to page
    page.overlay.append(file_picker)

    # add to the page - this area shows the inserted widgets
    page.add(
        main_column
    )

flet.app(target=main)
#flet.app(target=main, view=flet.WEB_BROWSER, assets_dir="assets") # you can comment the line above and uncomment this line to run it in a browser
#flet.app(target=main, assets_dir="assets") # when assets are used