import React from 'react';
import { motion } from 'framer-motion';

interface CorePanelProps {
  status: string; // "SLEEPING", "ACTIVE", "LISTENING", "PROCESSING"
  faceStatus: string; // "UNKNOWN", "VERIFYING", "VERIFIED", "LOCKDOWN"
}

export const CorePanel: React.FC<CorePanelProps> = ({ status, faceStatus }) => {
  const isListening = status === "LISTENING";
  const isProcessing = status === "PROCESSING";
  const isLockdown = faceStatus === "LOCKDOWN";
  
  let ringColor = "border-hud-cyan/50 shadow-[0_0_15px_rgba(0,229,255,0.3)]";
  let labelColor = "text-hud-cyan drop-shadow-[0_0_6px_rgba(0,229,255,0.8)]";
  let pulseColor = "rgba(0, 229, 255, 0.15)";
  let coreText = "JARVIS";
  let statusText = "AI ONLINE";
  
  if (isListening) {
    ringColor = "border-hud-green/60 shadow-[0_0_15px_rgba(0,255,102,0.4)]";
    labelColor = "text-hud-green drop-shadow-[0_0_6px_rgba(0,255,102,0.8)]";
    pulseColor = "rgba(0, 255, 102, 0.2)";
    statusText = "LISTENING";
  } else if (isProcessing) {
    ringColor = "border-hud-yellow/60 shadow-[0_0_15px_rgba(255,204,0,0.4)]";
    labelColor = "text-hud-yellow drop-shadow-[0_0_6px_rgba(255,204,0,0.8)]";
    pulseColor = "rgba(255, 204, 0, 0.2)";
    statusText = "THINKING";
  } else if (isLockdown) {
    ringColor = "border-hud-red/60 shadow-[0_0_15px_rgba(255,53,94,0.4)]";
    labelColor = "text-hud-red drop-shadow-[0_0_6px_rgba(255,53,94,0.8)]";
    pulseColor = "rgba(255, 53, 94, 0.2)";
    coreText = "LOCKDOWN";
    statusText = "ACCESS DENIED";
  }

  return (
    <div className="relative w-48 h-48 flex items-center justify-center select-none">
      {/* Outer pulsing ring shadow */}
      <motion.div
        className="absolute inset-0 rounded-full border border-hud-cyan/10"
        animate={{
          scale: [0.96, 1.04, 0.96],
          opacity: [0.6, 1, 0.6],
        }}
        transition={{
          repeat: Infinity,
          duration: 2.5,
          ease: "easeInOut"
        }}
        style={{
          boxShadow: `inset 0 0 20px ${pulseColor}, 0 0 20px ${pulseColor}`
        }}
      />

      {/* Rotating Outer Ring (Clockwise) */}
      <motion.div
        className={`absolute w-[92%] h-[92%] rounded-full border-2 border-dashed ${ringColor}`}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 25, ease: "linear" }}
      />

      {/* Rotating Middle Ring (Counter-Clockwise) */}
      <motion.div
        className={`absolute w-[80%] h-[80%] rounded-full border border-dotted ${ringColor} opacity-70`}
        animate={{ rotate: -360 }}
        transition={{ repeat: Infinity, duration: 18, ease: "linear" }}
      />

      {/* Solid Tech Ring with notch */}
      <div className="absolute w-[66%] h-[66%] rounded-full border border-hud-cyan/20 flex items-center justify-center">
        <div className="w-[88%] h-[88%] rounded-full border border-hud-cyan/10 bg-black/60 shadow-inner" />
      </div>

      {/* Center AI Text and Status */}
      <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none">
        <span className="text-[9px] uppercase font-orbitron tracking-widest text-hud-cyan/50 mb-0.5">
          {isLockdown ? "SECURITY" : "ASTRA CORE"}
        </span>
        
        <h1 className={`text-lg font-bold font-orbitron tracking-wider ${labelColor}`}>
          {coreText}
        </h1>
        
        <motion.span 
          className={`text-[9px] font-orbitron font-semibold tracking-wide ${
            isLockdown 
              ? 'text-hud-red' 
              : isListening 
                ? 'text-hud-green' 
                : isProcessing 
                  ? 'text-hud-yellow' 
                  : 'text-hud-cyan'
          }`}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
        >
          {statusText}
        </motion.span>
      </div>

      {/* Glowing center micro-orb */}
      <div className={`absolute w-2 h-2 rounded-full ${
        isLockdown 
          ? 'bg-hud-red shadow-[0_0_10px_#FF355E]' 
          : isListening 
            ? 'bg-hud-green shadow-[0_0_10px_#00FF66]' 
            : 'bg-hud-cyan shadow-[0_0_10px_#00E5FF]'
      } opacity-75`} />
    </div>
  );
};
export default CorePanel;
