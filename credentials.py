"""Windows-only secret storage. No fallback backend and no secret-bearing errors."""
import ctypes
from ctypes import wintypes
import os
import re

class CredentialError(Exception):
    pass

class CREDENTIAL(ctypes.Structure):
    _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)), ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]

class WindowsCredentials:
    def __init__(self):
        if os.name != 'nt':
            raise CredentialError('CREDENTIAL_STORE_UNAVAILABLE')
        self.api = ctypes.WinDLL('advapi32', use_last_error=True)
        self.api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]
        self.api.CredFree.restype = None

    def target(self, reference):
        if not isinstance(reference, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', reference):
            raise CredentialError('INVALID_CREDENTIAL_REFERENCE')
        return 'personal-ai-assistant/github/' + reference

    def get(self, reference):
        ptr = ctypes.POINTER(CREDENTIAL)()
        if not self.api.CredReadW(self.target(reference), 1, 0, ctypes.byref(ptr)):
            raise CredentialError('CREDENTIAL_NOT_CONFIGURED' if ctypes.get_last_error() == 1168 else 'CREDENTIAL_STORE_UNAVAILABLE')
        try:
            try:
                value = ctypes.string_at(ptr.contents.CredentialBlob, ptr.contents.CredentialBlobSize).decode('utf-8')
            except UnicodeDecodeError:
                raise CredentialError('CREDENTIAL_FORMAT_INVALID') from None
            if len(value) > 2500 or not value or not value.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in value):
                raise CredentialError('CREDENTIAL_FORMAT_INVALID')
            return value
        finally:
            self.api.CredFree(ptr)

    def set(self, reference, token):
        if not token or not token.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in token) or len(token) > 2500:
            raise CredentialError('CREDENTIAL_FORMAT_INVALID')
        raw = token.encode('ascii')
        blob = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        entry = CREDENTIAL(Type=1, TargetName=self.target(reference), CredentialBlobSize=len(raw),
                           CredentialBlob=blob, Persist=2, UserName='github-pat')
        try:
            if not self.api.CredWriteW(ctypes.byref(entry), 0):
                raise CredentialError('CREDENTIAL_STORE_UNAVAILABLE')
        finally:
            ctypes.memset(blob, 0, len(raw))

    def delete(self, reference):
        if not self.api.CredDeleteW(self.target(reference), 1, 0) and ctypes.get_last_error() != 1168:
            raise CredentialError('CREDENTIAL_STORE_UNAVAILABLE')
