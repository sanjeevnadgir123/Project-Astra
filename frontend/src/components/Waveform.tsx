import React from 'react';
import { motion } from 'framer-motion';

interface WaveformProps {
  status: string; // "SLEEPING", "ACTIVE", "LISTENING", "PROCESSING"
}

export const Waveform: React.FC<WaveformProps> = ({ status }) => {
  const isListening = status === "LISTENING";
  const isProcessing = status === "PROCESSING";
  const isActive = status === "ACTIVE";

  const barCount = 36;

  return (
    <div className="flex items-center justify-center gap-[3px] h-10 px-4 bg-black/60 border border-hud-cyan/20 rounded shadow-[inset_0_0_10px_rgba(0,229,255,0.1)] overflow-hidden">
      {Array.from({ length: barCount }).map((_, idx) => {
        // Create an envelope curve (tapered towards edges)
        const centerOffset = Math.abs(idx - barCount / 2);
        const maxAmplitude = Math.max(4, 28 - centerOffset * 1.2);
        
        let duration = 0.7 + (idx % 5) * 0.12;
        let animate = {};
        
        if (isListening) {
          animate = {
            height: [3, maxAmplitude, 3],
          };
        } else if (isProcessing) {
          animate = {
            height: [3, maxAmplitude * 0.4, 3],
          };
          duration = 0.4 + (idx % 3) * 0.08;
        } else if (isActive) {
          animate = {
            height: [3, maxAmplitude * 0.2, 3],
          };
          duration = 1.0 + (idx % 6) * 0.15;
        } else {
          // Flat sleeping line
          animate = {
            height: [3, 3, 3]
          };
        }

        return (
          <motion.div
            key={idx}
            className={`w-[3px] rounded-full transition-colors ${
              isListening 
                ? 'bg-hud-green shadow-[0_0_6px_rgba(0,255,102,0.8)]' 
                : isProcessing 
                  ? 'bg-hud-yellow shadow-[0_0_6px_rgba(255,204,0,0.8)]' 
                  : 'bg-hud-cyan shadow-[0_0_6px_rgba(0,229,255,0.6)]'
            }`}
            animate={animate}
            transition={{
              repeat: Infinity,
              duration: duration,
              ease: "easeInOut",
              delay: (idx * 0.015)
            }}
            style={{ height: '3px' }}
          />
        );
      })}
    </div>
  );
};
export default Waveform;
