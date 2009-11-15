A Sphinx theme for SourceForge hosted projects
==============================================

:Author: Antonio Valentino
:Contact: a_valentino@users.sf.net
:Version: 1.0
:Copyright (C): 2009 Antonio Valentino


All `SourceForge.net`_ projects that use the `SourceForge.net`_ project web 
services are required to display the `SourceForge.net`_ logo on all web pages, 
per the `Project Web, Shell and Database Services`__ site document.

It is also common practice for SF hosted projects to display links to the 
*SF project page*, *SF downloads page*, etc, in the project website.

.. _`SourceForge.net`: http://sourceforge.net
__ http://p.sf.net/sourceforge/logo


Summary of changes against the standard theme
---------------------------------------------

* SourceForge logo displayed in the sidebar of each page
* SourceForge project links displayed in the sidebar (optional)
* additional links (provided via conf.py) displayed in the sidebar (optional)
* `doctitle` displayed over the `relbar1` in the `master_doc`
* different (and customizable) colours for todo directive


SourceForge project info
------------------------

The *unixname* and the *groupid*, of the project are needed to compute the 
project paths on `SourceForge.net`_ site.
It is strongly recommended to to provide both *unixname* and *groupid* 
parameters.
It can be done by setting the `html_theme_options` in the documentation 
`conf.py` as shown in the following example::

    html_theme_options = {
        'unixname': 'gsdview',
        'groupid': '226458',
    }
    
If the *unixname* is not provided it is assumed: unixname = lower(project)

.. warning:: if the *groupid* is not provided links needing it, and **SF logo** 
             are not displayed.


`SourceForge.net`_ logo preferences
-----------------------------------

SF provides different version of the SF logo that have to be displayed in
all pages hosted on SF.
Logos are identified by a type id [8-16] and each logo has its own size.
The *sflogotype*, *sflogowidth* and *sflogoheight* allow to customize it::

    sflogotype      = 14
    sflogowidth     = 150
    sflogoheight    = 40

.. warning:: The SourceForge.net logo may not be modified for any purpose.
             The changing of things like size, color, and form factor is
             prohibited.


The sidebar *links* section
---------------------------

The *sporceforge* theme provides a custom html template for sidebars.
It adds to the sidebar a `Links` section with standard links to SF hosted 
project pages and an optional list of user provided additional links.

In order to display the customized sidebar, and the hence SF links, 
the `sfpagesidebar.html` template ave to be associated to the target document
using the `html_sidebars` optionin the `conf.py` file::

    html_sidebars = {'index': 'sfpagesidebar.html'}

`SourceForge.net`_ also provides `hosted apps`_, a number of well-written 
Open Source applications which are useful to developers for personal use and 
critical to meeting the needs of Open Source software development projects.

If the project provides a trac_ site hosted on `SourceForge.net`_ it is 
possible to include a link pointing to it in the sidebar using the `hastrac`
theme option::

    html_theme_options = {
        'hastrac': True,
    }

.. _`hosted apps`: https://sourceforge.net/apps/trac/sourceforge/wiki/Hosted%20Apps
.. _trac: http://trac.edgewall.org

Additional links can be specified using the `extralinks` theme option:: 

    html_theme_options = {
        'extralinks': [
            ('GSDView Pro', 'http://www.example.com/products/gsdview/index.html'),
        ],
    }

It is also possible to suppress *SF project linksé and  display only 
*extralinks* by using the `nosflinks` option::

    html_theme_options = {
        'nosflinks': True,
    }


A common example
----------------

Here it is a summery of options to set in the `conf.py` file in order to use 
the *sourceforge* sphinx theme::

    html_theme = 'sourceforge'
    html_theme_path = ['/path/to/themes/folder']
    html_theme_options = {
        'unixname': 'gsdview',
        'groupid': '226458',
        'hastrac': True,
        #'nosflinks': False,
        #'sflogotype': '14',
        #'sflogowidth': '150',
        #'sflogoheight': '40',
        #'docstitlecolor': 'white',
        'extralinks': [
            ('GSDView Pro', 'http://www.example.com/products/gsdview/index.html'),
        ],
    }
    html_sidebars = {'index': 'sfpagesidebar.html'}

