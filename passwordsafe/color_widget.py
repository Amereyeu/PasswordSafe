# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import typing
from enum import Enum
from uuid import UUID

from gi.repository import Gdk, GObject, Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.scrolled_page import ScrolledPage
    from passwordsafe.unlocked_database import UnlockedDatabase


class Color(Enum):
    NONE = "NoneColorButton"
    BLUE = "BlueColorButton"
    GREEN = "GreenColorButton"
    YELLOW = "YellowColorButton"
    ORANGE = "OrangeColorButton"
    RED = "RedColorButton"
    PURPLE = "PurpleColorButton"
    BROWN = "BrownColorButton"


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/color_button.ui")
class ColorButton(Gtk.FlowBoxChild):  # pylint: disable=too-few-public-methods

    __gtype_name__ = "ColorButton"

    _selected_image = Gtk.Template.Child()

    selected = GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, color: Color, selected: bool):
        """RadioButton to select the color of an entry

        :param Color color: color of the button
        :param bool selected: True if the color is selected
        """
        super().__init__()

        self._color: Color = color
        self.get_style_context().add_class(self._color.value)

        if self._color == Color.NONE:
            image_class: str = "DarkIcon"
        else:
            image_class = "BrightIcon"

        self._selected_image.get_style_context().add_class(image_class)

        self.bind_property("selected", self._selected_image, "visible")
        self.props.selected = selected

    @property
    def color(self) -> str:
        """"Color of the widget."""
        return self._color.value

    @Gtk.Template.Callback()
    def _on_enter_event(self, _widget: Gtk.EventBox, _event: Gdk.Event) -> None:
        self.set_state_flags(Gtk.StateFlags.PRELIGHT, False)

    @Gtk.Template.Callback()
    def _on_leave_event(self, _widget: Gtk.EventBox, _event: Gdk.Event) -> None:
        self.unset_state_flags(Gtk.StateFlags.PRELIGHT)


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/color_entry_row.ui")
class ColorEntryRow(Gtk.ListBoxRow):  # pylint: disable=too-few-public-methods

    __gtype_name__ = "ColorEntryRow"

    _flowbox = Gtk.Template.Child()

    def __init__(
            self, unlocked_database: UnlockedDatabase,
            scrolled_page: ScrolledPage, entry_uuid: UUID):
        """Widget to select the color of an entry

        :param UnlockedDatabase unlocked_database: unlocked database
        :param ScrolledPage scrolled_page: container of the widget
        :param UUID entry_uuid: uuid of the entry
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._scrolled_page: ScrolledPage = scrolled_page
        self._entry_uuid: UUID = entry_uuid

        self._selected_color: str = self._db_manager.get_entry_color(entry_uuid)

        for color in Color:
            active: bool = (self._selected_color == color.value)
            color_button: ColorButton = ColorButton(color, active)
            self._flowbox.insert(color_button, -1)
            if active:
                self._flowbox.select_child(color_button)

    @Gtk.Template.Callback()
    def _on_color_activated(
            self, _flowbox: Gtk.FlowBox, selected_child: Gtk.FlowBoxChild) -> None:
        self._unlocked_database.start_database_lock_timer()
        if selected_child.props.selected:
            return

        for child in self._flowbox.get_children():
            selected: bool = (child == selected_child)
            child.props.selected = selected

        self._scrolled_page.is_dirty = True
        self._db_manager.set_entry_color(self._entry_uuid, selected_child.color)
