# def channels(*argv):
#         cmd = "Hellow"
#         txt = f" (@"
#         print(type(argv))
#         if isinstance(argv, list):
#                 for z in range(0, len(argv)):
#                         txt = f'{txt}{arg},'
#                 txt = txt[:-1]
#                 txt = f'{cmd} {txt})'
#         else:
#                 for arg in argv:
#                         txt = f'{txt}{arg},'
#                 txt = txt[:-1]
#                 txt = f'{cmd} {txt})'
#         return txt
# channels(107)
#
# channels(107,108,109)
#
# list = [107,108,109]
#
# channels(list)
min = 101
max = 110
l = []
for z in range(0,(max - min)):
       l.append(f'{min+z},')
txt = "".join(l)
txt = txt[:-1]
print(txt)