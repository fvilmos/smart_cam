

class clPostDetections():
    '''
    Send camera picture over mqtt, can be used for camera integration
    '''
    import paho.mqtt.client as mqtt
    import time
    import cv2
    import threading
    import sys

    def __init__(self, brokerIP='127.0.0.1', brokerPort=1883, statustopic='/smart_cam/status', labelstopic = '/smart_cam/labels',detections='/smart_cam/detections'):
        '''
        init
        :param statustopic: the status topic
        :param labelstopic: labels detected topic
        '''
        self.client = None
        self.statustopic = statustopic
        self.labelstopic = labelstopic
        self.detections = detections
        self.bIP = brokerIP
        self.bPort = brokerPort

        # mqtt status timeout
        self.timeout = 30

        # termination flag
        self.running = True

        # worker to keep alive mqtt connection
        self.t = self.threading.Thread(target=self.worker)

        # start the publishing
        self.mqttMainLoop()


    def clbkOnConnect(self, mqttclient, data, flags, retc):
        '''
        mqtt callback
        :param mqttclient: clent
        :param data: data
        :param flags: flags
        :param retc: return code
        :return: none
        '''

        if retc == 0:
            # mqtt broker connected
            self.client.connected_flag = True
            self.client.publish(self.statustopic, payload="ON", qos=0, retain=True)
        else:
            # no connection to the broker
            print("Error, MQTT broker not connected , return code:", retc)

    def clbkOnPublish(self, client, data, mid):
        '''
        mqtt callback
        :param data: data
        :param mid:
        :return:
        '''
        pass

    def __mqttInit(self):
        '''
        Create MQTT client
        :return: None
        '''
        mqttcl = self.mqtt.Client()
        mqttcl.connected_flag = False
        mqttcl.on_connect = self.clbkOnConnect
        mqttcl.on_publish = self.clbkOnPublish
        mqttcl.will_set(self.statustopic,"OFF", qos=0, retain=True)

        self.client = mqttcl


    def mqttMainLoop(self):
        '''
        Main loop for mqtt
        :param mqttbroker: address of the broker
        :param mqttort: porrt used
        :return: none
        '''

        # create mqtt clinet
        self.__mqttInit()

        try:
            self.client.connect(self.bIP, port=self.bPort)
        except:
            print ("No mqtt server found, check the host IP")
            self.terminate()
            exit(0)

        # wait for connection
        self.time.sleep(3)

        # start alive signaling
        self.t.start()

        #start main loop
        self.client.loop_start()

    def imgPublish(self,img,labels):
        '''
        Transform image to byte array and publish it
        :param img: imag to publish
        :param labels: labels detected
        :return:
        '''

        if img is not None:
            byte_array = self.cv2.imencode('.jpg', img)[1].tostring()
            self.client.publish(self.detections, byte_array, qos=0)
            self.client.publish(self.labelstopic, labels, qos=0)
        else:
            # do error handling, if needed
            print ("No image to send over mqtt!")

    def worker(self):
        '''
        Worker for keeping status alive
        :return: none
        '''
        count = 0
        while self.running:

            # implement a non blocking timer 1s based
            if count <= self.timeout:
                count += 1
                self.time.sleep(1)
            else:
                # send status periodically
                self.client.publish(self.statustopic, payload="ON", qos=0, retain=True)
                count = 0

        return
    def terminate(self):
        '''
        Stope timer, allow threads to terminate
        :return:
        '''
        self.running = False
        self.t.join(100)


class clPostDetectionsHttp:
    '''
    Implement a basic http server
    '''
    from threading import Thread
    import sys

    class clWorker(Thread):
        '''
        implement a threaded basic http server. Will respond to get requests
        '''
        from http.server import HTTPServer
        from http.server import BaseHTTPRequestHandler
        from threading import Thread, Event

        def __init__(self, host, port):
            '''
            :param host: host IP address
            :param port: host port number
            '''

            self.Thread.__init__(self)

            self.running = True
            self.host = host
            self.port = port

        def terminate(self):
            '''
            terminates the thread
            :return:
            '''
            self.running = False

        def run(self):
            '''
            run thread
            :return:
            '''

            s = self.Server
            httpd = self.HTTPServer((self.host, self.port), s)

            while self.running:
                # run http server
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print ('HTTP server keyboard Interrupt received...')
                    pass
                self.running.wait(1.0)
            httpd.server_close()

        class Server(BaseHTTPRequestHandler):
            from threading import Event
            import cv2
            img = None
            event = Event()

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "image/jpg")
                self.end_headers()

                if self.img is not None:
                    # wait for a new image
                    self.event.wait()
                    success, encoded_image = self.cv2.imencode('.jpg', self.img)
                    if success:
                        try:
                            self.wfile.write(encoded_image)
                        except:
                            # issue with serving the clients
                            print ("issue serving the clients")
                        self.img = None
                    # clear event, prepare for a new image
                    self.event.clear()

            def log_message(self, format, *args):
                '''
                surpress log messages
                :param format:
                :param args:
                :return:
                '''
                pass

            def imgUpdate(self, inimg):
                '''
                Update the image over http
                :param inimg: image
                :return:
                '''

                self.img = inimg

                #signal a new image
                self.event.set()

    def __init__(self, host, port):
        '''
        init
        :param host:host IP
        :param port: host port
        '''
        self.host = host
        self.port = port
        self.wk = self.clWorker(host, port)
        self.t = self.Thread(target=self.wk.run, daemon=True)
        self.t.start()

    def terminate(self):
        '''
        terminate thread, and wait to finish all other threads
        :return:
        '''
        self.wk.terminate()
        self.sys.exit(1)

    def imgUpdate(self, img):
        '''
        Update image
        :param img: input image
        :return:
        '''
        self.clWorker.Server.imgUpdate(self.clWorker.Server, img)
