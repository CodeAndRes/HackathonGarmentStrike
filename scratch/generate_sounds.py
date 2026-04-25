import wave
import struct
import math
from pathlib import Path

def generate_tone(filename, freq_start, freq_end, duration, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Linear frequency sweep
            freq = freq_start + (freq_end - freq_start) * (i / num_samples)
            value = int(32767.0 * math.sin(2.0 * math.pi * freq * t) * (1.0 - t/duration)) # fade out
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

out_dir = Path("frontend/assets/sounds")
out_dir.mkdir(parents=True, exist_ok=True)

# Hit: High pitched beep
generate_tone(str(out_dir / "hit.wav"), 800, 800, 0.3)

# Miss: Low pitched boop
generate_tone(str(out_dir / "miss.wav"), 200, 100, 0.4)

# Sink: Triumphant sweep up
generate_tone(str(out_dir / "sink.wav"), 400, 1200, 0.6)

print("Sonidos WAV generados con éxito.")
