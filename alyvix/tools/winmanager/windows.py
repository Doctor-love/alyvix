# Alyvix allows you to automate and monitor all types of applications
# Copyright (C) 2015 Alan Pipitone
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
# Developer: Alan Pipitone (Violet Atom) - http://www.violetatom.com/
# Supporter: Wuerth Phoenix - http://www.wuerth-phoenix.com/
# Official website: http://www.alyvix.com/

import win32gui
import win32con
import win32com.client
import re
from .base import WinManagerBase


class WinManager(WinManagerBase):

    def __init__(self):
        pass

    def show_window(self, window_title):
        """
        show window.

        :type window_title: string
        :param window_title: regular expression for the window title
        """
        shell = win32com.client.Dispatch('WScript.Shell')
        shell.Run("python.exe -c \"from alyvix.tools.winmanager import WinManager; wm = WinManager(); wm._show_window('" + window_title + "')\"", 1, 1)

    def maximize_foreground_window(self):
        """
        maximize foreground window.
        """
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    def maximize_window(self, window_title):
        """
        maximize window(s).

        :type window_title: string
        :param window_title: regular expression for the window(s) title
        """
        hwnd_found_list = self._get_hwnd(window_title)
        for hwnd_found in hwnd_found_list:
            win32gui.ShowWindow(hwnd_found, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.ShowWindow(hwnd_found, win32con.SW_MAXIMIZE)

    def check_if_window_exists(self, window_title):
        """
        check if window(s) exist.

        :type window_title: string
        :param window_title: regular expression for the window(s) title
        """
        hwnd_found_list = self._get_hwnd(window_title)
        if len(hwnd_found_list) > 0:
            return True
        else:
            return False

    def close_window(self, window_title):
        """
        close window(s).

        :type window_title: string
        :param window_title: regular expression for the window(s) title
        """
        hwnd_found_list = self._get_hwnd(window_title)
        for hwnd_found in hwnd_found_list:
            win32gui.PostMessage(hwnd_found, win32con.WM_CLOSE, 0, 0)

    def _get_hwnd(self, window_title):
        windows_found = []
        hwnd_list = []
        win32gui.EnumWindows(self.__window_enumeration_handler, windows_found)
        for hwnd_found, title_found in windows_found:
            if re.match(".*" + window_title + ".*", title_found, re.DOTALL | re.IGNORECASE) is not None and \
                    (win32gui.IsWindowVisible(hwnd_found) != 0 or win32gui.GetWindowTextLength(hwnd_found) > 0):
                hwnd_list.append(hwnd_found)

        return hwnd_list

    def __window_enumeration_handler(self, hwnd, windows):
        windows.append((hwnd, win32gui.GetWindowText(hwnd)))

    def _show_window(self, window_title):

        hwnd_found_list = self._get_hwnd(window_title)
        for hwnd_found in hwnd_found_list:
            win32gui.ShowWindow(hwnd_found, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd_found,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetForegroundWindow(hwnd_found)