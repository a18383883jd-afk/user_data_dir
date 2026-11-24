[app]
title = Payment Tester Pro
package.name = paymenttesterpro
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,requests,urllib3,chardet,idna,openssl,certifi
android.permissions = INTERNET
android.archs = arm64-v8a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
