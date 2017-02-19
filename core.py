import datetime
import hashlib


class Binary:
    def __init__(self, path, date=None):
        self.path = path
        self.date = date

        with open(path, 'rb') as file:
            content = file.read()
        self.id = hashlib.sha256(content).hexdigest()


class Diff:
    def __init__(self, binary1, binary2):
        self.binary1 = binary1
        self.binary2 = binary2

    def to_html(self):
        pass


class Family:
    def __init__(self, family):
        self.name = family
        self.binaries = []

    def add(self, binary):
        self.binaries.append(binary)


class Service:
    def __init__(self):
        self.binaries = {}
        self.families = {}

    def add_binary(self, family, path):
        if family not in self.families:
            self.families[family] = Family(family)

        binary = Binary(path)
        self.binaries[binary.id] = binary
        self.families[family].add(binary)

        return binary

    def diff(self, bin0, bin1):
        return Diff(bin0, bin1)



def main():
    svc = Service()
    bin0 = svc.add_binary('cryptomix', './samples/decrypted0')
    bin1 = svc.add_binary('cryptomix', './samples/decrypted1')

    diff = svc.diff(bin0, bin1)
    print diff.to_html()


if __name__ == '__main__':
    main()
