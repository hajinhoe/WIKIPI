import json
import os


class Config:
    def __init__(self, file):
        self.file = file + '.json'

    def exist(self):
        if os.path.isfile(self.file):
            return True
        else:
            return False

    def load(self):
        with open(self.file, 'r') as f:
            config = json.load(f)
        f.close()
        return config

    def save(self, dictionary):
        with open(self.file, 'w') as f:
            json.dump(dictionary, f)
        f.close()
        with open(self.file, 'r') as f:
            config = json.load(f)
        f.close()
        return config
