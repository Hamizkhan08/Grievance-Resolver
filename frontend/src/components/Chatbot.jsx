import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Send, Bot, X, MessageCircle, Mic, Volume2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import "./Chatbot.css";
import { API_URL as API_BASE_URL } from "../lib/config";

const GREETINGS = {
  en: "Hi! I'm your AI assistant. I can help you with questions about your complaints. Ask me anything! 😊",
  hi: "नमस्ते! मैं आपकी AI सहायक हूँ। मैं आपकी शिकायतों के बारे में प्रश्नों में मदद कर सकती हूँ। कुछ भी पूछें! 😊",
  mr: "नमस्कार! मी तुमची AI सहायक आहे. मी तुमच्या तक्रारींबद्दल प्रश्नांमध्ये मदत करू शकते. काहीही विचारा! 😊",
};

const PLACEHOLDERS = {
  en: "Ask me anything about your complaint...",
  hi: "अपनी शिकायत के बारे में कुछ भी पूछें...",
  mr: "तुमच्या तक्रारीबद्दल काहीही विचारा...",
};

const Chatbot = ({ complaintId = null, citizenEmail = null }) => {
  const { language } = useLanguage(); // Use global language context
  const [isOpen, setIsOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      content: GREETINGS[language],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize Web Speech API
    if (
      typeof window !== "undefined" &&
      ("webkitSpeechRecognition" in window || "SpeechRecognition" in window)
    ) {
      try {
        const SpeechRecognition =
          window.SpeechRecognition || window.webkitSpeechRecognition;
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.maxAlternatives = 1;

        // Set language based on selection
        const langMap = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };
        recognitionRef.current.lang = langMap[language] || "en-IN";

        recognitionRef.current.onresult = (event) => {
          if (event.results.length > 0 && event.results[0].length > 0) {
            const transcript = event.results[0][0].transcript;
            setInput(transcript);
          }
          setIsListening(false);
        };

        recognitionRef.current.onerror = (event) => {
          console.error("Speech recognition error:", event.error);
          setIsListening(false);
          if (event.error === "not-allowed") {
            alert(
              "Microphone permission denied. Please enable microphone access in your browser settings."
            );
          }
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      } catch (error) {
        console.error("Failed to initialize speech recognition:", error);
      }
    }

    // Initialize Text-to-Speech
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      synthRef.current = window.speechSynthesis;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore errors on cleanup
        }
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, [language]);

  useEffect(() => {
    // Update greeting when language changes
    if (messages.length === 1 && messages[0].role === "bot") {
      setMessages([
        {
          role: "bot",
          content: GREETINGS[language],
        },
      ]);
    }
  }, [language]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        setIsListening(true);
        recognitionRef.current.start();
      } catch (error) {
        console.error("Failed to start speech recognition:", error);
        setIsListening(false);
        alert(
          "Voice input is not available. Please check your browser settings and microphone permissions."
        );
      }
    } else if (!recognitionRef.current) {
      alert(
        "Voice input is not supported in your browser. Please use Chrome, Edge, or Safari."
      );
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const speakText = (text) => {
    if (synthRef.current && text) {
      try {
        synthRef.current.cancel(); // Cancel any ongoing speech

        // Clean text for better TTS (remove emojis and special formatting)
        const cleanText = text
          .replace(/📋|📊|🏛️|⏰|💡|😊|✅/g, "") // Remove emojis
          .replace(/\n+/g, ". ") // Replace newlines with periods
          .trim();

        if (!cleanText) return;

        const utterance = new SpeechSynthesisUtterance(cleanText);
        const langMap = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };
        utterance.lang = langMap[language] || "en-IN";
        utterance.rate = 0.9; // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = (error) => {
          console.error("TTS error:", error);
          setIsSpeaking(false);
        };

        synthRef.current.speak(utterance);
      } catch (error) {
        console.error("Failed to speak text:", error);
        setIsSpeaking(false);
      }
    } else if (!synthRef.current) {
      console.warn("Text-to-speech is not supported in your browser");
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/chatbot/query`,
        null,
        {
          params: {
            question: userMessage,
            language: language,
            ...(complaintId && { complaint_id: complaintId }),
            ...(citizenEmail && { citizen_email: citizenEmail }),
          },
        }
      );

      if (response.data.success) {
        const botResponse = response.data.response;
        const complaintInfo = response.data.complaint_info;
        const suggestedActions = response.data.suggested_actions || [];

        let fullResponse = botResponse;

        // Add complaint info if available
        if (complaintInfo) {
          fullResponse += "\n\n";
          if (complaintInfo.id) {
            fullResponse += `📋 Complaint ID: #${complaintInfo.id.slice(
              0,
              8
            )}\n`;
          }
          if (complaintInfo.status) {
            fullResponse += `📊 Status: ${complaintInfo.status
              .replace("_", " ")
              .toUpperCase()}\n`;
          }
          if (complaintInfo.department) {
            fullResponse += `🏛️ Department: ${complaintInfo.department}\n`;
          }
          if (complaintInfo.time_remaining) {
            fullResponse += `⏰ Time Remaining: ${complaintInfo.time_remaining}\n`;
          }
        }

        // Add suggested actions
        if (suggestedActions.length > 0) {
          fullResponse += "\n\n💡 Suggested Actions:\n";
          suggestedActions.forEach((action, idx) => {
            fullResponse += `${idx + 1}. ${action}\n`;
          });
        }

        setMessages((prev) => [
          ...prev,
          { role: "bot", content: fullResponse },
        ]);

        // Auto-speak bot response
        speakText(botResponse);
      } else {
        const errorMsg = {
          en: `Sorry, I encountered an error: ${
            response.data.error || "Unknown error"
          }`,
          hi: `क्षमा करें, मुझे एक त्रुटि मिली: ${
            response.data.error || "अज्ञात त्रुटि"
          }`,
          mr: `माफ करा, मला एक त्रुटी आली: ${
            response.data.error || "अज्ञात त्रुटी"
          }`,
        };
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            content: errorMsg[language] || errorMsg.en,
          },
        ]);
      }
    } catch (err) {
      const errorMsg = {
        en: "Sorry, I'm having trouble connecting. Please try again later.",
        hi: "क्षमा करें, मुझे कनेक्ट करने में समस्या हो रही है। कृपया बाद में पुनः प्रयास करें।",
        mr: "माफ करा, मला कनेक्ट करण्यात समस्या येत आहे. कृपया नंतर पुन्हा प्रयत्न करा.",
      };
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: errorMsg[language] || errorMsg.en,
        },
      ]);
      console.error("Chatbot error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        className="chatbot-toggle"
        onClick={() => setIsOpen(true)}
        aria-label="Open chatbot"
      >
        <MessageCircle size={24} />
        <span>Ask AI</span>
      </button>
    );
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="chatbot-header-content">
          <Bot size={20} />
          <div>
            <h3>AI Assistant</h3>
            <p>Ask me about your complaints</p>
          </div>
        </div>
        <div className="chatbot-header-actions">
          {/* Voice Controls */}
          <div className="voice-controls">
            {isSpeaking ? (
              <button
                className="voice-btn stop"
                onClick={stopSpeaking}
                aria-label="Stop speaking"
                title="Stop speaking"
              >
                <Volume2 size={16} />
              </button>
            ) : (
              <button
                className="voice-btn"
                onClick={() => {
                  const lastBotMessage = [...messages]
                    .reverse()
                    .find((m) => m.role === "bot");
                  if (lastBotMessage) {
                    speakText(lastBotMessage.content);
                  }
                }}
                aria-label="Read last message"
                title="Read last message"
              >
                <Volume2 size={16} />
              </button>
            )}
          </div>

          <button
            className="chatbot-close"
            onClick={() => setIsOpen(false)}
            aria-label="Close chatbot"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      <div className="chatbot-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chatbot-message ${msg.role}`}>
            {msg.role === "bot" && <Bot size={16} className="message-icon" />}
            <div className="message-content">
              {msg.content.split("\n").map((line, lineIdx) => (
                <React.Fragment key={lineIdx}>
                  {line}
                  {lineIdx < msg.content.split("\n").length - 1 && <br />}
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chatbot-message bot">
            <Bot size={16} className="message-icon" />
            <div className="message-content">
              <span className="typing-indicator">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chatbot-input-form" onSubmit={handleSend}>
        <button
          type="button"
          className={`voice-input-btn ${isListening ? "listening" : ""}`}
          onClick={isListening ? stopListening : startListening}
          disabled={loading}
          aria-label={isListening ? "Stop listening" : "Start voice input"}
          title={isListening ? "Stop listening" : "Voice input"}
        >
          <Mic size={18} />
        </button>
        <input
          type="text"
          className="chatbot-input"
          placeholder={PLACEHOLDERS[language]}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="chatbot-send"
          disabled={loading || !input.trim()}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

export default Chatbot;
