import csv
import io


def decode_csv_bytes(data):
    """Return CSV text from UTF-8 or Windows ANSI (cp1252) bytes.

    Aerogest and French Excel export CSV in cp1252. In that encoding é is the
    single byte 0xE9, which is not valid UTF-8.
    """
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


class UnicodeReader:
    """CSV reader yielding Unicode strings from an encoded stream."""

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        data = f.read()
        if isinstance(data, bytes):
            if encoding in ("utf-8", "utf-8-sig"):
                data = decode_csv_bytes(data)
            else:
                data = data.decode(encoding)
        self.reader = csv.reader(io.StringIO(data), dialect=dialect, **kwds)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.reader)


class UnicodeWriter:
    """CSV writer encoding rows to the target stream."""

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.stream = f
        self.encoding = encoding
        self.writer = csv.writer(io.StringIO(), dialect=dialect, **kwds)
        self._dialect = dialect
        self._kwds = kwds

    def writerow(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer, dialect=self._dialect, **self._kwds)
        writer.writerow(row)
        self.stream.write(buffer.getvalue().encode(self.encoding))

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
