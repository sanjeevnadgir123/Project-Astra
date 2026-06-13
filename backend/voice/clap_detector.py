import pyaudio
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.ClapDetector")

# Audio stream settings
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def wait_for_claps(threshold_multiplier=3.5, min_threshold=600, debounce_time=0.1, max_interval=0.8, min_interval=0.2, timeout=None):
    """
    Monitors the microphone and blocks until a double clap is detected.
    
    - threshold_multiplier: How many times louder a spike must be compared to ambient noise.
    - min_threshold: Minimum absolute RMS volume to qualify as a clap.
    - debounce_time: Time in seconds to ignore spikes after a clap (prevents echo/ringing triggers).
    - min_interval/max_interval: Time window in seconds between the two claps.
    """
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
    except Exception as e:
        logger.error(f"Failed to open PyAudio input stream: {str(e)}")
        p.terminate()
        return False
        
    logger.info("Clap detector initialized. Listening for double claps...")
    print("Listening for double claps...")
    
    # Track rolling average ambient RMS
    ambient_noise_rms = 100.0
    alpha = 0.95 # Weight of history for moving average
    
    first_clap_time = 0
    
    start_time = time.time()
    try:
        while True:
            if timeout and (time.time() - start_time > timeout):
                break
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            except IOError:
                continue
                
            # Convert audio buffer to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            if len(audio_data) == 0:
                continue
                
            # Calculate Root Mean Square (RMS) as energy level
            rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
            
            # Update ambient noise moving average if it's a quiet/normal chunk
            if rms < ambient_noise_rms * 2.0:
                ambient_noise_rms = alpha * ambient_noise_rms + (1 - alpha) * rms
                
            # Check for a sudden spike (potential clap)
            if rms > min_threshold and rms > ambient_noise_rms * threshold_multiplier:
                current_time = time.time()
                
                # Check if this is the first clap or the second clap
                if first_clap_time == 0:
                    first_clap_time = current_time
                    logger.info("First clap detected!")
                    # Wait briefly to let the sound of the first clap decay
                    time.sleep(debounce_time)
                else:
                    time_difference = current_time - first_clap_time
                    
                    if min_interval <= time_difference <= max_interval:
                        logger.info("Double clap detected! Activating ASTRA...")
                        print("\n[CLAP TRIGGER] Double clap detected!")
                        # Success! Clean up and return
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        return True
                    elif time_difference > max_interval:
                        # Too much time passed, treat this as the new first clap
                        logger.info("Interval exceeded. Treating this as a new first clap.")
                        first_clap_time = current_time
                        time.sleep(debounce_time)
                    else:
                        # Too close to the first clap (could be echo or single clap decay)
                        pass
                        
            # Prevent CPU hogging
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        logger.info("Clap detector stopped by user.")
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()
        
    return False

if __name__ == "__main__":
    print("Testing clap detection...")
    wait_for_claps()
