import os
import random
import threading
import queue
import tkinter as tk
from tkinter import messagebox
import pygame
import speech_recognition as sr
import pyttsx3
from tkinter import ttk
from PIL import Image, ImageTk

# Global variables
song_dict = [
    {"name": "Dejavu", "path": "songs/Olivia Rodrigo - deja vu (Lyrics).mp3", "image": "images_display/dejavu.jfif"},
    {"name": "Dandelions", "path": "songs/Ruth B. - Dandelions (Lyrics).mp3", "image": "images_display/dandeline.jfif"},
    {"name": "Snowman", "path": "songs/Sia - Snowman.mp3", "image": "images_display/snowman.jfif"},
    {"name": "You are the reason", "path": "songs/Calum Scott - You Are The Reason (Lyrics).mp3", "image": "images_display/you are the reason.jpg"},
    {"name": "Perfect", "path": "songs/Perfect - Ed Sheeran (Lyrics).mp3", "image": "images_display/perfect.jpg"},
    {"name": "The lazy song", "path": "songs/Bruno Mars - The Lazy Song (Official Music Video).mp3", "image": "images_display/the lazy song.jpg"},
    {"name": "Can I be him", "path": "songs/James Arthur - Can I Be Him (Lyrics).mp3", "image": "images_display/can I be him.jpg"},
    {"name": "Impossible", "path": "songs/James Arthur - Impossible (Lyrics) (1).mp3", "image": "images_display/impossible.jpg"},
    {"name": "A thousand years", "path": "songs/James Arthur - A Thousand Years (Christina Perri Cover).mp3", "image": "images_display/a thousand year.jpg"},
    {"name": "Until I Found You", "path": "songs/Stephen Sanchez - Until I Found You (Lyrics).mp3", "image": "images_display/Until I found you.jfif"}
]

song_list = [song['name'] for song in song_dict]  # Extract song names from the song_dict
current_song = None
is_paused = False
music_volume = 0.5
tts_volume = 1.0
continuous_listening = False

# Initialize pygame mixer and TTS engine
pygame.mixer.init()
tts_engine = pyttsx3.init()

# Create a queue for handling TTS
tts_queue = queue.Queue()

def update_song_list():
    """Update the list of songs displayed in the ListBox."""
    song_listbox.delete(0, tk.END)
    for song in song_list:
        song_listbox.insert(tk.END, song)
        
def load_image(path, size):
    """Load an image with error handling."""
    try:
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        print(f"Image file not found: {path}")
        # Use a default image or handle gracefully
        return ImageTk.PhotoImage(Image.new('RGB', size, color=(200, 200, 200)))
    
def update_empty_box_image():
    """Update the empty box with the image of the currently playing song."""
    # Clear existing images (if any) from the empty box
    for widget in empty_box_frame.winfo_children():
        widget.destroy()

    if current_song:
        song = next((song for song in song_dict if song['name'] == current_song), None)
        if song:
            song_image = load_image(song['image'], (800, 400))  # Resize the image to fit the box size
            # Create a new image label and pack it into the frame
            image_label = tk.Label(empty_box_frame, image=song_image)
            image_label.image = song_image  # Keep a reference to avoid garbage collection
            image_label.pack(fill=tk.BOTH, expand=True)
        else:
            print(f"Song image for {current_song} not found.")
    else:
        # Display a default or placeholder image when no song is playing
        default_image = ImageTk.PhotoImage(Image.new('RGB', (800, 400), color=(200, 200, 200)))
        image_label = tk.Label(empty_box_frame, image=default_image)
        image_label.image = default_image
        image_label.pack(fill=tk.BOTH, expand=True)

def load_song(song_name):
    """Load a selected song."""
    global current_song
    song = next((song for song in song_dict if song['name'] == song_name), None)
    if song:
        pygame.mixer.music.load(song['path'])
        pygame.mixer.music.set_volume(music_volume)
        current_song = song_name
        update_selected_song_label()
        update_empty_box_image()  # Update the image in the empty box when a new song is loaded
    else:
        messagebox.showerror("Error", "Song not found.")

def play_music(selected_song=None):
    """Play a song, either the currently loaded song or a newly selected one."""
    global current_song
    if selected_song:  # Case 1: A specific song is selected using a voice command
        if selected_song in song_list:
            load_song(selected_song)
        else:
            messagebox.showerror("Error", "The selected song is not available.")
            return
    if current_song:  # Case 2: Resume or play the current song
        if not pygame.mixer.music.get_busy():  # If music was stopped
            pygame.mixer.music.play()
            speak(f"Now playing {current_song}.")
            update_empty_box_image()  # Update the image in the empty box
        else:  # If paused, just unpause and continue playing
            pygame.mixer.music.unpause()
            speak(f"Resuming {current_song}.")
            update_empty_box_image()  # Update the image in the empty box
    else:
        messagebox.showerror("Error", "No song selected to play.")


def pause_music():
    """Pause or unpause the music."""
    global is_paused
    if is_paused:
        pygame.mixer.music.unpause()
        is_paused = False
        speak("Music resumed.")
    else:
        pygame.mixer.music.pause()
        is_paused = True
        speak("Music paused.")

def stop_music():
    """Stop the music playback without deselecting the current song."""
    pygame.mixer.music.stop()
    global is_paused
    is_paused = False  # Reset paused state
    speak("Music stopped.")
    update_selected_song_label()

def shuffle_music():
    """Shuffle the playlist and play a random song."""
    random_song = random.choice(song_list)
    load_song(random_song)
    pygame.mixer.music.play()
    speak(f"Now playing a random song: {random_song}.")

def set_music_volume(value):
    """Set the music volume."""
    global music_volume
    music_volume = float(value)
    pygame.mixer.music.set_volume(music_volume)
    # volume_label.config(text=f"Volume: {int(music_volume * 100)}%")  # Update the label text to reflect the volume

def next_song():
    """Play the next song in the list."""
    global current_song
    if current_song:
        current_index = song_list.index(current_song)
        next_index = (current_index + 1) % len(song_list)
        load_song(song_list[next_index])
        play_music()
        song_listbox.selection_clear(0, tk.END)
        song_listbox.select_set(next_index)
        speak(f"Now playing {song_list[next_index]}.")
    else:
        messagebox.showerror("Error", "No song is currently playing.")

def back_song():
    """Play the previous song in the list."""
    global current_song
    if current_song:
        current_index = song_list.index(current_song)
        prev_index = (current_index - 1) % len(song_list)
        load_song(song_list[prev_index])
        play_music()
        song_listbox.selection_clear(0, tk.END)
        song_listbox.select_set(prev_index)
        speak(f"Now playing {song_list[prev_index]}.")
    else:
        messagebox.showerror("Error", "No song is currently playing.")

def update_selected_song_label():
    """Update the label to show the currently selected or playing song."""
    if current_song:
        selected_song_label.config(text=f"Now Playing: {current_song}")
    else:
        selected_song_label.config(text="No song selected.")

def on_song_select(event):
    """Handle the selection of a song from the list."""
    try:
        selected_index = song_listbox.curselection()[0]
        selected_song = song_list[selected_index]
        load_song(selected_song)
    except IndexError:
        messagebox.showerror("Error", "Please select a song.")

def process_voice_command(command):
    """Process voice commands and provide feedback."""
    global current_song
    command = command.lower()

    if "play" in command:
        for song in song_list:
            if song.lower() in command:  # If a specific song is mentioned
                play_music(selected_song=song)
                song_listbox.selection_clear(0, tk.END)
                song_listbox.select_set(song_list.index(song))
                return
        play_music()  # Resume if no specific song mentioned
    elif "pause" in command:
        pause_music()
    elif "stop" in command:
        stop_music()
    elif "shuffle" in command:
        shuffle_music()
    elif "next" in command:
        next_song()
    elif "back" in command:
        back_song()
    elif "volume up" in command:
        set_music_volume(min(music_volume + 0.1, 1.0))
    elif "volume down" in command:
        set_music_volume(max(music_volume - 0.1, 0.0))
    else:
        speak("Command not recognized. Please try again.")

def start_voice_thread():
    """Start a separate thread for voice recognition."""
    global continuous_listening
    continuous_listening = True  # Start continuous listening
    threading.Thread(target=continuous_voice_listening, daemon=True).start()
    speak("Listening started.")

def continuous_voice_listening():
    """Continuously listen for voice commands."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise
        while continuous_listening:
            try:
                # speak("Listening for your command.")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = recognizer.recognize_google(audio).lower()
                speak(f"You said: {command}")
                process_voice_command(command)
           
            except Exception as e:
                pass

def stop_voice_thread():
    """Stop the continuous voice listening thread."""
    global continuous_listening
    continuous_listening = False
    speak("Voice listening stopped.")

def speak(text):
    """Provide voice feedback using TTS."""
    # Add the text to the queue
    tts_queue.put(text)

def tts_worker():
    """Worker function to process the TTS queue and speak text."""
    while True:
        text = tts_queue.get()  # Block until something is added to the queue
        tts_engine.say(text)
        tts_engine.runAndWait()
        tts_queue.task_done()

# Start the TTS worker in a separate thread
threading.Thread(target=tts_worker, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Voice-Controlled Music Player")
root.geometry("1400x750")
root.config(bg="#ffffff")

# Load button images
play_image = load_image("images_song/play.jpg", (40, 40))
pause_image = load_image("images_song/pause.jpg", (28, 28))
stop_image = load_image("images_song/stop.jpg", (50, 50))
next_image = load_image("images_song/next.jpg", (50, 50))
back_image = load_image("images_song/back.jpg", (50, 50))
shuffle_image = load_image("images_song/shuffle.jpg", (35, 35))
reverse_image = load_image("images_song/reverse.webp", (30, 30))

# Font Style
font_default = ("Arial", 12, "bold")

# Header Section
header_frame = tk.Frame(root, bg="#2c3e50", pady=20)
header_frame.pack(fill=tk.X)
title_label = tk.Label(header_frame, text="Voice-Controlled Music Player", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white")
title_label.pack()

# Frame for the empty box and song list (side by side)
side_by_side_frame = tk.Frame(root, bg="#2c3e50")
side_by_side_frame.pack(fill=tk.BOTH, padx=0, pady=10)

# Empty Box Frame (left side) with 500 width
empty_box_frame = tk.Frame(side_by_side_frame, bg="#34495e", width=800, height=400)
empty_box_frame.grid(row=0, column=0, padx=0)

# Song List Section (Right side) with 500 width
song_list_frame = tk.Frame(side_by_side_frame, bg="#34495e", padx=10, pady=10, width=700, height=300)
song_list_frame.grid(row=0, column=1, padx=20, ipady=16)

song_listbox = tk.Listbox(song_list_frame, font=("Arial", 14), bg="#34495e", fg="white", selectbackground="lightblue", selectmode=tk.SINGLE, height=15, width=40, bd=0, highlightthickness=0)
song_listbox.pack(padx=0, ipadx=50)
song_listbox.bind("<ButtonRelease-1>", on_song_select)

# Populate the song list
update_song_list()

# Selected song label (below the song list)
selected_song_label = tk.Label(root, text="No song selected.", font=("Arial", 14), bg="#2c3e50", fg="white")
selected_song_label.pack(pady=4)

# Control Panel Section
control_frame = tk.Frame(root, bg="white")
control_frame.pack( padx=0, pady=10)

# Volume Control
# volume_label = tk.Label(root, text=f"Volume: {int(music_volume * 100)}%", font=("Arial", 14), bg="#2c3e50", fg="white")
# volume_label.pack(pady=0)

volume_slider = ttk.Scale(root, from_=0, to=1, orient="horizontal", length=300, command=set_music_volume)
volume_slider.set(music_volume)  # Set the initial value of the volume slider
volume_slider.pack(pady=10)

# Add control buttons
play_button = tk.Button(control_frame, image=play_image , font=font_default, command=lambda: play_music(), bd=0, bg="white")
play_button.grid(row=0, column=3, padx=10)

pause_button = tk.Button(control_frame, image=pause_image, font=font_default, command=pause_music, bd=0, bg="white")
pause_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(control_frame, image=stop_image, font=font_default, command=stop_music, bd=0, bg="white")
stop_button.grid(row=0, column=2, padx=10)

next_button = tk.Button(control_frame, image=next_image, font=font_default, command=next_song, bd=0, bg="white")
next_button.grid(row=0, column=4, padx=10)

back_button = tk.Button(control_frame, image=back_image, font=font_default, command=back_song, bd=0, bg="white")
back_button.grid(row=0, column=1, padx=10)

shuffle_button = tk.Button(control_frame, image=shuffle_image, font=font_default, command=shuffle_music, bd=0, bg="white")
shuffle_button.grid(row=0, column=5, padx=10, pady=10)

start_button = tk.Button(control_frame, bg="#34495e", fg="white", text="Start Listening", font=font_default, command=start_voice_thread)
start_button.grid(row=1, column=2, padx=10, pady=10)

stop_button = tk.Button(control_frame, bg="#34495e", fg="white", text="Stop Listening", font=font_default, command=stop_voice_thread)
stop_button.grid(row=1, column=3, padx=10, pady=10)

root.mainloop()
