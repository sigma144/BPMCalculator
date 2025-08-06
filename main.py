import os
import librosa
import statistics
import pygame
import math
from time import sleep

def get_onsets(path):
    outpath = path + '.beatmap.txt'
    if os.path.exists(outpath):
        with open(outpath, 'r') as f:
            frames = [int(l) for l in f.readlines()]
    else:
        x, sr = librosa.load(path)
        frames = librosa.onset.onset_detect(y=x, sr=sr)#, hop_length=500)
        #times = librosa.frames_to_time(frames)
        #with open(outpath, 'wt') as f:
        #    f.write('\n'.join([str(f) for f in frames]))
    return frames

def find_bpm(path):
    print("Finding onsets...")
    sr = librosa.get_samplerate(path)
    frames = get_onsets(path)
    #play_onsets(path, frames)
    print("Calculating BPM...")
    gaps = [frames[i+1] - frames[i] for i in range(len(frames)-1)]
    #Account for time resolution limit
    beat_estimate = int(statistics.median(gaps))
    bpm_estimate = round(60 / beat_estimate * sr / 1024)
    if bpm_estimate > 300: bpm_estimate //= 2
    times = librosa.frames_to_time(frames)
    #local search from estimate
    best_score = -1000000
    best_bpm = bpm_estimate // 2
    best_offset = 0
    tests = [bpm_estimate + r for r in range(-50, 50)]
    swingtests = [bpm_estimate + r*2/3 for r in range(-50, 50)]
    for bpm in tests:
        beat_len = 60 / bpm
        score, offset = score_match(times, beat_len, score_boost=0.05)
        if score > best_score:
            best_score = score
            best_bpm = bpm // 2 if bpm % 2 == 0 else bpm / 2
            best_offset = offset
    for bpm in swingtests:
        beat_len = 60 / bpm
        score, offset = score_match(times, beat_len, score_boost=0)
        if score > best_score:
            best_score = score
            best_bpm = bpm
            best_offset = offset
    if best_bpm < 100:
        best_bpm *= 2
    test = score_match([t - best_offset for t in times], 60 / best_bpm)
    return best_bpm, round(best_offset, 3) 
        
def score_match(times, beat_len, score_boost=0, index=0):
    precision = 0.03
    time = times[index]
    matches = []
    for i in range(index + 1, len(times)):
        while time < times[i]:
            time += beat_len
        dist = min(time - times[i], times[i] - (time - beat_len))
        if dist < precision:
            matches.append(dist * (1 if time - times[i] < precision else -1))           

    if len(matches) == 0: return 0, 0
    offset = times[index] + statistics.median(matches)
    while offset > beat_len: offset -= beat_len
    return len(matches) * (beat_len + score_boost), offset

def play_onsets(musicpath, frames):
    times = librosa.frames_to_time(frames)
    pygame.init()
    pygame.mixer.music.load(musicpath)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()
    i = 0
    click = pygame.mixer.Sound('click.wav')
    while i < len(times):
        if pygame.mixer.music.get_pos() / 1000 > times[i]:
            print(pygame.mixer.music.get_pos() / 1000)
            pygame.mixer.Channel(0).play(click)
            i += 1
            if i < len(times):
                sleep((times[i] - times[i-1]) * 0.99)

def play_beat(musicpath, bpm, offset):
    beat_length = 60 / bpm
    pygame.init()
    pygame.mixer.music.load(musicpath)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()
    time = offset
    i = 0
    click = pygame.mixer.Sound('click.wav')
    while pygame.mixer.music.get_busy():
        if pygame.mixer.music.get_pos() / 1000 > time:
            print(pygame.mixer.music.get_pos() / 1000)
            pygame.mixer.Channel(0).play(click)
            i += 1
            time = offset + beat_length * i
            sleep(beat_length * 0.99)

def run_tests():
    answers = {'24-7.mp3': 200, 'Afterglow.mp3': 250, 'Anniversary.mp3': 150,
            'bat.ogg': 230, 'catswing.ogg': 260, 'Counting Down.mp3': 110, 'Essence.mp3': 45,
            'darkzone.ogg': 200, 'fromnowon.ogg': 265, 'In conclusion.mp3': 180, 'White.mp3': 180,
            'third.ogg': 340, 'tvtime.ogg': 148, 'tvworld.ogg': 145}
    for song, target in answers.items():
        if not os.path.exists(song): continue
        bpm, offset = find_bpm(song)
        if bpm != target and bpm * 2 != target and bpm / 2 != target:
            print("FAILED!", song, ' BPM was', bpm, '- target', target)
            play_beat(song, bpm, offset)
            return
    print('ALL TESTS PASSED!')

def main():
    path = 'White.mp3'
    #path = 'darkzone.ogg'
    #path = 'Anniversary.mp3'
    #path = 'Counting Down.mp3'
    #path = 'Anniversary.mp3'
    bpm, offset = find_bpm(path)
    print(bpm, offset)
    play_beat(path, bpm, offset)

#run_tests()
main()
