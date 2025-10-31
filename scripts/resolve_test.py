import socket
host='db.julumxzweprvvcnealal.supabase.co'
print('host:',repr(host))
try:
    ai = socket.getaddrinfo(host, 5432)
    print('getaddrinfo OK, entries:', len(ai))
    for i,e in enumerate(ai[:5]):
        print(i, e[4])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('FAILED')
