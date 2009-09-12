# -*- coding: UTF8 -*-

### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


'''Window Menu

Python port of the Window Wenu component from Qt Solutions.

'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2009-09-04 20:24:24 +0200 (ven, 04 set 2009) $'
__revision__ = '$Revision: 531 $'

from PyQt4 import QtCore, QtGui

class QtWindowListMenu(QtGui.QMenu):
    '''The QtWindowListMenu class is a menu that provides navigation
    commands for the subwindows in a QMdiArea.

    It is typically used as the conventional "Windows" item in an MDI
    application's menubar. It provides some standard commands for
    arranging and closing the MDI subwindows, corresponding to the
    slots of QMdiArea, as well as shortcuts to navigate directly to
    each of them.

    Usage: After creation, use attachToMdiArea() to tell the
    QtWindowListMenu object which QMdiArea object it should provide
    navigation commands for.  It can then be added to a QMenuBar (or
    other objects that can take QMenus or QActions, like QToolButton
    or QMenu) in the ordinary way, since QtWindowListMenu is a QMenu
    subclass.

    The subwindow navigation items may be given a common icon with
    setDefaultIcon(). The item icon for a specific subwindow can be
    set with setWindowIcon().

    Customization: Additional menu items (actions) can be inserted
    into this menu in the ordinary way for a QMenu. The
    standardAction() method gives access to the standard navigation
    items, which can be used to change their icon, shortcut,
    visibility etc. Ultimately, the whole menu can be customized by
    overriding syncWithMdiArea() in a subclass of QtWindowListMenu.

    If a QtWindowListMenu is showed and opened before being attached
    to a QMdiArea, it will try to auto-attach itself to the closest
    sibling object that is or inherits QMdiArea, if any exists. This
    behaviour is intended for special usecases; normally you will want
    to explicitly specify the desired QMdiArea with attachToMdiArea().

    .. seealso:: QMdiArea, QMdiSubWindow, QMenuBar, QAction

    .. enum:: StandardAction

    This enum specifies the standard menu items of a QtWindowListMenu.

    * CloseAction    Ref. QMdiArea::closeActiveSubWindow()
    * CloseAllAction Ref. QMdiArea::closeAllSubWindows()
    * TileAction     Ref. QMdiArea::tileSubWindows()
    * CascadeAction  Ref. QMdiArea::cascadeSubWindows()
    * NextAction     Ref. QMdiArea::activateNextSubWindow()
    * PrevAction     Ref. QMdiArea::activatePreviousSubWindow()

    .. seealso:: standardAction()

    :Methods:

    * QtWindowListMenu(QWidget *parent = 0)
    * attachToMdiArea(QMdiArea *mdiArea)
    * QMdiArea *attachedMdiArea() const
    * setWindowIcon(const QMdiSubWindow *window, const QIcon &icon)
    * QIcon windowIcon(const QMdiSubWindow *window) const
    * setDefaultIcon(const QIcon &icon)
    * QIcon defaultIcon() const
    * QAction *standardAction(StandardAction item) const

    :protected SLOTS:

    * syncWithMdiArea()
    * activateWindow(QAction *act)
    * windowDestroyed(QObject *obj)

    '''

    CloseAction    = 0
    CloseAllAction = 1
    TileAction     = 3
    CascadeAction  = 4
    NextAction     = 6
    PrevAction     = 7

    def __init__(self, parent):
        '''Constructs a QtWindowListMenu object.

        The *parent* parameter is passed to the QMenu constructor.
        Although this parameter has the conventional default of 0,
        you will normally want to explicitly provide a parent object,
        since the later adding of this menu object to an action
        container (e.g. QMenuBar) does not cause a reparenting.
        The container is normally the natural choice for *parent*.

        '''

        super(QtWindowListMenu, self).__init__(parent)

        self.mdi = None
        self.setTitle(self.tr('&Windows'))
        self.connect(self, QtCore.SIGNAL('aboutToShow()'), self.syncWithMdiArea)

        self._stdGroup = QtGui.QActionGroup(self)
        self._stdGroup.setExclusive(False)
        self._winGroup = QtGui.QActionGroup(self)
        self._winGroup.setExclusive(True)
        self.connect(self._winGroup, QtCore.SIGNAL('triggered(QAction*)'),
                     self.activateWindow)

        # Create the standard menu items.
        # @Note: Creation order must match the StandardAction enum values ;-)
        act = QtGui.QAction(self.tr('Cl&ose'), self._stdGroup)
        act.setShortcut(self.tr('Ctrl+F4'))
        act.setStatusTip(self.tr('Close the active window'))

        act = QtGui.QAction(self.tr('Close &All'), self._stdGroup)
        act.setStatusTip(self.tr('Close all the windows'))

        act = self._stdGroup.addAction('')
        act.setSeparator(True)

        act = QtGui.QAction(self.tr('&Tile'), self._stdGroup)
        act.setStatusTip(self.tr('Tile the windows'))

        act = QtGui.QAction(self.tr('&Cascade'), self._stdGroup)
        act.setStatusTip(self.tr('Cascade the windows'))

        act = self._stdGroup.addAction('')
        act.setSeparator(True)

        act = QtGui.QAction(self.tr('Ne&xt'), self._stdGroup)
        act.setStatusTip(self.tr('Move the focus to the next window'))

        act = QtGui.QAction(self.tr('Pre&vious'), self._stdGroup)
        act.setStatusTip(self.tr('Move the focus to the previous window'))

        act = self._stdGroup.addAction('')
        act.setSeparator(True)

        self.addActions(self._stdGroup.actions())

        self._winMap = {}   # QMap<QAction *, QMdiSubWindow *>
        self._iconMap = {}  # QMap<const QMdiSubWindow *, QIcon>
        self._defIcon = QtGui.QIcon()

    def attachToMdiArea(self, mdiArea):
        '''Instructs this menu to display navigation actions for the
        QMdiArea *mdiArea*.

        This should be done before this menu is shown.
        Specifying a null *mdiArea* is meaningless and will generate
        a warning.

        For special usecases, see the note about auto-attachment in the
        class description.

        '''

        if mdiArea == self.mdi:
            return

        acts = self._stdGroup.actions()
        acts = dict(zip(['CloseAction', 'CloseAllAction', '', 'TileAction',
                         'CascadeAction', '', 'NextAction', 'PrevAction'],
                        acts))

        if self.mdi:
            # i.e. we have previously been attached
            self.disconnect(acts['CloseAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('closeActiveSubWindow()'))
            self.disconnect(acts['CloseAllAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('closeAllSubWindows()'))
            self.disconnect(acts['TileAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('tileSubWindows()'))
            self.disconnect(acts['CascadeAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('cascadeSubWindows()'))
            self.disconnect(acts['NextAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('activateNextSubWindow()'))
            self.disconnect(acts['PrevAction'], QtCore.SIGNAL('triggered()'),
                            self.mdi, QtCore.SLOT('activatePreviousSubWindow()'))

        self.mdi = mdiArea
        if not self.mdi:
            QtCore.qWarning('QtWindowListMenu::attachToMdiArea(): '
                            'mdiArea is 0; menu will be empty.')
            return

        self.connect(acts['CloseAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('closeActiveSubWindow()'))
        self.connect(acts['CloseAllAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('closeAllSubWindows()'))
        self.connect(acts['TileAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('tileSubWindows()'))
        self.connect(acts['CascadeAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('cascadeSubWindows()'))
        self.connect(acts['NextAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('activateNextSubWindow()'))
        self.connect(acts['PrevAction'], QtCore.SIGNAL('triggered()'),
                     self.mdi, QtCore.SLOT('activatePreviousSubWindow()'))

    def attachedMdiArea(self):
        '''Returns the QMdiArea this menu is currently attached to,
        or None if not yet attached.

        .. seealso:: attachToMdiArea()

        '''

        return self.mdi

    def _attachToClosestMdiAreaObject(self):
        '''Attach the menu to the most likely intended MDI area object

        Heuristic method to auto-attach to the most likely intended
        mdiArea object, i.e. the closest "sibling" mdiArea widget.

        In the typical case, there will be only one in the mainwindow
        that owns this menu, and this method will find it.

        '''

        if self.mdi:
            return True

        mdi = None
        parent = self
        while not mdi:
            parent = parent.parentWidget()
            if not parent:
                return False
            if isinstance(mdi, QtGui.QMdiArea):
                mdi = parent
            else:
                mdi = parent.findChild(QtGui.QMdiArea)

        self.attachToMdiArea(mdi)
        return True

    def syncWithMdiArea(self):
        '''Syncronize with MDI area

        This slot is executed immediately prior to each opening of this
        menu. It removes the previous subwindow navigation actions and
        adds new ones according to the current state of the attached
        QMdiArea.

        '''

        if not self.mdi and not self._attachToClosestMdiAreaObject():
            return

        self._stdGroup.setEnabled(len(self.mdi.subWindowList()) > 0)

        self._winMap.clear()
        for act in self._winGroup.actions():
            self.removeAction(act)
            self._winGroup.removeAction(act)
            del act

        idx = 1
        for idx, win in enumerate(self.mdi.subWindowList()):
            if win.isWindowModified():
                modMarker =  "*"
            else:
                modMarker = ""

            title = win.windowTitle().replace('[*]', modMarker)

            if idx < 8:
                text = self.tr('&%1 %2').arg(idx+1).arg(title)
            else:
                text = self.tr('%1 %2').arg(idx+1).arg(title)

            icon = self._iconMap.get(win, self._defIcon)
            action = QtGui.QAction(icon, text, self._winGroup)
            action.setCheckable(True)
            action.setChecked(win == self.mdi.activeSubWindow())
            self._winMap[action] = win

        self.addActions(self._winGroup.actions())

    def activateWindow(self, act):
        '''Activate the corresponding sub-window in the MDI area

        This slot is executed when the user selects one of the subwindow
        navigation actions, given in *act*. It causes the corresponding
        subwindow in the attached QMdiArea object to be activated.

        '''

        if not self.mdi and not self._attachToClosestMdiAreaObject():
            return
        self.mdi.setActiveSubWindow(self._winMap.get(act))

    def windowDestroyed(self, obj):
        '''This slot is executed whenever a subwindow (*obj*) of the
        attached QMdiArea, for which an icon has been, is deleted.
        It clears that icon.

        '''

        del self._iconMap[obj]

    def setWindowIcon(self, window, icon):
        '''Sets *icon* as the icon of the menu item corresponding to
        the mdi subwindow *window*. If *icon* is a null icon, the
        current item icon will be cleared.

        .. seealso:: windowIcon()

        '''
        if not window:
            return
        if icon.isNull():
            del self._iconMap[window]
        else:
            self._iconMap[window] = icon
            self.connect(window, QtCore.SIGNAL('destroyed(QObject *)'),
                         self, QtCore.SLOT('windowDestroyed(QObject *)'))

    def windowIcon(self, window):
        '''Returns the icon of the menu item corresponding to the mdi
        subwindow *window*. This will be a null icon if none has been
        explicitly set.

        .. seealso:: setWindowIcon()

        '''

        #return self._iconMap.get(window)
        return self._iconMap[window]

    def setDefaultIcon(self, icon):
        '''Sets *icon* as the default icon for the subwindow navigation
        items in this QtWindowListMenu. If *icon* is a null icon, then
        the default icon will be cleared.

        .. seealso:: defaultIcon()

        '''

        self._defIcon = icon

    def defaultIcon(self):
        '''Returns the default icon for the subwindow navigation items
        in this QtWindowListMenu. This will be a null icon if none has
        been explicitly set.

        .. seealso:: setDefaultIcon()

        '''

        return self._defIcon

    def standardAction(self, item):
        '''Returns a pointer to the standard navigation action of this
        menu specified by \a item. This can be used to customize the
        look, shortcut, tool tip, etc. of this item, or to provide
        alternative access to it through a tool button etc.

        The returned object is owned by this QtWindowListMenu, and must
        not be deleted. If you want QtWindowListMenu to not display this
        action, set its "visible" property to false.

        '''

        return self._stdGroup.actions()[item]
