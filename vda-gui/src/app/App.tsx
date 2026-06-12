import React, { useState } from 'react';
import { FloatingWidget } from './components/FloatingWidget';
import { SettingsModal } from './components/SettingsModal';
import { ChatPanel } from './components/ChatPanel';
import { motion, AnimatePresence } from 'motion/react';

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Default collapsed
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);

  const handleSendMessage = (text: string) => {
    // Open chat panel if it's closed
    if (!isChatOpen) {
      setIsChatOpen(true);
    }
    
    const newMessages = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    
    // Simulate AI response
    setTimeout(() => {
      setMessages([...newMessages, { 
        role: 'assistant', 
        content: "I'm a simulated AI assistant running locally. Let me know how else I can help you with your workspace!" 
      }]);
    }, 1000);
  };

  return (
    <div className="relative w-full min-h-screen bg-transparent text-white overflow-hidden font-sans pointer-events-none">
      
      {/* 
        The background is transparent to simulate a desktop environment. 
        Only the interactive widgets have pointer-events-auto.
      */}

      {/* Main Draggable Group containing both the FloatingWidget and the ChatPanel */}
      <div className="absolute inset-0 pointer-events-auto overflow-hidden">
        <motion.div
          drag
          dragMomentum={false}
          className="absolute top-20 right-12 z-[60] flex flex-col items-end gap-3"
          style={{ touchAction: "none" }}
        >
          {/* Top Floating Widget */}
          <FloatingWidget 
            onSendMessage={handleSendMessage}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onToggleChat={() => setIsChatOpen(!isChatOpen)}
            isChatOpen={isChatOpen}
          />

          {/* Chat Panel immediately below it */}
          <AnimatePresence>
            {isChatOpen && (
              <ChatPanel 
                messages={messages} 
                isSidebarOpen={isSidebarOpen} 
                setIsSidebarOpen={setIsSidebarOpen} 
                onClose={() => setIsChatOpen(false)}
              />
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Settings Modal Window (Centered overlay, so kept separate from dragging) */}
      <AnimatePresence>
        {isSettingsOpen && (
          <div className="absolute inset-0 pointer-events-auto z-[100]">
            <SettingsModal onClose={() => setIsSettingsOpen(false)} />
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}