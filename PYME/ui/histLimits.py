#!/usr/bin/python

##################
# histLimits.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##################
import time
import wx
import wx.lib.newevent

import sys,math
import numpy as np
import os

LimitChangeEvent, EVT_LIMIT_CHANGE = wx.lib.newevent.NewCommandEvent()

class HistLimitPanel(wx.Panel):
    def __init__(self, parent, id, data, limit_lower, limit_upper, log=False, size =(200, 100), pos=(0,0), threshMode= False):
        wx.Panel.__init__(self, parent, id, size=size, pos=pos, style=wx.BORDER_SUNKEN)

        self.data = data.ravel()
        self.data = self.data[np.isfinite(self.data)]

        self.dragging = None
        self.binSize=None
        
        dSort = np.argsort(self.data)
        
        self.upper_pctile = float(self.data[dSort[int(len(self.data)*.99)]])
        self.lower_pctile = float(self.data[dSort[int(len(self.data)*.01)]])

        self.dmin = self.data[dSort[0]]
        self.dmax = self.data[dSort[-1]]

        self.limit_lower = float(limit_lower)
        self.limit_upper = float(limit_upper)

        self.textSize = 10
        self.log = log

        self.threshMode = threshMode

        if self.threshMode:
            #thresh =  0.5*(self.limit_lower + self.limit_upper)
            thresh =  0.5*(self.lower_pctile + self.upper_pctile)
            self.limit_lower = thresh
            self.limit_upper = thresh

        self.GenHist()


        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
        wx.EVT_LEFT_UP(self, self.OnLeftUp)
        wx.EVT_MOTION(self, self.OnMouseMove)
        wx.EVT_KEY_DOWN(self, self.OnKeyPress)

    def SetData(self, data, lower, upper):
        self.data = np.array(data).ravel()
        self.data = self.data[np.isfinite(self.data)]

        dSort = np.argsort(self.data)

        self.upper_pctile = float(self.data[dSort[int(len(self.data)*.99)]])
        self.lower_pctile = float(self.data[dSort[int(len(self.data)*.01)]])

        self.dmin = self.data[dSort[0]]
        self.dmax = self.data[dSort[-1]]

        self.limit_lower = float(lower)
        self.limit_upper = float(upper)

        if self.threshMode:
            thresh =  0.5*(self.limit_lower + self.limit_upper)
            self.limit_lower = thresh
            self.limit_upper = thresh

        self.GenHist()
        self.Refresh()
        self.Update()

    def OnLeftDown(self, event):
        x = event.GetX()
        #y = event.GetY()

        #hit test the limits
        llx = (self.limit_lower - self.hmin)/self.hstep
        ulx = (self.limit_upper - self.hmin)/self.hstep

        if self.threshMode and abs(llx - x) < 3:
            self.dragging = 'thresh'
        elif abs(llx - x) < 3:
            self.dragging = 'lower'
        elif abs(ulx - x) < 3:
            self.dragging = 'upper'

        event.Skip()

    def OnLeftUp(self, event):
        #x = event.GetX()
        #y = event.GetY()

        if not self.dragging is None:
            evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
            #evt.ShouldPropagate()
            #wx.PostEvent(self, evt)
            self.ProcessEvent(evt)

        self.dragging=None
        self.GenHist()
        self.Refresh()
        self.Update()
        event.Skip()

    def OnMouseMove(self, event):
        x = event.GetX()
        #y = event.GetY()
        
        xt = self.hmin + x*self.hstep

        if self.dragging == 'thresh':
            self.limit_lower = xt
            self.limit_upper = xt
        elif self.dragging == 'lower' and not xt >= self.limit_upper:
            self.limit_lower = xt
        elif self.dragging == 'upper' and not xt <= self.limit_lower:
            self.limit_upper = xt

        self.Refresh()
        self.Update()

        event.Skip()

    def GenHist(self):
        #self.hmin = min(self.limit_lower, self.lower_pctile)
        #self.hmax = max(self.limit_upper, self.upper_pctile)
        if not self.limit_upper >= (self.limit_lower + 1e-9):
            self.limit_upper += 1e-9
            
        self.hmin = self.limit_lower
        self.hmax = self.limit_upper
        
        hmid = (self.hmin + self.hmax)/2.0

        #expand shown range to twice current range
        self.hmin = hmid - 1.5*(hmid-self.hmin)
        self.hmax = hmid + 1.5*(self.hmax-hmid)

        #go from 0 if in threshold mode
        if self.threshMode:
            self.hmin = 0.
            self.hmax = 2*hmid

        self.hstep = (self.hmax - self.hmin)/max(self.Size[0], 1)

        #print self.hmin, self.hmax, self.hstep, self.Size[0], self.limit_lower, self.limit_upper

        
        self.h, self.edges = np.histogram(self.data, np.arange(self.hmin, self.hmax, self.hstep))

        if self.log:
            self.h = np.log10(self.h+.01) - np.log10(.01)

        self.dmean = self.data.mean()
        

    def DoPaint(self, dc):
        if self.Size[0] < 1 or self.Size[1] < 1: #nothing to do
            return
        dc.SetFont(wx.NORMAL_FONT)
        self.textSize = dc.GetTextExtent('test')[1] + 4

        h = (self.Size[1] - self.textSize - 2)*(1.0-(self.h/(1.0*self.h[1:-1].max()+1e-9))) + 2

        maxy = self.Size[1] - self.textSize
        pointlist = [(i,h_i) for i, h_i in zip(range(len(h)), h)]
        pointlist = [(0,maxy)] + pointlist + [(self.Size[0], maxy)]

        dc.Clear()

        #when being used to determine histogram bins
        if not self.binSize is None:
            binEdges = np.arange(self.hmin, self.hmax + self.binSize, self.binSize)

            for i in range(len(binEdges) -1):
                llx = math.floor((binEdges[i] - self.hmin)/self.hstep)
                ulx = math.ceil((binEdges[i+1] - self.hmin)/self.hstep)

                dc.SetPen(wx.TRANSPARENT_PEN)

                if i % 2 == 0: #even
                    dc.SetBrush(wx.Brush(wx.Colour(0xC0, 0xC0, 0xFF)))
                else:
                    dc.SetBrush(wx.Brush(wx.Colour(0xA0, 0xA0, 0xFF)))

                dc.DrawRectangle(llx, 0, ulx - llx, maxy)

        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.BLACK_BRUSH)
        dc.DrawPolygon(pointlist)
        
        if self.dragging == 'lower':
            dc.SetPen(wx.Pen(wx.GREEN, 2))
        else:
            dc.SetPen(wx.Pen(wx.RED, 2))

        #print self.limit_lower

        llx = (self.limit_lower - self.hmin)/self.hstep
        dc.DrawLine(llx, 0, llx, maxy)
        lab = '%1.3G' % self.limit_lower
        labSize = dc.GetTextExtent(lab)
        dc.DrawText(lab, max(llx - labSize[0]/2, 0), maxy + 2)


        if not self.threshMode:
            if self.dragging == 'upper':
                dc.SetPen(wx.Pen(wx.GREEN, 2))
            else:
                dc.SetPen(wx.Pen(wx.RED, 2))

            ulx = (self.limit_upper - self.hmin)/self.hstep
            dc.DrawLine(ulx, 0, ulx, maxy)
            lab = '%1.3G' % self.limit_upper
            labSize = dc.GetTextExtent(lab)
            dc.DrawText(lab, min(ulx - labSize[0]/2, self.Size[0] - labSize[0]), maxy + 2)


        dc.SetPen(wx.NullPen)
        dc.SetBrush(wx.NullBrush)
        dc.SetFont(wx.NullFont)

    def OnPaint(self,event):
        DC = wx.PaintDC(self)
        #self.PrepareDC(DC)

        s = self.GetVirtualSize()
        MemBitmap = wx.EmptyBitmap(s.GetWidth(), s.GetHeight())
        #del DC
        MemDC = wx.MemoryDC()
        OldBitmap = MemDC.SelectObject(MemBitmap)
        try:
            DC.BeginDrawing()

            self.DoPaint(MemDC);

            DC.Blit(0, 0, s.GetWidth(), s.GetHeight(), MemDC, 0, 0)
            DC.EndDrawing()
        finally:

            del MemDC
            del MemBitmap

    def OnSize(self, event):
        self.Refresh()
        self.Update()
        
    def SetPercentile(self):
        self.limit_lower = self.lower_pctile
        self.limit_upper = self.upper_pctile
        self.GenHist()
        self.Refresh()
        self.Update()
        evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
        self.ProcessEvent(evt)
        
    def SetMinMax(self):
        self.limit_lower = float(np.nanmin(self.data))
        self.limit_upper = float(np.nanmax(self.data))
        self.GenHist()
        self.Refresh()
        self.Update()
        evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
        self.ProcessEvent(evt)

    def OnKeyPress(self, event):
        if event.GetKeyCode() == 76: #L - toggle log y axis
            self.log = not self.log
            self.GenHist()
            self.Refresh()
            self.Update()
        elif event.GetKeyCode() == 77: #M - set min-max
            self.SetMinMax()
        elif event.GetKeyCode() == 80: #P - set percentile
            self.SetPercentile()
        elif event.GetKeyCode() == 84: #T - toggle threshold mode
            self.threshMode = not self.threshMode
            if self.threshMode:
                self.oldLimits = (self.limit_lower, self.limit_upper)

                thresh =  0.5*(self.limit_lower + self.limit_upper)
                self.limit_lower = thresh
                self.limit_upper = thresh
            elif 'oldLimits' in dir(self):
                self.limit_lower, self.limit_upper = self.oldLimits
            else: #when coming out of threshold mode - min max scale
                self.limit_lower = float(self.data.min())
                self.limit_upper = float(self.data.max())

            self.GenHist()
            self.Refresh()
            self.Update()
            evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
            self.ProcessEvent(evt)
        else:
            event.Skip()

    def SetThresholdMode(self, tMode):
        if not self.threshMode == tMode:
            self.threshMode = tMode
            if self.threshMode:
                self.oldLimits = (self.limit_lower, self.limit_upper)

                thresh =  0.5*(self.limit_lower + self.limit_upper)
                self.limit_lower = thresh
                self.limit_upper = thresh
            elif 'oldLimits' in dir(self):
                self.limit_lower, self.limit_upper = self.oldLimits
            else: #when coming out of threshold mode - min max scale
                self.limit_lower = float(self.data.min())
                self.limit_upper = float(self.data.max())

            self.GenHist()
            self.Refresh()
            self.Update()
            evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
            self.ProcessEvent(evt)

    def SetValue(self, val):
        self.limit_lower = float(val[0])
        self.limit_upper = float(val[1])

        if self.threshMode:
            thresh = 0.5*(self.limit_lower + self.limit_upper)
            self.limit_lower = thresh
            self.limit_upper = thresh

        self.GenHist()
        self.Refresh()
        self.Update()

    def SetValueAndFire(self, val):
        self.SetValue(val)
        evt = LimitChangeEvent(self.GetId(), upper=self.limit_upper, lower=self.limit_lower)
        self.ProcessEvent(evt)


    def GetValue(self):
        return (self.limit_lower, self.limit_upper)

class SliderPanel(wx.Panel):
    def __init__(self, parent, id, hist_limit_panel, pos=(0, 0)):
        wx.Panel.__init__(self, parent, id, pos=pos)
        self.hist_limit_panel = hist_limit_panel
        vertical_box = wx.BoxSizer(wx.VERTICAL)
        horizontal_box_text = wx.BoxSizer(wx.HORIZONTAL)

        initial_boarders = self.hist_limit_panel.GetValue()

        self.min_text = wx.TextCtrl(self, -1, value=str(initial_boarders[0]), size=(40, -1))
        self.max_text = wx.TextCtrl(self, -1, value=str(initial_boarders[1]), size=(40, -1))
        self.slider = wx.Slider(self, minValue=initial_boarders[0], maxValue=initial_boarders[1])

        self.slider.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.update_limits)
        self.min_text.Bind(wx.EVT_TEXT, self.min_level_changed)
        self.max_text.Bind(wx.EVT_TEXT, self.max_level_changed)

        horizontal_box_text.Add(wx.StaticText(self, -1, 'SliderMin'), 0,
                                wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 5)
        horizontal_box_text.Add(self.min_text, 0, wx.ALL | wx.EXPAND, 5)
        horizontal_box_text.Add(wx.StaticText(self, -1, 'SliderMax'), 0,
                                wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 5)
        horizontal_box_text.Add(self.max_text, 0, wx.ALL | wx.EXPAND, 5)
        vertical_box.Add(horizontal_box_text, 0, wx.ALL | wx.EXPAND, 5)
        vertical_box.Add(self.slider, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizerAndFit(vertical_box)

    def update_limits(self, event):
        previous = self.hist_limit_panel.GetValue()
        slider_value = self.slider.GetValue()
        new_value = [slider_value, previous[1] - previous[0] + slider_value]
        self.hist_limit_panel.SetValue(new_value)

    def min_level_changed(self, event):
        new_min = float(self.min_text.GetValue())
        self.slider.SetMin(new_min)
        if self.slider.GetValue() < new_min:
            self.slider.SetValue(new_min)
            self.slider.ShowPosition(new_min)

    def max_level_changed(self, event):
        new_max = float(self.max_text.GetValue())
        self.slider.SetMax(new_max)
        if self.slider.GetValue() > new_max:
            self.slider.SetValue(new_max)


def ShowHistLimitFrame(parent, title, data, limit_lower, limit_upper, size=(200, 100), log=False):
    f = wx.Frame(parent, title=title, size=size)
    ID_HIST_LIM = wx.NewId()
    p = HistLimitPanel(f, ID_HIST_LIM, data, limit_lower, limit_upper, log=log)
    f.Show()
    return ID_HIST_LIM

class HistLimitDialog(wx.Dialog):
    def __init__(self, parent, data, lower, upper, title=''):
        wx.Dialog.__init__(self, parent, title=title)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        hor_box = wx.BoxSizer(wx.HORIZONTAL)
        self.min_value = wx.TextCtrl(self, -1, value=str(lower))
        self.max_value = wx.TextCtrl(self, -1, value=str(upper))

        hor_box.Add(self.min_value, 0, wx.ALL, 5)
        hor_box.Add(self.max_value, 0, wx.ALL, 5)

        self.min_value.Bind(wx.EVT_TEXT, self.min_level_changed)
        self.max_value.Bind(wx.EVT_TEXT, self.max_level_changed)

        sizer1.Add(hor_box, 0, wx.ALL, 5)

        self.hl = HistLimitPanel(self, -1, data, lower, upper, size=(240, 100))
        sizer1.Add(self.hl, 0, wx.ALL, 5)

        sizer1.Add(SliderPanel(self, -1, self.hl), 0, wx.ALL | wx.EXPAND, 5)

        btSizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()

        btSizer.AddButton(btn)

        #btn = wx.Button(self, wx.ID_CANCEL)

        #btSizer.AddButton(btn)

        btSizer.Realize()

        sizer1.Add(btSizer, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer1)
        sizer1.Fit(self)

    def GetLimits(self):
        return self.hl.GetValue()

    def min_level_changed(self, event):
        try:
            new_min = float(self.min_value.GetValue())
            old_max = self.hl.GetValue()[1]
            if new_min < old_max:
                self.hl.SetValue((new_min, old_max))
        except ValueError:
            pass

    def max_level_changed(self, event):
        try:
            new_max = float(self.max_value.GetValue())
            old_min = self.hl.GetValue()[0]
            if old_min < new_max:
                self.hl.SetValue((old_min, new_max))
        except ValueError:
            pass

