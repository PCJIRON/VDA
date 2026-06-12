import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Settings, Mic, Eye, Crop, ArrowUp, Sparkles, GripVertical } from 'lucide-react';

interface FloatingWidgetProps {
  onSendMessage: (msg: string) => void;
  onOpenSettings: () => void;
  onToggleChat: () => void;
  isChatOpen: boolean;
}

export function FloatingWidget({ onSendMessage, onOpenSettings, onToggleChat, isChatOpen }: FloatingWidgetProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const isExpanded = isHovered || isFocused;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue("");
      setIsFocused(false);
      inputRef.current?.blur();
    }
  };

  return (
    <motion.div 
      className="relative z-[60] flex items-center shadow-2xl shadow-black/50 bg-[#1e1e24] text-white border border-neutral-700 overflow-hidden cursor-grab active:cursor-grabbing"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      animate={{
        width: isExpanded ? 460 : 64,
        height: 64,
        borderRadius: 32
      }}
      transition={{ type: "spring", bounce: 0.25, duration: 0.5 }}
    >
      <div className="w-full h-full flex items-center relative">
        <AnimatePresence initial={false}>
          {isExpanded ? (
            <motion.form 
              key="expanded"
              initial={{ opacity: 0, filter: "blur(4px)" }}
              animate={{ opacity: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, filter: "blur(4px)" }}
              transition={{ duration: 0.2, delay: 0.1 }}
              className="absolute inset-0 flex items-center w-full px-2"
              onSubmit={handleSubmit}
            >
              {/* Drag Handle purely for visual cue */}
              <div className="pl-2 text-neutral-500 cursor-grab active:cursor-grabbing">
                <GripVertical size={16} />
              </div>
              <input 
                ref={inputRef}
                type="text" 
                placeholder="Ask anything..." 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                className="flex-1 bg-transparent border-none outline-none pl-2 pr-2 text-[15px] placeholder:text-neutral-500 min-w-0 cursor-text"
                onPointerDownCapture={(e) => e.stopPropagation()} // Allow clicking inside without dragging
              />
              <div 
                className="flex items-center space-x-0.5 text-neutral-400 shrink-0 pr-1"
                onPointerDownCapture={(e) => e.stopPropagation()} // Prevent dragging when clicking buttons
              >
                <button type="button" onClick={onOpenSettings} className="p-2 hover:text-white transition-colors rounded-full hover:bg-neutral-700" title="Settings"><Settings size={18} /></button>
                <button type="button" className="p-2 hover:text-white transition-colors rounded-full hover:bg-neutral-700" title="Voice Input"><Mic size={18} /></button>
                <button type="button" className="p-2 hover:text-white transition-colors rounded-full hover:bg-neutral-700" title="Vision"><Eye size={18} /></button>
                <button type="button" className="p-2 hover:text-white transition-colors rounded-full hover:bg-neutral-700" title="Crop/Screenshot"><Crop size={18} /></button>
                <button 
                  type="submit" 
                  disabled={!inputValue.trim()}
                  className="p-2 bg-white text-black rounded-full hover:bg-neutral-200 ml-1 disabled:opacity-50 disabled:hover:bg-white transition-all"
                >
                  <ArrowUp size={18} />
                </button>
              </div>
            </motion.form>
          ) : (
            <motion.div 
              key="collapsed"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <Sparkles size={24} className="text-white" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}