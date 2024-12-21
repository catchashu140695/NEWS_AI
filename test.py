import win32serviceutil
import win32service
import win32api

win32serviceutil.InstallService(
    'EmailSenderService',
    'EmailSenderService',
    'Python Email Sender Service',
    None, None, None,
    win32service.SERVICE_WIN32_OWN_PROCESS,
    win32service.SERVICE_AUTO_START
)
