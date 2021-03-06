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

import numpy
import cv2
import cv2.cv as cv


class ScreenManagerBase(object):

    def __init__(self):
        self._get_pil_image = 0
        self.get_color_mat = 1
        self.get_gray_mat = 2

    def grab_desktop(self, return_type=0):
        raise NotImplementedError

    def _get_cv_color_mat(self, pilimage):

        cv_im = cv.CreateImageHeader(pilimage.size, cv.IPL_DEPTH_8U, 3)

        cv.SetData(cv_im, pilimage.tostring())

        mat = cv.GetMat(cv_im)

        img = numpy.asarray(mat)

        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img

    def _get_cv_gray_mat(self, mat):

        gray_mat = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

        return gray_mat