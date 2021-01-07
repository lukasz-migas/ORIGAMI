"""User dialogs"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.config.config import USERS
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_static_text


class DialogAddUser(Dialog):
    """Simple dialog to add user"""

    # ui elements
    users_value, full_name_value, email_value, institution_value = None, None, None, None
    ok_btn, remove_btn, cancel_btn = None, None, None

    def __init__(self, parent):
        Dialog.__init__(self, parent, title="Add user...", size=(400, 300))
        self.parent = parent

        # make gui items
        self.make_gui()

        self.SetSize((500, -1))
        self.Centre()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    @property
    def full_name(self):
        """Full name"""
        return self.full_name_value.GetValue()

    @full_name.setter
    def full_name(self, value: str):
        """Full name"""
        self.full_name_value.SetValue(value.strip())

    @property
    def email(self):
        """Email"""
        return self.email_value.GetValue()

    @email.setter
    def email(self, value: str):
        """Email"""
        self.email_value.SetValue(value.strip())

    @property
    def institution(self):
        """Institution"""
        return self.institution_value.GetValue()

    @institution.setter
    def institution(self, value: str):
        """Institution"""
        self.institution_value.SetValue(value.strip())

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        super(DialogAddUser, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        users_value = make_static_text(panel, "Users:")
        self.users_value = wx.ComboBox(panel, -1, choices=USERS.user_list, style=wx.CB_READONLY)
        self.users_value.Bind(wx.EVT_COMBOBOX, self.on_select_user)

        full_name_value = make_static_text(panel, "Full name:")
        self.full_name_value = wx.TextCtrl(panel, wx.ID_ANY, "")

        email_value = make_static_text(panel, "Email:")
        self.email_value = wx.TextCtrl(panel, wx.ID_ANY, "")

        institution_value = make_static_text(panel, "Institution:")
        self.institution_value = wx.TextCtrl(panel, wx.ID_ANY, "")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Add", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_add_user_account)
        set_tooltip(self.ok_btn, "Add user account to the config")

        self.remove_btn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, -1))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_user_account)
        set_tooltip(self.remove_btn, "Remove user account from the config")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close window.")

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.ok_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.remove_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.cancel_btn)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(users_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.users_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(full_name_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.full_name_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(email_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.email_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(institution_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.institution_value, (n, 1), flag=wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_select_user(self, _evt):
        """Select user"""
        user = self.users_value.GetStringSelection()
        user = user.split("::")
        if user:
            self.full_name, self.email, self.institution = user
            USERS.current_user = self.full_name

    def on_add_user_account(self, _evt):
        """Add user account"""
        full_name = self.full_name
        email = self.email
        institution = self.institution
        if not full_name:
            # Local imports
            from origami.gui_elements.misc_dialogs import DialogBox

            DialogBox(
                title="Forbidden name", msg="Please fill-in at least the full name value to continue", parent=self
            )
            return
        USERS.add_user(full_name, email, institution)
        self.on_update_user_list()

    def on_remove_user_account(self, _evt):
        """Remove user accounts"""
        full_name = self.full_name
        USERS.remove_user(full_name)
        self.on_update_user_list()

    def on_update_user_list(self):
        """Update list of users"""
        user_list = USERS.user_list
        self.users_value.Clear()
        self.users_value.SetItems(user_list)
        if user_list:
            self.users_value.SetStringSelection(user_list[-1])

    def on_ok(self, _evt):
        """Add user"""
        # full_name = self.full_name
        # email = self.email
        # institution = self.institution
        # if not full_name:
        #     from origami.gui_elements.misc_dialogs import DialogBox
        #
        #     DialogBox(
        #         title="Forbidden name", msg="Please fill-in at least the full name value to continue", parent=self
        #     )
        #     return
        #
        # USERS.add_user(full_name, email, institution)

        super(DialogAddUser, self).on_ok(_evt)


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        app = App()
        ex = DialogAddUser(None)
        ex.Show()
        app.MainLoop()

    _main()
