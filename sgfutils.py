
import  re
import os
import argparse
import numpy as np

class HexColor:
    def __init__(self):
        pass
    BLACK, WHITE, EMPTY = range(1, 4)


class SGFPositionActionUtil:
    pattern=r';[B|W]\[[a-zA-Z][0-9]+\]'
    def __init__(self, srcdir, outfilename, offset=1):
        self.srcdir=srcdir
        self.outfilename=outfilename
        self.outfilewriter=open(outfilename, "w")
        self.offset=offset

    def strSGFtoPositions(self, strSGF, movesquence):
        game = re.findall(self.pattern, strSGF)
        x = ""
        for i, rawMove in enumerate(game):
            x += rawMove[1:] + " "
            if i < self.offset:
                continue
            movesquence.append(x.strip())
        return movesquence

    def doConvertInDir(self):
        onlyfiles = [f for f in os.listdir(self.srcdir) if os.path.isfile(os.path.join(self.srcdir, f))]
        print("processing convert...")
        for f in onlyfiles:
            print("converting", f)
            infile = open(os.path.join(self.srcdir, f), "r")
            strSGFGame = infile.read()
            positionActionsList = []
            self.strSGFtoPositions(strSGFGame, positionActionsList)
            self.writePositionActions(positionActionsList)
            infile.close()
        print("Done, position-actions writing to", self.outfilename)
        self.outfilewriter.close()

    def writePositionActions(self, positionList):
        for posi in positionList:
            self.outfilewriter.write(posi)
            self.outfilewriter.write('\n')
        self.outfilewriter.flush()

    @staticmethod
    def removeDuplicates(boardsize, infilename):
        print("position-action remove duplicates...")
        tt = {}
        #hashUtil = ZobristHash(boardsize=boardsize)
        tenaryBoard=np.ndarray(shape=(boardsize*boardsize), dtype=np.int16)
        with open(infilename) as f:
            for line in f:
                line = line.strip()
                movesquence = line.split()
                #intmoveseq = []
                tenaryBoard.fill(0)
                turn=HexColor.BLACK
                for m in movesquence:
                    m=m.strip()
                    move = m[2:-1]
                    x = ord(move[0].lower()) - ord('a')
                    y = int(move[1:]) - 1
                    assert (0 <= x < boardsize)
                    assert (0 <= y < boardsize)
                    #intmoveseq.append(x * boardsize + y)
                    tenaryBoard[x*boardsize+y]=turn
                    turn=HexColor.EMPTY-turn

                #code = hashUtil.get_hash(intmoveseq)
                code = ''.join(map(str, tenaryBoard))
                tt[code] = line

        outfile = infilename + "_no_duplicates"
        print("size: ", len(tt.values()))
        print("saved as", outfile)
        with open(outfile, "w") as f:
            for line in tt.values():
                # print(line)
                f.write(line)
                f.write('\n')

class SGFPositionValueUtil(object):
    pattern=r';[B|W]\[[a-zA-Z][0-9]+\]'
    winnerPattern=r'RE\[[B|W]\+\]'

    def __init__(self, srcdir, outfilename, offset=1):
        self.srcdir=srcdir
        self.outfilename=outfilename
        self.offset=offset
        self.outwriter=open(self.outfilename,"w")

    def toPositions(self, strSGF, ret):
        game=re.findall(self.pattern, strSGF)
        x=""
        if(game[0][1]!='B'):
            print("not starting from B?")
            exit(0)
        for i, rawMove in enumerate(game):
            x +=rawMove[1:]+" "
            if i < self.offset-1:
                continue
            ret.append(x.strip())
        return ret

    def toPositionValues(self, strSGF, positionValuesList):
        assert(self.offset>=1)
        resultStr=re.findall(self.winnerPattern, strSGF)
        self.toPositions(strSGF, positionValuesList)
        resultStr=resultStr[0]
        winner=HexColor.BLACK if resultStr[3]=='B' else HexColor.WHITE
        for i, posi in enumerate(positionValuesList):

            if((len(posi.split())%2) + 1==winner):
                posi = posi + " " + "1.0"
            else:
                posi = posi + " " + "-1.0"
            positionValuesList[i]=posi

        return positionValuesList

    def writePositionValuesList(self, pvList):
        for posi in pvList:
            self.outwriter.write(posi)
            self.outwriter.write('\n')
        self.outwriter.flush()

    def doConvertInDir(self):
        onlyfiles = [f for f in os.listdir(self.srcdir) if os.path.isfile(os.path.join(self.srcdir, f))]
        print("processing convert...")
        for f in onlyfiles:
            print("converting", f)
            infile=open(os.path.join(self.srcdir, f), "r")
            sgfGame=infile.read()
            pvList=[]
            self.toPositionValues(sgfGame, pvList)
            self.writePositionValuesList(pvList)
            infile.close()
        print("Done, position-values saved in", self.outfilename)
        self.outwriter.close()


    @staticmethod
    def postprocess(boardsize, positionValuesFileName):
        print("position-value postprocessing")
        tt={}
        tenaryBoard=np.ndarray(shape=(boardsize*boardsize), dtype=np.int16)
        with open(positionValuesFileName) as f:
            for line in f:
                line=line.strip()
                movesquence=line.split()
                value = float(movesquence[-1])
                movesquence=movesquence[:-1]

                #assert(value<-0.99 or value>0.99)
                tenaryBoard.fill(0)
                turn=HexColor.BLACK
                for m in movesquence:
                    m=m.strip()
                    move=m[2:-1]
                    x=ord(move[0].lower())-ord('a')
                    y=int(move[1:])-1

                    assert(0<=x<boardsize)
                    assert(0<=y<boardsize)
                    tenaryBoard[x*boardsize+y]=turn
                    turn = HexColor.EMPTY - turn
                code=''.join(map(str,tenaryBoard))
                if code in tt:
                    mq, one_count, neg_one_count=tt[code]
                    if value>0.99:
                        one_count +=1
                    else:
                        neg_one_count +=1
                    tt[code]=(mq, one_count, neg_one_count)
                else:
                    one_count=0
                    neg_one_count=0
                    if value > 0.99:
                        one_count = 1
                    else:
                        neg_one_count = 1
                    tt[code]=(movesquence, one_count, neg_one_count)

        outfile=positionValuesFileName+"-post"
        print("size: ", len(tt))
        print("saved as", outfile)
        with open(outfile, "w") as f:
            for line in tt.values():
                #print(line)
                mq, one_count, neg_one_count = line
                for m in mq:
                    f.write(m+' ')
                res=(one_count - neg_one_count )*1.0/(one_count+neg_one_count)
                f.write(repr(res)+'\n')


def RewardAugment(srcPositionAction, srcPositionValue, outputname, boardsize=8):

    print("reward augmenting..")
    tenaryBoard=np.ndarray(shape=(boardsize*boardsize), dtype=np.int16)
    valueDict={}
    pvfile=open(srcPositionValue,"r")
    fout=open(outputname,"w")
    nextMoveMarker="NextMove: "
    for line in pvfile:
        line=line.strip()
        arr=line.split()
        S=arr[:-1]
        V=arr[-1]
        assert(-1-0.001<float(V)<1+0.001)
        tenaryBoard.fill(0)
        turn = HexColor.BLACK
        for m in S:
            m=m.strip()
            move = m[2:-1]
            x = ord(move[0].lower()) - ord('a')
            y = int(move[1:]) - 1
            tenaryBoard[x * boardsize + y] = turn
            turn = HexColor.EMPTY - turn

        code = ''.join(map(str, tenaryBoard))
        valueDict[code]=float(V)
    pvfile.close()

    posiDict = {}
    pdict2={}

    with open(srcPositionAction) as pafile:
        for line in pafile:
            moveseq=line.split()
            tenaryBoard.fill(0)
            turn=HexColor.BLACK
            action=moveseq[-1]
            moveseq=moveseq[:-1]
            for m in moveseq:
                m=m.strip()
                move=m[2:-1]
                x = ord(move[0].lower()) - ord('a')
                y = int(move[1:]) - 1
                tenaryBoard[x * boardsize + y] = turn
                turn = HexColor.EMPTY - turn
            code = ''.join(map(str, tenaryBoard))
            move=action.strip()[2:-1]
            x=ord(move[0].lower())-ord('a')
            y=int(move[1:]) - 1
            tenaryBoard[x*boardsize+y]=turn
            codeAfterstate=''.join(map(str,tenaryBoard))
            value=valueDict[codeAfterstate]
            pdict2[code]=moveseq
            if code in posiDict:
                posiDict[code].append((action,value))
            else:
                posiDict[code]=[(action,value)]

    for keyItem in posiDict:
        pass
        moveseq=pdict2[keyItem]
        for j in moveseq:
            fout.write(j + ' ')
        fout.write(nextMoveMarker)
        for move,value in posiDict[keyItem]:
            fout.write(move+' '+repr(value)+ ' ')
        fout.write('\n')

    fout.close()
    print("Done.")

def process0():
    outfilename="8x8-2.txt"
    putil=SGFPositionActionUtil(srcdir="/home/cgao3/Documents/hex_data/8x8-2stones-open", outfilename=outfilename, offset=2)
    putil.doConvertInDir()
    #putil.removeDuplicates(boardsize=8, infilename=outfilename)

def positionRemoveDuplicates():
    dataMain="new8x8total.txt"
    SGFPositionActionUtil.removeDuplicates(boardsize=8, infilename=dataMain)

def process1():
    outfilename = "8x8-noah.txt"
    putil = SGFPositionActionUtil(srcdir="/tmp/games8x8/games2/", outfilename=outfilename,
                                  offset=2)
    putil.doConvertInDir()

def vprocess1():
    outfilename="8x8-v1.txt"
    vutil=SGFPositionValueUtil(srcdir="/tmp/games8x8/games2/", outfilename=outfilename, offset=1)
    vutil.doConvertInDir()

def vprocess2():
    outfilename="value-8x8.txt"
    vutil=SGFPositionValueUtil(srcdir="/home/cgao3/Documents/hex_data/8x8-games1", outfilename=outfilename, offset=1)
    vutil.doConvertInDir()
def vprocessa4():
    outfile="8x8-v-a4.txt"
    vutil = SGFPositionValueUtil(srcdir="/home/cgao3/Documents/hex_data/a4", outfilename=outfile,
                                 offset=1)
    vutil.doConvertInDir()

def vpostprocess():
    SGFPositionValueUtil.postprocess(boardsize=8, positionValuesFileName="newtotalvalue.txt")

def posi13Process():
    #putil=SGFPositionActionUtil(srcdir="datafactory/mohexData13x13", outfilename="13x13-pa.txt")
    #putil.doConvertInDir()
    infile="13x13pa-withlg.txt"
    SGFPositionActionUtil.removeDuplicates(boardsize=13, infilename=infile)
def v13Process():
    #vutil=SGFPositionValueUtil(srcdir="datafactory/mohexData13x13/", outfilename="value-13x13.txt")
    #vutil.doConvertInDir()
    SGFPositionValueUtil.postprocess(boardsize=13,positionValuesFileName="13x13pv-withlg.txt")
if __name__ == "__main__":

    parser=argparse.ArgumentParser()
    parser.add_argument("--sgf2pa", action='store_true', default=False, help='sgf to position-action pair')
    parser.add_argument("--sgf2pv", action='store_true', default=False, help='sgf to position-value pair')

    parser.add_argument("--input_dir", type=str, default=None, help='input directory, it should only contain sgf files in this dir')
    parser.add_argument("--output", type=str, default=None)

    '''Usage 1. convert all sgf files in a directory to pa pair or pv pair,
       Usage 2. input a pa file to remove duplicates'''

    parser.add_argument("--pa_remove_duplicates", action='store_true', default=False, help='to remove duplicated pa pair')
    parser.add_argument("--input_pa_file", default=None)
    parser.add_argument("--boardsize", default=0, type=int)
    args=parser.parse_args()

    if(args.sgf2pa):
        if (not args.input_dir or not args.output):
            print("please indicate --input_dir and --output")
            exit(0)

        pUtil=SGFPositionActionUtil(srcdir=args.input_dir, outfilename=args.output)
        pUtil.doConvertInDir()
        exit(0)

    if (args.pa_remove_duplicates):
        if (not args.input_pa_file or not args.boardsize):
            print("please indicate pa file and boardsize, use --help for more")
            exit(0)

        SGFPositionActionUtil.removeDuplicates(boardsize=args.boardsize, infilename=args.input_pa_file)
        exit(0)




