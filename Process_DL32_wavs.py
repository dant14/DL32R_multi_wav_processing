import os, re, subprocess, shutil, sys, glob, time, datetime
from pathlib import Path

numOfChannels = 32
path_audio = "generated_audio"
norm_level = "-5"

def listNorderMainFiles():
    wavFiles = {}
    wavFilesIdx = []
    wavFilesIdxSorted = []

    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        x = re.search("(_\d{1,3}.wav)", f)
        if x:
            idx = (x.group()).strip("_.wav")
            wavFiles[idx] = f
            wavFilesIdx.append(idx)

    wavFilesIdxSorted = sorted(wavFilesIdx, key=lambda x: int(x))

    return wavFiles, wavFilesIdxSorted


def createFolders():
    if os.path.isdir(path_audio):
        shutil.rmtree(path_audio)
    os.mkdir(path_audio)
    for i in range(numOfChannels):
        os.mkdir(path_audio + "/" + "channel_" + str(i+1))

def splitEachWav(fileName):
    startIdx = 1
    for ch in range(startIdx, (numOfChannels+startIdx)):
        newFileName = fileName.rstrip(".wav") + "_ch_" + str(ch) + ".wav"
        pathName = path_audio + "/channel_" + str(ch) + "/" + newFileName
        subprocess.run(["sox", fileName, pathName, "remix", str(ch)])


def processWavs(filesUnordered, idxsOrdered):
    i = 0
    lastIdx = 0
    # print(idxsOrdered)
    for idx in idxsOrdered:
        lastIdx = idx
        progress(i, len(idxsOrdered), status='Splitting the 32-ch wav files into tracks. File '
            + str(i+1) + ' of ' + str(len(idxsOrdered)) + '; ' + filesUnordered[str(int(idx))])
        
        splitEachWav(filesUnordered[str(int(idx))])

        i += 1

    progress(1, 1, status='Splitting the 32-ch wav files into tracks. File '
            + str(i) + ' of ' + str(i) + '; ' + filesUnordered[str(int(lastIdx))])

    # progress(len(idxsOrdered), len(idxsOrdered), status='                              Done splitting the 32-ch wav files into tracks.')

    print('\n', flush=True)
    for idx in idxsOrdered:
        print(filesUnordered[str(int(idx))])
    print('\n', flush=True)


def joinEachChannel(chIdx, orderedIdxs):
    outputFileName = "channel_" + str(chIdx) + "_joinedOutput.wav"
    chFiles = {}
    relPath = path_audio + "/channel_" + str(chIdx)
    finalOutputFileName = relPath + "/" + "ch_" + str(chIdx) + "_joined_norm.wav"

    files = [f for f in os.listdir(relPath)]
    for f in files:
        x = re.search("(_\d{1,3}_ch)", f)
        if x:
            idx = (x.group()).strip("_ch")
            chFiles[idx] = f

    firstOutFile = "0_" + outputFileName
    subprocess.run(["sox", (relPath + "/" + chFiles[orderedIdxs[0]]), (relPath + "/" + chFiles[orderedIdxs[1]]), (relPath + "/" + firstOutFile)])
    os.remove(relPath + "/" + chFiles[orderedIdxs[0]])
    os.remove(relPath + "/" + chFiles[orderedIdxs[1]])

    # sox Hv_vech_3.wav Seti_3.wav remix 22 norm -0.5

    i = 0
    lastFile = ''
    for idx in orderedIdxs[1:-1]:
        if len(orderedIdxs) == (i+1):
            break

        firstFile = relPath + "/" + str(i) + "_" + outputFileName
        secondFile = relPath + "/" + chFiles[str(int(idx) + 1)]
        outFile = relPath + "/" + str(i+1) + "_" + outputFileName
        lastFile = outFile

        subprocess.run(["sox", firstFile, secondFile, outFile])
        os.remove(firstFile)
        os.remove(secondFile)
        i += 1

    subprocess.run(["sox", lastFile, finalOutputFileName, "norm", norm_level])
    os.remove(lastFile)
    up_one_dir(finalOutputFileName)
    

def processChannels(sortedIdxs):
    startIdx = 1
    for ch in range(startIdx, (numOfChannels+startIdx)):
        joinEachChannel(ch, sortedIdxs)
        progress(ch, numOfChannels, status='Joined ' + str(ch) + ' of ' + str(numOfChannels) + ' channels.')


def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s %s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def up_one_dir(path):
    try:
        # from Python 3.6
        parent_dir = Path(path).parents[1]
        # for Python 3.4/3.5, use str to convert the path to string
        # parent_dir = str(Path(path).parents[1])
        shutil.move(path, parent_dir)
    except IndexError:
        # no upper directory
        pass

def deleteFolders():
    flist = os.listdir(path_audio)
    chDirList = [f for f in flist if "channel_" in f]
    for dr in chDirList:
        shutil.rmtree(path_audio + "/" + dr)

if __name__ == "__main__":
    start_time = time.time()
    print('\n', flush=True)
    createFolders()
    unsortedFiles, sortedIdxs = listNorderMainFiles()
    processWavs(unsortedFiles, sortedIdxs)
    processChannels(sortedIdxs)
    deleteFolders()
    print("\nSUCCESS\n", flush=True)
    end_time = time.time()
    hours, rem = divmod(end_time-start_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print("\nTime Elapsed:")
    print("\nhh:mm:ss.ms")
    print("{:0>2}:{:0>2}:{:05.2f}\n".format(int(hours),int(minutes),seconds))
