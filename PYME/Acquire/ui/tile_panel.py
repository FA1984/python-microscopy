import wx
from PYME.Acquire.Utils import tiler

class TilePanel(wx.Panel):
    def __init__(self, parent, scope):
        wx.Panel.__init__(self, parent)
        
        self.scope=scope
        
        self._gui_proc = None
        
        vsizer=wx.BoxSizer(wx.VERTICAL)

        # hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        # hsizer2.Add(wx.StaticText(pan, -1, 'Step Size x[mm]:'), 0, wx.ALL, 2)
        # self.tPixelSizeX = wx.TextCtrl(pan, -1, value='%3.4f' % ps.pixelsize[0])
        # hsizer2.Add(self.tPixelSizeX, 0, wx.ALL, 2)
        # vsizer.Add(hsizer2)
        #
        # hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        # hsizer2.Add(wx.StaticText(pan, -1, 'Step Size y[mm]:'), 0, wx.ALL, 2)
        # self.tPixelSizeY = wx.TextCtrl(pan, -1, value='%3.4f' % ps.pixelsize[1])
        # hsizer2.Add(self.tPixelSizeY, 0, wx.ALL, 2)
        # vsizer.Add(hsizer2)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(wx.StaticText(self, -1, '# x steps:'), 0, wx.ALL, 2)
        self.tXTiles = wx.TextCtrl(self, -1, value='%d' % 10)
        hsizer2.Add(self.tXTiles, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(wx.StaticText(self, -1, '# y steps:'), 0, wx.ALL, 2)
        self.tYTiles = wx.TextCtrl(self, -1, value='%d' % 10)
        hsizer2.Add(self.tYTiles, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(wx.StaticText(self, -1, 'Save to:'), 0, wx.ALL, 2)
        self.tDestination = wx.TextCtrl(self, -1, value='')
        hsizer2.Add(self.tDestination, 1, wx.ALL|wx.EXPAND, 2)
        vsizer.Add(hsizer2, 0, wx.EXPAND, 0)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.pProgress = wx.Gauge(self, -1, range=100)
        hsizer2.Add(self.pProgress, 1, wx.ALL|wx.EXPAND, 2)
        vsizer.Add(hsizer2, 0, wx.EXPAND, 0)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        #self.bTest = wx.Button(self, -1, 'Test')
        #self.bTest.Bind(wx.EVT_BUTTON, self.OnTest)
        #self.bTest.Disable()
        #hsizer2.Add(self.bTest, 0, wx.ALL, 2)
        self.bGo = wx.Button(self, -1, 'Go')
        self.bGo.Bind(wx.EVT_BUTTON, self.OnGo)
        hsizer2.Add(self.bGo, 0, wx.ALL, 2)
        self.bStop = wx.Button(self, -1, 'Stop')
        self.bStop.Disable()
        self.bStop.Bind(wx.EVT_BUTTON, self.OnStop)
        hsizer2.Add(self.bStop, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)
        
        self.SetSizerAndFit(vsizer)
        
    def OnGo(self, event=None):
        # run a triggered tile acquisition if the camera is capable
        # FIXME - the hasattr test becomes problematic once we add FireSoftwareTrigger to our base camera class (to
        # document API)
        trigger = hasattr(self.scope.cam, 'FireSoftwareTrigger')
        
        self.scope.tiler = tiler.Tiler(self.scope, tile_dir = self.tDestination.GetValue(),
                                       n_tiles=(int(self.tXTiles.GetValue()), int(self.tYTiles.GetValue())),
                                       trigger=trigger)
        
        self.bStop.Enable()
        self.bGo.Disable()
        
        self.scope.tiler.on_stop.connect(self._on_stop)
        self.scope.tiler.progress.connect(self._update)
        self.scope.tiler.start()
        
        
    def OnStop(self, event=None):
        self.scope.tiler.stop()
        
    def _update(self, *args, **kwargs):
        self.pProgress.SetValue(100*float(self.scope.tiler.callNum)/self.scope.tiler.imsize)
        
    def _on_stop(self, *args, **kwargs):
        self.bStop.Disable()
        self.bGo.Enable()
        
        self.scope.tiler.on_stop.disconnect(self._on_stop)
        self.scope.tiler.progress.disconnect(self._update)
        
        wx.CallAfter(wx.CallLater,1e3, self._launch_viewer)
        
        
    def _launch_viewer(self):
        import subprocess
        import sys
        import webbrowser
        import time
        import requests

        self.scope.tiler.P.update_pyramid()
        
        #if not self._gui_proc is None:
        #    self._gui_proc.kill()
        
        try:
            requests.get('http://127.0.0.1:8979/set_tile_source?tile_dir=%s' % self.scope.tiler._tiledir)
        except requests.ConnectionError:
            self._gui_proc = subprocess.Popen('%s -m PYME.tileviewer.tileviewer %s' % (sys.executable, self.scope.tiler._tiledir), shell=True)
            time.sleep(3)
            
        webbrowser.open('http://127.0.0.1:8979/')

class CircularTilePanel(TilePanel):
    def __init__(self, parent, scope):
        wx.Panel.__init__(self, parent)

        self.scope = scope

        self._gui_proc = None

        vsizer = wx.BoxSizer(wx.VERTICAL)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(wx.StaticText(self, -1, 'Scan radius [\u03BCm]:'), 0, wx.ALL, 2)
        self.radius_um = wx.TextCtrl(self, -1, value='%.1f' % 250)
        hsizer2.Add(self.radius_um, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.return_home_checkbox = wx.CheckBox(self, -1, 'Return to start on completion')
        hsizer2.Add(self.return_home_checkbox, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(wx.StaticText(self, -1, 'Save to:'), 0, wx.ALL, 2)
        self.tDestination = wx.TextCtrl(self, -1, value='')
        hsizer2.Add(self.tDestination, 1, wx.ALL | wx.EXPAND, 2)
        vsizer.Add(hsizer2, 0, wx.EXPAND, 0)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.pProgress = wx.Gauge(self, -1, range=100)
        hsizer2.Add(self.pProgress, 1, wx.ALL | wx.EXPAND, 2)
        vsizer.Add(hsizer2, 0, wx.EXPAND, 0)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        # self.bTest = wx.Button(self, -1, 'Test')
        # self.bTest.Bind(wx.EVT_BUTTON, self.OnTest)
        # self.bTest.Disable()
        # hsizer2.Add(self.bTest, 0, wx.ALL, 2)
        self.bGo = wx.Button(self, -1, 'Go')
        self.bGo.Bind(wx.EVT_BUTTON, self.OnGo)
        hsizer2.Add(self.bGo, 0, wx.ALL, 2)
        self.bStop = wx.Button(self, -1, 'Stop')
        self.bStop.Disable()
        self.bStop.Bind(wx.EVT_BUTTON, self.OnStop)
        hsizer2.Add(self.bStop, 0, wx.ALL, 2)
        vsizer.Add(hsizer2)

        self.SetSizerAndFit(vsizer)

    def OnGo(self, event=None):
        trigger = hasattr(self.scope.cam, 'FireSoftwareTrigger')

        self.scope.tiler = tiler.CircularTiler(self.scope, tile_dir=self.tDestination.GetValue(),
                                               max_radius_um=float(self.radius_um.GetValue()), trigger=trigger,
                                               return_to_start=self.return_home_checkbox.GetValue())

        self.bStop.Enable()
        self.bGo.Disable()

        self.scope.tiler.on_stop.connect(self._on_stop)
        self.scope.tiler.progress.connect(self._update)
        self.scope.tiler.start()


class MultiwellTilePanel(TilePanel):
    def __init__(self, parent, scope):
        wx.Panel.__init__(self, parent)

        self.scope = scope

        self._gui_proc = None

        vsizer = wx.BoxSizer(wx.VERTICAL)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 'Save to:'), 0, wx.ALL, 2)
        self.tDestination = wx.TextCtrl(self, -1, value='')
        hsizer.Add(self.tDestination, 1, wx.ALL | wx.EXPAND, 2)
        vsizer.Add(hsizer, 0, wx.EXPAND, 0)

        # hsizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.pProgress = wx.Gauge(self, -1, range=100)
        # hsizer.Add(self.pProgress, 1, wx.ALL | wx.EXPAND, 2)
        # vsizer.Add(hsizer, 0, wx.EXPAND, 0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 'Well Scan radius [\u03BCm]:'), 0, wx.ALL, 2)
        self.radius_um = wx.TextCtrl(self, -1, value='%.1f' % 250)
        hsizer.Add(self.radius_um, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, '# wells x:'), 0, wx.ALL, 2)
        self.n_x = wx.TextCtrl(self, -1, value='%d' % 3)
        hsizer.Add(self.n_x, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 'x cent. dist [mm]:'), 0, wx.ALL, 2)
        self.x_spacing_mm = wx.TextCtrl(self, -1, value='%.1f' % 3)
        hsizer.Add(self.x_spacing_mm, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, '# wells y:'), 0, wx.ALL, 2)
        self.n_y = wx.TextCtrl(self, -1, value='%d' % 3)
        hsizer.Add(self.n_y, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 'y cent. dist [mm]:'), 0, wx.ALL, 2)
        self.y_spacing_mm = wx.TextCtrl(self, -1, value='%.1f' % 3)
        hsizer.Add(self.y_spacing_mm, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.bGo = wx.Button(self, -1, 'Go')
        # self.bGo.Disable()
        self.bGo.Bind(wx.EVT_BUTTON, self.OnGo)
        hsizer.Add(self.bGo, 0, wx.ALL, 2)
        self.bStop = wx.Button(self, -1, 'Stop')
        self.bStop.Disable()
        self.bStop.Bind(wx.EVT_BUTTON, self.OnStop)
        hsizer.Add(self.bStop, 0, wx.ALL, 2)
        vsizer.Add(hsizer)

        self.SetSizerAndFit(vsizer)


    def OnGo(self, event=None):
        trigger = hasattr(self.scope.cam, 'FireSoftwareTrigger')

        self.scope.tiler = tiler.MultiwellCircularTiler(float(self.radius_um.GetValue()),
            float(self.x_spacing_mm.GetValue()) * 1e3, float(self.y_spacing_mm.GetValue()) * 1e3,
            int(self.n_x.GetValue()), int(self.n_y.GetValue()), self.scope, self.tDestination.GetValue(),
            trigger=trigger)

        self.bStop.Enable()
        self.bGo.Disable()

        # self.scope.tiler.on_stop.connect(self._on_stop)
        # self.scope.tiler.progress.connect(self._update)
        self.scope.tiler.start()

    def OnStop(self, event=None):
        self.scope.tiler.stop()