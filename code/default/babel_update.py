#!/usr/env/bin python

import os


# pip install googletrans==4.0.0-rc1
from googletrans import Translator
import polib


translator = Translator(service_urls=[
      'translate.google.com',
    ])

for lang in ["ru_RU"]:  # "fa_IR",
    for module in ["launcher", "smart_router", "x_tunnel"]:  #
        source_po = polib.pofile(f'{module}/lang/zh_CN/LC_MESSAGES/messages.po')
        lang_path = f'{module}/lang/{lang}/LC_MESSAGES'
        if not os.path.isdir(lang_path):
            os.makedirs(lang_path, exist_ok=True)

        new_fp = f'{lang_path}/translated.po'
        with open(new_fp, "w") as fd:
            fd.write("")

        new_po = polib.pofile(new_fp)

        for entry in source_po:
            try:
                result = translator.translate(entry.msgid, dest=lang[0:2])
                res_text = result.text
            except Exception as e:
                print(f"translate {entry.msgid} failed, e:{e}")
                res_text = ""

            new_entry = polib.POEntry(
                msgid=entry.msgid,
                msgstr=res_text,
                occurrences=entry.occurrences )

            new_po.append(new_entry)

        new_po.save(new_fp)
        print(f"module {module} translated to {lang}.")
