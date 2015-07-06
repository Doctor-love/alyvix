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

import sys
import os
import time
import cv2
import copy

from PyQt4.QtGui import QApplication, QWidget, QCursor, QImage, QPainter, QPainter, QPen, QColor, QPixmap, QBrush, QPainterPath, QDialog, QListWidgetItem , QTextEdit, QHBoxLayout, QTextCharFormat, QMessageBox, QFont, QFontMetrics, QTextCursor
from PyQt4.QtCore import Qt, QThread, SIGNAL, QTimer, QUrl, QPoint, QRect, QModelIndex, SLOT, pyqtSlot, QString, QChar
from PyQt4.Qt import QFrame

from PyQt4.QtWebKit import QWebSettings

from alyvix_rect_finder_view import AlyvixRectFinderView
from alyvix_image_finder_view import AlyvixImageFinderView
from alyvix_text_finder_view import AlyvixTextFinderView
#from alyvix_object_selection_controller import AlyvixMainMenuController

from alyvix_object_finder_properties_view import Ui_Form
from alyvix_object_finder_obj_selection import Ui_Form as Ui_Form_2

from alyvix.tools.screenmanager import ScreenManager

from stat import S_ISREG, ST_CTIME, ST_MODE

import shutil

import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

import codecs

from distutils.sysconfig import get_python_lib


class dummy():
    def __init__(self):
        self.window = None
        self.full_file_name = None
        self.path = None
        self.robot_file_name = None
        self.action = ""
        self.xml_name = ""
        self.parent = None
        
    def set_parent(self, parent):
        self.parent = parent
        
    def show(self):
        self.parent._sub_objects_finder = []
        self.parent._code_blocks = []
        self.parent._main_object_finder = None
        self.parent.build_objects()
        self.parent.show()

class AlyvixObjectFinderView(QDialog, Ui_Form):
    def __init__(self, parent):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.setFixedSize(self.size())
        
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        
        self.parent = parent
        self._path = self.parent.path
        self.action = self.parent.action
        self._xml_name = self.parent.xml_name
        
        self.button_selected = "set_main_object"
        
        self.esc_pressed = False
        
        self._main_object_finder = MainObjectForGui()
        self._sub_objects_finder = []
        self._deleted_sub_objects = []
        
        self._code_lines = []
        self._code_lines_for_object_finder = []
        
        self._code_blocks = []
        
        self.added_block = False
        self.textEdit = LineTextWidget(self.tab_code)
        self.textEdit.setGeometry(QRect(8, 9, 520, 172))
        self.textEdit.setText(self.build_code_string())
        
        self.build_objects()
        #print self._main_object_finder.xml_path
        
        self.__old_code = self.get_old_code()
        #self.__alyvix_proxy_path = os.getenv("ALYVIX_HOME") + os.sep + "robotproxy"
        self.__alyvix_proxy_path = get_python_lib() + os.sep + "alyvix" + os.sep + "robotproxy"
        self._robot_file_name = self.parent.robot_file_name
        
        if self.action == "edit":
            filename = self._main_object_finder.xml_path
            filename = filename.split(os.sep)[-1]
                        
            item = QListWidgetItem()
                
            if filename.endswith('_RectFinder.xml'):
                item.setText(filename[:-15] + " [RF]")
            elif filename.endswith('_ImageFinder.xml'):
                item.setText(filename[:-16] + " [IF]")
            elif filename.endswith('_TextFinder.xml'):
                item.setText(filename[:-15] + " [TF]")
                
            item.setData(Qt.UserRole, filename)
            
            self.listWidget.addItem(item)
        
        if self.action == "edit":
            self.namelineedit.setEnabled(False)
            
        if self._main_object_finder.find is True:
            self.find_radio.setChecked(True)
            self.timeout_label.setEnabled(False)
            self.timeout_spinbox.setEnabled(False)
        else:
            self.find_radio.setChecked(False)
            self.timeout_label.setEnabled(True)
            self.timeout_spinbox.setEnabled(True)

        if self._main_object_finder.click is True:
            self.clickRadio.setChecked(True)
        else:
            self.clickRadio.setChecked(False)
            
        if self._main_object_finder.doubleclick is True:
            self.doubleclickRadio.setChecked(True)
        else:
            self.doubleclickRadio.setChecked(False)
            
        if self._main_object_finder.click is False and self._main_object_finder.doubleclick is False:
            self.dontclickRadio.setChecked(True)
        else:
            self.dontclickRadio.setChecked(False)
                    
        self.widget_2.hide()
        
        self.sub_object_index = 0
        
        cnt = 1
        for sub_object in self._sub_objects_finder:
        
            #item = QListWidgetItem()
            
            filename = sub_object.xml_path
            filename = filename.split(os.sep)[-1]
                        
            item = QListWidgetItem()
                
            if filename.endswith('_RectFinder.xml'):
                item.setText(filename[:-15] + " [RF]")
            elif filename.endswith('_ImageFinder.xml'):
                item.setText(filename[:-16] + " [IF]")
            elif filename.endswith('_TextFinder.xml'):
                item.setText(filename[:-15] + " [TF]")
                
            item.setData(Qt.UserRole, filename)
            
            self.listWidget.addItem(item)
            cnt = cnt + 1
        
        #self.listWidget.setCurrentIndex(QModelIndex(self.listWidget.rootIndex()))
        #self.listWidget.item(0).setSelected(True)
        self.timeout_spinbox.setValue(self._main_object_finder.timeout)      
        self.inserttext.setPlainText(self._main_object_finder.sendkeys)       

        if self._main_object_finder.sendkeys == "":
            self.inserttext.setPlainText("Type here the Keyboard macro")
        else:
            self.inserttext.setPlainText(unicode(self._main_object_finder.sendkeys, 'utf-8'))       

        if self._main_object_finder.name == "":
            self.namelineedit.setText("Type here the name of the object")
        else:
            self.namelineedit.setText(self._main_object_finder.name)      

        
        self.spinBoxArgs.setValue(self._main_object_finder.args_number)
        
        self.init_block_code()
        
        self.connect(self.listWidget, SIGNAL('itemSelectionChanged()'), self.listWidget_selection_changed)
        #self.connect(self.listWidget, SIGNAL('itemChanged(QListWidgetItem*)'), self, SLOT('listWidget_state_changed(QListWidgetItem*)'))
        
        self.connect(self.wait_radio, SIGNAL('toggled(bool)'), self.wait_radio_event)
        self.connect(self.timeout_spinbox, SIGNAL('valueChanged(int)'), self.timeout_spinbox_event)
        
        self.connect(self.clickRadio, SIGNAL('toggled(bool)'), self.clickRadio_event)
        self.connect(self.doubleclickRadio, SIGNAL('toggled(bool)'), self.doubleclickRadio_event)
        self.connect(self.dontclickRadio, SIGNAL('toggled(bool)'), self.dontclickRadio_event)
        
        self.connect(self.inserttext, SIGNAL("textChanged()"), self, SLOT("inserttext_event()"))
        self.connect(self.namelineedit, SIGNAL("textChanged(QString)"), self, SLOT("namelineedit_event(QString)"))
        self.connect(self.pushButtonAddBlock, SIGNAL('clicked()'), self.add_block_code)
        self.connect(self.pushButtonRemoveBlock, SIGNAL('clicked()'), self.remove_block_code)
        self.connect(self.listWidgetBlocks, SIGNAL('itemSelectionChanged()'), self.listWidgetBlocks_selection_changed)
        
        self.inserttext.viewport().installEventFilter(self)
        self.inserttext.installEventFilter(self)
        
        self.namelineedit.installEventFilter(self)
        
        self.connect(self.tabWidget, SIGNAL('currentChanged(int)'), self.tab_changed_event)
        
        self.connect(self.checkBoxEnablePerformance, SIGNAL('stateChanged(int)'), self.enable_performance_event)
        self.connect(self.doubleSpinBoxWarning, SIGNAL('valueChanged(double)'), self.warning_event)
        self.connect(self.doubleSpinBoxCritical, SIGNAL('valueChanged(double)'), self.critical_event)
        
        self.connect(self.spinBoxArgs, SIGNAL('valueChanged(int)'), self.args_spinbox_change_event)
            
        self.connect(self.pushButtonSetMainObj, SIGNAL('clicked()'), self.open_select_obj_main)
        self.connect(self.pushButtonAddSubObj, SIGNAL('clicked()'), self.open_select_obj_sub)
        self.connect(self.pushButtonEditObj, SIGNAL('clicked()'), self.edit_obj)
        self.connect(self.pushButtonRemoveObj, SIGNAL('clicked()'), self.remove_obj)
        
        ##################
        ##################
        
        self.connect(self.roi_x_spinbox, SIGNAL('valueChanged(int)'), self.roi_x_spinbox_event)
        self.connect(self.roi_y_spinbox, SIGNAL('valueChanged(int)'), self.roi_y_spinbox_event)
        self.connect(self.roi_height_spinbox, SIGNAL('valueChanged(int)'), self.roi_height_spinbox_event)
        self.connect(self.roi_width_spinbox, SIGNAL('valueChanged(int)'), self.roi_width_spinbox_event)
        
        self.connect(self.clickRadio_2, SIGNAL('toggled(bool)'), self.clickRadio_event_2)
        self.connect(self.doubleclickRadio_2, SIGNAL('toggled(bool)'), self.doubleclickRadio_event_2)
        self.connect(self.dontclickRadio_2, SIGNAL('toggled(bool)'), self.dontclickRadio_event_2)
        
        self.connect(self.inserttext_2, SIGNAL("textChanged()"), self, SLOT("inserttext_event_2()"))
        
        self.inserttext_2.viewport().installEventFilter(self)
        self.inserttext_2.installEventFilter(self)
        
        self.textEditCustomLines.installEventFilter(self)
        self.roi_y_spinbox.installEventFilter(self)
        self.roi_height_spinbox.installEventFilter(self)
        self.roi_x_spinbox.installEventFilter(self)
        self.roi_width_spinbox.installEventFilter(self)
        
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._main_object_finder != None and self.esc_pressed is False and self._main_object_finder.xml_path != "":
                self.esc_pressed = True
                self.build_code_array()
                self.build_xml()
                self.save_python_file()
                self.update_lock_list()
                self.build_perf_data_xml()
                #image_name = self._path + os.sep + self._main_object_finder.name + "_ImageFinder.png"
                #self._bg_pixmap.save(image_name,"PNG", -1)
                #self.save_template_images(image_name)
                #time.sleep(0.4)
                if self.action == "new":
                    self.parent.add_new_item_on_list()
                
            self.parent.show()
            self.close()
    
    def delete_lock_list(self):
        filename = self._path + os.sep + "lock_list.xml"
        
        if os.path.exists(filename):
            doc = minidom.parse(filename)
            root_node = doc.getElementsByTagName("items")[0]
            
            items_node = doc.getElementsByTagName("item")
            
            for item_node in items_node:
                owner = item_node.getElementsByTagName("owner")[0].firstChild.nodeValue
                if owner == self._main_object_finder.name + "_ObjectFinder.xml":
                    root_node.removeChild(item_node)

            string = str(doc.toxml())
            python_file = open(filename, 'w')
            python_file.write(string)

    def update_lock_list(self):
    
        filename = self._path + os.sep + "lock_list.xml"
        
        if os.path.exists(filename):
            doc = minidom.parse(filename)
            root_node = doc.getElementsByTagName("items")[0]
            
            items_node = doc.getElementsByTagName("item")
            
            for item_node in items_node:
                owner = item_node.getElementsByTagName("owner")[0].firstChild.nodeValue
                if owner == self._main_object_finder.name + "_ObjectFinder.xml":
                    root_node.removeChild(item_node)
            
            item = doc.createElement("item")
            name = doc.createElement("name")
            txt = doc.createTextNode(self._main_object_finder.xml_path.split(os.sep)[-1])
            name.appendChild(txt)
            item.appendChild(name)

            owner = doc.createElement("owner")
            txt = doc.createTextNode(self._main_object_finder.name + "_ObjectFinder.xml")
            owner.appendChild(txt)
            item.appendChild(owner)
            root_node.appendChild(item)
            
            for sub_obj in self._sub_objects_finder:
                item = doc.createElement("item")
                name = doc.createElement("name")
                txt = doc.createTextNode(sub_obj.xml_path.split(os.sep)[-1])
                name.appendChild(txt)
                item.appendChild(name)

                owner = doc.createElement("owner")
                txt = doc.createTextNode(self._main_object_finder.name + "_ObjectFinder.xml")
                owner.appendChild(txt)
                item.appendChild(owner)
            
                root_node.appendChild(item)
            string = str(doc.toxml())
            python_file = open(filename, 'w')
            python_file.write(string)
            
        else:
            root = ET.Element("items")

            main_item_node = ET.SubElement(root, "item")
            
            name_node = ET.SubElement(main_item_node, "name")
            name_node.text = str(self._main_object_finder.xml_path.split(os.sep)[-1])
            
            name_node = ET.SubElement(main_item_node, "owner")
            name_node.text = str(self._main_object_finder.name + "_ObjectFinder.xml")
            
            for sub_obj in self._sub_objects_finder:
                main_item_node = ET.SubElement(root, "item")
            
                name_node = ET.SubElement(main_item_node, "name")
                name_node.text = str(sub_obj.xml_path.split(os.sep)[-1])

                name_node = ET.SubElement(main_item_node, "owner")
                name_node.text = str(self._main_object_finder.name + "_ObjectFinder.xml")
            
            #object_node = ET.SubElement(main_object_node, "object")
            #object_node.text = str(self._main_object_finder.click)
            
            tree = ET.ElementTree(root)
            python_file = open(filename, 'w')
            tree.write(python_file, encoding='utf-8', xml_declaration=True) 
            #python_file.write(rough_string)        
        python_file.close()
            
    
    def build_objects(self):
        
        #filename = open(self._path + os.sep + self._xml_name,"r")
        #print filename
        
        try:
            filehandler = open(self._path + os.sep + self._xml_name,"r")
        except:
            return

        doc = minidom.parse(filehandler)
        
        main_obj_xml_path = "xml_path"
        
        root_node = doc.getElementsByTagName("object_finder")[0]
        main_obj_node = doc.getElementsByTagName("main_object")[0]

        xml_name = main_obj_node.getElementsByTagName("xml_path")[0].firstChild.nodeValue
        
        main_obj = None           
        m_controller = dummy()
        m_controller.action = "new"
        m_controller.path = self.parent.path
        m_controller.xml_name = xml_name.split(os.sep)[-1]
        
        if xml_name.endswith('_RectFinder.xml'):
            main_obj = AlyvixRectFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_rect_finder
        elif xml_name.endswith('_ImageFinder.xml'):
            main_obj = AlyvixImageFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_template
        elif xml_name.endswith('_TextFinder.xml'):
            main_obj = AlyvixTextFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_text
            
        self._main_object_finder = MainObjectForGui()
        self._main_object_finder.xml_path = xml_name
        self._main_object_finder.x = main_obj.x
        self._main_object_finder.y = main_obj.y
        self._main_object_finder.height = main_obj.height
        self._main_object_finder.width = main_obj.width
        
        self._main_object_finder.name = root_node.attributes["name"].value
        #self._main_object_finder.find = main_obj_node.attributes["find"].value
        #self._main_object_finder.wait = main_obj_node.attributes["wait"].value
        self._main_object_finder.timeout = int(root_node.attributes["timeout"].value)
        self._main_object_finder.args_number = int(root_node.attributes["args"].value)
        
        if "True" in root_node.attributes["find"].value: #main_obj_node.getElementsByTagName("find")[0].firstChild.nodeValue:
            self._main_object_finder.find = True
        else:
            self._main_object_finder.find = False    
            
        if "True" in root_node.attributes["wait"].value: #main_obj_node.getElementsByTagName("wait")[0].firstChild.nodeValue:
            self._main_object_finder.wait = True
        else:
            self._main_object_finder.wait = False    
            
        if "True" in main_obj_node.getElementsByTagName("click")[0].firstChild.nodeValue:
            self._main_object_finder.click = True
        else:
            self._main_object_finder.click = False
            
        if "True" in main_obj_node.getElementsByTagName("doubleclick")[0].firstChild.nodeValue:
            self._main_object_finder.doubleclick = True
        else:
            self._main_object_finder.doubleclick = False
            
        if "True" in root_node.attributes["enable_performance"].value:
            self._main_object_finder.enable_performance = True
        else:
            self._main_object_finder.enable_performance = False
            
        self._main_object_finder.warning = float(root_node.attributes["warning_value"].value)
            
        self._main_object_finder.critical = float(root_node.attributes["critical_value"].value)
        
        try:
            self._main_object_finder.sendkeys = main_obj_node.getElementsByTagName("sendkeys")[0].toxml()
            self._main_object_finder.sendkeys = self._main_object_finder.sendkeys.replace("<sendkeys><!-- -->","")
            self._main_object_finder.sendkeys = self._main_object_finder.sendkeys.replace("<!-- --></sendkeys>","")
            self._main_object_finder.sendkeys = self._main_object_finder.sendkeys.replace("<![CDATA[","")
            self._main_object_finder.sendkeys = self._main_object_finder.sendkeys.replace("]]>","")
            self._main_object_finder.sendkeys = self._main_object_finder.sendkeys.encode('utf-8')
        except AttributeError:
            self._main_object_finder.sendkeys = ''.encode('utf-8')
        
        #self.__flag_capturing_main_rect = False
        #self.__flag_capturing_sub_rect_roi = True
                
        sub_object_nodes = doc.getElementsByTagName("sub_object")
        
        for sub_object_node in sub_object_nodes:
            filename = sub_object_node.getElementsByTagName("xml_path")[0].firstChild.nodeValue
                        
            item = QListWidgetItem()
            
            main_obj = None           
            m_controller = dummy()
            m_controller.action = "new"
            m_controller.path = self.parent.path
            m_controller.xml_name = filename.split(os.sep)[-1]

            if filename.endswith('_RectFinder.xml'):
                main_obj = AlyvixRectFinderView(m_controller)
                main_obj.build_objects()
                main_obj = main_obj._main_rect_finder
            elif filename.endswith('_ImageFinder.xml'):
                main_obj = AlyvixImageFinderView(m_controller)
                main_obj.build_objects()
                main_obj = main_obj._main_template
            elif filename.endswith('_TextFinder.xml'):
                main_obj = AlyvixTextFinderView(m_controller)
                main_obj.build_objects()
                main_obj = main_obj._main_text
            
            sub_object = SubObjectForGui()
            sub_object.xml_path = filename
                
            sub_object.x = main_obj.x
            sub_object.y = main_obj.y
            sub_object.height = main_obj.height
            sub_object.width = main_obj.width
            
            sub_object.roi_x = int(sub_object_node.getElementsByTagName("roi_x")[0].firstChild.nodeValue)
            sub_object.roi_y = int(sub_object_node.getElementsByTagName("roi_y")[0].firstChild.nodeValue)
            sub_object.roi_width = int(sub_object_node.getElementsByTagName("roi_width")[0].firstChild.nodeValue)
            sub_object.roi_height = int(sub_object_node.getElementsByTagName("roi_height")[0].firstChild.nodeValue)
                
            if "True" in sub_object_node.getElementsByTagName("click")[0].firstChild.nodeValue:
                sub_object.click = True
            else:
                sub_object.click = False
                
            if "True" in sub_object_node.getElementsByTagName("doubleclick")[0].firstChild.nodeValue:
                sub_object.doubleclick = True
            else:
                sub_object.doubleclick = False
            
            try:
                sub_object.sendkeys = sub_object_node.getElementsByTagName("sendkeys")[0].toxml()                
                sub_object.sendkeys = sub_object.sendkeys.replace("<sendkeys><!-- -->","")
                sub_object.sendkeys = sub_object.sendkeys.replace("<!-- --></sendkeys>","")
                sub_object.sendkeys = sub_object.sendkeys.replace("<![CDATA[","")
                sub_object.sendkeys = sub_object.sendkeys.replace("]]>","")
                sub_object.sendkeys = sub_object.sendkeys.encode('utf-8')
            except AttributeError:
                sub_object.sendkeys = ''.encode('utf-8')
            
            self._sub_objects_finder.append(sub_object)
            
        sub_block_nodes = doc.getElementsByTagName("code_block")
        
        #print len(sub_rect_nodes)

        for sub_block_node in sub_block_nodes:

            start_line = int(sub_block_node.getElementsByTagName("start_line")[0].firstChild.nodeValue)
            end_line = int(sub_block_node.getElementsByTagName("end_line")[0].firstChild.nodeValue)
            code = sub_block_node.getElementsByTagName("code")[0].toxml()
            
            code = code.replace("<code><!-- -->","")
            code = code.replace("<!-- --></code>","")
            code = code.replace("<![CDATA[","")
            code = code.replace("]]>","")

            #print code.encode('utf-8')
            self._code_blocks.append((start_line, code.encode('utf-8'), end_line))
            #print sub_block_node.childNodes[0].nodeValue #sub_block_node.toxml()
     
    def build_perf_data_xml(self):
    
        filename = self._path + os.sep + "perf_data.xml"
    
        if os.path.exists(filename):
            perf_is_present = False
            
            doc = minidom.parse(filename)
            root_node = doc.getElementsByTagName("performance")[0]
            
            items_node = doc.getElementsByTagName("perfdata")
            
            for item_node in items_node:
                name = item_node.getElementsByTagName("name")[0].firstChild.nodeValue
                if name == self._main_object_finder.name and self._main_object_finder.enable_performance is False:
                    root_node.removeChild(item_node)
                elif name == self._main_object_finder.name:
                    perf_is_present = True
                    
            if perf_is_present is False and self._main_object_finder.enable_performance is True:
                item = doc.createElement("perfdata")
                
                name = doc.createElement("name")
                txt = doc.createTextNode(self._main_object_finder.name)
                name.appendChild(txt)
                item.appendChild(name)

                warning = doc.createElement("warning")
                txt = doc.createTextNode(str(self._main_object_finder.warning))
                warning.appendChild(txt)
                item.appendChild(warning)
                
                critical = doc.createElement("critical")
                txt = doc.createTextNode(str(self._main_object_finder.critical))
                critical.appendChild(txt)
                item.appendChild(critical)
                
                root_node.appendChild(item)

            string = str(doc.toxml())
            python_file = open(filename, 'w')
            python_file.write(string)

        else:
            root = ET.Element("performance")

            main_item_node = ET.SubElement(root, "perfdata")
            
            name_node = ET.SubElement(main_item_node, "name")
            name_node.text = str(self._main_object_finder.name)
            
            warning_node = ET.SubElement(main_item_node, "warning")
            warning_node.text = str(self._main_object_finder.warning)
            
            critical_node = ET.SubElement(main_item_node, "critical")
            critical_node.text = str(self._main_object_finder.critical)
            
            tree = ET.ElementTree(root)
            python_file = open(filename, 'w')
            tree.write(python_file, encoding='utf-8', xml_declaration=True) 
            #python_file.write(rough_string)        
        python_file.close()  
    
    def build_code_string(self):
    
        last_block_line = 0
        lines = 0
        
        for block in self._code_blocks:
            start_line = block[0]
            end_line = block[2]
            lines = lines + (end_line - start_line) + 1
            
            if end_line > last_block_line:
                last_block_line = end_line
                
        #print "lines", lines
        #print "code lines", len(self._code_lines)
                
        while(len(self._code_lines) - 1 + lines < last_block_line):
            
            self._code_lines.append("")
            
    
        string = ""
        
        line_cnt = 1
        for element in self._code_lines:
            
            for block in self._code_blocks:
                code_line = block[0]
                code_text = unicode(block[1], 'utf-8')
                #print "code_text:", code_text
                
                if code_line == line_cnt:
                    
                    string = string + code_text + os.linesep
                    
                    line_cnt = line_cnt + len(str(code_text.encode('utf-8')).split("\n"))
                
            string = string + element + os.linesep
            line_cnt = line_cnt + 1

        #string = string[:-1]
        return string.encode('UTF-8')
        
    def build_code_array(self):
    
        pykeyboard_declared = False
        pymouse_declared = False
       
        if self._main_object_finder is None:
            return
            
        self._code_lines = []
        self._code_lines_for_object_finder = []
            
        name = self._main_object_finder.name
        
        if name == "":
            name = time.strftime("object_finder_%d_%m_%y_%H_%M_%S")
            self._main_object_finder.name = name
            
        #self._code_lines.append("def " + name + "():")
        
        string_function_args = "def " + name + "("
        
        args_range = range(1, self._main_object_finder.args_number + 1)
        
        for arg_num in args_range:
            string_function_args = string_function_args + "arg" + str(arg_num) + ", " 
        
        if string_function_args.endswith(", "):
            string_function_args = string_function_args[:-2]
        string_function_args = string_function_args + "):"
        self._code_lines.append(string_function_args)
        
        #self._code_lines.append("\n")
        strcode = "    object_finder = ObjectFinder(\"" + name + "\")"
        self._code_lines.append(strcode)
        self._code_lines_for_object_finder.append(strcode)
        #self._code_lines.append("\n")
        
        path_main_xml = self._main_object_finder.xml_path
        main_obj = None           
        m_controller = dummy()
        m_controller.action = "new"
        m_controller.path = self.parent.path
        m_controller.xml_name = path_main_xml.split(os.sep)[-1]
        
        if m_controller.xml_name == "":
            return
 
        #print m_controller.path
        #print m_controller.xml_name
        
        if path_main_xml.endswith('_RectFinder.xml'):
            main_obj = AlyvixRectFinderView(m_controller)
            strcode = "    object_finder.set_main_object(rect_finder)"
        elif path_main_xml.endswith('_ImageFinder.xml'):
            main_obj = AlyvixImageFinderView(m_controller)
            strcode = "    object_finder.set_main_object(image_finder)"
        elif path_main_xml.endswith('_TextFinder.xml'):
            main_obj = AlyvixTextFinderView(m_controller)
            strcode = "    object_finder.set_main_object(text_finder)"
        
        main_obj.build_code_array()
            
        self._code_lines.extend(main_obj._code_lines_for_object_finder)
        
        self._code_lines.append(strcode)
        self._code_lines_for_object_finder.append(strcode)
        
        #self._code_lines.append("\n")
        
        cnt = 1
        for sub_object in self._sub_objects_finder:
            if sub_object.height != 0 and sub_object.width !=0:
            
                #roi_x = str(sub_object.roi_x - self._main_object_finder.x)
                roi_x = str(sub_object.roi_x)
                roi_y = str(sub_object.roi_y)
                
                roi_width = str(sub_object.roi_width)
                roi_height = str(sub_object.roi_height)
                
                path_sub_xml = sub_object.xml_path
                sub_obj = None           
                s_controller = dummy()
                s_controller.action = "new"
                s_controller.path = self.parent.path
                s_controller.xml_name = path_sub_xml.split(os.sep)[-1]
        
                if path_sub_xml.endswith('_RectFinder.xml'):
                    sub_obj = AlyvixRectFinderView(s_controller)
                    strcode = "    object_finder.add_sub_object(rect_finder, {\"roi_x\": " + roi_x + ", \"roi_y\": " + roi_y + ", \"roi_width\": " + roi_width + ", \"roi_height\": " + roi_height + "})"
                elif path_sub_xml.endswith('_ImageFinder.xml'):
                    sub_obj = AlyvixImageFinderView(s_controller)
                    strcode = "    object_finder.add_sub_object(image_finder, {\"roi_x\": " + roi_x + ", \"roi_y\": " + roi_y + ", \"roi_width\": " + roi_width + ", \"roi_height\": " + roi_height + "})"
                elif path_sub_xml.endswith('_TextFinder.xml'):
                    sub_obj = AlyvixTextFinderView(s_controller)
                    strcode = "    object_finder.add_sub_object(text_finder, {\"roi_x\": " + roi_x + ", \"roi_y\": " + roi_y + ", \"roi_width\": " + roi_width + ", \"roi_height\": " + roi_height + "})"

                sub_obj.build_code_array()
                self._code_lines.extend(sub_obj._code_lines_for_object_finder)
                self._code_lines.append(strcode)
                self._code_lines_for_object_finder.append(strcode)

                cnt = cnt + 1

        if self._main_object_finder.find is True:  
            self._code_lines.append("    object_finder.find()")
        else:
           self._code_lines.append("    wait_time = object_finder.wait(" + str(self._main_object_finder.timeout) + ")")
           
        if self._main_object_finder.enable_performance is True and self._main_object_finder.find is False:
            self._code_lines.append("    if wait_time == -1:")
            self._code_lines.append("        raise Exception(\"step " + str(self._main_object_finder.name) + " timed out, execution time: " + str(self._main_object_finder.timeout) + "\")")
            self._code_lines.append("    elif wait_time < " + repr(self._main_object_finder.warning) + ":")
            self._code_lines.append("        print \"step " + self._main_object_finder.name + " is ok, execution time:\", wait_time, \"sec.\"")
            self._code_lines.append("    elif wait_time < " + repr(self._main_object_finder.critical) + ":")
            self._code_lines.append("        print \"*WARN* step " + str(self._main_object_finder.name) + " has exceeded the performance warning threshold:\", wait_time, \"sec.\"")
            self._code_lines.append("    else:")
            self._code_lines.append("        print \"*WARN* step " + str(self._main_object_finder.name) + " has exceeded the performance critical threshold:\", wait_time, \"sec.\"")
        elif self._main_object_finder.find is False:
            self._code_lines.append("    if wait_time == -1:")
            self._code_lines.append("        raise Exception(\"step " + str(self._main_object_finder.name) + " timed out, execution time: " + str(self._main_object_finder.timeout) + "\")")
        
        if self._main_object_finder.click == True or self._main_object_finder.doubleclick == True:
        
            self._code_lines.append("    main_object_pos = object_finder.get_result(0)")  
        
            if pymouse_declared is False:
                self._code_lines.append("    m = PyMouse()")
                pymouse_declared = True
                
            self._code_lines.append("    time.sleep(2)")
                                
            if self._main_object_finder.click == True:
                self._code_lines.append("    m.click(main_object_pos.x + (main_object_pos.width/2), main_object_pos.y + (main_object_pos.height/2), 1)")
            elif self._main_object_finder.doubleclick == True:
                self._code_lines.append("    m.click(main_object_pos.x + (main_object_pos.width/2), main_object_pos.y + (main_object_pos.height/2), 1, 2)")
            
        if self._main_object_finder.sendkeys != "":
            if pykeyboard_declared is False:
                self._code_lines.append("    k  = PyKeyboard()")
                pykeyboard_declared = True
            keys = unicode(self._main_object_finder.sendkeys, 'utf-8')
            macro_list = keys.split('\n')
            self._code_lines.append("    time.sleep(2)")
            
            for keyboard_macro in macro_list:
                self._code_lines.append("    " + keyboard_macro)
            
        cnt = 0
        for sub_object in self._sub_objects_finder:
        
            if sub_object.height != 0 and sub_object.width !=0:
                if sub_object.click == True or sub_object.doubleclick == True:
            
                    self._code_lines.append("    sub_object_" + str(cnt) + "_pos = object_finder.get_result(0, " + str(cnt) + ")")  
                
                    if pymouse_declared is False:
                        self._code_lines.append("    m = PyMouse()")
                        pymouse_declared = True
                    self._code_lines.append("    time.sleep(2)")
                                        
                    if sub_object.click == True:
                        self._code_lines.append("    m.click(sub_object_" + str(cnt) + "_pos.x + (sub_object_" + str(cnt) + "_pos.width/2), sub_object_" + str(cnt) + "_pos.y + (sub_object_" + str(cnt) + "_pos.height/2), 1)")
                    elif sub_object.doubleclick == True:
                        self._code_lines.append("    m.click(sub_object_" + str(cnt) + "_pos.x + (sub_object_" + str(cnt) + "_pos.width/2), sub_object_" + str(cnt) + "_pos.y + (sub_object_" + str(cnt) + "_pos.height/2), 1, 2)")
                    
                if sub_object.sendkeys != "":
                    if pykeyboard_declared is False:
                        self._code_lines.append("    k  = PyKeyboard()")
                        pykeyboard_declared = True
                    keys = unicode(sub_object.sendkeys, 'utf-8')
                    macro_list = keys.split('\n')
                    self._code_lines.append("    time.sleep(2)")
                    
                    for keyboard_macro in macro_list:
                        self._code_lines.append("    " + keyboard_macro)
                                    
                cnt = cnt + 1
        
        self._code_lines.append("")
        self._code_lines.append("") 
        
    def get_old_code(self):
        file_code_string = ""
        filename = self._path + os.sep + self._main_object_finder.name + "_old_code.txt"
        
        if os.path.exists(filename):
            file = codecs.open(filename, encoding="utf-8")  
            lines = file.readlines()
            
            for line in lines:
                file_code_string = file_code_string + line   
                
        return file_code_string.encode('utf-8')
    
    def save_python_file(self):
    
        file_code_string = ""
        filename = self.__alyvix_proxy_path + os.sep + "AlyvixProxy" + self._robot_file_name + ".py"
        
        if os.path.exists(filename):
            file = codecs.open(filename, encoding="utf-8")  
            lines = file.readlines()
            
            for line in lines:
                file_code_string = file_code_string + line   
                
        self.build_code_array()
        current_code_string = unicode(self.build_code_string(), 'utf-8')
        
        """
        if not os.path.exists(filename) and sel.action == "edit":
            sel.action = "new"
        """
        
        #print "old code:", self.__old_code
        
        if self.action == "new":
            file_code_string = file_code_string + current_code_string
        elif self.action == "edit":
            file_code_string = file_code_string.replace(unicode(self.__old_code, 'utf-8'), current_code_string)
            """
            print self.__old_code
            print "---"
            print current_code_string
            print "---"
            print file_code_string
            """

        string = file_code_string
        string = string.encode('utf-8')

        file = codecs.open(filename, 'w', 'utf-8')
        file.write(unicode(string, 'utf-8'))
        file.close()
        
        string = current_code_string
        string = string.encode('utf-8')
        
        filename = self._path + os.sep + self._main_object_finder.name + "_old_code.txt"
        file = codecs.open(filename, 'w', 'utf-8')
        file.write(unicode(string, 'utf-8'))
        file.close()

    
    def remove_code_from_py_file(self):
    
        file_code_string = ""
        filename = self.__alyvix_proxy_path + os.sep + "AlyvixProxy" + self._robot_file_name + ".py"
        
        if os.path.exists(filename):
            file = codecs.open(filename, encoding="utf-8")  
            lines = file.readlines()
            
            for line in lines:
                file_code_string = file_code_string + line
            
        self.build_code_array()
        current_code_string = unicode(self.build_code_string(), 'utf-8')
        #current_code_string = current_code_string.replace(os.linesep + os.linesep, os.linesep)
        
        file_code_string = file_code_string.replace(unicode(self.__old_code, 'utf-8'), "")
        
        string = file_code_string
        string = string.encode('utf-8')

        file = codecs.open(filename, 'w', 'utf-8')
        file.write(unicode(string, 'utf-8'))
        file.close()    
    
    def open_select_obj_main(self):
        self.button_selected = "set_main_object"
        self.open_select_obj_window()
        
    def open_select_obj_sub(self):
        
        if self.listWidget.count() == 0:
            msgBox = QMessageBox()
            msgBox.setWindowTitle('Error')
            msgBox.setIcon (QMessageBox.Critical)
            msgBox.setText("You have to set the Main Object first")
            msgBox.setWindowFlags(Qt.WindowStaysOnTopHint)

            msgBox.exec_()
        else:
            
            self.button_selected = "add_sub_object"
            self.open_select_obj_window()
            
    def remove_obj(self):
    
        selected_index = self.listWidget.currentRow()
    
        if selected_index == 0:
            item = QListWidgetItem()
            item.setText("")
            self.listWidget.takeItem(0)
            self.listWidget.insertItem(0, item)
        
            self.button_selected = "set_main_object"
            self.open_select_obj_window()
        else:
            item = self.listWidget.takeItem(selected_index)
            self.listWidget.removeItemWidget(item)
            del self._sub_objects_finder[-1]
        
    def edit_obj(self):
    
        m_controller = dummy()
        m_controller.set_parent(self)
        m_controller.action = "edit"
        m_controller.path = self.parent.path
        m_controller.robot_file_name =  self._robot_file_name
        m_controller.xml_name = str(self.listWidget.currentItem().data(Qt.UserRole).toString())
        
        image = QImage(m_controller.path + os.sep + m_controller.xml_name.replace("xml", "png"))
        
        if m_controller.xml_name.endswith('_RectFinder.xml'):
            self.object = AlyvixRectFinderView(m_controller)
        elif m_controller.xml_name.endswith('_ImageFinder.xml'):
            self.object = AlyvixImageFinderView(m_controller)
        elif m_controller.xml_name.endswith('_TextFinder.xml'):
            self.object = AlyvixTextFinderView(m_controller)
        
        self.hide()
        
        self.object.set_bg_pixmap(image)
        self.object.showFullScreen()
    
    def open_select_obj_window(self):
        self.select_main_object_view = AlyvixObjectsSelection(self)
        self.select_main_object_view.show()
        
    def set_main_object(self, xml_name):
        filename = xml_name
        filename = filename.split(os.sep)[-1]
        
        #self.update_lock_list(filename)
                    
        item = QListWidgetItem()
        
        path_main_xml = self._main_object_finder.xml_path
        main_obj = None           
        m_controller = dummy()
        m_controller.action = "new"
        m_controller.path = self.parent.path
        m_controller.xml_name = filename
        
        if filename.endswith('_RectFinder.xml'):
            item.setText(filename[:-15] + " [RF]")
            main_obj = AlyvixRectFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_rect_finder
        elif filename.endswith('_ImageFinder.xml'):
            item.setText(filename[:-16] + " [IF]")
            main_obj = AlyvixImageFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_template
        elif filename.endswith('_TextFinder.xml'):
            item.setText(filename[:-15] + " [TF]")
            main_obj = AlyvixTextFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_text
            
        item.setData(Qt.UserRole, filename)
        
        if self.listWidget.count() > 0:
            self.listWidget.takeItem(0)
            self.listWidget.insertItem(0, item)
        else:
            self.listWidget.addItem(item)
            
        self._main_object_finder = MainObjectForGui()
        self._main_object_finder.xml_path = xml_name
        self._main_object_finder.x = main_obj.x
        self._main_object_finder.y = main_obj.y
        self._main_object_finder.height = main_obj.height
        self._main_object_finder.width = main_obj.width
        
        #print self._main_object_finder.x
        #print self._main_object_finder.y
        #print self._main_object_finder.height
        #print self._main_object_finder.width
        
        #self.listWidget.addItem(item)
        #self.build_main_object()
        
    def add_sub_object(self, xml_name):
        filename = xml_name
        filename = filename.split(os.sep)[-1]
        
        #self.update_lock_list(filename)
                    
        item = QListWidgetItem()
        
        main_obj = None           
        m_controller = dummy()
        m_controller.action = "new"
        m_controller.path = self.parent.path
        m_controller.xml_name = filename

        if filename.endswith('_RectFinder.xml'):
            item.setText(filename[:-15] + " [RF]")
            main_obj = AlyvixRectFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_rect_finder
        elif filename.endswith('_ImageFinder.xml'):
            item.setText(filename[:-16] + " [IF]")
            main_obj = AlyvixImageFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_template
        elif filename.endswith('_TextFinder.xml'):
            item.setText(filename[:-15] + " [TF]")
            main_obj = AlyvixTextFinderView(m_controller)
            main_obj.build_objects()
            main_obj = main_obj._main_text

        item.setData(Qt.UserRole, filename)
        self.listWidget.addItem(item)
        
        sub_object = SubObjectForGui()
        sub_object.xml_path = xml_name
            
        sub_object.x = main_obj.x
        sub_object.y = main_obj.y
        sub_object.height = main_obj.height
        sub_object.width = main_obj.width
        self._sub_objects_finder.append(sub_object)
        #self.build_sub_object(sub_object)
        
        self.pv = PaintingView(self)
        image = QImage(self._main_object_finder.xml_path.replace("xml", "png"))   
        self.pv.set_bg_pixmap(image)
        self.pv.showFullScreen()
                
    def add_new_item_on_list(self): 
        dirpath = self._path

        # get all entries in the directory w/ stats
        entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
        entries = ((os.stat(path), path) for path in entries)

        # leave only regular files, insert creation date
        entries = ((stat[ST_CTIME], path)
                   for stat, path in entries if S_ISREG(stat[ST_MODE]))
        #NOTE: on Windows `ST_CTIME` is a creation date 
        #  but on Unix it could be something else
        #NOTE: use `ST_MTIME` to sort by a modification date
        
        cdate, path = sorted(entries)[-1]
        
        filename = os.path.basename(path)
        
        item = QListWidgetItem()

        if filename.endswith('_RectFinder.xml'):
            item.setText(filename[:-15] + " [RF]")
        elif filename.endswith('_ImageFinder.xml'):
            item.setText(filename[:-16] + " [IF]")
        elif filename.endswith('_TextFinder.xml'):
            item.setText(filename[:-15] + " [TF]")
                    
        item.setData(Qt.UserRole, filename)
        self.listWidget.addItem(item)
        
    def build_xml(self):
        
        if self._main_object_finder is None:
            return

        name = str(self._main_object_finder.name)
        
        if name == "":
            name = time.strftime("object_finder_%d_%m_%y_%H_%M_%S")
            self._main_object_finder.name = name
        
        root = ET.Element("object_finder")
        root.set("name", name)
        root.set("find", str(self._main_object_finder.find))
        root.set("wait", str(self._main_object_finder.wait))
        root.set("timeout", str(self._main_object_finder.timeout))
        root.set("enable_performance", str(self._main_object_finder.enable_performance))
        root.set("warning_value", repr(self._main_object_finder.warning))
        root.set("critical_value", repr(self._main_object_finder.critical))
        root.set("args", str(self._main_object_finder.args_number))

        main_object_node = ET.SubElement(root, "main_object")
        
        path_node = ET.SubElement(main_object_node, "xml_path")
        path_node.text = str(self._main_object_finder.xml_path)
        
        click_node = ET.SubElement(main_object_node, "click")
        click_node.text = str(self._main_object_finder.click)

        doubleclick_node = ET.SubElement(main_object_node, "doubleclick")
        doubleclick_node.text = str(self._main_object_finder.doubleclick)

        sendkeys_node = ET.SubElement(main_object_node, "sendkeys")
        
        sendkey_text = unicode(self._main_object_finder.sendkeys, 'utf-8')

        sendkeys_node.append(ET.Comment(' --><![CDATA[' + sendkey_text.replace(']]>', ']]]]><![CDATA[>') + ']]><!-- '))
        
        sub_objects_root = ET.SubElement(root, "sub_objects")
        
        cnt = 1
        for sub_object in self._sub_objects_finder:
            if sub_object.height != 0 and sub_object.width !=0:
            
                sub_object_node = ET.SubElement(sub_objects_root, "sub_object") #ET.SubElement(sub_objects_root, "sub_object_" + str(cnt))
                sub_object_node.set("id", str(cnt))
                     
                path_node = ET.SubElement(sub_object_node, "xml_path")
                #path_node.text = str(self._path + os.sep + self._main_object_finder.name + os.sep + "sub_object_" + str(cnt) + ".png")
                path_node.text = str(sub_object.xml_path)
                
                roi_x_node = ET.SubElement(sub_object_node, "roi_x")
                roi_x_node.text = str(sub_object.roi_x)
                
                roi_y_node = ET.SubElement(sub_object_node, "roi_y")
                roi_y_node.text = str(sub_object.roi_y)
                
                roi_width_node = ET.SubElement(sub_object_node, "roi_width")
                roi_width_node.text = str(sub_object.roi_width)
                
                roi_height_node = ET.SubElement(sub_object_node, "roi_height")
                roi_height_node.text = str(sub_object.roi_height)
                
                click_node = ET.SubElement(sub_object_node, "click")
                click_node.text = str(sub_object.click)
                
                doubleclick_node = ET.SubElement(sub_object_node, "doubleclick")
                doubleclick_node.text = str(sub_object.doubleclick)
                
                sendkeys_node = ET.SubElement(sub_object_node, "sendkeys")
                #sendkeys_node.text = unicode(sub_object.sendkeys, 'utf-8')
                sendkeys_node.append(ET.Comment(' --><![CDATA[' + unicode(sub_object.sendkeys.replace(']]>', ']]]]><![CDATA[>'), 'utf-8') + ']]><!-- '))
                
                cnt = cnt + 1
        
        code_blocks_root = ET.SubElement(root, "code_blocks")
        for block in self._code_blocks:
            block_start_line = block[0]
            block_text = block[1]
            block_end_line = block[2]
           # block_text = unicode(block_text, "utf-8")
            code_block = ET.SubElement(code_blocks_root, "code_block") #ET.SubElement(sub_objects_root, "sub_object_" + str(cnt))
            #code_block.set("id", str(block_start_line) + "_" + str(block_end_line))
            
            start_line_node = ET.SubElement(code_block, "start_line")
            start_line_node.text = str(block_start_line)
         
            end_line_node = ET.SubElement(code_block, "end_line")
            end_line_node.text = str(block_end_line)
            
            code_node = ET.SubElement(code_block, "code")
            code_node.append(ET.Comment(' --><![CDATA[' + unicode(block_text.replace(']]>', ']]]]><![CDATA[>'), 'utf-8') + ']]><!-- '))
            #code_node.text = str(block_start_line)
            
        tree = ET.ElementTree(root)
        
        python_file = open(self._path + os.sep + self._main_object_finder.name + "_ObjectFinder.xml", 'w')
        tree.write(python_file, encoding='utf-8', xml_declaration=True) 
        #python_file.write(rough_string)        
        python_file.close()
    
    @pyqtSlot()
    def inserttext_event(self):
        if self.inserttext.toPlainText() == "Type here the Keyboard macro" or self.inserttext.toPlainText() == "#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)":
            self._main_object_finder.sendkeys = "".encode('utf-8')
        else:
            self._main_object_finder.sendkeys = str(self.inserttext.toPlainText().toUtf8())
    
    @pyqtSlot(QString)
    def namelineedit_event(self, text):
        if text == "Type here the name of the object":
            self._main_object_finder.name = "".encode('utf-8')
        else:
            self._main_object_finder.name = str(text.toUtf8()).replace(" ", "_")
  
    def args_spinbox_change_event(self, event):
        self._main_object_finder.args_number = self.spinBoxArgs.value()
        self.build_code_array()
        self.textEdit.setText(unicode(self.build_code_string(), 'utf-8'))
  
    def warning_event(self, event):
        self._main_object_finder.warning = self.doubleSpinBoxWarning.value()
        
    def critical_event(self, event):
        self._main_object_finder.critical = self.doubleSpinBoxCritical.value()
        
    def tab_changed_event(self, tab_index):
        if tab_index is 1:
            self.build_code_array()
            self.textEdit.setText(unicode(self.build_code_string(), 'utf-8'))
        elif tab_index is 3:
            self.doubleSpinBoxWarning.setValue(self._main_object_finder.warning)
            self.doubleSpinBoxCritical.setValue(self._main_object_finder.critical)
            
            if self._main_object_finder.enable_performance is True:
                self.checkBoxEnablePerformance.setCheckState(Qt.Checked)
                self.doubleSpinBoxWarning.setEnabled(True)
                self.doubleSpinBoxCritical.setEnabled(True)
                self.labelWarning.setEnabled(True)
                self.labelCritical.setEnabled(True)
            else:
                self.checkBoxEnablePerformance.setCheckState(Qt.Unchecked)
                self.doubleSpinBoxWarning.setEnabled(False)
                self.doubleSpinBoxCritical.setEnabled(False)
                self.labelWarning.setEnabled(False)
                self.labelCritical.setEnabled(False)
                
    def enable_performance_event(self, event):
        if self.checkBoxEnablePerformance.isChecked() is True:
            self._main_object_finder.enable_performance = True
            self.doubleSpinBoxWarning.setEnabled(True)
            self.doubleSpinBoxCritical.setEnabled(True)
            self.labelWarning.setEnabled(True)
            self.labelCritical.setEnabled(True)
        else:
            self._main_object_finder.enable_performance = False
            self.doubleSpinBoxWarning.setEnabled(False)
            self.doubleSpinBoxCritical.setEnabled(False)
            self.labelWarning.setEnabled(False)
            self.labelCritical.setEnabled(False)
    
    def wait_radio_event(self, event):
        if event is True:
            self.timeout_spinbox.setEnabled(True)
            self.timeout_label.setEnabled(True)
            self._main_object_finder.wait = True
            self._main_object_finder.find = False
        else:
            self.timeout_spinbox.setEnabled(False)
            self.timeout_label.setEnabled(False)
            self._main_object_finder.wait = False
            self._main_object_finder.find = True
            
    def timeout_spinbox_event(self, event):
        self._main_object_finder.timeout = self.timeout_spinbox.value()
    
    def clickRadio_event(self, event):
        if event is False:
            self._main_object_finder.click = False
        else:
            self._main_object_finder.click = True
            
    def doubleclickRadio_event(self, event):
        if event is False:
            self._main_object_finder.doubleclick = False
        else:
            self._main_object_finder.doubleclick = True 
             
    def dontclickRadio_event(self, event):
        if event is True:
            self._main_object_finder.click = False
            self._main_object_finder.doubleclick = False
            
    def listWidget_selection_changed(self):
    
        selected_index = self.listWidget.currentRow()
        
        if selected_index == 0:
            self.widget_2.hide()
            self.widget.show()
            self.widget.setGeometry(QRect(149, 9, 381, 291))

        else:
            self.widget.hide()
            self.widget_2.show()
            self.widget_2.setGeometry(QRect(149, 9, 381, 311))
            self.sub_object_index = selected_index - 1
            self.update_sub_object_view()
    
            
    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
        
            if self.namelineedit.text() == "Type here the name of the object" and obj.objectName() == "namelineedit":
                self.namelineedit.setText("")
                return True
        
            if obj.objectName() == 'qt_scrollarea_viewport':    
               
                parent_obj_name = obj.parent().objectName()
               
                if self.inserttext.toPlainText() == "Type here the Keyboard macro" and parent_obj_name == "inserttext":
                    self.inserttext.setPlainText("#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)")
                    return True
                    
                if self.inserttext_2.toPlainText() == "Type here the Keyboard macro" and parent_obj_name == "inserttext_2":
                    self.inserttext_2.setPlainText("#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)")
                    return True
                
        if event.type()== event.FocusOut:
            if obj.objectName() == "roi_y_spinbox":

                absolute_sub_roi_y = self.parent._main_object_finder.y + self.parent._sub_objects_finder[self.sub_object_index].roi_y
                absolute_sub_rect_y = self.parent._sub_objects_finder[self.sub_object_index].y
        
                if absolute_sub_roi_y > absolute_sub_rect_y:
                    self.parent._sub_objects_finder[self.sub_object_index].roi_y = self.parent._sub_objects_finder[self.sub_object_index].y - self.parent._main_object_finder.y
                    self.roi_y_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_y)
                    self.parent.update()
                    return True
                    
                if absolute_sub_roi_y + self.parent._sub_objects_finder[self.sub_object_index].roi_height < absolute_sub_rect_y + self.parent._sub_objects_finder[self.sub_object_index].height:
                    self.parent._sub_objects_finder[self.sub_object_index].roi_y = self.parent._sub_objects_finder[self.sub_object_index].y - self.parent._main_object_finder.y
                    self.roi_y_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_y)
                    self.parent.update()
                    return True
                    
            elif obj.objectName() == "roi_height_spinbox":
                
                absolute_sub_roi_y = self.parent._main_object_finder.y + self.parent._sub_objects_finder[self.sub_object_index].roi_y
                absolute_sub_rect_y = self.parent._sub_objects_finder[self.sub_object_index].y
                if absolute_sub_roi_y + self.parent._sub_objects_finder[self.sub_object_index].roi_height < absolute_sub_rect_y + self.parent._sub_objects_finder[self.sub_object_index].height:
                    px_to_add = (absolute_sub_rect_y + self.parent._sub_objects_finder[self.sub_object_index].height) - (absolute_sub_roi_y + self.parent._sub_objects_finder[self.sub_object_index].roi_height)
                    height = absolute_sub_roi_y - px_to_add
                    self.parent._sub_objects_finder[self.sub_object_index].roi_height = self.parent._sub_objects_finder[self.sub_object_index].roi_height  + px_to_add
                    self.roi_height_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_height)
                    self.parent.update()
                    return True
                    
            elif obj.objectName() == "roi_x_spinbox":

                absolute_sub_roi_x = self.parent._main_object_finder.x + self.parent._sub_objects_finder[self.sub_object_index].roi_x
                absolute_sub_rect_x = self.parent._sub_objects_finder[self.sub_object_index].x
        
                if absolute_sub_roi_x > absolute_sub_rect_x:
                    self.parent._sub_objects_finder[self.sub_object_index].roi_x = self.parent._sub_objects_finder[self.sub_object_index].x - self.parent._main_object_finder.x
                    self.roi_x_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_x)
                    self.parent.update()
                    return True
                    
                if absolute_sub_roi_x + self.parent._sub_objects_finder[self.sub_object_index].roi_width < absolute_sub_rect_x + self.parent._sub_objects_finder[self.sub_object_index].width:
                    self.parent._sub_objects_finder[self.sub_object_index].roi_x = self.parent._sub_objects_finder[self.sub_object_index].x - self.parent._main_object_finder.x
                    self.roi_x_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_x)
                    self.parent.update()
                    return True
                    
            elif obj.objectName() == "roi_width_spinbox":
                
                absolute_sub_roi_x = self.parent._main_object_finder.x + self.parent._sub_objects_finder[self.sub_object_index].roi_x
                absolute_sub_rect_x = self.parent._sub_objects_finder[self.sub_object_index].x
                if absolute_sub_roi_x + self.parent._sub_objects_finder[self.sub_object_index].roi_width < absolute_sub_rect_x + self.parent._sub_objects_finder[self.sub_object_index].width:
                    px_to_add = (absolute_sub_rect_x + self.parent._sub_objects_finder[self.sub_object_index].width) - (absolute_sub_roi_x + self.parent._sub_objects_finder[self.sub_object_index].roi_width)
                    height = absolute_sub_roi_x - px_to_add
                    self.parent._sub_objects_finder[self.sub_object_index].roi_width = self.parent._sub_objects_finder[self.sub_object_index].roi_width  + px_to_add
                    self.roi_width_spinbox.setValue(self.parent._sub_objects_finder[self.sub_object_index].roi_width)
                    self.parent.update()
                    return True
            elif self.namelineedit.text() == "" and obj.objectName() == "namelineedit":
                self.namelineedit.setText("Type here the name of the object")
                return True
            elif obj.objectName() == "namelineedit":
                self.namelineedit.setText(self._main_object_finder.name)
                return True
        
            if (self.inserttext.toPlainText() == "" or self.inserttext.toPlainText() == "#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)") and obj.objectName() == "inserttext":
                self.inserttext.setPlainText("Type here the Keyboard macro")
                return True
                
            if (self.inserttext_2.toPlainText() == "" or self.inserttext_2.toPlainText() == "#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)") and obj.objectName() == "inserttext_2":
                self.inserttext_2.setPlainText("Type here the Keyboard macro")
                return True
                
            if obj.objectName() == "textEditCustomLines" and self.added_block is False:
                self.update_code_block_array()
                return True
            elif obj.objectName() == "textEditCustomLines" and self.added_block is True:
                self.added_block = False
                return True
                
        if event.type() == event.KeyPress and obj.objectName() == "textEditCustomLines" and event.key() == Qt.Key_Tab:
            
            select_start = self.textEditCustomLines.textCursor().selectionStart()
            
            new_text = self.textEditCustomLines.textCursor().selection().toPlainText()
            
            if new_text == "":
                self.textEditCustomLines.insertPlainText("    ")
            else:
                new_text = "    " + new_text.replace("\n", "\n    ")
                self.textEditCustomLines.textCursor().insertText(new_text)
                            
                select_end = self.textEditCustomLines.textCursor().position()

                c = self.textEditCustomLines.textCursor()
                c.setPosition(select_start)
                c.setPosition(select_end, QTextCursor.KeepAnchor)
                self.textEditCustomLines.setTextCursor(c)

            return True
            
        if event.type() == event.KeyPress and obj.objectName() == "textEditCustomLines" and event.key() == Qt.Key_Backtab:
            
            cursors_pos = self.textEditCustomLines.textCursor().position()
            new_pos = 0
            select_start = self.textEditCustomLines.textCursor().selectionStart()
            
            new_text = str(self.textEditCustomLines.textCursor().selection().toPlainText().toUtf8())
            
            if new_text == "":
                #self.textEditCustomLines.insertPlainText("    ")
                #print self.textEditCustomLines.textCursor().block().text().toAscii()

                textedit_string = str(self.textEditCustomLines.toPlainText().toUtf8())
                textedit_strings = textedit_string.split("\n")
                
                cursor_line_number = self.textEditCustomLines.textCursor().blockNumber()
                
                cnt = 0
                for string in textedit_strings:
                    if cnt == cursor_line_number:
                        #current_line = str(self.textEditCustomLines.textCursor().block().text().toAscii())
                        #print current_line
                        if string.startswith("    "):
                            string_trimmed = string[4:]
                            #new_text = new_text.replace(first_line, firt_line_trimmed, 1)
                            #self.textEditCustomLines.textCursor().insertText(current_line_trimmed)
                            textedit_strings[cnt] = string_trimmed
                            new_pos = cursors_pos -4
                            
                            new_string = ""
                            
                            for string in textedit_strings:
                                new_string = new_string + string + "\n"
                            new_string = new_string[:-1]

                            self.textEditCustomLines.setPlainText(unicode(new_string, 'utf-8'))
                            
                            if new_pos < 0:
                                new_pos = 0
                            
                            c = self.textEditCustomLines.textCursor()
                            c.setPosition(new_pos)
                            self.textEditCustomLines.setTextCursor(c)
                            
                            
                            
                            #print string_trimmed
                    cnt = cnt + 1
                    
            else:
                first_line = new_text.split("\n")[0]
                #firt_line_trimmed = str(first_line).lstrip('    ')
                if first_line.startswith("    "):
                    firt_line_trimmed = first_line[4:]
                    new_text = new_text.replace(first_line, firt_line_trimmed, 1)
                new_text = new_text.replace("\n    ", "\n")

                self.textEditCustomLines.textCursor().insertText(unicode(new_text,'utf-8'))
                
                select_end = self.textEditCustomLines.textCursor().position()
                
                c = self.textEditCustomLines.textCursor()
                c.setPosition(select_start)
                c.setPosition(select_end, QTextCursor.KeepAnchor)
                self.textEditCustomLines.setTextCursor(c)
                
            return True
            
        return False  
    
    def init_block_code(self):
                
        for block in self._code_blocks:
            block_index_start_line = block[0]
            block_index_end_line = block[2]

            item = QListWidgetItem()
            item.setText(str(block_index_start_line) + ":" + str(block_index_end_line))
            self.listWidgetBlocks.addItem(item)
                
    def add_block_code(self):
    
        if self.pushButtonAddBlock.text() == "Unselect":
            self.listWidgetBlocks.item(self.listWidgetBlocks.currentRow()).setSelected(False)
            self.listWidgetBlocks.setCurrentItem(None)
            self.pushButtonAddBlock.setText("Add Block")
            self.textEditCustomLines.setPlainText("")
        elif self.textEditCustomLines.toPlainText() != "":
            
            index = self.spinBoxLine.value()

            is_present = False
                            
            block_index_start_line = None
            block_index_end_line = None
                
            for block in self._code_blocks:
                block_index_start_line = block[0]
                block_index_end_line = block[2]

                if index >= block_index_start_line and index <= block_index_end_line:
                    is_present = True
                    break

            if is_present is False:

                end_line = index + len(self.textEditCustomLines.toPlainText().split("\n")) -1
                item = QListWidgetItem()
                #item.setCheckState(Qt.Checked)
                item.setText(str(index) + ":" + str(end_line))
                #print str(index) + ":" + str(end_line)
                self.listWidgetBlocks.addItem(item)
                
                self._code_blocks.append((index, str(self.textEditCustomLines.toPlainText().toUtf8()), end_line))
                #print self._code_blocks
                self.textEditCustomLines.setPlainText("")
                self.added_block = True
            else:
                msgBox = QMessageBox()
                msgBox.setWindowTitle('Error')
                msgBox.setIcon (QMessageBox.Critical)
                msgBox.setText("You cannot add block of code into another block.\nLines from " + str(block_index_start_line) + " to " + str(block_index_end_line) + " belongs to block " + str(block_index_start_line) + ":" + str(block_index_end_line))
                msgBox.setWindowFlags(Qt.WindowStaysOnTopHint)

                msgBox.exec_()

    def remove_block_code(self):
        selected_index = self.listWidgetBlocks.currentRow()
        
        if selected_index == -1:
            return
        
        del self._code_blocks[selected_index]
        
        item = self.listWidgetBlocks.takeItem(selected_index)
        self.listWidgetBlocks.removeItemWidget(item)
        self.textEditCustomLines.setPlainText("")
        
        if len(self._code_blocks) == 1:
            block = self._code_blocks[0]
            code_text = block[1]
            self.textEditCustomLines.setPlainText(code_text)
            
    def listWidgetBlocks_selection_changed(self):
        
        selected_index = self.listWidgetBlocks.currentRow()
        
        if len(self._code_blocks) > 0:
            block = self._code_blocks[selected_index]
            code_text = block[1]
            self.textEditCustomLines.setPlainText(unicode(code_text, 'utf-8'))
            self.pushButtonAddBlock.setText("Unselect")

    def update_code_block_array(self):
        
        list_current_item = self.listWidgetBlocks.currentItem()
        
        if list_current_item is None:
            return
        
        selected_index = self.listWidgetBlocks.currentRow()
        
        if len(self._code_blocks) > 0:
            text = str(self.textEditCustomLines.toPlainText().toUtf8())
            end_line = self._code_blocks[selected_index][0] + len(self.textEditCustomLines.toPlainText().split("\n")) -1
            new_tuple = (self._code_blocks[selected_index][0], text, end_line)
            self._code_blocks[selected_index] = new_tuple
            self.listWidgetBlocks.currentItem().setText(str(self._code_blocks[selected_index][0]) + ":" + str(end_line))
        
    
    def update_sub_object_view(self):
    
        index = self.sub_object_index 
                    
        if index < 0:
            return
        
        if self._sub_objects_finder[index].sendkeys == "":
            self.inserttext_2.setPlainText("Type here the Keyboard macro")
        else:
            self.inserttext_2.setPlainText(unicode(self._sub_objects_finder[index].sendkeys, 'utf-8'))
            
        self.roi_x_spinbox.setValue(self._sub_objects_finder[self.sub_object_index].roi_x)
        self.roi_y_spinbox.setValue(self._sub_objects_finder[self.sub_object_index].roi_y)
        self.roi_width_spinbox.setValue(self._sub_objects_finder[self.sub_object_index].roi_width)
        self.roi_height_spinbox.setValue(self._sub_objects_finder[self.sub_object_index].roi_height)
        
            
        if self._sub_objects_finder[self.sub_object_index].click is True:
            self.clickRadio_2.setChecked(True)
        else:
            self.clickRadio_2.setChecked(False)
            
        if self._sub_objects_finder[self.sub_object_index].doubleclick is True:
            self.doubleclickRadio_2.setChecked(True)
        else:
            self.doubleclickRadio_2.setChecked(False)
            
        if self._sub_objects_finder[self.sub_object_index].click is False and self._sub_objects_finder[self.sub_object_index].doubleclick is False:
            self.dontclickRadio_2.setChecked(True)
        else:
            self.dontclickRadio_2.setChecked(False)
            
    #################
    #################
    
            
    @pyqtSlot()
    def inserttext_event_2(self):
        if self.inserttext_2.toPlainText() == "Type here the Keyboard macro" or self.inserttext_2.toPlainText() == "#k.type_string('Type here the text')\n#time.sleep(1)\n#k.tap_key(k.enter_key)":
            self._sub_objects_finder[self.sub_object_index].sendkeys = "".encode('utf-8')
        else:
            self._sub_objects_finder[self.sub_object_index].sendkeys = str(self.inserttext_2.toPlainText().toUtf8())
            
    def roi_x_spinbox_event(self, event):
        self._sub_objects_finder[self.sub_object_index].roi_x = self.roi_x_spinbox.value()
        self.update()
        
    def roi_y_spinbox_event(self, event):
        self._sub_objects_finder[self.sub_object_index].roi_y = self.roi_y_spinbox.value()
        self.update()
        
    def roi_width_spinbox_event(self, event):
        self._sub_objects_finder[self.sub_object_index].roi_width = self.roi_width_spinbox.value()
        self.update()
        
    def roi_height_spinbox_event(self, event):
        self._sub_objects_finder[self.sub_object_index].roi_height = self.roi_height_spinbox.value()
        self.update()
    
    def clickRadio_event_2(self, event):
        if event is False:
            self._sub_objects_finder[self.sub_object_index].click = False
        else:
            self._sub_objects_finder[self.sub_object_index].click = True
        
    def doubleclickRadio_event_2(self, event):
        if event is False:
            self._sub_objects_finder[self.sub_object_index].doubleclick = False
        else:
            self._sub_objects_finder[self.sub_object_index].doubleclick = True 
             
    def dontclickRadio_event_2(self, event):
        if event is True:
            self._sub_objects_finder[self.sub_object_index].click = False
            self._sub_objects_finder[self.sub_object_index].doubleclick = False
            
class MainObjectForGui:
    
    def __init__(self):
        self.name = ""
        self.x = 0
        self.y = 0
        self.height = 0
        self.width = 0
        self.show = True
        self.xml_path = ""
        self.click = False
        self.doubleclick = False
        self.wait = True
        self.find = False
        self.args_number = 0
        self.timeout = 60
        self.sendkeys = ""
        self.enable_performance = True
        self.warning = 15.00
        self.critical = 40.00
        
class SubObjectForGui:
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.height = 0
        self.width = 0
        self.roi_x = 0
        self.roi_y = 0
        self.roi_height = 0
        self.roi_width = 0
        self.show = True
        self.xml_path = ""
        self.click = False
        self.doubleclick = False
        self.sendkeys = ""
        
class AlyvixObjectsSelection(QDialog, Ui_Form_2):
    def __init__(self, parent):
        QDialog.__init__(self)
        
        self.setupUi(self)
        
        self.setFixedSize(self.size())
        
        self.parent = parent
        
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        
        self.update_list()
        
        self.connect(self.pushButtonSelect, SIGNAL('clicked()'), self.push_button_select_event)   
        self.connect(self.pushButtonCancel, SIGNAL('clicked()'), self.push_button_cancel_event)   
        
    def update_list(self):
        #dirs = os.listdir(self.full_file_name)
        #dirs = [d for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, d))]
        
        # path to the directory (relative or absolute)
        dirpath = self.parent._path

        # get all entries in the directory w/ stats
        entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
        entries = ((os.stat(path), path) for path in entries)

        # leave only regular files, insert creation date
        entries = ((stat[ST_CTIME], path)
                   for stat, path in entries if S_ISREG(stat[ST_MODE]))
        #NOTE: on Windows `ST_CTIME` is a creation date 
        #  but on Unix it could be something else
        #NOTE: use `ST_MTIME` to sort by a modification date

        lock_list_name = self.parent._path + os.sep + "lock_list.xml"
        
        doc = None
        if os.path.exists(lock_list_name):
            doc = minidom.parse(lock_list_name)
            root_node = doc.getElementsByTagName("items")[0]
            
            items_node = doc.getElementsByTagName("item")
            
        for cdate, path in sorted(entries):
            filename = os.path.basename(path)
            #print filename
            
            continue_the_loop = False
            
            if doc is not None:

                for item_node in items_node:
                    owner = item_node.getElementsByTagName("owner")[0].firstChild.nodeValue
                    item_name = item_node.getElementsByTagName("name")[0].firstChild.nodeValue
                    if owner != self.parent._main_object_finder.name + "_ObjectFinder.xml" and item_name == filename:
                        continue_the_loop = True
                    
            if filename.endswith('.xml'):
                if filename.endswith('_ObjectFinder.xml') or filename.endswith('list.xml') or filename.endswith('data.xml') or continue_the_loop is True:
                    continue_the_loop = False
                    continue
                    
                item = QListWidgetItem()
                if filename.endswith('_RectFinder.xml'):
                    item.setText(filename[:-15] + " [RF]")
                elif filename.endswith('_ImageFinder.xml'):
                    item.setText(filename[:-16] + " [IF]")
                elif filename.endswith('_TextFinder.xml'):
                    item.setText(filename[:-15] + " [TF]")
                    #print "tf"
                item.setData(Qt.UserRole, filename)
                self.listWidgetAlyObj.addItem(item)
                
    def push_button_select_event(self):
        if self.parent.button_selected == "set_main_object":
            self.set_main_object()
        elif self.parent.button_selected == "add_sub_object":
            self.add_sub_object()
            
    def push_button_cancel_event(self):
        self.close()
                
    def set_main_object(self):
            
        #print self.listWidgetAlyObj.currentRow()
        
        selected_item_data = self.listWidgetAlyObj.currentItem().data(Qt.UserRole).toString()
        xml_name = str(selected_item_data)
        
        xml_name = self.parent._path + os.sep + xml_name
        
        #self.parent._main_object_finder.xml_path = xml_name
        
        self.parent.set_main_object(xml_name)
        
        self.close()
        
    def add_sub_object(self):
            
        #print self.listWidgetAlyObj.currentRow()
        
        selected_item_data = self.listWidgetAlyObj.currentItem().data(Qt.UserRole).toString()
        xml_name = str(selected_item_data)
        
        xml_name = self.parent._path + os.sep + xml_name
        
        self.parent.add_sub_object(xml_name)
        
        self.close()
        
            

class LineTextWidget(QFrame):
 
    class NumberBar(QWidget):
 
        def __init__(self, *args):
            QWidget.__init__(self, *args)
            self.edit = None
            # This is used to update the width of the control.
            # It is the highest line that is currently visibile.
            self.highest_line = 0
 
        def setTextEdit(self, edit):
            self.edit = edit
 
        def update(self, *args):
            '''
            Updates the number bar to display the current set of numbers.
            Also, adjusts the width of the number bar if necessary.
            '''
            # The + 4 is used to compensate for the current line being bold.
            width = self.fontMetrics().width(str(self.highest_line)) + 4
            if self.width() != width:
                self.setFixedWidth(width)
            QWidget.update(self, *args)
 
        def paintEvent(self, event):
            contents_y = self.edit.verticalScrollBar().value()
            page_bottom = contents_y + self.edit.viewport().height()
            font_metrics = self.fontMetrics()
            current_block = self.edit.document().findBlock(self.edit.textCursor().position())
 
            painter = QPainter(self)
 
            line_count = 0
            # Iterate over all text blocks in the document.
            block = self.edit.document().begin()
            while block.isValid():
                line_count += 1
 
                # The top left position of the block in the document
                position = self.edit.document().documentLayout().blockBoundingRect(block).topLeft()
 
                # Check if the position of the block is out side of the visible
                # area.
                if position.y() > page_bottom:
                    break
 
                # We want the line number for the selected line to be bold.
                bold = False
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
 
                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(self.width() - font_metrics.width(str(line_count)) - 3, round(position.y()) - contents_y + font_metrics.ascent(), str(line_count))
 
                # Remove the bold style if it was set previously.
                if bold:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
 
                block = block.next()
 
            self.highest_line = line_count
            painter.end()
 
            QWidget.paintEvent(self, event)
 
 
    def __init__(self, *args):
        QFrame.__init__(self, *args)
 
        #self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
 
        self.edit = QTextEdit(*args)
        #self.edit.setFrameStyle(QFrame.NoFrame)
        self.edit.setLineWrapMode(QTextEdit.NoWrap)
        self.edit.setAcceptRichText(False)
        self.edit.setReadOnly(True)
 
        self.number_bar = self.NumberBar()
        self.number_bar.setTextEdit(self.edit)
 
        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        self.edit.installEventFilter(self)
        self.edit.viewport().installEventFilter(self)
        
                    
    def setText(self, text):
        self.edit.setText(text)
 
    def eventFilter(self, object, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary singals.
        if object in (self.edit, self.edit.viewport()):
            self.number_bar.update()
            return False
        return QFrame.eventFilter(object, event)

 
    def getTextEdit(self):
        return self.edit
        
    
class PaintingView(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self)
        
        self.parent = parent
        
        self._bg_pixmap = QPixmap()
        self.__capturing = False
        
        self.__click_position = QPoint(0,0)
        
        self._sub_rects_finder = []
        
        #flags
        #self.__flag_mouse_left_button_is_pressed = False
        self.__flag_mouse_is_inside_rect = False
        self.__flag_capturing_sub_rect_roi = False
        self.__flag_capturing_sub_rect = False
        self.__flag_need_to_delete_roi = False
        self.__flag_need_to_restore_roi = False
        self._flag_show_min_max = False
        self._self_show_tolerance = False

        self.__index_deleted_rect_inside_roi = -1
        self.__restored_rect_roi = False
        
        self.setMouseTracking(True)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z: 
            self.delete_sub_roi()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Y:
            self.restore_sub_roi()    
        if event.key() == Qt.Key_Escape:
            if self.parent._sub_objects_finder[-1].roi_height != 0 and self.parent._sub_objects_finder[-1].roi_width != 0:
                #self.parent.show()
                self.close()
        
    def set_bg_pixmap(self, image):
        self._bg_pixmap = QPixmap.fromImage(image)
        
    def mouseMoveEvent(self, event):
        self.update()  
            
    def mouseDoubleClickEvent(self, event):
        pass
        """
        if False is True:
            #self.BringWindowToFront()
            return
        if self.is_mouse_inside_rect(self._main_rect_finder):
            self.rect_view_properties = AlyvixRectFinderPropertiesView(self)
            self.rect_view_properties.show()
        """
        
    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
        
            self.__click_position = QPoint(QCursor.pos())
            self.__capturing = True
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.__capturing = False

            if len(self.parent._deleted_sub_objects) > 0:
                del self.parent._deleted_sub_objects[-1]
                
            self.add_sub_rect_roi()
            
        self.update()
        
    def delete_sub_roi(self):
    
        sub_obj = self.parent._sub_objects_finder[-1]    
        
        if sub_obj.roi_height == 0 or sub_obj.roi_width == 0:
            return
        
        print sub_obj.roi_x, sub_obj.roi_y, sub_obj.roi_height,sub_obj.roi_width
        
        self.parent._deleted_sub_objects.append(copy.deepcopy(sub_obj))
        
        sub_obj.roi_x = 0
        sub_obj.roi_y = 0
        sub_obj.roi_height = 0
        sub_obj.roi_width = 0
        
        self.update()
        
    def restore_sub_roi(self):
    
        if len(self.parent._deleted_sub_objects) > 0:
            sub_obj_deleted = self.parent._deleted_sub_objects[-1]    
            
            sub_obj = self.parent._sub_objects_finder[-1] 
            
            sub_obj.roi_x = sub_obj_deleted.roi_x
            sub_obj.roi_y = sub_obj_deleted.roi_y
            sub_obj.roi_height = sub_obj_deleted.roi_height
            sub_obj.roi_width = sub_obj_deleted.roi_width
            
            del self.parent._deleted_sub_objects[-1]
            
        self.update()
        
    def add_sub_rect_roi(self):
    
        rect_attributes = self.convert_mouse_position_into_rect()
        
        if rect_attributes is not None:
        
            x, y, width, height = rect_attributes

            sub_obj = self.parent._sub_objects_finder[-1]            
            sub_obj.roi_x = x - self.parent._main_object_finder.x
            sub_obj.roi_y = y - self.parent._main_object_finder.y
            sub_obj.roi_height = height
            sub_obj.roi_width = width
            
    def convert_mouse_position_into_rect(self):
            
        #self.__click_position
        
        mouse_position = QPoint(QCursor.pos())
        
        width = mouse_position.x() - self.__click_position.x()
        height = mouse_position.y() - self.__click_position.y()

        rect = QRect(self.__click_position.x(), self.__click_position.y(), width, height)

        if (rect.width() >= 3 or rect.width() <= -3) and (rect.height() >= 3 or rect.height() <= -3):

            if (rect.width() < 0 and rect.height() < 0):

                x = rect.x() + rect.width()
                y = rect.y() + rect.height()
                w = -rect.width()
                h = -rect.height()
                ##rect = QRect(x, y, w, h)

            elif (rect.width() < 0 and rect.height() > 0):

                x = rect.x() + rect.width()
                y = rect.y()
                w = -rect.width()
                h = rect.height()
                ##rect = QRect(x, y, w, h)

            elif (rect.width() > 0 and rect.height() < 0):

                x = rect.x()
                y = rect.y() + rect.height()
                w = rect.width()
                h = -rect.height()
                ##rect = QRect(x, y, w, h)
            else:
                x = rect.x()
                y = rect.y()
                w = rect.width()
                h = rect.height()
                ##rect = QRect(x, y, w, h)

            if width < 0:
                width = width * -1
            if height < 0:
                height = height * -1
        
            return (x, y, width, height)
            
        else:
            return None
            
    def paintEvent(self, event):
    
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self._bg_pixmap)
        
        self.__flag_mouse_is_inside_rect = False
        self.__index_of_rectangle_with_mouse_inside = -2
        
        if self.parent._main_object_finder is not None:
            
            self.draw_main_object_rect(qp)
            
            if self.is_mouse_inside_rect(self.parent._main_object_finder):
                self.__flag_mouse_is_inside_rect = True
        
        rect_index = 0
        #self.__sub_template_color_index = 0
        for sub_object_finder in self.parent._sub_objects_finder:
        
            self.draw_sub_templateangle(qp, sub_object_finder)
            
            if self.is_mouse_inside_rect(sub_object_finder):
                self.__flag_mouse_is_inside_rect = True
 
        if self.__capturing is False:
            self.draw_cross_lines(qp)
        else:    
            self.draw_capturing_roi_lines(qp)
        qp.end()   
       
    def is_mouse_inside_rect(self, rect):
    
        mouse_position = QPoint(QCursor.pos())
        
        if (mouse_position.x() > rect.x and
                mouse_position.x() < rect.width + rect.x and
                mouse_position.y() > rect.y and
                mouse_position.y() < rect.height + rect.y):
            return True
        else:
            return False
 
    def draw_main_object_rect(self, qp):
    
            if self.parent._main_object_finder.show is False:
                return
                
            pen = QPen()
            pen.setBrush(QColor(255, 0, 0, 255))
            pen.setWidth(1)
            qp.setPen(pen)
            
            qp.fillRect(self.parent._main_object_finder.x,
                self.parent._main_object_finder.y,
                self.parent._main_object_finder.width,
                self.parent._main_object_finder.height,
                QBrush(QColor(255, 0, 255, 130)))
                
            qp.drawRect(QRect(self.parent._main_object_finder.x,
                self.parent._main_object_finder.y,
                self.parent._main_object_finder.width,
                self.parent._main_object_finder.height))  
        
     
    def draw_sub_templateangle(self, qp, image_finder):
    
            if image_finder.show is False:
                return
    
            pen = QPen()
            pen.setWidth(1)
            pen.setStyle(Qt.SolidLine)
            pen.setBrush(QBrush(QColor(255, 0, 198, 255)))
            qp.setPen(pen)
            
            OuterPath_roi = QPainterPath()
            OuterPath_roi.setFillRule(Qt.WindingFill)
            
            OuterPath_roi.addRect(image_finder.roi_x + self.parent._main_object_finder.x,
                image_finder.roi_y + self.parent._main_object_finder.y,
                image_finder.roi_width,
                image_finder.roi_height)
                
            if image_finder.x != 0 and image_finder.y != 0:
            
                InnerPath_roi = QPainterPath()
                
                """
                InnerPath_roi.addRect(image_finder.x,
                    image_finder.y,
                    image_finder.width,
                    image_finder.height)
                """
                

                InnerPath_roi.addRect(image_finder.x,
                    image_finder.y,
                    image_finder.width,
                    image_finder.height)
                    
                                            
                FillPath_roi = OuterPath_roi.subtracted(InnerPath_roi)
                qp.fillPath(FillPath_roi, QBrush(QColor(172, 96, 246, 180), Qt.BDiagPattern))
                
                qp.drawRect(QRect(image_finder.roi_x + self.parent._main_object_finder.x,
                    image_finder.roi_y + self.parent._main_object_finder.y,
                    image_finder.roi_width,
                    image_finder.roi_height))  
                    
                qp.fillRect(image_finder.x,
                    image_finder.y,
                    image_finder.width,
                    image_finder.height,
                    QBrush(QColor(172, 96, 246, 130)))
                
                    
                qp.drawRect(QRect(image_finder.x,
                    image_finder.y,
                    image_finder.width,
                    image_finder.height))
            
            else:
                qp.fillRect(image_finder.roi_x + self.parent._main_object_finder.x,
                    image_finder.roi_y + self.parent._main_object_finder.y,
                    image_finder.roi_width,
                    image_finder.roi_height,
                    QBrush(QColor(172, 96, 246, 180), Qt.BDiagPattern))
                    
                qp.drawRect(QRect(image_finder.roi_x + self.parent._main_object_finder.x,
                    image_finder.roi_y + self.parent._main_object_finder.y,
                    image_finder.roi_width,
                    image_finder.roi_height))  
                
            """
            qp.fillRect(image_finder.x,
                image_finder.y,
                image_finder.width,
                image_finder.height,
                QBrush(QColor(172, 96, 246, 130)))
            
                
            qp.drawRect(QRect(image_finder.x,
                image_finder.y,
                image_finder.width,
                image_finder.height))
            """
     
    def draw_cross_lines(self, qp):
    
        self.setCursor(QCursor(Qt.CrossCursor))
                
        center = QPoint(QCursor.pos())
        
        pen = QPen()
        pen.setDashPattern([1, 1])
        pen.setWidth(1)
        pen.setBrush(QColor(32, 178, 170, 255))
        
        qp.setPen(pen)

        qp.drawLine(center.x(), center.y(), center.x(), 0)
        qp.drawLine(center.x(), center.y(), center.x(), self.height())
        qp.drawLine(center.x(), center.y(), 0, center.y())
        qp.drawLine(center.x(), center.y(), self.width(), center.y())

    def draw_capturing_roi_lines(self, qp):
           
        self.draw_capturing_rectangle_lines(qp)
        """
        mouse_position = QPoint(QCursor.pos())
        
        pen = QPen()
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        pen.setBrush(QBrush(QColor(0, 255, 0, 255)))
        
        qp.setPen(pen)
            
        rect = QRect(self.__click_position.x(), self.__click_position.y(),
            mouse_position.x() - self.__click_position.x(), mouse_position.y() - self.__click_position.y())
            
        qp.drawRect(rect)
        """
        
    def draw_capturing_rectangle_lines(self, qp):
            
        mouse_position = QPoint(QCursor.pos())
        
        pen = QPen()
        pen.setWidth(1)
        pen.setStyle(Qt.SolidLine)
        pen.setBrush(QBrush(QColor(0, 255, 0, 255)))
        
        qp.setPen(pen)
        
        qp.fillRect(self.__click_position.x() + 1,
            self.__click_position.y() + 1,
            mouse_position.x() - self.__click_position.x() - 1,
            mouse_position.y() - self.__click_position.y() - 1,
            QBrush(QColor(32, 178, 170, 100)))
            
        rect = QRect(self.__click_position.x(), self.__click_position.y(),
            mouse_position.x() - self.__click_position.x(), mouse_position.y() - self.__click_position.y())
            
        qp.drawRect(rect)