# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import threading
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

import passwordsafe.config_manager
from passwordsafe import const
from passwordsafe.database_manager import DatabaseManager
from passwordsafe.unlocked_database import UnlockedDatabase
from passwordsafe.utils import KeyFileFilter


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/gtk/unlock_database.ui")
class UnlockDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "UnlockDatabase"

    database_filepath = None
    keyfile_path = None
    _keyfile_hash = None

    database_manager = None

    clear_button = Gtk.Template.Child()
    keyfile_button = Gtk.Template.Child()
    keyfile_label = Gtk.Template.Child()
    keyfile_spinner = Gtk.Template.Child()
    keyfile_stack = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    spinner_stack = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    unlock_button = Gtk.Template.Child()
    status_page = Gtk.Template.Child()

    def __init__(self, window, database):
        super().__init__()

        filepath = database.get_path()

        self.window = window
        self.database_filepath = filepath
        self.headerbar = self.window.unlock_database_headerbar

        # Reset headerbar to initial state if it already exists.
        self.headerbar.title.props.title = database.get_basename()
        self.headerbar.back_button.props.sensitive = True

        self.install_action("clear-keyfile", None, self.on_clear_keyfile)

        database = self.window.unlocked_db
        if database:
            is_current = database.database_manager.database_path == filepath
            if is_current:
                self.database_manager = database.database_manager

        if passwordsafe.config_manager.get_remember_composite_key():
            self._get_last_used_keyfile()

        if passwordsafe.const.IS_DEVEL:
            self.status_page.props.icon_name = passwordsafe.const.APP_ID

    def do_realize(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_realize(self)

        self.password_entry.grab_focus()

    @Gtk.Template.Callback()
    def _on_keyfile_button_clicked(self, _widget):
        """cb invoked when we unlock a database via keyfile"""
        dialog = Gtk.FileChooserNative.new(
            _("Select Keyfile"), self.window, Gtk.FileChooserAction.OPEN, None, None
        )
        dialog.add_filter(KeyFileFilter().file_filter)
        dialog.connect("response", self.on_dialog_response, dialog)
        dialog.show()

    def on_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType, _dialog: Gtk.Dialog
    ) -> None:
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            keyfile = dialog.get_file()
            self.set_keyfile(keyfile)

    def set_keyfile(self, keyfile: Gio.File) -> None:
        self.keyfile_path = keyfile.get_path()
        keyfile.load_bytes_async(None, self.load_keyfile_callback)

        self.keyfile_stack.props.visible_child_name = "spinner"
        self.keyfile_spinner.start()
        self.keyfile_button.props.sensitive = False

        logging.debug("Keyfile selected: %s", keyfile.get_path())

    def load_keyfile_callback(self, keyfile, result):
        try:
            gbytes, _etag = keyfile.load_bytes_finish(result)
            if not gbytes:
                raise Exception("IO operation error")

        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not set keyfile hash: %s", err)

            self._wrong_keyfile()
        else:
            keyfile_hash = GLib.compute_checksum_for_bytes(
                GLib.ChecksumType.SHA1, gbytes
            )
            file_path = keyfile.get_path()
            basename = keyfile.get_basename()
            if keyfile_hash:
                self.keyfile_hash = keyfile_hash
                self.keyfile_path = file_path

            self._reset_keyfile_button()
            self.keyfile_label.set_label(basename)
        finally:
            self.keyfile_stack.props.visible_child_name = "label"
            self.keyfile_spinner.stop()
            self.keyfile_button.props.sensitive = True

    def is_safe_open_elsewhere(self) -> bool:
        """Returns True if the safe is already open but not in the current window."""
        is_current = False
        filepath = self.database_filepath
        database = self.window.unlocked_db
        is_open = self.window.application.is_safe_open(filepath)

        if database:
            is_current = database.database_manager.database_path == filepath

        return is_open and not is_current

    @Gtk.Template.Callback()
    def _on_password_entry_activate(self, _entry):
        self.unlock_button.activate()

    @Gtk.Template.Callback()
    def _on_unlock_button_clicked(self, _widget):
        entered_pwd = self.password_entry.get_text()
        if not (entered_pwd or self.keyfile_path):
            return

        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                _("Safe {} is Already Open".format(self.database_filepath))
            )
            return

        if self.database_manager:
            if (
                entered_pwd == self.database_manager.password
                and self.database_manager.keyfile_hash == self.keyfile_hash
            ):
                self.database_manager.props.locked = False
                if passwordsafe.config_manager.get_remember_composite_key():
                    self._set_last_used_keyfile()
            else:
                self._unlock_failed()
        else:
            self._open_database()

    def _set_last_used_keyfile(self):
        remove = self.keyfile_path is None
        pairs = passwordsafe.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_filepath).get_uri()
        pair_array = []
        already_added = False

        for pair in pairs:
            if pair[0] == uri:
                pair[1] = self.keyfile_path
                already_added = True
                if remove:  # We skip adding
                    continue

            pair_array.append(pair)

        if not already_added and not remove:
            pair_array.append([uri, self.keyfile_path])

        # We need to check if the new value differs from the old one, since lists
        # aren't hasheable we need to turn the inner lists into tuples.
        if {tuple(pair) for pair in pairs} != {tuple(pair) for pair in pair_array}:
            passwordsafe.config_manager.set_last_used_composite_key(pair_array)

    def _get_last_used_keyfile(self):
        pairs = passwordsafe.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_filepath).get_uri()
        if pairs:
            keyfile_path = None

            for pair in pairs:
                if pair[0] == uri:
                    keyfile_path = pair[1]
                    break

            if keyfile_path is not None:
                keyfile = Gio.File.new_for_path(keyfile_path)
                if keyfile.query_exists():
                    self.set_keyfile(keyfile)

    #
    # Open Database
    #

    def _open_database(self):
        self.spinner_stack.props.visible_child_name = "spinner"
        self.spinner.start()

        self._set_sensitive(False)
        unlock_thread = threading.Thread(target=self._open_database_process)
        unlock_thread.daemon = True
        unlock_thread.start()

    def _open_database_process(self):
        password = self.password_entry.props.text
        keyfile = self.keyfile_path

        if Path(self.database_filepath).suffix == ".kdb":
            GLib.idle_add(self._unlock_failed)
            # NOTE kdb is a an older format for Keepass databases.
            GLib.idle_add(
                self.window.send_notification, _("The kdb Format is not Supported")
            )
            return

        try:
            self.database_manager = DatabaseManager(
                self.database_filepath, password, keyfile, self.keyfile_hash
            )
        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not open safe: %s", err)
            GLib.idle_add(self._unlock_failed)
        else:
            GLib.idle_add(self._open_database_success)

    def _open_database_success(self):
        logging.debug("Opening of database was successful")

        opened = Gio.File.new_for_path(self.database_filepath)
        passwordsafe.config_manager.set_last_opened_database(opened.get_uri())

        if passwordsafe.config_manager.get_remember_composite_key():
            self._set_last_used_keyfile()

        if passwordsafe.config_manager.get_development_backup_mode():
            self.store_backup(opened)

        already_added = False
        path_listh = []
        for path in passwordsafe.config_manager.get_last_opened_list():
            path_listh.append(path)
            if path == opened.get_uri():
                already_added = True

        if not already_added:
            path_listh.append(opened.get_uri())
        else:
            path_listh.sort(key=opened.get_uri().__eq__)

        if len(path_listh) > 10:
            path_listh.pop(0)

        passwordsafe.config_manager.set_last_opened_list(path_listh)

        if self.window.unlocked_db is None:
            database = UnlockedDatabase(self.window, self.database_manager)
            self.window.unlocked_db = database
            self.window.unlocked_db_bin.props.child = database

        self.window.view = self.window.View.UNLOCKED_DATABASE
        self._reset_page()

    #
    # Helper Functions
    #

    def _unlock_failed(self):
        self.window.send_notification(_("Failed to Unlock Safe"))

        self.password_entry.add_css_class("error")
        self._set_sensitive(True)
        self._reset_unlock_button()

        logging.debug("Could not open database")

    def _wrong_keyfile(self):
        self.keyfile_button.add_css_class("destructive-action")

        self.keyfile_label.set_label(_("_Try Again"))

    def _reset_keyfile_button(self):
        self.keyfile_button.remove_css_class("destructive-action")

        self.keyfile_label.set_label(_("_Select Keyfile"))

    def _reset_unlock_button(self):
        self.spinner.stop()
        self.spinner_stack.props.visible_child_name = "image"

    def _reset_page(self):
        self.keyfile_path = None
        self.keyfile_hash = None

        self.password_entry.set_text("")
        self.password_entry.remove_css_class("error")

        self._set_sensitive(True)

        self._reset_keyfile_button()
        self._reset_unlock_button()

    def _set_sensitive(self, sensitive):
        self.password_entry.set_sensitive(sensitive)
        self.keyfile_button.set_sensitive(sensitive)
        self.unlock_button.set_sensitive(sensitive)

        self.action_set_enabled("clear-keyfile", sensitive)

        back_button = self.headerbar.back_button
        back_button.set_sensitive(sensitive)

    def on_clear_keyfile(self, _widget, _name, _param):
        self.keyfile_path = None
        self.keyfile_hash = None

        self._reset_keyfile_button()

    def store_backup(self, gfile):
        cache_dir = os.path.join(GLib.get_user_cache_dir(), const.SHORT_NAME, "backup")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        current_time = GLib.DateTime.new_now_local().format("%F_%T")
        basename = os.path.splitext(gfile.get_basename())[0]
        backup_name = basename + "_backup_" + current_time + ".kdbx"
        backup = Gio.File.new_for_path(os.path.join(cache_dir, backup_name))

        def callback(gfile, result):
            try:
                success = gfile.copy_finish(result)
                if not success:
                    raise Exception("IO operation error")
            except Exception as err:  # pylint: disable=broad-except
                logging.warning("Could not save database backup: %s", err)

        gfile.copy_async(
            backup,
            Gio.FileCopyFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            None,
            None,
            callback,
        )

    @property
    def keyfile_hash(self) -> str | None:
        return self._keyfile_hash

    @keyfile_hash.setter  # type: ignore
    def keyfile_hash(self, keyfile_hash: str | None) -> None:
        self._keyfile_hash = keyfile_hash
        self.clear_button.props.visible = keyfile_hash is not None
