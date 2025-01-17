from pcbnewTransition import pcbnew
import wx
import re
import os
import kikit
from kikit import modify
from kikit.common import PKG_BASE

class HideReferencesDialog(wx.Dialog):
    def __init__(self, parent=None, board=None):
        wx.Dialog.__init__(self, parent, title=f'Specify which components to hide (version {kikit.__version__})')
        self.board = board

        self.Bind(wx.EVT_CLOSE, self.OnCancel, id=self.GetId())

        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        item_grid = wx.FlexGridSizer(0, 2, 3, 5)
        item_grid.AddGrowableCol(1)

        label = wx.StaticText(panel,
            label="Apply to labels pattern:\n(regular expression)",
            size=wx.Size(200, -1),
            style=wx.ALIGN_RIGHT)
        label.Wrap(200)
        item_grid.Add(label, 1, wx.ALIGN_CENTRE_VERTICAL)
        self.pattern = wx.TextCtrl(panel, style=wx.TE_LEFT, value='.*',
            size=wx.Size(350, -1))
        self.Bind(wx.EVT_TEXT, self.OnPatternChange, id=self.pattern.GetId())
        item_grid.Add(self.pattern, 1, wx.EXPAND)

        label = wx.StaticText(panel, label="What to do:",
            size=wx.Size(200, -1),
            style=wx.ALIGN_RIGHT)
        label.Wrap(200)
        item_grid.Add(label, 1, wx.ALIGN_CENTRE_VERTICAL)
        self.action = wx.Choice(panel, style=wx.CB_DROPDOWN,
            choices=["Show", "Hide"])
        self.action.SetSelection(1)
        item_grid.Add(self.action, 1, wx.EXPAND)

        label = wx.StaticText(panel, label="Apply to:",
            size=wx.Size(200, -1),
            style=wx.ALIGN_RIGHT)
        label.Wrap(200)
        item_grid.Add(label, 1, wx.ALIGN_CENTRE_VERTICAL)
        self.scope = wx.Choice(panel, style=wx.CB_DROPDOWN,
            choices=["References only", "Values only", "References and values"])
        self.scope.SetSelection(2)
        item_grid.Add(self.scope, 1, wx.EXPAND)

        label = wx.StaticText(panel, label="Include all text items:",
            size=wx.Size(200, -1),
            style=wx.ALIGN_RIGHT)
        label.Wrap(200)
        item_grid.Add(label, 1, wx.ALIGN_CENTRE_VERTICAL)
        self.generous = wx.CheckBox(panel)
        self.generous.SetValue(True)
        item_grid.Add(self.generous, 1, wx.EXPAND)

        label = wx.StaticText(panel,
            label="Matching references:",
            size=wx.Size(200, -1),
            style=wx.ALIGN_RIGHT)
        label.Wrap(200)
        item_grid.Add(label, 1, wx.ALIGN_TOP)
        self.matchingText = wx.StaticText(panel,
            label="Matching references:",
            size=wx.Size(350, 80),
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        self.matchingText.Wrap(350)
        self.matchingText.SetMaxSize(wx.Size(350, 80))
        item_grid.Add(self.matchingText, 1, wx.EXPAND)

        button_box = wx.BoxSizer(wx.HORIZONTAL)
        cancelButton = wx.Button(panel, label='Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=cancelButton.GetId())
        button_box.Add(cancelButton, 1, wx.RIGHT, 10)
        self.okButton = wx.Button(panel, label='Apply')
        self.Bind(wx.EVT_BUTTON, self.OnCreate, id=self.okButton.GetId())
        button_box.Add(self.okButton, 1)

        vbox.Add(item_grid, 1, wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL, 10)
        vbox.Add(button_box, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.Centre()

        self.OnPatternChange(None)

    def OnCancel(self, event):
        self.EndModal(0)

    def OnCreate(self, event):
        self.EndModal(1)

    def GetShowLabels(self):
        return self.action.GetSelection() == 0

    def GetPattern(self):
        return self.pattern.GetValue()

    def GetGenerous(self):
        return self.generous.GetValue()

    def ModifyReferences(self):
        return self.scope.GetSelection() in [0, 2]

    def ModifyValues(self):
        return self.scope.GetSelection() in [1, 2]

    def OnPatternChange(self, event):
        try:
            regex = re.compile(self.pattern.GetValue())
            self.okButton.Enable()
            if not self.board:
                self.matchingText.SetLabel("")
            else:
                refs = []
                for footprint in self.board.GetFootprints():
                    if regex.match(footprint.GetReference()):
                        refs.append(footprint.GetReference())
                if len(refs) > 0:
                    self.matchingText.SetLabel(", ".join(refs))
                else:
                    self.matchingText.SetLabel("None")
            self.matchingText.Wrap(350)
        except re.error as e:
            self.okButton.Disable()
            self.matchingText.SetLabel(f"Invalid regular expression: {e}")
            self.matchingText.Wrap(350)


class HideReferencesPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiKit: Show/hide references"
        self.category = "KiKit"
        self.description = "Show/hide references in the board based on regular expression"
        self.icon_file_name = os.path.join(PKG_BASE, "resources", "graphics", "removeRefIcon_24x24.png")
        self.show_toolbar_button = True

    def Run(self):
        try:
            board = pcbnew.GetBoard()
            dialog = HideReferencesDialog(board=board)
            ok = dialog.ShowModal()
            if not ok:
                return
            if dialog.ModifyReferences():
                modify.references(board, dialog.GetShowLabels(), dialog.GetPattern(), dialog.GetGenerous())
            if dialog.ModifyValues():
                modify.values(board, dialog.GetShowLabels(), dialog.GetPattern(), dialog.GetGenerous())
        except Exception as e:
            dlg = wx.MessageDialog(None, f"Cannot perform: {e}", "Error", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
        finally:
            dialog.Destroy()

plugin = HideReferencesPlugin

if __name__ == "__main__":
    import sys
    # Run test dialog
    app = wx.App()

    dialog = HideReferencesDialog(board=pcbnew.LoadBoard(sys.argv[1]))
    dialog.ShowModal()

    app.MainLoop()
