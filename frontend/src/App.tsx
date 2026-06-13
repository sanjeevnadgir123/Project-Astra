import React, { useState, useEffect, useRef } from 'react';
import { 
  HardDrive, 
  Network, 
  Terminal, 
  ShieldAlert, 
  Settings, 
  Activity, 
  Layers, 
  Folder, 
  Trash2,
  MessageSquare,
  FileCode,
  CheckCircle,
  Clock,
  Globe,
  Video,
  Power
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';
import CorePanel from './components/CorePanel';
import Waveform from './components/Waveform';

// Interface definitions for WebSocket payloads
interface MetricHistory {
  cpu: number;
  ram: number;
  disk: number;
  time: string;
}

interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
}

interface DriveInfo {
  device: string;
  mountpoint: string;
  fstype: string;
  total_gb: number;
  used_gb: number;
  free_gb: number;
  percent: number;
}

interface AstraStateInfo {
  voice_status: string;
  last_transcript: string;
  last_response: string;
  face_status: string;
  two_claps_detected: boolean;
}

interface SystemEvent {
  time: string;
  type: string;
  message: string;
}

interface StorageInfo {
  is_scanning: boolean;
  total_files: number;
  junk_count: number;
  junk_size_mb: number;
  drives: DriveInfo[];
  largest_files: { path: string; size_gb: number }[];
}

export default function App() {
  // Websocket status
  const [connected, setConnected] = useState(false);
  
  // Real-time metric history (last 15 entries)
  const [history, setHistory] = useState<MetricHistory[]>([]);
  
  // App state managers
  const [metrics, setMetrics] = useState({ cpu: 0, ram: 0, disk: 0, uptime: "0h 0m 0s" });
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [astraState, setAstraState] = useState<AstraStateInfo>({
    voice_status: "SLEEPING",
    last_transcript: "",
    last_response: "",
    face_status: "UNKNOWN",
    two_claps_detected: false
  });
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [storage, setStorage] = useState<StorageInfo>({
    is_scanning: false,
    total_files: 0,
    junk_count: 0,
    junk_size_mb: 0.0,
    drives: [],
    largest_files: []
  });

  // Manual typing command terminal console state
  const [consoleInput, setConsoleInput] = useState("");
  const [consoleLogs, setConsoleLogs] = useState<string[]>([
    "ASTRA v1.0.0 Online & Ready.",
    "System Operational: All systems nominal.",
    "Say 'Jarvis' or double clap to activate."
  ]);
  const consoleBottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll the terminal logs to the bottom
  useEffect(() => {
    if (consoleBottomRef.current) {
      consoleBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [consoleLogs]);

  // System Time State
  const [currentTime, setCurrentTime] = useState("");
  const [currentDate, setCurrentDate] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setCurrentTime(d.toLocaleTimeString('en-US', { hour12: true }));
      setCurrentDate(d.toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Format uptime from seconds
  const formatUptime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours}h ${minutes}m ${seconds}s`;
  };

  // Connect to FastAPI WebSockets
  useEffect(() => {
    let ws: WebSocket;
    let reconnectInterval: any;

    const connect = () => {
      const wsUrl = `ws://localhost:8000/api/ws`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        console.log("WebSocket connected to ASTRA backend.");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setMetrics({
            cpu: Math.round(data.metrics.cpu_percent),
            ram: Math.round(data.metrics.ram_percent),
            disk: Math.round(data.metrics.disk_percent),
            uptime: formatUptime(data.metrics.uptime_sec)
          });

          setProcesses(data.processes || []);
          setAstraState(data.astra || {});
          setEvents(data.events || []);
          setStorage(data.storage || {});

          setHistory(prev => {
            const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
            const nextHistory = [...prev, {
              cpu: Math.round(data.metrics.cpu_percent),
              ram: Math.round(data.metrics.ram_percent),
              disk: Math.round(data.metrics.disk_percent),
              time: timeStr
            }];
            return nextHistory.slice(-15);
          });
        } catch (e) {
          console.error("Error parsing WS payload:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectInterval = setTimeout(() => {
          connect();
        }, 3000);
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectInterval) clearTimeout(reconnectInterval);
    };
  }, []);

  // Update Console Logs based on ASTRA spoken/listening changes
  useEffect(() => {
    if (astraState.last_transcript) {
      setConsoleLogs(prev => [...prev, `You: ${astraState.last_transcript}`]);
    }
  }, [astraState.last_transcript]);

  useEffect(() => {
    if (astraState.last_response) {
      setConsoleLogs(prev => [...prev, `Jarvis: ${astraState.last_response} [SUCCESS]`]);
    }
  }, [astraState.last_response]);

  // Execute quick action via HTTP post/get requests
  const runQuickAction = async (commandStr: string, actionLabel: string) => {
    try {
      setConsoleLogs(prev => [...prev, `You: Triggered quick command - ${actionLabel}`]);
      
      const response = await fetch("http://localhost:8000/api/command", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ command: commandStr })
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setConsoleLogs(prev => [...prev, `Jarvis: ${data.reply} [SUCCESS]`]);
      } else {
        setConsoleLogs(prev => [...prev, `Jarvis: ${data.reply} [WARNING]`]);
      }
    } catch (e) {
      setConsoleLogs(prev => [...prev, `Jarvis: Connection to backend failed for - '${actionLabel}' [ERROR]`]);
    }
  };

  // Trigger manual terminal commands
  const handleConsoleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consoleInput.trim()) return;

    const command = consoleInput.trim();
    setConsoleLogs(prev => [...prev, `You: ${command}`]);
    setConsoleInput("");

    try {
      setConsoleLogs(prev => [...prev, `Jarvis: Executing command '${command}'...`]);
      const response = await fetch("http://localhost:8000/api/command", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ command })
      });
      const data = await response.json();
      
      if (data.status === "success") {
        setConsoleLogs(prev => [...prev, `Jarvis: ${data.reply} [SUCCESS]`]);
      } else {
        setConsoleLogs(prev => [...prev, `Jarvis: ${data.reply} [ERROR]`]);
      }
    } catch (err) {
      setConsoleLogs(prev => [...prev, `Jarvis: Failed to communicate command. [ERROR]`]);
    }
  };

  return (
    <div className="relative min-h-screen text-[#E2E8F0] p-4 flex flex-col font-inter bg-black/30 overflow-x-hidden">
      {/* HUD Scanline Overlay */}
      <div className="scanlines" />
      {/* 1. Header System Panel */}
      <header className="flex flex-col md:flex-row items-center justify-between hud-panel px-6 py-3 mb-4 border-b border-hud-cyan/30">
        {/* Header Left (Logo & Status) */}
        <div className="flex items-center gap-4 mb-2 md:mb-0">
          <div className="relative flex items-center justify-center">
            <div className="absolute w-5 h-5 bg-hud-cyan/20 rounded-full border border-hud-cyan animate-ping" />
            <div className="w-3 h-3 bg-hud-cyan rounded-full border border-hud-cyan shadow-neon-cyan" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-orbitron font-extrabold text-xl tracking-wider text-glow-cyan text-hud-cyan">ASTRA</h1>
              <span className="text-[9px] font-orbitron px-1.5 py-0.5 rounded bg-hud-cyan/10 border border-hud-cyan/20 text-hud-cyan">v1.0.0</span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-hud-green animate-pulse shadow-[0_0_6px_#00FF66]' : 'bg-hud-red shadow-[0_0_6px_#FF355E]'}`} />
              <span className={`text-[10px] font-orbitron font-medium tracking-wide ${connected ? 'text-hud-green text-glow-green' : 'text-hud-red'}`}>
                {connected ? "SYSTEM ONLINE & NOMINAL" : "CONNECTION OFFLINE"}
              </span>
            </div>
          </div>
        </div>

        {/* Header Center (HUD Date/Time) */}
        <div className="text-center mb-2 md:mb-0 flex flex-col items-center">
          <h2 className="text-glow-cyan font-orbitron font-medium text-xs tracking-[0.25em] text-hud-cyan/80">SYSTEM HUD MONITOR</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-orbitron text-base font-bold text-white tracking-widest">{currentTime}</span>
            <span className="text-hud-blue/50">|</span>
            <span className="font-orbitron text-[10px] text-hud-cyan/60 tracking-wider uppercase">{currentDate}</span>
          </div>
        </div>

        {/* Header Right (Voice Status) */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-[9px] font-orbitron text-hud-blue/60 tracking-wider">VOICE ASSISTANT</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-[11px] font-orbitron font-bold uppercase tracking-wider ${
                astraState.voice_status === "LISTENING" 
                  ? 'text-hud-green text-glow-green' 
                  : astraState.voice_status === "PROCESSING" 
                    ? 'text-hud-yellow' 
                    : 'text-hud-cyan'
              }`}>
                {astraState.voice_status}
              </span>
            </div>
          </div>
          <Waveform status={astraState.voice_status} />
        </div>
      </header>

      {/* 2. Main Dashboard Grid Layout */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* COLUMN LEFT (Width: 3/12) */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {/* Section: System Overview */}
          <section className="hud-panel p-4 flex-1 flex flex-col min-h-[200px]">
            <div className="flex items-center justify-between border-b border-hud-blue/20 pb-2 mb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-hud-cyan" />
                <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">SYSTEM OVERVIEW</h3>
              </div>
              <Clock className="w-3.5 h-3.5 text-hud-cyan/40" />
            </div>

            <div className="grid grid-cols-12 gap-2 flex-1 items-center">
              <div className="col-span-7 space-y-2.5 text-[11px]">
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">OPERATING SYSTEM</span>
                  <span className="font-orbitron font-medium text-white">Windows 11 Pro 64-bit</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">PROCESSOR SPEC</span>
                  <span className="font-orbitron font-medium text-white">Intel Core i7-10750H</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">TOTAL RAM</span>
                  <span className="font-orbitron font-medium text-white">16 GB DDR4 Dual-Channel</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">SYSTEM UPTIME</span>
                  <span className="font-orbitron font-medium text-hud-cyan text-glow-cyan">{metrics.uptime}</span>
                </div>
              </div>
              <div className="col-span-5 flex items-center justify-center">
                <div className="relative w-24 h-24 rounded-full border border-hud-cyan/20 flex items-center justify-center">
                  <div className="absolute w-[80%] h-[80%] rounded-full border border-dashed border-hud-cyan/40 animate-spin-slow" />
                  <div className="absolute w-[60%] h-[60%] rounded-full border border-dotted border-hud-blue/50 animate-spin-reverse-slow" />
                  <div className="w-3 h-3 bg-hud-cyan/30 rounded-full animate-ping" />
                  <div className="absolute w-2 h-2 bg-hud-cyan rounded-full shadow-neon-cyan" />
                </div>
              </div>
            </div>
          </section>

          {/* Section: Drives Overview */}
          <section className="hud-panel p-4 flex-1 flex flex-col">
            <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-3">
              <HardDrive className="w-4 h-4 text-hud-cyan" />
              <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">DRIVES OVERVIEW</h3>
            </div>

            <div className="space-y-3 flex-1 overflow-y-auto max-h-[220px] pr-1">
              {storage.drives && storage.drives.length > 0 ? (
                storage.drives.map((drive, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-orbitron font-bold text-white flex items-center gap-1.5">
                        <HardDrive className="w-3 h-3 text-hud-blue" />
                        {drive.device} ({drive.fstype})
                      </span>
                      <span className="text-hud-cyan/70 font-orbitron">{drive.free_gb} GB free of {drive.total_gb} GB</span>
                    </div>
                    <div className="w-full bg-black/40 border border-hud-blue/20 h-2.5 rounded-full overflow-hidden relative">
                      <div 
                        className={`h-full bg-gradient-to-r from-hud-blue to-hud-cyan rounded-full transition-all duration-500`}
                        style={{ width: `${drive.percent}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="space-y-3">
                  {[
                    { label: "C:\\ (SSD)", free: "237 GB", total: "476 GB", pct: 50 },
                    { label: "D:\\ (HDD)", free: "512 GB", total: "931 GB", pct: 45 }
                  ].map((mock, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-orbitron font-bold text-white flex items-center gap-1.5">
                          <HardDrive className="w-3 h-3 text-hud-blue" />
                          {mock.label}
                        </span>
                        <span className="text-hud-cyan/70 font-orbitron">{mock.free} free of {mock.total}</span>
                      </div>
                      <div className="w-full bg-black/40 border border-hud-blue/20 h-2 rounded overflow-hidden">
                        <div className="h-full bg-hud-cyan rounded" style={{ width: `${mock.pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Section: Network Status */}
          <section className="hud-panel p-4 flex-1 flex flex-col">
            <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-3">
              <Network className="w-4 h-4 text-hud-cyan" />
              <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">NETWORK STATUS</h3>
            </div>

            <div className="grid grid-cols-2 gap-4 flex-1 items-center text-[11px]">
              <div className="space-y-3">
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">CONNECTIVITY</span>
                  <span className="font-orbitron font-semibold text-hud-green text-glow-green">CONNECTED</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">LOCAL IP</span>
                  <span className="font-orbitron font-medium text-white">192.168.1.105</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">GATEWAY</span>
                  <span className="font-orbitron font-medium text-white">192.168.1.1</span>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">DOWNLOAD SPEED</span>
                  <span className="font-orbitron font-semibold text-hud-cyan text-glow-cyan">125.6 Mbps</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">UPLOAD SPEED</span>
                  <span className="font-orbitron font-semibold text-hud-blue">42.3 Mbps</span>
                </div>
                <div>
                  <span className="text-hud-blue/60 uppercase block text-[9px]">LATENCY</span>
                  <span className="font-orbitron font-medium text-white">8 ms</span>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* COLUMN MIDDLE (Width: 6/12) */}
        <div className="lg:col-span-6 flex flex-col gap-4">
          {/* Main Circular AI Core & Activation Center */}
          <div className="hud-panel p-4 flex flex-col items-center justify-center flex-1 min-h-[300px]">
            <CorePanel status={astraState.voice_status} faceStatus={astraState.face_status} />
            
            <div className="mt-4 flex flex-col items-center text-center">
              <span className={`text-[10px] font-orbitron px-3 py-1 rounded border ${
                astraState.two_claps_detected 
                  ? 'bg-hud-green/10 border-hud-green/30 text-hud-green text-glow-green'
                  : 'bg-hud-cyan/10 border-hud-cyan/25 text-hud-cyan text-glow-cyan'
              } uppercase tracking-widest`}>
                {astraState.two_claps_detected ? "DOUBLE CLAP TRIGGER DETECTED" : "CLAP TRIGGER MONITOR ACTIVE"}
              </span>
              <p className="text-[10px] text-hud-blue/50 mt-1 font-orbitron">Say "Jarvis" or double clap to verify & command ASTRA</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Processes Panel */}
            <section className="hud-panel p-4 min-h-[220px] flex flex-col">
              <div className="flex items-center justify-between border-b border-hud-blue/20 pb-2 mb-2">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-hud-cyan" />
                  <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">TOP PROCESSES</h3>
                </div>
              </div>

              <div className="flex-1 overflow-x-auto">
                <table className="w-full text-left text-[10px] font-orbitron border-collapse">
                  <thead>
                    <tr className="text-hud-blue/60 border-b border-hud-blue/10">
                      <th className="py-1 uppercase">PROCESS</th>
                      <th className="py-1 text-right uppercase">CPU</th>
                      <th className="py-1 text-right uppercase">RAM</th>
                      <th className="py-1 text-right uppercase">STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {processes && processes.length > 0 ? (
                      processes.slice(0, 6).map((proc, idx) => (
                        <tr key={idx} className="border-b border-hud-blue/5 text-white/90 hover:bg-hud-blue/5">
                          <td className="py-1 truncate max-w-[90px] font-semibold text-glow-cyan/20">{proc.name}</td>
                          <td className="py-1 text-right text-hud-cyan">{(proc.cpu_percent || 0).toFixed(1)}%</td>
                          <td className="py-1 text-right text-hud-blue">{Math.round(proc.memory_percent * 160)} MB</td>
                          <td className="py-1 text-right text-hud-green">Active</td>
                        </tr>
                      ))
                    ) : (
                      [
                        { name: "chrome.exe", cpu: "12.4%", ram: "512 MB" },
                        { name: "Code.exe", cpu: "6.7%", ram: "320 MB" },
                        { name: "Spotify.exe", cpu: "4.1%", ram: "240 MB" },
                        { name: "Discord.exe", cpu: "3.3%", ram: "180 MB" },
                        { name: "explorer.exe", cpu: "2.1%", ram: "150 MB" }
                      ].map((mock, idx) => (
                        <tr key={idx} className="border-b border-hud-blue/5 text-white/90">
                          <td className="py-1 font-semibold text-glow-cyan/20">{mock.name}</td>
                          <td className="py-1 text-right text-hud-cyan">{mock.cpu}</td>
                          <td className="py-1 text-right text-hud-blue">{mock.ram}</td>
                          <td className="py-1 text-right text-hud-green">Active</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Drive Contents Summary */}
            <section className="hud-panel p-4 min-h-[220px] flex flex-col">
              <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-3">
                <HardDrive className="w-4 h-4 text-hud-cyan" />
                <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">DRIVE CONTENTS SUMMARY</h3>
              </div>

              <div className="grid grid-cols-12 gap-3 flex-1 items-center">
                <div className="col-span-7 space-y-2.5 text-[9px] font-orbitron">
                  <div className="flex items-center justify-between text-white border-b border-hud-blue/10 pb-0.5">
                    <span className="flex items-center gap-1 font-semibold"><Folder className="w-3 h-3 text-hud-cyan" /> C:\ (SSD)</span>
                    <span className="text-hud-cyan">{storage.total_files ? storage.total_files.toLocaleString() : "215,672"} Files</span>
                  </div>
                  <div className="flex items-center justify-between text-white border-b border-hud-blue/10 pb-0.5">
                    <span className="flex items-center gap-1 font-semibold"><Folder className="w-3 h-3 text-hud-blue" /> D:\ (HDD)</span>
                    <span className="text-hud-blue">125,431 Files</span>
                  </div>
                  <div className="flex items-center justify-between text-white border-b border-hud-blue/10 pb-0.5">
                    <span className="flex items-center gap-1 font-semibold"><Folder className="w-3 h-3 text-hud-blue" /> E:\ (CD-ROM)</span>
                    <span className="text-hud-blue">15 Tracks</span>
                  </div>
                  <div className="flex items-center justify-between text-white border-b border-hud-blue/10 pb-0.5">
                    <span className="flex items-center gap-1 font-semibold"><Folder className="w-3 h-3 text-hud-cyan" /> F:\ (USB)</span>
                    <span className="text-hud-cyan">8,532 Files</span>
                  </div>
                </div>

                <div className="col-span-5 flex flex-col items-center justify-center text-center">
                  <div className="relative w-20 h-20 rounded-full border border-hud-cyan/20 flex flex-col items-center justify-center bg-black/40">
                    <svg className="absolute w-full h-full transform -rotate-90">
                      <circle cx="40" cy="40" r="34" className="stroke-hud-blue/10 fill-none" strokeWidth="5" />
                      <circle 
                        cx="40" 
                        cy="40" 
                        r="34" 
                        className="stroke-hud-cyan fill-none transition-all duration-500" 
                        strokeWidth="5" 
                        strokeDasharray={213} 
                        strokeDashoffset={213 * (1 - 0.65)}
                      />
                    </svg>
                    <span className="font-orbitron font-extrabold text-sm text-glow-cyan text-hud-cyan">463 GB</span>
                    <span className="text-[8px] font-orbitron uppercase text-hud-blue/60 mt-0.5">USED</span>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* COLUMN RIGHT (Width: 3/12) */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {/* Section: Performance Monitor */}
          <section className="hud-panel p-4 flex-1 flex flex-col">
            <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-3">
              <Activity className="w-4 h-4 text-hud-cyan" />
              <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">PERFORMANCE MONITOR</h3>
            </div>

            <div className="flex-1 min-h-[140px] flex flex-col gap-3 justify-center">
              {/* CPU Live Meter */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[10px] font-orbitron">
                  <span className="text-white">CPU USAGE</span>
                  <span className="text-hud-cyan text-glow-cyan">{metrics.cpu}%</span>
                </div>
                <div className="h-10 w-full bg-black/40 border border-hud-blue/10 rounded overflow-hidden">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#00E5FF" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="cpu" stroke="#00E5FF" strokeWidth={1} fillOpacity={1} fill="url(#colorCpu)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* RAM Live Meter */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[10px] font-orbitron">
                  <span className="text-white">RAM USAGE</span>
                  <span className="text-hud-cyan text-glow-cyan">{metrics.ram}%</span>
                </div>
                <div className="h-10 w-full bg-black/40 border border-hud-blue/10 rounded overflow-hidden">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0088FF" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#0088FF" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="ram" stroke="#0088FF" strokeWidth={1} fillOpacity={1} fill="url(#colorRam)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </section>

          {/* Section: Unwanted/Waste Files */}
          <section className="hud-panel p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between border-b border-hud-blue/20 pb-2 mb-3">
              <div className="flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-hud-red" />
                <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-red">UNWANTED / WASTE FILES</h3>
              </div>
            </div>

            <div className="space-y-2.5 flex-1 text-[10px] font-orbitron">
              <div className="flex items-center justify-between border-b border-hud-blue/5 pb-1">
                <span className="text-white/80">Temp Files</span>
                <span className="text-hud-cyan">{storage.junk_size_mb ? `${(storage.junk_size_mb * 0.4).toFixed(2)} MB` : "2.34 GB"}</span>
              </div>
              <div className="flex items-center justify-between border-b border-hud-blue/5 pb-1">
                <span className="text-white/80">Cache Files</span>
                <span className="text-hud-cyan">{storage.junk_size_mb ? `${(storage.junk_size_mb * 0.2).toFixed(2)} MB` : "1.12 GB"}</span>
              </div>
              <div className="flex items-center justify-between border-b border-hud-blue/5 pb-1">
                <span className="text-white/80">Prefetch Files</span>
                <span className="text-hud-cyan">512 MB</span>
              </div>
              <div className="flex items-center justify-between border-b border-hud-blue/5 pb-1">
                <span className="text-white/80">Recycle Bin</span>
                <span className="text-hud-cyan">1.08 GB</span>
              </div>
              
              <div className="flex items-center justify-between pt-1 border-t border-hud-red/30">
                <span className="text-hud-red font-bold text-glow-red">TOTAL CLUTTER</span>
                <span className="text-hud-red font-bold text-glow-red text-sm">
                  {storage.junk_size_mb ? `${storage.junk_size_mb.toFixed(2)} MB` : "5.99 GB"}
                </span>
              </div>
            </div>
          </section>

          {/* Section: Activity Logs */}
          <section className="hud-panel p-4 flex-1 flex flex-col max-h-[200px]">
            <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-2">
              <Activity className="w-4 h-4 text-hud-cyan" />
              <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">ACTIVITY LOGS</h3>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 max-h-[140px]">
              {events && events.length > 0 ? (
                events.map((ev, idx) => (
                  <div key={idx} className="text-[9px] font-orbitron flex gap-2">
                    <span className="text-hud-blue/60">{ev.time}</span>
                    <span className={`font-semibold ${
                      ev.type === "SECURITY" ? "text-hud-red" : ev.type === "ASTRA" ? "text-hud-cyan" : "text-white/80"
                    }`}>{ev.message}</span>
                  </div>
                ))
              ) : (
                [
                  { time: "23:45:12", log: "System Boot Initialized" },
                  { time: "23:45:18", log: "Voice Recognition Active" },
                  { time: "23:45:20", log: "User Face Verified: Sanjeev" },
                  { time: "23:45:30", log: "Dashboard Services Connected" }
                ].map((mock, idx) => (
                  <div key={idx} className="text-[9px] font-orbitron flex gap-2">
                    <span className="text-hud-blue/60">{mock.time}</span>
                    <span className="text-white/80">{mock.log}</span>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </main>

      {/* 3. Bottom Row: Security, Quick Actions & Voice Terminal Console */}
      <footer className="grid grid-cols-1 lg:grid-cols-12 gap-4 mt-4 items-stretch">
        {/* Security Overlay / Alerts (Col Span: 3) */}
        <section className="lg:col-span-3 hud-panel p-4 flex flex-col justify-between min-h-[160px] border border-hud-red/20 shadow-[inset_0_0_10px_rgba(255,53,94,0.05)]">
          <div className="flex items-center gap-2 border-b border-hud-red/25 pb-2 mb-2">
            <ShieldAlert className="w-4 h-4 text-hud-red animate-pulse" />
            <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-red">SECURITY LAYER</h3>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-2 text-[11px] font-orbitron">
            <div className="flex items-center justify-between">
              <span className="text-white/80">Authorized User:</span>
              <span className="text-hud-cyan font-semibold text-glow-cyan">Sanjeev</span>
            </div>
            <div className="flex items-center justify-between border-b border-hud-blue/5 pb-1">
              <span className="text-white/80">Face Scanner Status:</span>
              <span className={`font-bold ${
                astraState.face_status === "VERIFIED" 
                  ? 'text-hud-green text-glow-green' 
                  : astraState.face_status === "VERIFYING" 
                    ? 'text-hud-yellow animate-pulse' 
                    : 'text-hud-red'
              }`}>
                {astraState.face_status}
              </span>
            </div>
            
            <div className={`p-2 rounded border text-[9px] ${
              astraState.face_status === "LOCKDOWN"
                ? 'bg-hud-red/10 border-hud-red/30 text-hud-red animate-bounce'
                : 'bg-hud-cyan/10 border-hud-cyan/25 text-hud-cyan'
            }`}>
              {astraState.face_status === "LOCKDOWN" 
                ? "WARNING: SECURITY LOCKDOWN TRIGGERED! UNKNOWN FACE" 
                : astraState.face_status === "VERIFIED" 
                  ? "SYSTEM STATE: SECURE - ALL AUTHENTICATED ACCESS ON"
                  : "SYSTEM STATE: STANDBY - REQUIRES FACE VERIFICATION"
              }
            </div>
          </div>
        </section>

        {/* Jarvis Terminal Command Console (Col Span: 6) */}
        <section className="lg:col-span-6 hud-panel p-4 flex flex-col min-h-[160px] border border-hud-cyan/20">
          <div className="flex items-center gap-2 border-b border-hud-cyan/20 pb-1.5 mb-2">
            <Terminal className="w-4 h-4 text-hud-cyan" />
            <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">ASTRA COMMAND CONSOLE</h3>
          </div>

          <div className="flex-1 overflow-y-auto bg-black/60 border border-hud-blue/20 rounded p-2 text-[10px] font-mono text-hud-green space-y-1 max-h-[85px]">
            {consoleLogs.map((log, idx) => (
              <div key={idx} className="whitespace-pre-wrap leading-relaxed">
                {log.startsWith("You:") ? (
                  <span className="text-white/80">{log}</span>
                ) : log.includes("[ERROR]") ? (
                  <span className="text-hud-red">{log}</span>
                ) : (
                  <span className="text-hud-green text-glow-cyan/10">{log}</span>
                )}
              </div>
            ))}
            <div ref={consoleBottomRef} />
          </div>

          <form onSubmit={handleConsoleSubmit} className="flex gap-2 mt-2">
            <span className="font-mono text-hud-cyan text-sm flex items-center">&gt;&gt;&gt;</span>
            <input
              type="text"
              className="flex-1 bg-black/40 border border-hud-blue/30 rounded px-2.5 py-1 text-[11px] font-mono text-white placeholder-hud-blue/40 focus:outline-none focus:border-hud-cyan"
              placeholder="Enter manual desktop command (e.g. open notepad, open downloads)..."
              value={consoleInput}
              onChange={(e) => setConsoleInput(e.target.value)}
            />
          </form>
        </section>

        {/* Quick Commands (Col Span: 3) */}
        <section className="lg:col-span-3 hud-panel p-4 flex flex-col justify-between min-h-[160px]">
          <div className="flex items-center gap-2 border-b border-hud-blue/20 pb-2 mb-2">
            <Settings className="w-4 h-4 text-hud-cyan" />
            <h3 className="font-orbitron text-xs font-bold tracking-widest text-hud-cyan">QUICK COMMANDS</h3>
          </div>

          <div className="grid grid-cols-3 gap-2 flex-1 items-center">
            <button 
              onClick={() => runQuickAction("open youtube", "YouTube")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-cyan/20 bg-hud-cyan/5 hover:bg-hud-cyan/25 hover:border-hud-cyan text-[9px] font-orbitron font-medium tracking-wide transition-all"
            >
              <Video className="w-3.5 h-3.5 text-hud-red" />
              YouTube
            </button>
            <button 
              onClick={() => runQuickAction("open whatsapp", "WhatsApp")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-cyan/20 bg-hud-cyan/5 hover:bg-hud-cyan/25 hover:border-hud-cyan text-[9px] font-orbitron font-medium tracking-wide transition-all"
            >
              <MessageSquare className="w-3.5 h-3.5 text-hud-green" />
              WhatsApp
            </button>
            <button 
              onClick={() => runQuickAction("open chrome", "Chrome")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-cyan/20 bg-hud-cyan/5 hover:bg-hud-cyan/25 hover:border-hud-cyan text-[9px] font-orbitron font-medium tracking-wide transition-all"
            >
              <Globe className="w-3.5 h-3.5 text-hud-cyan" />
              Chrome
            </button>
            <button 
              onClick={() => runQuickAction("open vs code", "VS Code")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-cyan/20 bg-hud-cyan/5 hover:bg-hud-cyan/25 hover:border-hud-cyan text-[9px] font-orbitron font-medium tracking-wide transition-all"
            >
              <FileCode className="w-3.5 h-3.5 text-hud-blue" />
              VS Code
            </button>
            <button 
              onClick={() => runQuickAction("system cleanup", "Cleanup")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-yellow/20 bg-hud-yellow/5 hover:bg-hud-yellow/25 hover:border-hud-yellow text-[9px] font-orbitron font-medium tracking-wide transition-all text-hud-yellow"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              Clean-up
            </button>
            <button 
              onClick={() => runQuickAction("shutdown pc", "Shutdown")}
              className="flex items-center justify-center gap-1 p-1 rounded border border-hud-red/20 bg-hud-red/5 hover:bg-hud-red/25 hover:border-hud-red text-[9px] font-orbitron font-medium tracking-wide transition-all text-hud-red"
            >
              <Power className="w-3.5 h-3.5" />
              Shutdown
            </button>
          </div>
        </section>
      </footer>
    </div>
  );
}
