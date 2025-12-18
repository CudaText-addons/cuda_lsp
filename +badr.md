
i used this version https://github.com/PurpleMyst/sansio-lsp-client/tree/de46dbf5fef94652dda2a3c47e5eedd5e3ed965f
__init__.py shows 0.12.0 but in fact it is 13 or 14, because 12 was before introducing pydantic2 , and they already published in pypi v13, so the master repo in github have to version wrong, it is 14 at least

they already dropped python 3.8 and now they use v3.10, so from time to time they will introduce some non 3.8 compatible methods, like match/case instead of if/elif or | union ...etc so when you merge the new updates you have to keep compatibility with 3.8 to keep win7 support

doc https://tomlin7.github.io/tarts/ this is a fork of sansio-lsp-client , it added doc to sansio

_________________
deleted lsp_modules313 its code is inlined now
lsp plugin is already broken in python 36/37 so no need for lsp_modules36 dir