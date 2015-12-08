#!/usr/bin/env python
# coding:utf-8

# Created on Dec. 5, 2015 Sat to enable i18n support in XX-Net.
# Based on http://stackoverflow.com/questions/18683905/how-to-use-jinja2-and-its-i18n-extenstion-using-babel-outside-flask
#
# I. See jinja2: https://github.com/mitsuhiko/jinja2
# II. See MarkupSafe-0.23.tar.gz: https://pypi.python.org/packages/source/M/MarkupSafe/MarkupSafe-0.23.tar.gz
# III. See Python babel: https://github.com/python-babel/babel
# IV. See pytz-2015.7.tar.gz: https://pypi.python.org/packages/source/p/pytz/pytz-2015.7.tar.gz#md5=252bb731883f37ff9c7f462954e8706d
# V. See Language_contry code list: http://www.fincher.org/Utilities/CountryLanguageList.shtml
# IMPORTANT:
# By the way, module decimal.py and numbers.py are also needed on Windows when run with the bundled Python,
# which were already appended to folder python27/1.0/lib. 

# See for these steps at http://tlphoto.googlecode.com/git/jinja2_i18n_howto.txt
# 0. Create the folder structure (no whitespace after the commas!!!)
# mkdir -pv ./lang/{en_US,zh_CN,fa_IR,es_VE,de_DE,ja_JP}/LC_MESSAGES/
# 1. Extract
#    pybabel -v extract -F babel.config -o ./lang/messages.pot ./
# 2. Init/Update
# 2.1 Init
#    pybabel init -l zh_CN -d ./lang -i ./lang/messages.pot
# 2.2 Update
#    pybabel update -l zh_CN -d ./lang -i ./lang/messages.pot
# 3. Compile
#    pybabel compile -f -d ./lang

import os
import sys
import locale

# Determines jinja2 and babel library path, and appends them to sys.path
current_path = os.path.dirname(os.path.abspath(__file__))

# When run standalonely
#if __name__ == '__main__':
python_path = os.path.abspath(os.path.join(current_path, os.pardir, 'python27', '1.0'))
python_lib = os.path.abspath(os.path.join(python_path, 'lib'))
noarch_lib = os.path.abspath(os.path.join(python_lib, 'noarch'))

# Michael.X: common lib should put in python27/1.0/lib/noarch, so all platform can use it.
# the path struct is not good because some history reason. python27/1.0/ is a win32 env.
# Appended modules decimal.py and numbers.py were copied from Python code on Windows,
# so they're put in folder python27/1.0/lib
if python_lib not in sys.path:
    sys.path.append(python_lib)

# As packages jinja2, markupsafe, babel, pytz are OS-independent,
# they're put in folder python27/1.0/lib/noarch
if noarch_lib not in sys.path:
    sys.path.append(noarch_lib)

#print("The current path: %s" % current_path)	
#print("The python path: %s" % python_path)
#print(sys.path)

import yaml
from jinja2 import Environment, FileSystemLoader
from babel.support import Translations
		

class Jinja2I18nHelper():
    """Demonstrates how to use jinja2 i18n engine to internationalize. A class-encapsulated version.
    Language files reside under folder lang of the current file location.
    """
    def __init__(self):
        """Sets up the i18n environment"""
        # The current language, i.e., the default system language
        self.current_locale, self.encoding = locale.getdefaultlocale() # tuple, e.g., ('en_US', 'UTF-8')                
        self.extensions = ['jinja2.ext.i18n', 'jinja2.ext.autoescape', 'jinja2.ext.with_']

        # Specifies the language path (the i10n path), ./lang which holds all the translations
        self.locale_dir = os.path.join(current_path, "lang")
        self.template_dir = "web_ui" # template file root folder
        
        self.loader = FileSystemLoader(self.template_dir)
        self.env = Environment(extensions=self.extensions, loader=self.loader) # add any other env options if needed
        #print("The current language is %s" % self.current_locale)
        #print("The locale dir: %s" % self.locale_dir)


    def refresh_env(self, locale_dir, template_dir):
        """Refreshes the locale environment by changing the locale directory and the temple file directory."""
        self.locale_dir = locale_dir
        self.template_dir = template_dir

        self.loader = FileSystemLoader(self.template_dir)
        self.env = Environment(extensions=self.extensions, loader=self.loader)
        #print("The current path: %s" % current_path)
        #print("The locale dir: %s" % self.locale_dir)
        #print("The current language is %s" % self.current_locale)


    def render(self, template_name, desired_lang):
        """Returns the rendered template with the desired language."""
        if not desired_lang:
		    desired_lang =  self.current_locale
		    
        desired_locales_list = [desired_lang]
        #print("Your desired language is %s" % desired_lang)
        translations = Translations.load(self.locale_dir, desired_locales_list)
        self.env.install_gettext_translations(translations)
        template = self.env.get_template(template_name)
        return template.render().encode('utf-8') # magic here & avoid error UnicodeEncodeError


# Creates the global singleton object (?)
ihelper = Jinja2I18nHelper()

    
if __name__ == '__main__':
    # Test cases. If not found, en_US is used instead.
    # Language_contry code list: http://www.fincher.org/Utilities/CountryLanguageList.shtml
    #desired_lang = "en_US" # American English
    #desired_lang = "zh_CN" # Simple Chinese
    #desired_lang = "es_VE" #Venezuela
    #desired_lang = "de_DE" # Geman
    desired_lang = "fa_IR" # Iran-Persian
    #desired_lang = "ja_JP" # Japanese

    root_path =  os.path.abspath(os.path.join(current_path, os.pardir))

    print("--- launcher/web_ui/about.html ---")
    launcher_path = os.path.abspath(os.path.join(root_path, 'launcher'))
    print("The launcher_path: %s" % launcher_path)
    locale_dir = os.path.abspath(os.path.join(launcher_path, 'lang'))
    template_dir = os.path.abspath(os.path.join(launcher_path, 'web_ui'))
    ihelper.refresh_env(locale_dir, template_dir)
    #print( ihelper.render("about.html", desired_lang) )
    
    print("\n--- launcher/web_ui/menu.yaml ---")    
    #stream = ihelper.render("menu.yaml", desired_lang)
    stream = ihelper.render("menu.yaml", None)
    print(yaml.load(stream))
    
    # Test locale in module gae_proxy
    print("\n--- gae_proxy/web_ui/menu.yaml ---")
    gae_proxy_path = os.path.abspath(os.path.join(root_path, 'gae_proxy'))
    print("The gae_proxy_path: %s" % gae_proxy_path)
    locale_dir = os.path.abspath(os.path.join(gae_proxy_path, 'lang'))
    template_dir = os.path.abspath(os.path.join(gae_proxy_path, 'web_ui'))
    ihelper.refresh_env(locale_dir, template_dir)
    stream = ihelper.render("menu.yaml", desired_lang)
    print(yaml.load(stream))    
