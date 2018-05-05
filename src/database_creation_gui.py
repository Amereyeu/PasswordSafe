import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import database
from database import KeepassLoader
import database_creation_success_gui
from database_creation_success_gui import DatabaseCreationSuccessGui

class DatabaseCreationGui:
    builder = NotImplemented
    keepass_loader = NotImplemented
    parent_widget = NotImplemented
    window = NotImplemented
    switched = False

    def __init__(self, window, widget, kpl):
        self.keepass_loader = kpl
        self.window = window
        self.parent_widget = widget
        self.password_creation()
 
    def password_creation(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/create_database.ui")

        self.set_headerbar()

        self.stack = self.builder.get_object("database_creation_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
        password_creation_button = self.builder.get_object("password_creation_button")
        password_creation_button.connect("clicked", self.on_password_creation_button_clicked)

        password_creation_input = self.builder.get_object("password_creation_input")
        password_creation_input.connect("activate", self.on_password_creation_button_clicked)

        self.parent_widget.add(self.stack)

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        self.window.set_titlebar(headerbar)
        self.parent_widget.set_headerbar(headerbar)
        back_button = self.builder.get_object("back_button")
        back_button.connect("clicked", self.on_headerbar_back_button_clicked)



    def on_headerbar_back_button_clicked(self, widget):
        if self.stack.get_visible_child_name() == "page0":
            self.window.close_tab(self.parent_widget)
        elif self.stack.get_visible_child_name() == "page1":
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
            self.switched = True
            self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
            self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        elif self.stack.get_visible_child_name() == "page2":
            back_button = self.builder.get_object("back_button")
            back_button.destroy()


    def on_password_creation_button_clicked(self, widget):
        password_creation_input = self.builder.get_object("password_creation_input")
        self.keepass_loader.set_password_try(password_creation_input.get_text())

        if self.switched:
            self.stack.set_visible_child(self.stack.get_child_by_name("page1"))
        else:
            self.check_password_page()

    def check_password_page(self):
        self.stack.set_visible_child(self.stack.get_child_by_name("page1"))

        password_check_button = self.builder.get_object("password_check_button")
        password_check_button.connect("clicked", self.on_password_check_button_clicked)

        password_check_input = self.builder.get_object("password_check_input")
        password_check_input.connect("activate", self.on_password_check_button_clicked)


    def on_password_check_button_clicked(self, widget):
        print("führe funktion aus: on_password_check_button_clicked")
        password_check_input = self.builder.get_object("password_check_input")
        self.keepass_loader.set_password_check(password_check_input.get_text())

        if self.keepass_loader.compare_passwords():
            self.keepass_loader.set_database_password(password_check_input.get_text())
            self.success_page()
        else:
            self.repeat_page()

    def success_page(self):
        print("Datenbank Pfad: " + self.keepass_loader.get_database())
        self.clear_input_fields()
        self.parent_widget.remove(self.stack)
        DatabaseCreationSuccessGui(self.window, self.parent_widget)

    def repeat_page(self):
        self.stack.set_visible_child(self.stack.get_child_by_name("page2"))

        password_repeat_button = self.builder.get_object("password_repeat_button")
        password_repeat_button.connect("clicked", self.on_password_repeat_button_clicked)

        password_repeat_input2 = self.builder.get_object("password_repeat_input2")
        password_repeat_input2.connect("activate", self.on_password_repeat_button_clicked)

    def on_password_repeat_button_clicked(self, widget):
        password_repeat_input1 = self.builder.get_object("password_repeat_input1")
        password_repeat_input2 = self.builder.get_object("password_repeat_input2")

        self.keepass_loader.set_password_try(password_repeat_input1.get_text())
        self.keepass_loader.set_password_check(password_repeat_input2.get_text())

        if self.keepass_loader.compare_passwords():
            self.keepass_loader.set_database_password(password_repeat_input2.get_text())
            self.success_page()
        else:
            self.clear_input_fields()
            password_repeat_input1.get_style_context().add_class("error")
            password_repeat_input2.get_style_context().add_class("error")

    def clear_input_fields(self):
        password_creation_input = self.builder.get_object("password_creation_input")
        password_check_input = self.builder.get_object("password_check_input")
        password_repeat_input1 = self.builder.get_object("password_repeat_input1")
        password_repeat_input2 = self.builder.get_object("password_repeat_input2")

        password_creation_input.set_text("")
        password_check_input.set_text("")
        password_repeat_input1.set_text("")
        password_repeat_input2.set_text("")
