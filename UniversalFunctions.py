from PyQt6.QtCore import QObject, QMetaMethod

import timeit

count = 0


def get_signal(oObject: QObject, strSignalName: str):
    oMetaObj = oObject.metaObject()
    for i in range(oMetaObj.methodCount()):
        oMetaMethod = oMetaObj.method(i)
        if not oMetaMethod.isValid():
            continue
        if oMetaMethod.methodType() == QMetaMethod.MethodType.Signal and \
                oMetaMethod.name() == strSignalName:
            return oMetaMethod

    return None


def get_time(function):
    print(timeit.timeit('function()', number=1, globals=locals()))
