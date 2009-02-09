#!/usr/bin/python
# generated by wxGlade 0.3.3 on Mon Jun 14 06:48:07 2004

import wx
import wx.aui

import os
import sys

#import viewpanel
import PYME.cSMI as example
import dCrop
import logparser

import tables
import wx.py.crust

from myviewpanel_numarray import MyViewPanel

class DSViewFrame(wx.Frame):
    def __init__(self, parent=None, title='', dstack = None, log = None, filename = None):
        wx.Frame.__init__(self,parent, -1, title,size=wx.Size(626,500))

        self.ds = dstack
        self.log = log

        self.saved = True		

        if (dstack == None):
            if (filename == None):
                fdialog = wx.FileDialog(None, 'Please select Data Stack to open ...',
                    wildcard='*.h5', style=wx.OPEN|wx.HIDE_READONLY)
                succ = fdialog.ShowModal()
                if (succ == wx.ID_OK):
                    #self.ds = example.CDataStack(fdialog.GetPath().encode())
                    #self.ds = 
                    self.h5file = tables.openFile(fdialog.GetPath())
                    self.ds = self.h5file.root.ImageData
                    self.SetTitle(fdialog.GetFilename())
                    self.saved = True
                    #fn =
            else:
                self.h5file = tables.openFile(filename)
                self.ds = self.h5file.root.ImageData
                self.SetTitle(filename)
                self.saved = True
                #self.ds = example.CDataStack(filename)
                #self.SetTitle(fdialog.GetFilename())
                self.saved = True

        
        self.notebook1 = wx.aui.AuiNotebook(id=-1, parent=self, pos=wx.Point(0, 0), size=wx.Size(618,
              450), style=wx.aui.AUI_NB_TAB_SPLIT)


        self.vp = MyViewPanel(self.notebook1, self.ds)
        self.sh = wx.py.shell.Shell(id=-1,
              parent=self.notebook1, pos=wx.Point(0, 0), size=wx.Size(618, 451), style=0, locals=self.__dict__, 
              introText='Python SMI bindings - note that help, license etc below is for Python, not PySMI\n\n')
        self.sh.runfile(os.path.join(os.path.dirname(__file__),'fth5.py'))

        self.notebook1.AddPage(page=self.vp, select=True, caption='Data')
        self.notebook1.AddPage(page=self.sh, select=False, caption='Console')
        #self.notebook1.Split(0, wx.TOP)
        

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.notebook1, 1,wx.EXPAND,0)
        #self.SetAutoLayout(1)
        self.SetSizer(self.sizer)
        #sizer.Fit(self)
        #sizer.SetSizeHints(self)

        # Menu Bar
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        tmp_menu = wx.Menu()
        #F_SAVE = wx.NewId()
        #F_CLOSE = wx.NewId()
        tmp_menu.Append(wx.ID_SAVEAS, "Save As", "", wx.ITEM_NORMAL)
        tmp_menu.Append(wx.ID_CLOSE, "Close", "", wx.ITEM_NORMAL)
        self.menubar.Append(tmp_menu, "File")

        mEdit = wx.Menu()
        EDIT_CLEAR_SEL = wx.NewId()
        EDIT_CROP = wx.NewId()
        mEdit.Append(EDIT_CLEAR_SEL, "Reset Selection", "", wx.ITEM_NORMAL)
        mEdit.Append(EDIT_CROP, "Crop", "", wx.ITEM_NORMAL)
        self.menubar.Append(mEdit, "Edit")

        # Menu Bar end
        wx.EVT_MENU(self, wx.ID_SAVEAS, self.saveStack)
        wx.EVT_MENU(self, wx.ID_CLOSE, self.menuClose)
        wx.EVT_MENU(self, EDIT_CLEAR_SEL, self.clearSel)
        wx.EVT_MENU(self, EDIT_CROP, self.crop)
        wx.EVT_CLOSE(self, self.OnCloseWindow)
		
        self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)

        self.Layout()
        self.update()

    def update(self):
        self.vp.imagepanel.Refresh()
        self.statusbar.SetStatusText('Slice No: (%d/%d)' % (self.vp.zp, self.vp.ds.shape[2]))

    def saveStack(self, event=None):
        fdialog = wx.FileDialog(None, 'Save Data Stack as ...',
            wildcard='*.kdf', style=wx.SAVE|wx.HIDE_READONLY)
        succ = fdialog.ShowModal()
        if (succ == wx.ID_OK):
            self.ds.SaveToFile(fdialog.GetPath().encode())
            if not (self.log == None):
                lw = logparser.logwriter()
                s = lw.write(self.log)
                log_f = file('%s.log' % fdialog.GetPath().split('.')[0], 'w')
                log_f.write(s)
                log_f.close()
                
            self.SetTitle(fdialog.GetFilename())
            self.saved = True

    def menuClose(self, event):
        self.Close()

    def OnCloseWindow(self, event):
        if (not self.saved):
            dialog = wx.MessageDialog(self, "Save data stack?", "pySMI", wx.YES_NO|wx.CANCEL)
            ans = dialog.ShowModal()
            if(ans == wx.ID_YES):
                self.saveStack()
                self.Destroy()
            elif (ans == wx.ID_NO):
                self.Destroy()
            else: #wxID_CANCEL:   
                if (not event.CanVeto()): 
                    self.Destroy()
                else:
                    event.Veto()
        else:
            self.Destroy()
			
    def clearSel(self, event):
        self.vp.ResetSelection()
        self.vp.Refresh()
        
    def crop(self, event):
        cd = dCrop.dCrop(self, self.vp)
        if cd.ShowModal():
            ds2 = example.CDataStack(self.ds, cd.x1, cd.y1, cd.z1, cd.x2, cd.y2, cd.z2, cd.chs)
            dvf = DSViewFrame(self.GetParent(), '--cropped--', ds2)
            dvf.Show()



class MyApp(wx.App):
    def OnInit(self):
        #wx.InitAllImageHandlers()
        if (len(sys.argv) > 1):
            vframe = DSViewFrame(None, sys.argv[1], filename=sys.argv[1])
        else:
            vframe = DSViewFrame(None, '')           

        self.SetTopWindow(vframe)
        vframe.Show(1)

        #crFrame = wx.py.shell.ShellFrame(parent = vframe, locals = vframe.__dict__)
        #crFrame.Show()
        #print __file__
        #crFrame.shell.runfile(os.path.join(os.path.dirname(__file__),'fth5.py'))
        return 1

# end of class MyApp

def main():
    app = MyApp(0)
    app.MainLoop()


if __name__ == "__main__":
    main()
