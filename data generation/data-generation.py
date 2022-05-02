import os


def wavFileGeneratorKEC():
    src = 'workspace/data/KEC'
    recFolders = list(filter(lambda f: rec_filter(f), os.listdir(src)))
    print(recFolders)
    
def rec_filter(x):
    return True if 'rec' in x else False

def generate():
    wavFileGeneratorKEC()

if __name__ == '__main__':
    generate()