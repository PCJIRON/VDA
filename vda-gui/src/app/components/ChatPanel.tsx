import React, { useRef, useEffect } from 'react';
import { Plus, MessageSquare, PanelLeftClose, PanelLeftOpen, User, Sparkles, X, GripHorizontal } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ChatPanelProps {
  messages: { role: string; content: string }[];
  isSidebarOpen: boolean;
  setIsSidebarOpen: (val: boolean) => void;
  onClose: () => void;
}

export function ChatPanel({ messages, isSidebarOpen, setIsSidebarOpen, onClose }: ChatPanelProps) {
  const history = [
    "Design system planning",
    "React optimization tips",
    "Floating UI components",
    "Tailwind configuration"
  ];
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10, scale: 0.95 }}
      animate={{ 
        opacity: 1, 
        y: 0, 
        scale: 1, 
        width: isSidebarOpen ? 680 : 460 
      }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
      className="relative z-50 flex h-[500px] max-w-[90vw] max-h-[80vh] bg-[#0f0f11] text-white rounded-2xl shadow-2xl border border-neutral-700/50 overflow-hidden font-sans"
    >
      {/* Sidebar */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div 
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 220, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="flex-shrink-0 bg-[#151518] border-r border-neutral-800/50 overflow-hidden flex flex-col z-10"
          >
            <div 
              className="p-3 flex items-center justify-between mt-2"
              onPointerDownCapture={(e) => e.stopPropagation()} // Prevent dragging when clicking new chat
            >
              <button className="flex items-center gap-2 text-sm font-medium text-neutral-200 hover:bg-neutral-800 p-2 rounded-xl w-full transition-colors border border-neutral-800">
                <Plus size={16} /> New chat
              </button>
            </div>
            <div 
              className="flex-1 overflow-y-auto px-2 space-y-0.5 mt-2"
              onPointerDownCapture={(e) => e.stopPropagation()} // Prevent dragging when scrolling/clicking history
            >
              <div className="px-2 py-2 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">History</div>
              {history.map((title, i) => (
                <button key={i} className="flex items-center gap-3 w-full p-2 text-[13px] text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/80 rounded-xl text-left truncate transition-colors">
                  <MessageSquare size={14} className="flex-shrink-0" />
                  <span className="truncate">{title}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full min-w-0">
        {/* Header / Drag Handle */}
        <header className="h-12 flex items-center px-3 shrink-0 relative z-10 border-b border-neutral-800/50 bg-[#0f0f11]/80 backdrop-blur-md cursor-grab active:cursor-grabbing">
          <button 
            onPointerDownCapture={(e) => e.stopPropagation()}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 text-neutral-400 hover:text-white rounded-lg hover:bg-neutral-800 transition-colors"
          >
            {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
          
          <div className="flex-1 flex items-center justify-center pointer-events-none opacity-20">
             <GripHorizontal size={24} />
          </div>

          <div 
            className="flex items-center gap-2"
            onPointerDownCapture={(e) => e.stopPropagation()}
          >
            <span className="px-2 py-0.5 rounded-md bg-neutral-800 text-[10px] text-neutral-400 uppercase font-bold tracking-wider">GPT-4o</span>
            <button 
              onClick={onClose}
              className="p-1.5 text-neutral-400 hover:text-white rounded-lg hover:bg-neutral-800 transition-colors ml-1"
            >
              <X size={18} />
            </button>
          </div>
        </header>

        {/* Messages */}
        <div 
          className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth bg-[#0f0f11]"
          onPointerDownCapture={(e) => e.stopPropagation()} // Prevent dragging when scrolling/selecting messages
        >
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-neutral-500">
              <div className="w-12 h-12 bg-neutral-800 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-black/20">
                <Sparkles className="text-white animate-pulse" size={20} />
              </div>
              <h2 className="text-lg font-medium text-neutral-300 mb-1">New Chat Session</h2>
              <p className="text-sm">Type in the floating bar to begin.</p>
            </div>
          ) : (
            <div className="pb-10 flex flex-col gap-6">
              {messages.map((msg, i) => (
                <motion.div 
                  key={i} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                      msg.role === 'user' ? 'bg-blue-600' : 'bg-neutral-800 border border-neutral-700'
                    }`}>
                      {msg.role === 'user' ? <User size={14} className="text-white" /> : <Sparkles size={14} className="text-neutral-300" />}
                    </div>
                    <div className={`rounded-2xl px-4 py-2.5 text-[14px] leading-relaxed shadow-sm ${
                      msg.role === 'user' 
                        ? 'bg-neutral-800 text-white rounded-tr-sm' 
                        : 'bg-transparent text-neutral-200 border border-neutral-800/60 rounded-tl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}