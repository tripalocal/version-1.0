def isEnglish(s):
    try:
        s.decode('ascii') if isinstance(s, bytes) else s.encode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True