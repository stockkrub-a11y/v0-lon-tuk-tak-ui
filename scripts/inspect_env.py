p = 'D:\\lontuktak_v0_supa\\v0-lon-tuk-tak-ui\\scripts\\.env'
with open(p,'rb') as f:
    b = f.read()
print('BYTES:', b)
# show around the port substring
s = b.decode('utf-8', errors='backslashreplace')
index = s.find('5432')
print('INDEX OF 5432:', index)
print('SURROUNDING (20 chars before/after):')
print(repr(s[max(0,index-20):index+20]))
