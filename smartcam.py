#! /usr/bin/python3
import cv2
import os
import numpy as np
import requests
import argparse
from requests.auth import HTTPBasicAuth
from datetime import datetime



class clDnnHandler():

    def __init__(self, net, weights, imgsize=(640,382), netsize=(300,300), target="cpu"):
        '''
        :param net: optimized net file, in bin format
        :param weights: net weight file in xml format
        :param imgsize: default image size
        :param netsize: input image size for the net
        '''
        # Load network and weights
        self.net = cv2.dnn.readNet(net, weights)

        if target =="cpu":
            # no NCS try CPU
            print ("Smart Cam Running on CPU...")
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        else:
            # set target to NCS
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

        self.imgSize = imgsize

        self.netSize = netsize

    def inference(self, img):
        '''
        Get an image, return the detections
        :param img: input image
        :return: detections
        '''

        frame = cv2.resize(img,self.imgSize)

        # convert to blob
        blob = cv2.dnn.blobFromImage(frame, size=self.netSize, ddepth=cv2.CV_8U)

        # load image into dnn and inter it
        self.net.setInput(blob)
        out = self.net.forward()

        return out


class clFileProcessor():
    def __init__(self):
        pass

    def LoadList(self, file):
        '''
        Load list items
        :param file: file
        :return: list
        '''
        with open(file) as labels_file:
            labels_list = labels_file.read().splitlines()

        return labels_list

    def LoadConfig(self, file):
        '''
        Load the cinfiguration file
        :param file: filename i.e. ./config.txt
        :return: dictionarry of configuration items
        '''

        # config file schema format
        cdict = {'url':[], 'user':[],'password':[], 'blacklist':[], 'net':[], 'weights':[],'target':[],'savedetections':[],'saveraw':[],'showinfo':[]}

        # load file
        ll = self.LoadList(file)

        # fill dictionary
        for l in ll:
            if '#' in l or len(l)<=0:
                #skipp lines with comments
                pass
            else:
                sl = l.split('=')
                sitems = sl[1].split(',')

                #split line to items
                for i in sitems:
                    try:
                        cdict[sl[0]].append(str(i))
                    except:
                        print ("Config file issue detected...")
                        pass

        return cdict


class clIpCamera():
    def __init__(self, cam=None):
        self.cam = None
        self.camid = None

        if cam != None:
            # create cam instance
            self.cam = cv2.VideoCapture(int(cam))
            self.camid = int(cam)

    def Retrive(self, url="", usr="", passw="",imgsize=(640,382)):
        '''
        Grab a picture form IP camera, over http protocol
        :param url: camera url
        :param usr: user name
        :param passw: password
        :param imgsize:
        :return:
        '''

        frame = np.zeros((imgsize[0], imgsize[1], 3), dtype=np.uint8)
        try:
            if self.cam != None:
                # process usb cam
                _,img = self.cam.read()

                if type (img) != None:
                    frame = img

            else:
                # process IP cams
                img = requests.get(str(url), auth=HTTPBasicAuth(str(usr), str(passw))).content

                imgNp = np.array(bytearray(img), dtype=np.uint8)
                frame = cv2.imdecode(imgNp, -1)

        except:
            print ("Check access credentials...")

        frame = cv2.resize(frame, imgsize)

        return  frame


class clDetectionProcessor():

    def __init__(self, defaultConfidence=0.7):
        self.defConf = defaultConfidence

    def Process(self, frame, dnnOut,labels,blacklist, id, saveLabeled=0, saveRaw=0, cmdshow=1):
        '''

        :param frame: input image
        :param dnnOut: net output
        :param labels: net labels
        :param blacklist: skip labels
        :param id: cam id
        :param saveLabeled: will save labeled image
        :param saveRaw: will save unlabeled image
        :return: timestanp, detection and conficence, image
        '''

        # process results
        for detection in dnnOut.reshape(-1, 7):

            # get detection descriptors
            confidence = float(detection[2])

            if len(labels)>0:
                classLabel = labels[int(detection[1])]
            else:
                classLabel = str(int(detection[1]))

            # test if detected labe is on the skipp list
            if classLabel not in blacklist:

                # test if detection meet the confidence criteria
                if confidence > self.defConf:
                    xmin = int(detection[3] * frame.shape[1])
                    ymin = int(detection[4] * frame.shape[0])
                    xmax = int(detection[5] * frame.shape[1])
                    ymax = int(detection[6] * frame.shape[0])

                    # create naming, write unlabeled and labeled images
                    now = datetime.now()
                    dtStr = 'cam' + str(id) + '_' + now.strftime("%Y%m%d_%H%M%S")

                    if saveRaw > 0:
                        cv2.imwrite('./detections/' + dtStr + '.png', frame)

                    # draw boxes and markers
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color=(0, 255, 0))
                    cv2.rectangle(frame, (xmin, ymin), (xmin + 80, ymin+15), color=(0, 255, 0), thickness=cv2.FILLED)
                    labelStr = classLabel + "," + str("{0:.2f}".format(confidence))
                    cv2.putText(frame, labelStr, (int(xmin), int(ymin + 11)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0),1)

                    # list to the command line the detections, and save labeled image
                    if cmdshow > 0:
                        print(dtStr + "," + labelStr)

                    if saveLabeled > 0:
                        cv2.imwrite('./detections/' + dtStr + "_an" + '.png', frame)

                    return dtStr,labelStr,frame

def main():

    # process cmd line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('-cam', type=int, metavar='camera', default=None, choices=[None, 0, 1, 2, 3], help='use usb cam, id=[None,0,1,2,3], default=None - IPCams will be used')
    parser.add_argument('-l', type=str, required=False, metavar='labelfile', help='label file, like ./labels.txt')
    parser.add_argument('-c', type=str, required=True, metavar='config', help='config file, holds the access credentials, urls, like ./config.txt')
    parser.add_argument('-s', type=int, metavar='showdetections', default=0, choices=[0,1], help='show/ hide detection window [0,1], default=0')
    parser.add_argument('-conf', type=float, metavar='confidence', default=0.8, help='confidence value [0.0 - 1.0], default=0.8')
    parser.add_argument('-si', type=bool, metavar='showcmdinfo', default=False, help='show cmd line info on detection, default=False')

    args = parser.parse_args()

    # load configs
    fp = clFileProcessor()
    cff = fp.LoadConfig(args.c)


    blacklist = cff['blacklist']
    urls = cff['url']
    usr = cff['user'][0]
    passw = cff['password'][0]
    netbin = cff['net'][0]
    weights = cff['weights'][0]
    target = cff['target'][0]
    sdet = int(cff['savedetections'][0])
    sraw = int(cff['saveraw'][0])
    sinfo = int(cff['showinfo'][0])

    # load labels, if file available
    if args.l:
        labels = fp.LoadList(args.l)
    else:
        # no label file, blacklist will not work
        labels = []
        blacklist = []

    # camera handler
    ipcam = clIpCamera(args.cam)

    # create net
    dnn = clDnnHandler(netbin, weights,target=target)

    # image processor
    imgProcessor = clDetectionProcessor(args.conf)

    while True:
        count = 0

        # prepare for camera usage only
        if args.cam != None: urls =[""]

        for url in urls:

            # get camera picture
            img = ipcam.Retrive(url,usr,passw)

            out = dnn.inference(img)

            imgProcessor.Process(img,out,labels,blacklist,count,sdet,sraw,sinfo)

            # test if system can display windows
            if 'DISPLAY' in os.environ and args.s:
                cv2.namedWindow("Detections")
                cv2.moveWindow("Detections", 20, 20)
                cv2.imshow("Detections",img)

            k = cv2.waitKey(1)
            if k == ord('q'):
                # release cam
                cv2.destroyAllWindows()
                quit()

            count +=1

# main loop
if __name__ == "__main__":
    main()
