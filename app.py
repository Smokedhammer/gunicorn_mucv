from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re, glob, os,cv2,ast
import numpy as np
import pandas as pd
from shutil import copyfile
import shutil
from distutils.dir_util import copy_tree
import pyaudio
import detect

# Flask utils
from flask import Flask, redirect, url_for, request, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
import speech_recognition as sr

# Define a flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

#################### TEXT TO SPEECH ##################
import pyttsx3


def text_to_speech(text, gender):
    """
    Function to convert text to speech
    :param text: text
    :param gender: gender
    :return: None
    """
    voice_dict = {'Male': 0, 'Female': 1}
    code = voice_dict[gender]

    engine = pyttsx3.init()

    # Setting up voice rate
    engine.setProperty('rate', 125)

    # Setting up volume level  between 0 and 1
    engine.setProperty('volume', 0.8)

    # Change voices: 0 for male and 1 for female
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[code].id)

    engine.say(text)
    engine.runAndWait()
    



FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

 
audio1 = pyaudio.PyAudio()
 


def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

@app.route('/audio')
def audio():
    # start Recording
    def sound():

        CHUNK = 1024
        sampleRate = 44100
        bitsPerSample = 16
        channels = 2
        wav_header = genHeader(sampleRate, bitsPerSample, channels)

        stream = audio1.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,input_device_index=1,
                        frames_per_buffer=CHUNK)
        print("recording...")
        #frames = []
        first_run = True
        while True:
           if first_run:
               data = wav_header + stream.read(CHUNK)
               first_run = False
           else:
               data = stream.read(CHUNK)
           yield(data)

    return Response(sound())

@app.route('/', methods = ['GET'])
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/detect', methods=['GET','POST'])
def index1():
    # Main page
    
    ############################## TAKE AUDIO IN STUFF ########################
    
    
     
    transcript = ""
    if request.method == "POST":
        print("FORM DATA RECEIVED")

        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)
            
            
    ################################# RUN THE DETECTION ALGORITHM #####################
    
    text = "Welcome to the eyes for the elderly tool"
    
    if re.search(r"(where).*(watch).*|(find).*(watch).*",transcript,re.I):
        # we write a function here to run the detect.py file
        
        output= detect.run()
        
        #exec(open('detect.py').read())
        
        print(output)
        
        
        if re.search(r"Watch",str(output[-1])):
            
            #output_dict = ast.literal_eval(output[-2])
            
            output_dict = output[-2]
            
            location_of_object = output_dict['Watch']
            text=f"I found the watch. It is on the {location_of_object}"
        else:
            text = "object not found"
        
                
    
    # FOR DETECTING FOR GLASSES        
    if re.search(r"(where).*(glasses).*|(find).*(glasses).*",transcript,re.I):
        # we write a function here to run the detect.py file
        
        output= detect.run()
        
        #exec(open('detect.py').read())
    
        
        print(output)
        
        
        if re.search(r"Glasses",str(output[-1])):
            
            output_dict = ast.literal_eval(output[-2])
            
            #maybe add a try except block over here
            location_of_object = output_dict['Glasses']
            text=f"I found the glasses. It is on the {location_of_object}"

        else:
            text = "object not found"
    
            
    # FOR DETECTION FOR THE PHONE
    if re.search(r"(where).*(phone).*|(find).*(phone).*",transcript,re.I):
        
        output= detect.run()
        #exec(open('detect.py').read())
    
        print(output)
        
        if re.search(r"Mobile phone",str(output[-1])):
            
            output_dict = ast.literal_eval(output[-2])
            
            location_of_object = output_dict['Mobile phone']
            text=f"I found the phone. It is on the {location_of_object}"
        
        else:
            text = "object not found"
               
                
    ##################### TEXT TO SPEECH ###########################
    # Over here we want to convert our findings into speech and all
    
    
    
    text = text
    gender = "Male" # request.form['voices']
    text_to_speech(text, gender)
            
    

    return render_template('detect.html', transcript=transcript)
   

    
      
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True,port=5000)
    
    
    ############################################################

#Over here we are trying to build a database to store the information that we are trying to represent

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(200), nullable= False)

    def __repr__(self):
        return '<Task %r>' % self.id
    

print('Model loaded. Check http://127.0.0.1:5000/')
"""

REMOVED AND REPLACED

@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')

"""



    # We need to be able to get a continuous stream of audio input and feed it to the run.py. 
    # We can also keep the code here and functionalize it. 
    
    # Then we need to be able to get inputs from the camera and all and to run detect.py
    # After that we return it in form of audio to the user (Maybe save in the database)     
    
    
    
    
    
    

@app.route('/lol', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        get_detected_object=detect_object.glass_detector(file_path)
        #return get_detected_object
        # Over here get_detected_object is probably the name of the object
        # Let us try populating this into the table
        new_img_name = Todo(content=get_detected_object)
        #f.save()
        
        return str(get_detected_object)
        try:
            db.session.add(new_img_name)
            db.session.commit()
            return redirect('/')
        except:
            return 'Error occurred somewhere while detecting'
        
    else: 
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html',tasks=tasks)
    
    return None


if __name__ == '__main__':
    app.run(debug=True)